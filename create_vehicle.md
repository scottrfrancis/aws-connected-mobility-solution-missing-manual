# Creating a New Vehicle in CMS Instructions

To see the response from the Connected Device Framework, open up the AWS IoT Management Console, navigate to Test, and subscribe to `cdf/#`

*These steps work on stable branch, have not been tested with development/head branch.*

1. Get the following endpoints from API Gateway:
    * CDF Asset Library = {asset_library_endpoint}, CDF Auto Facade = {auto_facade_endpoint}, {certificateId}
    
```bash
export env_name='development' # or whatever your env is...

export asset_library_endpoint=$(aws cloudformation list-exports --query "Exports[?Name=='cdf-core-$env_name-assetLibrary-apiGatewayUrl'].Value" --output text)
export auto_facade_endpoint=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-facade-apiGatewayUrl'].Value" --output text)
export certificateId=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-certificateId'].Value" --output text)

echo $asset_library_endpoint
echo $auto_facade_endpoint
echo $certificateId
```

2. Login to the FleetManager app and capture the cognito id token
    * open debugger
    * inspect "Local Storage" from the "Application" tab
    * look for "CognitoIdentity....idToken" and copy the Value -- be sure to "Select All" and Copy, otherwise, intermediate word breaks may copy only part of the token.

_Tokens are generally only good for 60 minutes, if you receive an authorization error in calls, refresh this token._
    
## Method 1 [Recommended]

3. Open Postman and import the [CMS-Demo.postman_collection.json](#)

4. From the 'Environment' Icon (eyeball) **Edit** the 'CMS-Demo-xxx' environment and set the current values as collected in previous steps for
    * assetlibrary
    * facade_endpoint
    * certificateId
    * cognito_id_token
 
5. Additionally set environment values of your choice fo
    * devicemakername (can be anything)
    * externalId (must be unique like a serial number or guid or append the account number for uniqueness)
    * thingname (unique for account, this is how your device will publish data)
    * username (unique for account)
    * firstName, lastName (for the user)
    
**Update** and close the environment editor.

6. Open the "1 - Create-Supplier (AssetLibrary)" request from the imported "CMS-Demo" collection. Click **Send.**
    an empty body with a `204` return code is normal.
 
7. Open the "2 - Create-User (Facade)" request. Click **Send.**
    if you get an unauthorized error, refresh and reset the `cognito_id_token` value in the environment.
  
8. Open the "3 - Register-Device (Facade)" request. Click **Send.**
    a `201` response with a certificate in the response body is expected.
    
9. Open the "4 - Activate-Device (Facade)" request. Make any changes desired to the Body of the request. **NB- VIN numbers are verified at multiple steps in CMS and if not correctly formatted, other downstream errors may occur.** Also note that the `vehicle.ecus.type` is hard-coded (`tcu`) to match the IoT Thing Type created when CMS was installed and is further hard-coded in request "3 - Register-Device (Facade)".  

Click **Send.**
    a `204` response code is normal
    
10. Open the "5 - Associate-User-Car (AssetLibrary)" request. Click **Send.**
    verify the `204` response code
   
 **Done**
 
 You may now publish telemetry on `dt/cvra/{thingName}/cardata`. Skip ahead to that section.
  
## Method 2 -- will require modification -- these steps are general guidelines
    
3. Create a supplier in the **Asset Library API**:
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

4. Create a User using **Facade API**:
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

5. Create a new certificate in AWS IoT, and attach the CvraTcuDevicePolicy policy to it ( created by CMS CloudFormation deployment )

6. Register a device using **Facade API**:
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

7. Activate the device using **Facade API**:
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

8. Sell the car to a user / associate with the user created in step 2, using **AssetLibrary API** (register vehicle to owner Facade API is broken in stable branch):
    1. `curl -X PUT -H "Accept: application/vnd.aws-cdf-v1.0+json" -H "Content-Type: application/vnd.aws-cdf-v1.0+json" https://{asset_library_endpoint}/Prod/groups/<full path to user>/owns/groups/<full path to vehicle>`
    2. Replace <full path to user> with the *full path* to the asset library group, including URL encoded slashes, from the user created in Step 2. You can get the full URL encoded path  from the MQTT message that is published from CDF after User creation in step 2.
    3. Replace <full path to vehicle> with the *full path* to the asset library group, including URL encoded slashes, from the vehicle created in Step 5. You can get the full URL encoded path  from the MQTT message that is published from CDF after Vehicle creation in step 5. 
    4. Example:
        1. `https://{asset_library_endpoint}/Prod/groups/%2Fauto%2Fusers%2Fspacemanspiff/owns/groups/%2Fauto%2Fvehicles%2Fkl4cjhsb2db198124`
        2. Username was spacemanspiff, full path is /auto/users/spacemanspiff
        3. Vehicle vin number is kl4cjhsb2db198124, full path is /auto/vehicles/kl4cjhsb2db198124
        4. URL encode for / is %2F
        5. Include leading /
        
## Publish Telemetry (after either Method 1 or 2)    
    
Publish telemetry on the topic  `dt/cvra/{thingName}/cardata`
    * Replace {thingName} with your Thing Name as Activated in the '{{facade_endpoint}}/suppliers/{{exernalId}}/devices/{{thingName}}/register' call (Postman request #3).

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

**Observe Vehicle location in CMS Fleet Manager UI**
