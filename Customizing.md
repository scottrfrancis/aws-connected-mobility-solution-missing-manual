# Customizing and Extending Fleet Manager, CMS, and CDF

Installation and setup of the CDF Framework and the CMS suite of applications including FleetManager is covered sepately. This guide focuses on how to adapt the installation
to various use cases and customizations. In this guide, the term 'the application' will generally refer to Fleet Manager and the components of CMS and CDF necessary to deliver
it. While this is a bit imprecise in general, it should make the guide easier to read and understand. Where needed, more precise references to components will be used.

## Provisioning and Simulation

Feeding the application with telemetry data is easiest from the supplied simulators. The Quick Deploy guide covered an initial setup of simulators. Starting from simulation 
is easiest when starting to customize. However, it is easy to 'over-provision' simulators and then have to debug through a large volume of data. Therefore, it is recommended
to either roll back and reinstall any previous installation or delay setting simulation until you have read this guide.

**NOTE:** This guid is by no means comprehensive and the reader is encouraged to debug and inspect the working behavior of the solution from a running system. To facilitate that,
use of an account and region that has minimal additional deployments is advised.

### Debugging and inspecting operation

After deployment, suggest either clearing CloudWatch logs or making a note of time stamps so that you can easily find new logs for the various APIs and other systems that
are used.  Some logs and resources to keep an eye on include 

* logs for the Facade API - delivered as single lambda. From the API Gateway console, find the Facade API, navigate to find the lambda function, observe its configuration, 
and click on 'monitoring' to get to the right Log Group.  Again, noting time stamps can help to understand what is happening.
* IoT Core Topics - monitoring '#' is always valuable, but can be a bit noisy. Some more targeted topics to monitor are
    1. `cdf/{thingName}/activate/accepted` - announcements of new TCU. Payload has pairing of `deviceId` and `vin`. The `deviceId` is also used as `thingName`, but most other systems key off of `vin`
    2. `dt/cvra/{thingName}/cardata` - the main telemetry topic -- simulators publish here and you can too! either manually or with another device.

### Basic sequence for provisioning -- what the scripts do

When the simulation manager (another API Gateway front for a single Lambda) is used to provision simulators (using, for example the `dataGen.sh` script curl wrapper)
1. Tasks are created in ECS -- one for each of the requested number of devices. 
2. These containers are configured with common resources from S3 ($RSRC_BUCKET/simulations ... ca, modules, plans) as well as the $SIM_ID that is returned by the POST
3. In executing, the tasks create their own repository of data in $RSRC_BUCKET/simluations{$SIM_ID}/{index}.
4. Simulators (ECS tasks running from ECR containers) are built using the JMeter test scripting framework and have TWO test plans -- one for provisioning and another for running.
Additionally, each simulators copies three module progams  (auto-route, data-generator, and simulation-engine) which are delivered in zip archives. The simulators expand
these archives and invoke them according to the test plan. 
5. The simulation-engine program calls IoT to create a JITP profile (and receives credentials -- which should be a copy of the credentials in the `ca/` prefix as ALL devices
share a common certificate).
6. Calls the Facade API to create necessary relationships -- suppliers, users, vehicles, and then link them all together. The final step in this is the announcement in the 
IoT topic `cdf/{thingName}/activate/accepted` where the binding of deviceId (aka thingName) and vin are given.
7. These ids and relationships are also published into various DynamoDB tables.
8. Lambda funtions triggered by various IoT Rules and DynamoDB streams also insert data into Elasticsearch.

**NOTE:** for the purposes of the UI, *EVERYTHING* comes from Elasticsearch and that data movement is a one-way function. There is no affordance for deleting or refreshing
data in Elasticsearch -- it is evergrowing. 

Due to the number of services and their interactions, it is recommended to always use the provisioning scripts and interfaces at least when getting started. 

#### Configuration options for provisioning

_Consult the `dataGen.sh` script_

