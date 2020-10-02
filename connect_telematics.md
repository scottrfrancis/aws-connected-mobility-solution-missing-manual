# Connecting a telematics source (TCU) to CMS with AWS Greengrass

This guide will help you set up a reference implementation to replay telemetry from a CSV File to a Greengrass Core, transform the data fields to be compatible with CMS, and publish the telemetry so that the CMS Fleet Manager UI will show the data.

For this guide, a Greengrass core will be provisioned on a Cloud9 environment and a group created with the [Telemetry Thing](https://github.com/scottrfrancis/aws-connected-vehicle-solution-telemetry-demo) also running on the Cloud9 environment. It should be straightforward to adapt this to other configurations of Greengrass Cores, groups, things, and IoT Core.


### Setup Greengrass Core and Telemetry Thing

Navigate to the repository for the [Telemetry Thing](https://github.com/scottrfrancis/aws-connected-vehicle-solution-telemetry-demo) and follow the directions in the [README](https://github.com/scottrfrancis/aws-connected-vehicle-solution-telemetry-demo) to

* create a Cloud9 environment
* install greengrass core
* create the virtual telemetry device
* setup the greengrass group

You may optionally configure the Telemetry Thing with alternate data sources, etc. Most of the notes are inline with the code and can be configured from the `Config.py` file or through the device shadow.

### Test Telemetry Publishing

From the IoT Console, Choose **Test** and subscribe to topic `vt/cvra/#`.
Start the Telemetry Thing as describe in the [README](https://github.com/scottrfrancis/aws-connected-vehicle-solution-telemetry-demo).

Note the raw telemetry being published in the Test client. 

### Transform messages

From the IoT Console, Choose **Act** then **Rules** and **Create** a new rule. Use 'transformRawTelemetry' for the Name and provide a SQL statement that will 

* provide an ISO9601 timestamp `parse_time("yyyy-MM-dd'T'HH:mm:ss.sss'Z'", timestamp()) AS timestamp` 
* ensure all other needed properties are passed along
* pull from the right topic -- `vt/cvra/#`

Click **Add action** and select "Send a message to a Lambda function". Click **Configure action.**

Click **Create a new Lambda function** to open the Lambda console.

Choose "Author from scratch," use 'transformRawTelemetry' as the function name, choose "Python 3.7" for the Runtime and click **Create function.**

Paste the content from the [transform lambda](blob/master/transform/lambda_function.py) into the code editor.

Under **Concurrency**, click **Edit** and set "Reserve concurrency" to 1.
This limits lambda to precisely one invokation.  You will also notice a `sleep` statement near the bottom of the function.  This sleep and the concurrency reservation serve to throttle the incoming telemetry to be at a rate that the downstream processing can handle without accummulating stale updates in the UI. 

Save the Lambda, return to IoT Console and complete the Action setup.

#### Customize the Lambda

When messages are published on `dt/cvra/{thingName}/cardata` a CMS-configured action will route these message to a lambda that 

* validates telemetry
* validates VIN
* validates deviceId
* organizes by timestamp
* pushes to Elasticsearch

For these reasons, data must be formatted very specifically--the schema is validated strictly and no extraneous fields are allowed. While it is possible to modify the validation schema in the telemetry-to-elasticsearch lambda, it is prudent to test common telemetry mappings like latitude and longitude before customizing further.

This lambda takes a template and fills it in based on the new telemetry. **You will likely need to modify the lambda to match the incoming telemetry format.** 

The template dict itself is taken from a simulation run by provisioning and running a simulation and monitoring `dt/cvra/+/cardata` and selecting a recent message.  Also note that the VIN and deviceIs must be previously provisioned and match. 

A more direct method to provision a device is using the [Create Vehicle Guide](blob/master/create_vehicle.md).

Once the lambda is customized, save everyting and monitor both the `vt/cvra/#` and `dt/cvra/#` topics and start the telemetry thing. Verify that data is coming IN from the telemetry thing on `vt/cvra/#` and that it is being properly transformed to `dt/cvra/{thingName}/cardata`. If all is correct, the vehicle icon should animate about 2x/second in the Fleet Manager UI.