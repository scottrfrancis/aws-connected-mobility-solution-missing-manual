# How to Run Simulations on CMS

This guide describes how to provision and run simulations with the simulation manager included in CMS. Modifying or Customizing the behavior of those simulations is covered sepearately.

### Overview

CMS relies on a variety of inter-connected database records and configurations to display vehicles in the Fleet Manager. The Facade API is helpful in setting those up and the `create_vehicle.md` guide describes the steps to do so manually which is most effective if you are developing a system to provision vehicles or want specific control over how a vehicle works. 

This guide is for more general, bulk simulation.

Simulators must first be provisioned. Provisioning takes some time while container tasks are created, initialized, and resources allocated for the simulators. The more simulators that are requested, the longer provisioning will take.

Once complete, simulations can be RUN and re-RUN as many times as desired. Simulations choose a random route, run it, and then terminate. Simulations are not long-lived. 

Completion of a route is detectable by the 'trip end' message on the appropriate MQTT Topic.

The Simulation Manager API is protected by Cognito Authentication. This can make performing ad hoc requests challenging.

**A Postman Collection is provided and recommended for use**

#### Prerequsites

* Download and install Postman, then import the collection before proceeding. 
* Log in to the Fleet Manager UI with the access credentials you wish to use.
* procure a Mapbox token

## Step 1 - Provision Simulation Capacity

1. Open the request `1 - Create Simulation` in Postman.

2. Create an 'Environment' in Postman specific to your project/deployment and create these variables (you can leave the values blank for the moment):

    * `simulation_manager_base_url`
    * `mapboxToken`
    * `certificateId`
    * `facadeApiFunctionName`
    * `simulation_id`
    * `cognito_id_token`

3. Extract values from CloudFormation using

```bash
export simulation_manager_base_url=$(aws cloudformation list-exports --query "Exports[?Name=='cdf-core-$env_name-simulationManager-apiGatewayUrl'].Value" --output text)
export certificateId=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-certificateId'].Value" --output text)
export facadeApiFunctionName=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-facade-restApiFunctionName'].Value" --output text)

echo $simulation_manager_base_url
echo $certificateId
echo $facadeApiFunctionName
```

Copy the `echo'd` values and paste into the 'Current Value's for each of these variables.  Leave `cognito_id_token` and `simulation_id` blank.  All other values should be filled out in the Postman environment.

4. Login to the FleetManager app and capture the cognito id token from the browser by

*   open debugger
*   inspect "Local Storage" from the "Application" tab
*   look for "CognitoIdentity....idToken" and copy the Value -- be sure to "Select All" and Copy, otherwise, intermediate word breaks may copy only part of the token.
*   paste the value into the `cognito_id_token` Postman environment variable.

**Tokens are generally only good for 60 minutes, if you receive an authorization error in calls, refresh this token.**

5. Inspect the body of the Run Simulations request and adjust `deviceCount`, `region1`, and `region2` properties as desired. **Ensure that the `simulation.threads.total` property is not greater than `deviceCount` or odd behaviors may result.**

6. Send the 'start' simulations request by postman. It may take a few minutes for simulations to start running. Progress can be monitored through the ECS console or IoT Core Test client.

This call will return a `simulation_id` in the response header. This id is needed for any and all future requests to start the simulation. The Postman request includes a Test script that will extract this ID and set the appropriate environment variable. However, you may wish to note it or persist it if you wish to re-start these same simulations in the future.

When Provisioning is complete, the requested number of 'cars' should be visible on the map in initial locations.

## Step 2 -- Start the Simulation

1. Open the `2 - Run Simulation` request in Postman. Review the `deviceCount` parameter in the 'body' of the request. If this number is greater than the number provisioned in Step 1, a timeout could occur. 

2. If you recently provisioned the simulation, simply 'Send' the request. If it has been some time, or if you receive and authorization error, refresh the `cognito_id_token` value as in Step 1.  If you wish to run a simulation with a different ID, change the `simulation_id` value in the environment.

3. If you receive a Timeout error from the Request, it is likely that the simulations have not yet finished being provisioned.  Wait unti the cars are visible on the map--generally about 5 - 10 minutes, but could be longer for a large number of devices. 

A '204' response indicates the simulations have been successfully started. 