#!/usr/bin/python3

import json
# import os.path
import os


config_files = [
    'bulkcerts/development-config.json',
    'certificateactivator/development-config.json',
    'certificatevendor/development-config.json',
    'provisioning/development-config.json',
    'simulator/launcher/development-config.json',
    'simulator/manager/development-config.json'
]
BASE_DIR='cdf-infrastructure-auto'
BUCKET_NAME='cdf-svc-artifacts'
REGION = 'us-east-1'
ORIG = 'orig'

def change_key_value(d: dict, key: str, val: str) -> dict:
    try:
        for k in d.keys():
            if k == key:
                d[key] = val
            else:
                d[k] = change_key_value(d[k], key, val)
    except Exception as e:
        pass

    return d

for cf in config_files:
    print(cf)
    orig_file = os.path.join(BASE_DIR, cf)
    with open(orig_file, 'r') as f:
        config = json.load(f)
        print(json.dumps(config))
    print("--->")

    config['aws']['region'] = REGION
    config['aws']['s3']['bucket'] = BUCKET_NAME

    # look for any embedded 'bucket' keys and update
    config = change_key_value(config, 'bucket', BUCKET_NAME)
    print(json.dumps(config))

    # backup old file and write new
    os.rename(orig_file, os.path.join(BASE_DIR, ".".join([cf, ORIG])))
    with open(orig_file, 'w+') as f:
        json.dump(config, f, indent=4)
    print("\n")


