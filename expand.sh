#!/bin/bash

# export paws='aws --profile CMS'

# starting from CMS root director
# $paws s3 cp s3://cdf-157731826412-us-west-2/releases/core/cdf-core-20200428171955.tar .
mkdir cdf-core
tar -xf cdf-core-20200428171955.tar -C cdf-core

# $paws s3 cp s3://cdf-157731826412-us-west-2/releases/clients/cdf-clients-20200428171955.tar .
mkdir cdf-clients
tar -xf cdf-clients-20200428171955.tar -C cdf-clients

# $paws s3 cp s3://cdf-157731826412-us-west-2/cdf-auto-artifacts/cdf-facade-auto.zip .
# $paws s3 cp s3://cdf-157731826412-us-west-2/cdf-auto-artifacts/cdf-infrastructure-auto.zip .
# $paws s3 cp s3://cdf-157731826412-us-west-2/cdf-auto-artifacts/cdf-simulator.zip .
# $paws s3 cp s3://cdf-157731826412-us-west-2/cdf-auto-artifacts/cdf-auto-fleetmanager-backend.zip .
# $paws s3 cp s3://cdf-157731826412-us-west-2/cdf-auto-artifacts/cdf-auto-fleetmanager-ui.zip .

unzip -q '*.zip'

./fixConfigs.py

# cd cdf-infrastructure-auto
# ./deploy.bash -e development -u cdf-svc-artifacts -p cdf-keys -i 0.0.0.0/0 -g scofrcan@amazon.com -b cdf-cf-rsrc -R us-east-1 -P default -B -C