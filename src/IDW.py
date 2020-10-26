from math import radians, cos, sin, asin, sqrt, pow, atan
import utm

db_configs=()
# WGS84 distance function
def distance(lat1, lat2, lon1, lon2):      
    # The math module contains a function named 
    # radians which converts from degrees to radians. 
    lon1 = radians(lon1) 
    lon2 = radians(lon2) 
    lat1 = radians(lat1) 
    lat2 = radians(lat2) 
       
    # Haversine formula  
    dlon = lon2 - lon1  
    dlat = lat2 - lat1 
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
  
    c = 2 * asin(sqrt(a))  
     
    # Radius of earth in kilometers. Use 3956 for miles 
    r = 6371
       
    # calculate the result 
    return(c * r)

def get_azimuth(deltaX, deltaY):
    alpha = atan(abs(deltaX) / abs(deltaY))
    azimuth = 0
    if (deltaX > 0 and deltaY > 0):
        azimuth = alpha
    elif (deltaX > 0 and deltaY < 0):
        azimuth = 180 - alpha
    elif (deltaX < 0 and deltaY < 0):
        azimuth = 180 + alpha
    else:
        azimuth = 360 - alpha
    return azimuth


def get_angle(azimuth_known_station, azimuth_unknown_station):
    alpha = 0
    if (abs(azimuth_unknown_station - azimuth_known_station) < 180):
        alpha = (azimuth_unknown_station - azimuth_known_station)
    elif (abs(azimuth_unknown_station - azimuth_known_station) > 180):
        alpha = 360 - abs(azimuth_unknown_station - azimuth_known_station)
    return alpha

# get leak in target when it is windy
def get_leak_in_target(db,con,cur,ID,target_time,wind_speed,dist):
    t_leak=target_time-dist/wind_speed
    c_leak=db.select_table(cur,t_leak,ID,'leaking')
    if c_leak is not None:
        return c_leak[1]
    else:
        return None

def get_db_config(db,con,cur):
    global db_configs
    db_configs=(db,con,cur)
        
# IDW
def run(x,y,x_block,y_block,z_block,p,wind_enabled,wind_speed,wind_direction,time,ID):
    inter_value=0
    inverse_distance=0
    Z_value=0
    total_speed=0
    total_speed_imact=0
    for i in range(0,x_block.__len__()):
        dist=0
        (X,Y,zone,T)=utm.from_latlon(y, x)
        (Xs,Ys,zones,Ts)=utm.from_latlon(y_block[i], x_block[i])
        if wind_enabled==False:
            # uncomment the following code in case you want to measure 
            # arc distance between points 
            # dist=distance(y,y_block[i],x,x_block[i])
            dist=sqrt(pow(X-Xs,2)+pow(Y-Ys,2))
            inverse_distance+= 1/(pow(dist,p))
            Z_value+= z_block[i]/(pow(dist,p))
        else:
            # uncomment the following code in case you want to measure 
            # arc distance between points 
            # dist=distance(y,y_block[i],x,x)
            station_direction = get_azimuth(X - Xs, Y - Ys)
            alpha = get_angle(station_direction, wind_direction)
            projected_wind = wind_speed * cos(alpha)

            dist=sqrt(pow(Xs-X,2)+pow(Y-Ys,2))
            parameter=1
            if Xs-x==0:
                parameter=abs(Ys-Y)/abs(Xs-X-.001)
            else:
                parameter=abs(Ys-Y)/abs(Xs-X)
            # the first condition 
            if alpha<180:
                (db,con,cur)=db_configs
                z=get_leak_in_target(db,con,cur,ID[i],time,wind_speed,dist)
                if z is None:
                    z=0
                dist=dist/parameter
                inverse_distance+= 1/(pow(dist,p))
                Z_value+= z/(pow(dist,p))
                total_speed+=projected_wind
                total_speed_imact+=projected_wind*z_block[i]
                                 
    if Z_value==0:
        inter_value=0
    else:
        if not wind_enabled:
            inter_value=Z_value/inverse_distance
        else:
            inter_value=(Z_value/inverse_distance+total_speed_imact/total_speed)/2
    return inter_value