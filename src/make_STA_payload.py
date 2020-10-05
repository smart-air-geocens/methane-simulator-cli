import json

templateJson = {
        "common": {
            "Datastream": {
                "Thing": {
                    "name": "",
                    "description": "",
                    "Locations": [{
                        "name": "",
                        "description":"",
                        "location": {
                            "type": "Point",
                            "coordinates": [ 0, 0 ]
                        }
                    }]
                }
            }
        },
        "Observations": []
    }

def update_thing(longitude,latitude,name,method,known_stations,trajectory):
    station_string=''
    for station in known_stations:
        station_string+=station+','
    description='This station is sumilated by '+method+' by '+station_string[:-1]+' stations'
    templateJson['common']['Datastream']['Thing']['name']='methane_sim '+name
    templateJson['common']['Datastream']['Thing']['description']=description
    if not trajectory:
        templateJson['common']['Datastream']['Thing']['Locations'][0]['location']['coordinates']=[longitude,latitude]
        templateJson['common']['Datastream']['Thing']['Locations'][0]['description']=description
        templateJson['common']['Datastream']['Thing']['Locations'][0]['name']='methane_sim '+name


def update_observations(name,time,ch4,method,longitude,latitude):
    Observation={
                "result": ch4,
                "resultTime":time,
                "Datastream": {
                    "name": name + ":ch4",
                    "description": "The Methane Datastream for station "+ name,
                    "Sensor": {
                        "name": name + ":ch4",
                        "encodingType": "text/html",
                        "metadata":"https://en.wikipedia.org/wiki/Inverse_distance_weighting",
                        "description":"This is a synthetic sensor that its observations is calculated based on "+method
                    },
                    "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                    "unitOfMeasurement": {
                        "symbol": "ppm",
                        "name": "ppm",
                        "definition": "https://groups.molbiosci.northwestern.edu/holmgren/Glossary/Definitions/Def-P/parts_per_million.html"
                    },
                    "ObservedProperty": {
                        "name": "ppm",
                        "definition": "https://groups.molbiosci.northwestern.edu/holmgren/Glossary/Definitions/Def-P/parts_per_million.html",
                        "description": "ppm"
                    }
                },
                "FeatureOfInterest": {
                    "encodingType": "application/vnd.geo+json",
                    "description": "Generated using location details: The location that " + name + " is deployed",
                    "name": "Methane Station - " + name,
                    "feature": {
                        "type": "Point",
                        "coordinates": [ longitude, latitude ]
                    }
                }
            }
    return Observation

def find_columns(headers,keyword):
    index=0
    matched=[s for s in headers if keyword in s]
    return matched

def get_STA_payload(values,method,known_stations,trajectory):
    observations=[]
    for data in values:
        name=data['ID']
        time=data['time']
        latitude=data['latitude']
        longitude=data['longitude']
        ch4=data['ch4']
        update_thing(longitude,latitude,name,method,known_stations,trajectory)
        observations.append(update_observations(name,time,ch4,method,longitude,latitude))
    templateJson['Observations']=observations
    return templateJson