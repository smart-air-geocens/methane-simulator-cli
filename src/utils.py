import json
import csv
import geojson

# read json file
def read_json(path):
    data={}
    with open(path) as jsonfile:
        data=json.load(jsonfile)
        return data

# read geojson file
def read_geojson(path):
    data={}
    with open(path) as jsonfile:
        data=geojson.load(jsonfile)
        return data

# read csv files
def read_csv(path):
    rows=[]
    with open(path,encoding = 'utf-8-sig') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        for row in csv_reader:
            rows.append(row)
        return rows

# write csv files
def write_csv(rows,header,path):
    with open(path, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(header)
        for row in rows:
            csv_writer.writerow(row)
            
# function to get unique values 
def unique(lists): 
      
    # insert the list to the set 
    list_set = set(lists) 
    # convert the set to the list 
    unique_list = (list(list_set)) 
    return unique_list

# find the index of the json with key and value
# in a json list
def get_json_index(list_,key_,value_):
    index=0
    counter=0
    for i in list_:
        if i[key_]==value_:
            index=counter
            break
        counter+=1
    return index