**Preparation**
The `dataGen.sh` script uses the environment variables `$MGR_ENDPOINT, $CERT_ID, $MAPBOX_TOKEN`. Set these prior to calling the script.
```bash
REGION=$(aws configure get region)
MGR_ID=$(aws apigateway get-rest-apis --query "items[?contains(name,'SimulationManager')].id" --output text)
STAGE='Prod'
export MGR_ENDPOINT=https://$MGR_ID.execute-api.$REGION.amazonaws.com/$STAGE

STACK_NAME='cms-dev'
export CERT_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query "Stacks[0].Outputs[?OutputKey=='CertificateId'].OutputValue" --output text)

export MAPBOX_TOKEN='<your mapbox token>'
```


In calling the manager provisioning API, a JSON body is POSTed to the endpoint. A couple properties of interest in that body include:
* `.deviceCount` - a number of devices to provision
* `tasks.provisioning.attributes.region[1,2]` - two geo boxes, with `weight` properties to distribute the `.deviceCount` devices among

You might want to modify the lat/lon min/max properties as well as weights.
**NOTE: there is a bug in the allocation that always provisions ONE MORE simulator that requested**

Monitor the `cdf/+/activate/accepted` topic and keep track of the pairings so you know when the simulators have been provisioned and paired. 
You may also see traffice on `cdf/assetlibrary/+` as the various relationships (users, groups, suppliers, etc) are provisioned.
Monitor `dt/cvra/+/cardata` for the INITIAL telemetry messages that position the cars on the map.

```bash
export SIM_ID=$(./dataGen.sh | tr -d '\r')
```

Saves the `$SIM_ID` for later use to START the sim (this value can also be looked up in DynamoDB).

**Provisioning can take 5 - 10 minutes or more**

Following the publication of the deviceid / vin pairing on cdf/+/activate/accepted, the simulators will publish initial telemetry on `dt/cvra/{thingName}/cardata`.
Only ONE message will be published to set the initial starting point of the vehicle. This message can be used as a starting template for more vehicle telemetry. 
There are a few ids that are needed for subsequent telemetry publication -- including `tripid`.


### Running a simulation

The curl wrapper script `startSim.sh` call the Simulation Manager API again to start the simulation given by $SIM_ID. Note that it is possible to have multiple, varying
simluations configured and then run independently. And again, since all data is AGGREGATED in Elasticsearch, succesive runs will be accreted, not replaced in the UI.

The `.deviceCount` property in the request again will configure how many devices to run. This control also seems a bit buggy in relation to the provisioned count.
For example, if you provision 50 devices and then start the simulation with 10, that will work. But, if you provision 1 device, you will get 2. And then attempts to start
the simulation with less than 2 devices will fail.  

After a minute or two, you should see data on `dt/cvra/{thingName}/cardata` and in the UI. As it can be hard to find 'moving' cars in the UI sometimes, watch
the telemetry topic for the VIN numbers and find those in the map. 

#### Routes

Routes are randomly selected and the simulation will run until the route is completed. These routes will accummulate in Elasticsearch to feed the UI, but as each
simulator's route is completed, 'activity' in the UI will cease. 

**It doesn't seem necessary to END a trip or route.  So if you took the initial telemetry message, and just kept updating, I think the car would keep moving.**

#### Sending telemetry messages

