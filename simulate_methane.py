
import geojson,json
import os
import sys
import schedule
import time
import datetime
from random import randint
import julian

import src.IDW as IDW
import src.make_STA_payload as make_STA_payload
import src.utils as utils
import src.leak_simulator as ls
import src.submit_results as submit_results
import src.error_handler as error_handler
import src.database as db

# find matched time
def find_matched_time(destination_list,time):
    destination_index=destination_list[0].index('Time')
    matched_rows=[]
    for row in destination_list:
        if row[destination_index]==time:
            matched_rows.append(row)
    return matched_rows

# make sensors measurements if they are static
def init_static_sensors(leak_lists,trajectory_list):
    ID_index=0
    first_id=0
    leak_counter=0
    counter=1
    sensor_lists=[]
    sensor_lists.append(trajectory_list[0])
    for leak_list in leak_lists:
        if leak_counter==0:
            ID_index=leak_list.index('ID')
            leak_time_index=leak_list.index('Time')
        elif leak_counter==1:
            first_id=leak_list[ID_index]
                          
        if leak_list[ID_index]==first_id:
            traj_time_index=0
            traj_counter=0
            for row in trajectory_list:
                if traj_counter==0:
                    traj_id_index=row.index('ID')
                    traj_time_index=row.index('Time')
                else:                    
                    sensor_lists.append([ leak_list[leak_time_index] if x==traj_time_index else row[x] for x in range(0, row.__len__()) ])
                    counter+=1
                traj_counter+=1
                
                
        leak_counter+=1
    return sensor_lists

# resample data based on the time
def resample_data(leak_lists,time_index,time_stamp):
    accepted_time=[]
    resampled_list=[]
    resampled_list.append(leak_lists[0])
    resampled_list.append(leak_lists[1])
    for leak_list in leak_lists[1:]:
        utc_time=leak_list[time_index]
        x = time.strptime(utc_time.split('T')[1],'%H:%M:%S.000Z')
        total_seconds = datetime.timedelta(hours=x.tm_hour,minutes=x.tm_min,seconds=x.tm_sec).total_seconds()
        accepted_time.append(total_seconds)
        if total_seconds-accepted_time[0]>=time_stamp-1:
            accepted_time.clear()
            resampled_list.append(leak_list)
    return resampled_list

# build a matrix of the gojson data        
def get_matrix_geojson(path):
    json_object=utils.read_geojson(path)
    output_matrix=[]
    if type(json_object)==dict:
        print('The input geojson file does not have valid form!')
        sys.exit()
    else:
        features=json_object.features
        properties=list(features[0].properties.keys())
        if (not 'longitude') and (not 'Longitude') in properties:
            properties.append('Longitude')
        if (not 'latitude') and (not 'Latitude') in properties:
            properties.append('Latitude')
        output_matrix.append(properties)
        for feature in features:
            longitude=feature.geometry.coordinates[0]
            latitude=feature.geometry.coordinates[1]
            values=list(feature.properties.values())
            values.append(longitude)
            values.append(latitude)
            output_matrix.append(values)
    return output_matrix       
                
known_file=''
unknown_file=''

# loads configs
configs=utils.read_json(os.path.join('data','config.json'))
STA_info=configs['STA']
endpoint=STA_info['STA_endpoint']
user_name=STA_info['user_name']
password=STA_info['password']
sample_rate=configs['sampling_rate']
simulation_rate=configs['post_rate']
simulation_method=configs['simulation_method']
wind_info=configs['wind']
wind_activated=wind_info['wind_activated']
wind_speed=wind_info['wind_speed']
wind_direction=wind_info['wind_direction']
use_case=configs['use_case']
uc_configs={}
is_trajectory=False
is_random=False

# TODO: set program to read use_case configs if we decide that file names and values are the same
if use_case=='known_static':
    uc_configs=utils.read_json(os.path.join('data','known_static.json'))
    known_file=os.path.join('',uc_configs['known_station'])
    unknown_file=os.path.join('',uc_configs['unknown_station'])
