#!/usr/bin/python3

"""
pip3 install boto3
pip3 install elasticsearch
pip3 install requests
pip3 install requests-aws4auth
"""

import argparse
from elasticsearch import Elasticsearch, RequestsHttpConnection
import logging
from requests_aws4auth import AWS4Auth
import boto3
import requests


parser = argparse.ArgumentParser()

parser.add_argument("-e", "--endpoint", action="store", required=True, dest="endpoint", help="Elasticsearch endpoint")
parser.add_argument("-v", "--vin", action="store", required=True, dest="vin", help="VIN number to delete")

args = parser.parse_args()


endpoint = args.endpoint # 'search-cms-es-development-5ucfts45z4wmntf3ed4cnuunpu.us-east-1.es.amazonaws.com')
vin = args.vin
path = ''
region = 'us-east-1'

service = 'es'


#
# Delete 'vin' from all indices in ES
#   - shared_cardata -- has map of vin to deviceid
#   - cardata -- 
#   - devices -- has alternate 'rows'  -- 1st wih VIN, 2nd with deviceid
#


def getClient(endpoint, region):
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

    es = Elasticsearch(hosts=[{'host': endpoint, 'port': 443}],
            http_auth = awsauth, use_ssl = True, verify_certs = True,
            connection_class = RequestsHttpConnection )
    
    return es

es = getClient(endpoint, region)


def getDeviceIdFromVin(es, vin):
  def searchIndex(index):
    res = es.search(index=index, body={'query':{'match': {'vin':vin}}} )
    return  res['hits']['hits'][0]['_source']['devices'][0]['deviceid'] 

  
  try:
    deviceid = searchIndex('shared_cardata')
  except Exception as e:
    try: 
      deviceid = searchIndex('cardata')
    except Exception as e:
      deviceid = None
  
  return deviceid
    
deviceid = getDeviceIdFromVin(es, vin)
print(f'Found thing name: {deviceid} for VIN: {vin}')

def deleteDocsFromIndex(es, index, key, val):
  try:
    res = es.search(index=index, body={'query':{'match': {key:val}}} )
    [ es.delete(index=index, id=r['_id']) for r in res['hits']['hits'] ]
  except Exception as e:
    pass

indices = es.cat.indices(format='json') 
[ deleteDocsFromIndex(es, i['index'], 'deviceid', deviceid) for i in indices]

[ deleteDocsFromIndex(es, i['index'], 'vin', vin) for i in indices ]

# dump all
# [ print(es.search(index=i['index'], body={'query':{'match_all':{}}})) for i in indices  ]  

