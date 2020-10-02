import boto3
import json
import logging
import math
import os
import sys
import time

"""
must manually add IOT analytics to call lambda

aws lambda add-permission --function-name nxp-sim-to-CMS --action lambda:InvokeFunction --statement-id iotanalytics --principal iotanalytics.amazonaws.com
""" 

# test event
test = {'deviceid': 'ECU-AWS-2014-DLK4MXS_O_', 'timestamp': '2020-09-17T19:18:34.034Z', 
'Engine Torque': '0', 'Motor Torque': '6.462857143', 'Accel': '0.0078', 'Decel': '2.98E-151', 'speed_ mph': '15.35819998', 
'batt_soc': '79.97736836', 'batt_current': '1.6146311', 'batt_voltage': '381.4785617', 
'X_pos': '54.17729085', 'Y_Pos': '-11.69713948', 'Odometer': '200.34'}

template = {
  "MessageId": "5AZSL56XXKB10000-2020-09-25T17:12:39.958Z",
  "SimulationId": "vqRX_CnYn",
  "CreationTimeStamp": "2020-09-25T17:12:39.958Z",
  "SendTimeStamp": "2020-09-25T17:12:39.958Z",
  "VIN": "5AZSL56XXKB10000",
  "TripId": "ZcJUYWgue",
  "DriverID": "",
  "GeoLocation": {
    "Latitude": 42.46005999815096,
    "Longitude": -83.59190004869589,
    "Altitude": 0,
    "Heading": 267.0536375567732,
    "Speed": 75.6993396485681
  },
  "Communications": {
    "GSM": {
      "Satelites": "",
      "Fix": "",
      "NetworkType": "",
      "MNC": "",
      "MCC": "",
      "LAC": "",
      "CID": ""
    },
    "WiFi": {
      "NetworkID ": ""
    },
    "Wired": {
      "NetworkID ": ""
    }
  },
  "Acceleration": {
    "MaxLongitudinal": {
      "Axis": 0,
      "Value": 0.2442455635230658
    },
    "MaxLateral": {
      "Axis": 0,
      "Value": 0.2442455635230658
    }
  },
  "Throttle": {
    "Max": 30.665122822671627,
    "Average": 0
  },
  "Speed": {
    "Max": 75.6993396485681,
    "Average": 0
  },
  "Odometer": {
    "Metres": 36772.61923815102,
    "TicksFL": 0,
    "TicksFR": 0,
    "TicksRL": 0,
    "TicksRR": 0
  },
  "Fuel": 33.770159918496745,
  "Name": "9gSDTBwZR",
  "OilTemp": 300.57613602390444
}



logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# can also look this up in Dynamo -- cdf-simulation-devices-development
# simulationId = os.environ.get('SimulationId', 'EJdhw1c_S')     
# vin = os.environ.get('VIN', '1AZZH82ZXCC10000')
# tripId = os.environ.get('TripId', "MzVoJP847")

simulationId = template['SimulationId']
vin = template['VIN']
tripId = template['TripId']

#longitudeMin:-83.699294,latitudeMax:42.30272
# Curt: 42.299845, -83.698849
origin = {
    "Latitude":  42.299845,
    "Longitude": -83.698849,
    "Altitude": 0,
    "Heading": 0,
    "Speed": 0
  }
region = os.environ.get('Region', 'us-east-1')
topic = os.environ.get('TopicTemplate', 'dt/cvra/{deviceid}/cardata')

  
client = boto3.client('iot-data', region)

# X increases to E
# Y increases to S
def offsetFromOrigin(o, d):
#  Earth’s radius, sphere
    R=6378137.0    
    pos = o.copy()
    
    pos['Latitude'] = float(o['Latitude']) + (float(d['x_m'])/(R*math.cos(math.pi*float(o['Latitude'])/180)))*(180/math.pi)
    pos['Longitude'] = float(o['Longitude']) - (float(d['y_m'])/R)*(180/math.pi)

    return pos 
 
def mphToKph(s):
    return abs(s)*1.60934

def transformEvent(e):
    global origin, simulationId, template, tripId, vin
    
    t = template.copy()    
    # not all properties are updated from template
    t['SimulationId'] = simulationId
    t['CreationTimeStamp'] = e['timestamp']
    t['SendTimeStamp'] = t['CreationTimeStamp']

    t['VIN'] = vin
    t['MessageId'] = f"{t['VIN']}-{t['CreationTimeStamp']}"
    t['TripId'] = tripId

    t['GeoLocation'] = offsetFromOrigin(origin, {'x_m': e['X_pos'], 'y_m': e['Y_Pos']})
    t['GeoLocation']['Speed'] = mphToKph(float(e['speed_ mph']))

    t['Acceleration']['MaxLongitudinal']['Value'] = float(e['Accel']) - float(e['Decel'])
    
    t['Speed']['Max'] = t['GeoLocation']['Speed']
    
    t['Odometer']['Metres'] = float(e['Odometer'])
    
    # [ e.pop(k) for k in ['timestamp', 'deviceid', 'X_pos', 'Y_Pos', 'speed_ mph', 'Accel', 'Decel', 'Odometer'] ]
    # t.update(e)
    t['batt_soc'] = e['batt_soc']
    
    return t

def lambda_handler(event, context):
    logger.info(f"received event {event} in {context}")

    # deviceid = event['deviceid']
    deviceid = 'ECU-AWS-2014-DQAHOYSERV'
    msg = transformEvent(event)
    logger.info(f"new event: {msg}")
    
    # send to proper topic
    res = client.publish( topic=topic.format(deviceid=deviceid), qos=0, payload=json.dumps(msg) )
    
    time.sleep(0.45)

if __name__ == "__main__":
    lambda_handler(test, {})
