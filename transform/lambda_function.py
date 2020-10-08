import boto3
import json
import logging
import math
import os
from dict_recursive_update import recursive_update
import sys
import time


# Defaults.. overridable with environment vars
#
region = os.environ.get('Region', 'us-east-1')
topic = os.environ.get('TopicTemplate', 'dt/cvra/{deviceid}/cardata')
# deviceid = os.environ.get('DeviceId', 'goldbox')
delay = os.environ.get('Delay', 0.45)

# test event
test_old = {'deviceid': 'ECU-AWS-2014-DLK4MXS_O_', 'timestamp': '2020-09-17T19:18:34.034Z', 
'Engine Torque': '0', 'Motor Torque': '6.462857143', 'Accel': '0.0078', 'Decel': '2.98E-151', 'speed_ mph': '15.35819998', 
'batt_soc': '79.97736836', 'batt_current': '1.6146311', 'batt_voltage': '381.4785617', 
'X_pos': '54.17729085', 'Y_Pos': '-11.69713948', 'Odometer': '200.34'}

test = {
  # supplied by IoT Rule SQL
  'deviceid': 'goldbox', 
  'timestamp': '2020-09-17T19:18:34.034Z', 
  # from GBII 
  "engine-torque": 135,
  "motor-torque": 135,
  "accelerate": 67.5,
  "decelerate": 67.5,
  "speed-mph": 13.499999,
  "battery-soc": 40.499999,
  "battery-current": 31.05,
  "battery-voltage": 62.1,
  "gps-x-pos": -83.692098,
  "gps-y-pos": 42.306595
}

# a proper template sample
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

#
# transforms -- various functions used to adjust formats, scale, etc.
#
def cast_to_Float(x):
  return float(x)

def mDeg_to_Deg(x):
  return float(x)/1000.0

def mphToKph(s):
    return abs(float(s))*1.60934

#longitudeMin:-83.699294,latitudeMax:42.30272
# Curt: 42.299845, -83.698849
origin = {
    "Latitude":  42.299845,
    "Longitude": -83.698849,
    "Altitude": 0,
    "Heading": 0,
    "Speed": 0
  }
# X increases to E
# Y increases to S
#  Earth’s radius, sphere
R=6378137.0  

def latOffset_to_Deg(x_m):
  global origin, R
  return float(origin['Latitude']) + (float(x_m)/(R*math.cos(math.pi*float(origin['Latitude'])/180)))*(180/math.pi)

def lonOffset_to_Deg(y_m):
  global origin, R
  return float(origin['Longitude']) - (float(y_m)/R)*(180/math.pi)
  
def deviceId_to_VIN(d):
  m = { 'goldcloud-telemetry' : 'NX4CJHSB2DB198124',    # alejandro's real goldbox
        'goldbox': 'KL4CJHSB2DB198124'      # scott's sim from CSV
  }
  
  return m.get(d, '5AZSL56XXKB10000')
        

# transformMapper maps incoming fieldnames to outgoing field names
# -- note 'dot' notation
#
# Format is a dict with key for the incoming field then a dict with
# transform function and outgoing keyname
#
# only handes 1::1 transforms.  for combinations or fan -in/-out use code
#
TransformMapper = {
  'deviceid': {
     'transform': deviceId_to_VIN, 'output': 'VIN' },
  'timestamp': {
     'transform': None, 'output': 'CreationTimeStamp' },
  "engine-torque":{
     'transform': None, 'output': None },
  "motor-torque":{
     'transform': None, 'output': None },
  "accelerate": {
     'transform': None, 'output': 'Acceleration.Longitudinal.accel' },
  "decelerate": {
     'transform': None, 'output': 'Acceleration.Longitudinal.decel' },
  "speed-mph": {
     'transform': mphToKph, 'output': 'GeoLocation.Speed' },
  "battery-soc": {
     'transform': None, 'output': None },
  "battery-current":{
     'transform': None, 'output': None },
  "battery-voltage": {
     'transform': None, 'output': None },
  "gps-x-pos": {
     'transform': mDeg_to_Deg, 'output': 'GeoLocation.Longitude' },
  "gps-y-pos": {
     'transform': mDeg_to_Deg, 'output': 'GeoLocation.Latitude' },
  # older events
  'X_pos': { 
    'transform': latOffset_to_Deg, 'output': 'GeoLocation.Latitude' },
  'Y_Pos': {
    'transform': lonOffset_to_Deg, 'output': 'GeoLocation.Longitude' },
  'speed_ mph': {
    'transform': mphToKph, 'output': 'GeoLocation.Speed' }
  # common?
  ,'Odometer': {
    'transform': cast_to_Float, 'output': 'Odometer.Metres' }
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

client = boto3.client('iot-data', region)

simulationId = template['SimulationId']
tripId = template['TripId']


def dotExpand(k, v):
  if len(k) == 0:
    return v
    
  keys = k.split('.')
  key = keys.pop(0)
  
  if len(keys) == 0:
    return { key: v }

  return { key: dotExpand(".".join(keys), v) }
  

def transform(k, v):
  global TransformMapper
  out = None
  
  if k in TransformMapper:
    key = TransformMapper[k].get('output') 
    if key:
      f = TransformMapper[k].get('transform')
      val = f(v) if f else v
    
      out = dotExpand(key, val)

  return out


def mapTransformEvent(e):
  global template, simulationId, tripId
  
  t = template.copy()
  [ recursive_update(t, o)  for o in [ transform(k, e[k]) for k in e.keys() ] if o ]
  
  # not all properties are updated from template
  t['SimulationId'] = simulationId

  t['MessageId'] = f"{t['VIN']}-{t['CreationTimeStamp']}"
  t['TripId'] = tripId

  # some fields are duplicated
  t['Speed']['Max'] = t['GeoLocation']['Speed']
  t['SendTimeStamp'] = t['CreationTimeStamp']
  
  # and some get combined
  if 'Longitudinal' in t['Acceleration']:
    la = t['Acceleration'].pop('Longitudinal')
    t['Acceleration']['MaxLongitudinal']['Value'] = float(la.get('accel', 0.0)) - float(la.get('decel', 0.0))

  return t
  

def lambda_handler(event, context):
  global delay
  logger.info(f"received event {event} in {context}")

  msg = mapTransformEvent(event)
  logger.info(f"new event: {msg}")
  
  # send to proper topic
  deviceid = event.get('deviceid', 'goldboxii')
  res = client.publish( topic=topic.format(deviceid=deviceid), qos=0, payload=json.dumps(msg) )
  
  time.sleep(delay)

if __name__ == "__main__":
    lambda_handler(test_old, {})
    lambda_handler(test, {})
