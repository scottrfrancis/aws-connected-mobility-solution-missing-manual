#!/bin/bash


curl --include --silent --location --request POST "$MGR_ENDPOINT/simulations" \
--header 'Accept: application/vnd.aws-cdf-v1.0+json' \
--header 'Content-Type: application/vnd.aws-cdf-v1.0+json' \
--data-raw "{
    \"name\": \"test\",
    \"deviceCount\": 1,
    \"modules\": {
        \"dataGenerator\": \"simulations/modules/data-generator.zip\",
        \"simulationEngine\": \"simulations/modules/simulation-engine.zip\",
        \"routeGen\": \"simulations/modules/auto-route-gen.zip\"
    },
    \"tasks\": {
        \"provisioning\": {
            \"attributes\": {
                \"ca\": \"simulations/ca/aws-ca.pem\",
                \"privateKey\": \"simulations/ca/private.pem.key\",
                \"certificate\": \"simulations/ca/certificate.pem.crt\",
                \"supplierTemplate\": \"auto_supplier\",
                \"certificateId\": \"$CERT_ID\",
                \"mapboxToken\": \"$MAPBOX_TOKEN\",
                \"region1\": \"latitudeMin:30,longitudeMin:-98,latitudeMax:31,longitudeMax:-97,weight:100\"
            },
            \"plan\": \"simulations/plans/auto-provisioning.jmx\",
            \"threads\": {
                \"total\": 40,
                \"rampUpSecs\": 60
            }
        },
        \"simulation\": {
            \"attributes\": {},
            \"plan\": \"simulations/plans/auto-devices.jmx\",
            \"threads\": {
                \"total\": 100,
                \"rampUpSecs\": 30
            }
        }
    }
}" | grep 'location' | cut -d"/" -f3