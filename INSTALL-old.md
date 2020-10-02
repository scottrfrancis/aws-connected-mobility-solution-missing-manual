# Quick Deploy CMS and Fleet Manager

**DEPRECATED**
This guide is for the (now old) 'stable' binary release from Apr 2020. Use the new Install-from-Source guide instead.

These notes are for setting up the Automotive Connected Mobility Solution (CMS), including the Fleet Manager Application from pre-built bundles.

### Resources

Prebuilt bundles are cached in an S3 bucket hosted in other accounts. There are at least two ways to get those resources into this account.

- Pull from source account
- Push to this account (perhaps using intermediate system)

 ### General workflow
 
 1. Provision and set up a system to run the deployment scripts. For this example, this will be a Cloud 9 instance for convenience and portability.
 2. Copy all the source resources.
 3. Run scripts and perform manual procedures.
 4. Verify deployment.
 5. Start simulator to add 'cars' to FleetManager.

**NOTE**: these scripts can take hours to run--regardless of machine type.

Using Cloud9 has the advantage of very high bandwidth, which is important because lots of files will be copied. Further, the instance will keep running if the client gets disconnected, thereby keeping your deployment process going. This guide was written from a fresh Isengard account, created for a specific customer purpose, with a fresh Cloud9 installation. As the guide and scripts are modular, adapting to other setups should be fairly straightforward.

For that reason, a LONG timeout is suggested -- like 1 day. To compensate, a small machine type is acceptable, as the amount of computation is rather low.

## Step 0 -- setup a system to deploy

(Using Cloud9)

Create a Cloud9 instance in the account and region you wish to deploy into. 
- Ubuntu 18.04
- t3.small
- **IMPORTANT** Do set up a larger disk, though.  100GB or larger recommended.  If necessary, 'STOP' the EC2 instance backing Cloud9, navigate to the EBS volume, and increase it's size.  Cloud9 can be restarted from the Cloud9 console.

#### Install tools

```bash
sudo apt install -y jq 
```

**DOUBLE CHECK `aws configure` FOR DESIRED REGION**

## Step 1 -- Get the Stuff

scofranc@ can provide a signed URL to get all the assets in one go.  hkhokhar@ is the master keeper.
Getting the resources may be the most complex part of this guide and require the most coordination with others.

#### method 1 -- a big ball from signed URL

1. **NOTE** get the current signed URL, these will expire from time to time and this example is likely old
2. Download the file (.tar.bz2)
3. Launch the Cloud9 Instance
5. enter these commands in the terminal window.


```bash
cd CMS && cd $_

# replace with correnct url -- quotes are important
# wget 'current-url' -O dist.tar.bz2
wget 'https://cms-demo-code.s3.amazonaws.com/dist.tar.bz2?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIARXXQ3ZEWP5ZKMNO5/20200903/us-east-2/s3/aws4_request&X-Amz-Date=20200903T025800Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=28962e0c119ca077d616359f7dc8fbf310d4ba3e0561f37caf770e91d00d62d8' -O dist.tar.bz2

tar jxvf dist.tar.bz2
```

Verify these files are present:

```
-rw-rw-r-- ubuntu/ubuntu 63331506 2020-09-02 20:26 cdf-auto-fleetmanager-backend.zip
-rw-rw-r-- ubuntu/ubuntu 43002844 2020-09-02 20:27 cdf-auto-fleetmanager-ui.zip
-rw-rw-r-- ubuntu/ubuntu  3471360 2020-09-02 20:16 cdf-clients-20200428171955.tar
-rw-rw-r-- ubuntu/ubuntu 187781120 2020-09-02 20:16 cdf-core-20200428171955.tar
-rw-rw-r-- ubuntu/ubuntu  92674049 2020-09-02 20:29 cdf-facade-auto.zip
-rw-rw-r-- ubuntu/ubuntu  60974711 2020-09-02 20:32 cdf-infrastructure-auto.zip
-rw-rw-r-- ubuntu/ubuntu 143182673 2020-09-02 20:34 cdf-simulator.zip
-rw-rw-r-- ubuntu/ubuntu       217 2020-09-02 21:59 deploy.sh
-rw-rw-r-- ubuntu/ubuntu      1074 2020-09-02 20:57 downloadAll.sh
-rw-rw-r-- ubuntu/ubuntu       439 2020-09-02 21:59 expand.sh
-rw-rw-r-- ubuntu/ubuntu      1383 2020-09-02 20:16 fixConfigs.py
```

6. Create TWO S3 buckets. One will be used to hold resources used during the deployment, the second is populated during deployment with assets that are needed by the apps (e.g. FleetManager).

```bash
export REGION=$(aws configure get region)
export ACCT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export RSRC_BUCKET=deploy-cms-$ACCT_ID
export ASSET_BUCKET=assets-cmd-$ACCT_ID

aws s3api create-bucket --bucket $RSRC_BUCKET
aws s3api create-bucket --bucket $ASSET_BUCKET
```

