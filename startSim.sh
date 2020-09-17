#!/bin/bash

url="$MGR_ENDPOINT/simulations/$SIM_ID/runs"

curl --include --location --request POST $url  \
--header 'Content-Type: application/vnd.aws-cdf-v1.0+json' \
--header 'Accept: application/vnd.aws-cdf-v1.0+json' \
--data-raw '{
    "deviceCount": 2
}' 
echo ""