Perhaps the simplest way to send custom telemetry is to 'take over' a pre-provisioned device. Following the previous steps, you should have captured an 
initial message for the device you wish to takeover. (See sample at the end of this document. There are a few properties that require special handling.

| property | comments |
| ------- | ------- |
| `.MessageId` | constructed as '{vin}-{iso_timestamp_gmt}' |
| `.SimulationId` | this is the simulation Id created by simulation manager |
| `.CreationTimeStamp` | creation time of simulation? in ISO GMT |
| `.SendTimeStamp` | ISO format GMT Time when message was sent -- see also `.MessageId` |
| `.VIN` | vin bound as part of the `activate/accepted` message for this `deviceid` |
| `.Name` | have no idea what this field is |
| ---- | ---- |
| `.GeoLocation` | Lat, Lon probbably most important, not clear others are used. |
| `.Speed` | this is what seems to drive the UI |
| `.Odometer` | says Metres, but it's kilometers |
| `.Fuel` | doesn't work in UI -- known bug |

It should be possible to add additional telemetry without much grief, but the rules, lambdas, etc may need to be adjusted to *do* something with that new data.

Note that the message is published on `dt/cvra/{thingName}/cardata` where thingName is bound with vin in the accepted message.

General sequence to send data:
1. acquire the credentials for a device from the S3 bucket
2. wait for an accepted message, not the `vin` and `deviceid` which you will use as the `thingName`
3. change your thingName to `deviceid`
3. wait for the first cardata message and extract `.SimulationId`, `.CreationTimeStamp`, `.Name` for re-use in your own messages
4. acquire your own telemetry values and format/modify the message, adding current time in ISO Z format to `.SendTimeStamp` and constructing `.MessageId` with this 
value and the `vin` as described
5. publish message on `dt/cvra/{vin}/cardata`

Suggestions:
- use a gg lambda to subscribe to the accepted and cardata topics and then publish the values noted to a shadow
- let your telemetry device free run
- use a second greengrass lambda that subscribes to your device and reformats/publishes the messages using the values from the shadow



## Cleaning up

Okay... so now you have a bunch of cars and none of them where you want and too many that you want to clean up the display. There are two main options:

1. Delete the entire deployment (perhaps just CMS when CDF and CMS are separated)
2. Selectively delete data from Elasticsearch, DynamoDB, IoT, and possibly S3 -- this is a mostly manual operation

The first option is Draconian, but self-explantory. Delete all the stacks and nested stacks. Consider if you want to delete the S3 buckets (recommended). Then redeploy.
This will give a nice, clean start, but will take hours.

Option 2 - which is also good to clean up things, but it can have some unintended side effects as not all the dependencies are mapped. 

Use the `rmVin.py` tool to delete a single VIN (and device ID) from Elasticsearch, DynamoDB, and IoT Core. This tool does NOT delete any S3 buckets, but those will
generally accrete based on sim run usage, so deletion isn't critical. It is possible that this could leave dangling refernces.

## UI Customization

* Telemetry values seem to be hard coded, but needs more investigation
* All cars share the smae image - https://cdf-auto-fleetmanager-backen-cdfautowebsitebucket-156hfqu1zl65f.s3.amazonaws.com/static/media/amz_vehicle.61edab1d.jpg
    -- I was able to replace it, but it replaces for all cars
    -- code changes needed to individualize for each car

### adding users

Users are easily added in the Cognito console, or you can set the user pool for users to self-signup.


##### Sample Message

```json
{
  "MessageId": "1AZRP14VX9C10001-2020-09-14T22:30:10.246Z",
  "SimulationId": "7r5x8EbPJ",
  "CreationTimeStamp": "2020-09-14T20:40:10.246Z",
  "SendTimeStamp": "2020-09-14T20:40:10.246Z",
  "VIN": "1AZRP14VX9C10001",
  "TripId": "MzVoJP847",
  "DriverID": "",
  "GeoLocation": {
    "Latitude": 30.492959890203142,
    "Longitude": -97.2655699533912,
    "Altitude": 0,
    "Heading": 159.90803207226497,
    "Speed": 103.10882016931925
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
      "Value": -0.37493163447162203
    },
    "MaxLateral": {
      "Axis": 0,
      "Value": -0.37493163447162203
    }
  },
  "Throttle": {
    "Max": 11.693368304181401,
    "Average": 0
  },
  "Speed": {
    "Max": 53.10882016931925,
    "Average": 0
  },
  "Odometer": {
    "Metres": 67244.36788468927,
    "TicksFL": 0,
    "TicksFR": 0,
    "TicksRL": 0,
    "TicksRR": 0
  },
  "Fuel": 127.47549257669135,
  "Name": "CRtdESVEf",
  "OilTemp": 298.52831665785095
}

```