Using the account id as part of the bucket name should ensure uniqueness. If desired, modify the names above.

_Problems?_ 
If the `create-bucket` command gives errors, you may need to create or replace your account credentials with `aws configure`.  If prompted, disable the automatic refresh in Cloud9.


## Step 2 -- expand and prep the repo

Scripts are provided for convenience and completeness of documentation. However, review and modifcation of these scripts is recommended prior to invocation.

1. Open the script `expand.sh` and review.  This script will 
  a. uncompress the zips and tars
  b. run a script, `fixConfigs.py`, to modify the config files
2. Open the script `fixConfigs.py` and review.
  - veify BUCKET_NAME in the environment variable is correct.
  - likewise, the region
  - modify if necessary
  - `-config.json` files will have `ORIG` suffixed if reversion is needed. modify this suffix if desired
3. the scripts DO NOT have their execute bit set by default to ensure review

```bash
chmod +x ./fixConfigs.py
chmod +x ./expand.sh

# expand will call fixConfigs
./expand.sh
```

## Step 3 -- DEPLOY!

1. Create a key pair.  Modify the variable name if desired.

```bash
export KEY_PAIR=cms-keys

aws ec2 create-key-pair --key-name $KEY_PAIR --query 'KeyMaterial' --output text >~/.ssh/$KEY_PAIR.pem
chmod 400 ~/.ssh/$KEY_PAIR.pem
```
2. Set Admin Email address. FleetManager will send an admin login email to this address.


```bash
export EMAIL='scofranc@amazon.com'
```

3. Deploy stacks and assets. Review deploy.sh for any changes, like the environment stage. Again the 'x' bit is not set to ensure review. 

```bash
chmod +x ./deploy.sh

./deploy.sh
```

Verify the configuration and proceed (Y) or abort (N).

Output is `tee`d to $LOG_FILE (default `deploy.log`) for later inspection of any errors.

**NOTE** The FIRST time you run a deployment, you will need to accept a new host into `~/.ssh/known_hosts`.  This is not automated. If you do not accept the host, later steps will fail. However, if you miss this, run `deploy.sh` again -- components deployed successfully before will be skipped and the host will be presented again so that deployment can continue.

It is also normal to have a '204' error at the end of the script.  If there are no other errors, that can be disregarded.

## Step 4 -- Activate FleetManager

1. The email address provided in Step 3 will receive a 'verification' email with a temporary password.
2. Open the URL provided in the mail, login with the temporary password and username provided
3. Change the password if prompted.
4. Supply a Mapbox token for the app.  If you don't have one, follow the link on screen to sign up for one.

**SAVE the token as it will be needed later**

You can always recover your token (or create a new one) from your Mapbox account.

## Step 5 -- Start Simulator

To start the vehicle simulator, the Simulations Manager must be enabled and provisioned with capacity. THEN, simulations can be started with a second call. These calls go to the varioss API Gateways deployed above. Postman collections are provided in the `cdf-infrastructure-auto/postman` directory if desired. 

**Manual configuration of IDs and keys are needed**

1. retrieve the CertificateId from IoT Core that was created during the deployment. As this guide was written with a fresh deployment, this is easy and there is only one certificate. For other configurations, the general steps should help.
    a. list all certificates with the command

    ```bash
    aws iot list-certificates
    ```
    
    If you have more than one, the dates can be converted with `date -d @<timestamp>`.
    
    Identify the correct certificate and copy the 'certificateId' to an environment variable. This command will extract the Id from the FIRST certificate. Verify this is the correct certificate or modify the command. The Id can also be retrieved from the IoT Console.
    
    ```bash
    export CERT_ID=$(aws iot list-certificates --query 'certificates[0].certificateId' --output text)
    ```
2. Get the Simulation Manager API Endpoint and assign to environment variable. This can be found from the API Gateway console or with the following commands. Review and modify if needed for you situation.

```bash
export MGR_ID=$(aws apigateway get-rest-apis --query "items[?name=='CDF Simulation Manager (development)'].id" --output text)
export STAGE='Prod'
export MGR_ENDPOINT=https://$MGR_ID.execute-api.$REGION.amazonaws.com/$STAGE
```

3. Set the Mapbox token retrieved in Step 4 to an environment variable.  Modify with your token inside the quotes.

```bash
export MAPBOX_TOKEN='<token string>'
```

4. Command the Simulation Manager to initialize with the curl command packaged in `dataGen.sh`. Review the parameters in the request body, specifically `threads` and `rampup` properties. Save the returned SimulationId in an environment variable

```bash
export SIM_ID=$(./dataGen.sh | tr -d '\r')
```

5. Start the simulation with the curl command packaged in `startSim.sh`.  Review the request body, specifically the `deviceCount` property, then issue the command with

```bash
./startSim.sh
```

## Step 6 -- Log in to FleetManager and Verify

The URL to FleetManager was in the email you received in Step 4.  Login with the username provided and your password (recall may have chagned it).

Verify that you have cars in the fleet list.

