# Creating a New Vehicle in CMS Instructions

To see the response from the Connected Device Framework, open up the AWS IoT Management Console, navigate to Test, and subscribe to `cdf/#`

*These steps work on stable branch, have not been tested with development/head branch.*

1. Get the following endpoints from API Gateway:
    1. CDF Asset Library = {asset_library_endpoint}
```bash
aws cloudformation list-exports --query "Exports[?Name=='cdf-core-$env_name-assetLibrary-apiGatewayUrl'].Value" --output text
```
    2. CDF Auto Facade = {auto_facade_endpoint}
```bash
aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-facade-apiGatewayUrl'].Value" --output text
```

2. Login to the FleetManager app and capture the cognito id token
    * open debugger
    * inspect "Local Storage" from the "Application" tab
    * look for "CognitoIdentity....idToken" and copy the Value -- be sure to "Select All" and Copy, otherwise, intermediate word breaks may copy only part of the token.

_Tokens are generally only good for 60 minutes, if you receive an authorization error in calls, refresh this token._
    
2. Create a supplier in the **Asset Library API**:
    1. `curl -X POST -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{asset_library_endpoint}/Prod/groups -d @newsupplier.json`
    2. newsupplier.json:

```
{
    "groupPath" : "/auto/suppliers/<devicemakername>",
    "parentPath" : "/auto/suppliers",
    "templateId" : "auto_supplier",
    "name" : "<devicemakername>",
    "attributes" : {
        "externalId": "<must be unique, like ABCDEFG12345>"
    }
}
```

3. Create a User using **Facade API**:
    1. `curl -X POST -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{auto_facade_endpoint}/Prod/users -d @newuser.json`
    2. newuser.json:

```
{
    "username" : "<unique>",
    "firstName" : "<firstname>",
    "lastName" : "<lastname>",
    "email" : "[<email>](mailto:spacemanspiff@gmail.com)",
    "addressLine1" : "<address>",
    "city" : "<city>"
}
```
_Only `username, firstName, lastName` are required. Use Approved Fictious Names when not for real person._

4. Create a new certificate in AWS IoT, and attach the CvraTcuDevicePolicy policy to it ( created by CMS CloudFormation deployment )

5. Register a device using **Facade API**:
    1. `curl -X POST -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{auto_facade_endpoint}/Prod/suppliers/<supplier>/devices/<Thing Name>/register -d @newdeviceregisterfacade.json`
    2. Replace `<supplier>` with the externalId set in step 1. Replace `<Thing Name>` with the desired Thing Name.
    3. This will create the Thing in the AWS IoT Device registry of type ‘tcu’
    4. newdeviceregisterfacade.json:

```
{
    "templateId": "auto_ecu",
    "certificateId": "<certificate id from step 3>",
    "attributes": {
        "type": "tcu",
        "model": "TCU-1"
    }
}
```

6. Activate the device using **Facade API**:
    1. `curl -X POST -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{auto_facade_endpoint}/Prod/suppliers/<supplier>/devices/<ThingName>/activate -d @newdevicactivatefacade.json`
    2. Replace `<supplier>` with the externalId set in step 1. Replace `<Thing Name>` with Thing Name created in step 5.
    3. VIN number must be valid, no errors will throw if it’s not valid. Recommend using a pre-defined Vin number. Replace `<Thing Name>` with Thing created in step 4.
    4. newdeviceactivatefacade.json:

```
{
    "vehicle": {
        "make": "DENSO",
        "model": "DN",
        "modelYear": 2019,
        "marketCode": "NA",
        "vin": "KL4CJHSB2DB198124",
        "bodyType": "Saloon",
        "fuelType": "Gas",
        "transmissionType": "Auto",
        "transmissionAutoType": "7-speed",
        "colorCode": "B1B!",
        "iviType": "Premium",
        "ecus": [{
            "type": "tcu",
            "id": "<Thing Name>",
            "softwareVersion": "1.9.1"
        }]
    }
}
```

7. Sell the car to a user / associate with the user created in step 2, using **AssetLibrary API** (register vehicle to owner Facade API is broken in stable branch):
    1. `curl -X PUT -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{asset_library_endpoint}/Prod/groups/<full path to user>/owns/groups/<full path to vehicle>`
    2. Replace <full path to user> with the *full path* to the asset library group, including URL encoded slashes, from the user created in Step 2. You can get the full URL encoded path  from the MQTT message that is published from CDF after User creation in step 2.
    3. Replace <full path to vehicle> with the *full path* to the asset library group, including URL encoded slashes, from the vehicle created in Step 5. You can get the full URL encoded path  from the MQTT message that is published from CDF after Vehicle creation in step 5. 
    4. Example:
        1. `https://{asset_library_endpoint}/Prod/groups/%2Fauto%2Fusers%2Fspacemanspiff/owns/groups/%2Fauto%2Fvehicles%2Fkl4cjhsb2db198124`
        2. Username was spacemanspiff, full path is /auto/users/spacemanspiff
        3. Vehicle vin number is kl4cjhsb2db198124, full path is /auto/vehicles/kl4cjhsb2db198124
        4. URL encode for / is %2F
        5. Include leading /
        
8. Publish telemetry on the topic  `dt/cvra/<Thing Name>/cardata`
    1. Replace <Thing Name> with your Thing Name

```
{
    "MessageId": "<Vin number>-2020-09-28T16:59:51.248Z",
    "CreationTimeStamp": "2020-09-30T17:28:51.248Z",
    "SendTimeStamp": "2020-09-28T17:28:51.248Z",
    "VIN": "<Vin number>",
    "TripId": "DD55642_2",
    "DriverID": "",
    "GeoLocation": {
        "Latitude": 29.091378,
        "Longitude": -81.005141,
        "Altitude": 0,
        "Heading": 0,
        "Speed": 0
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
            "Value": 0
        },
        "MaxLateral": {
            "Axis": 0,
            "Value": 0
        }
    },
    "Throttle": {
        "Max": 0,
        "Average": 0
    },
    "Speed": {
        "Max": 0,
        "Average": 0
    },
    "Odometer": {
        "Metres": 14358,
        "TicksFL": 0,
        "TicksFR": 0,
        "TicksRL": 0,
        "TicksRR": 0
    },
    "Fuel": 0,
    "Name": "",
    "OilTemp": 0.1286271
}
```

9. Vehicle should be in CMS now