elif use_case=='random_static':
    uc_configs=utils.read_json(os.path.join('data','random_static.json'))
    known_file=os.path.join('',uc_configs['known_station'])
    unknown_file=os.path.join('',uc_configs['unknown_station'])
    is_random=True
elif use_case=='known_trajectory':
    uc_configs=utils.read_json(os.path.join('data','known_trajectory.json'))
    known_file=os.path.join('',uc_configs['known_station'])
    unknown_file=os.path.join('',uc_configs['trajectory'])
    is_trajectory=True
else:
    print("Please determine a correct value for your use case")
    sys.exit()

error_handler.handle_wrong_arguments(known_file,unknown_file)
known_filename, known_file_extension = os.path.splitext(known_file)
unknown_filename, unknown_file_extension = os.path.splitext(unknown_file)

trajectory_list=[]
leak_lists=[]

# read trajectories and leaking source files
if known_file_extension=='.csv':
    leak_lists=utils.read_csv(known_file)
elif known_file_extension=='.json':   
    leak_lists=get_matrix_geojson(known_file)
if unknown_file_extension=='.csv':
    trajectory_list=utils.read_csv(unknown_file)
elif unknown_file_extension=='.json':   
    trajectory_list=get_matrix_geojson(unknown_file)   

print('checking requirements of known stations...')
error_handler.check_requirements(leak_lists[0],is_random)
print('checking requirements of trajectories or unknown stations...')
error_handler.check_requirements(trajectory_list[0],is_random)

# initialize variables  
uknown_stations=trajectory_list
sensors_payload=[]
count=0
output_rows=[]
origin_index=0
x_index=0
y_index=0
id_index=0
id_leak=leak_lists[0].index('ID')

# get unique names of known stations
knowns=[i[id_leak] for i in leak_lists]
known_names=utils.unique(knowns[1:])

# initialize local database
(con,curs)=db.open_connection()
db.init(con,curs)
db.clear_cache(con,curs)

# sort leak sources based on the time
if not is_random:
    time_leak=leak_lists[0].index('Time')
    meth_index=leak_lists[0].index('CH4')
    if not (((leak_lists[1][meth_index] is None) or (leak_lists[1][meth_index]=='')) and ((leak_lists[1][time_leak] is None) or (leak_lists[1][time_leak]==''))):
        print('sorting methane records...')
        sorted_lists = sorted(leak_lists[1:], key=lambda x: x[time_leak])
        sorted_lists = sorted(leak_lists[1:], key=lambda x: x[id_leak])
        leak_sorted=[]
        leak_sorted.append(leak_lists[0])
        leak_lists=leak_sorted+sorted_lists

        # resampling data simulation
        if sample_rate>1:
            leak_lists=resample_data(leak_lists,time_leak,sample_rate)
        
        # runs if the unknown stations are static
        if not bool(is_trajectory):
            print('init static sensors')
            trajectory_list=init_static_sensors(leak_lists,trajectory_list)
        # generate csv file rows
        print('calculating simulation values and formatting to STA readable payloads')
        for row in trajectory_list:
            x_block=[]
            y_block=[]
            methane_block=[]
            if count==0:
                id_index=row.index('ID')
                origin_index=row.index('Time')
                y_index=row.index('Latitude')
                x_index=row.index('Longitude')
            else:
                inner_count=0
                matched_rows=[]
                matched_rows=find_matched_time(leak_lists,row[origin_index])
                for leak_list in matched_rows:
                    lat_index=leak_lists[0].index('Latitude')
                    long_index=leak_lists[0].index('Longitude')
                    x_block.append(float(leak_list[long_index]))
                    y_block.append(float(leak_list[lat_index]))
                    methane_block.append(float(leak_list[meth_index]))
                    inner_count+=1
                x=float(row[x_index])
                y=float(row[y_index])
                ch4=IDW.run(x,y,x_block,y_block,methane_block,2,bool(wind_activated),wind_speed,wind_direction)
                output_row={"ID":row[id_index],"time":row[origin_index],"ch4":ch4,"latitude":float(row[y_index]),"longitude":float(row[x_index])}
                formated_time= (row[origin_index])[:-5].replace('T',' ')
                formated_time=datetime.datetime.strptime(formated_time, '%Y-%m-%d %H:%M:%S')
                jul_time=julian.to_jd(formated_time,fmt='jd')
                db.insert_table(con,curs,output_row["ID"],output_row["ch4"],output_row["longitude"],output_row["latitude"],jul_time,"target")
                message=make_STA_payload.get_STA_payload([output_row],simulation_method,known_names,bool(is_trajectory))
                if output_row.__len__()>0:
                    output_rows.append(message)
               
            count+=1
        print('start posting with '+str(simulation_rate)+' seconds time intervals.')
        post_count=0
        while post_count<output_rows.__len__():
            if bool(is_trajectory):
                submit_results.post_single_STA(output_rows,post_count,endpoint,user_name,password)
                post_count+=1
            else:
                submit_results.post_batch_STA(output_rows,post_count,uknown_stations.__len__(),endpoint,user_name,password)
                post_count+=uknown_stations.__len__()
            time.sleep(int(simulation_rate))
else:
    leak_configs=uc_configs['leak_simulator']
    x_block=[]
    y_block=[]
    methane_block=[]
    value_holder=0
    sim_counter=0
    output_rows=[]
    while True:
        for row in trajectory_list[1:]:
            x_block=[]
            y_block=[]
            methane_block=[]
            for leak_list in leak_lists[1:]:
                if leak_configs['method']=='random_walk':
                    conf_indx=utils.get_json_index(leak_configs['random_walk'],'ID',leak_list[id_leak])
                    sim_leak=leak_configs['random_walk'][conf_indx]
                    sim_range=sim_leak['range']
                    sim_step=sim_leak['step']
                    if sim_counter==0:
                        value_holder=randint(sim_range[0],sim_range[1])+0.01*randint(0,100)
                    sim_value=ls.random_walk(value_holder,sim_step,sim_range[0],sim_range[1])
                    value_holder=sim_value
                lat_index=leak_lists[0].index('Latitude')
                long_index=leak_lists[0].index('Longitude')
                x_block.append(float(leak_list[long_index]))
                y_block.append(float(leak_list[lat_index]))
                methane_block.append(sim_value)
            x=float(row[x_index])
            y=float(row[y_index])
            ch4=IDW.run(x,y,x_block,y_block,methane_block,2,bool(wind_activated),wind_speed,wind_direction)
            iso_time=datetime.datetime.now().replace(microsecond=0).isoformat()
            iso_time=str(iso_time)+'.000Z'
            output_row={"ID":row[id_index],"time":iso_time,"ch4":ch4,"latitude":float(row[y_index]),"longitude":float(row[x_index])}
            db.insert_table(con,curs,output_row["ID"],output_row["ch4"],output_row["longitude"],output_row["latitude"],output_row["time"],"target")
            message=make_STA_payload.get_STA_payload([output_row],simulation_method,known_names,bool(is_trajectory))
            if output_row.__len__()>0:
                output_rows.append(message)
            sim_counter+=1
        print(output_rows.__len__())
        print('start posting with '+str(simulation_rate)+' seconds time intervals.')
        post_count=0
        if bool(is_trajectory):
            print('')
        else:
            submit_results.post_batch_STA(output_rows,post_count,uknown_stations.__len__(),endpoint,user_name,password)
            post_count+=uknown_stations.__len__()
        time.sleep(int(simulation_rate))
        output_rows.clear()
db.close_connection(con)
        


