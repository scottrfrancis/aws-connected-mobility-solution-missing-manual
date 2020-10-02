# Build and Deploy CMS from Source

**NB: all commands BASH shell**

1. Fresh Isengard Account
3. Created Cloud9 env in us-east-1 (region to be used for all deployment)
    -- t3.xl (to speed building, otherwise t3.small is fine); Ubuntu 18.04
    -- shutdown and expand EFS volume -- 25GB -- and restart
4. Will follow 'approach 1' from the [CMS Developmet Guide](https://quip-amazon.com/hLrnALX7bgCd/CMS-Development)
5. Install Dependencies

    * pnmp@3.5.3, nvm for Node@12.18.2, jq 

```bash
nvm install v12.18.2
nvm use v12.18.2

npm install -g pnpm@3.5.3

sudo apt install -y jq
```


* aws cli@v2, python3@3.6.9, docker@19.03.13, git@2.17.1 -- already installed
    
6. Have CSV credentials for code repos handy to copy/paste when cloning repos 
7. Clone Repos as per the Quip doc (copy/paste credentials when asked)
(copied from quip guide)
```bash
# first time only
git config --global credential.helper store

git clone https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-core -b refactor_solution_builder
git clone https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-auto-solution 
git clone https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-infrastructure-demo
```


8. Build CMS (takes about 10 min)

```bash
cd ~/environment/cdf-auto-solution/source

./bundle.bash
```

9. Build CDF (another 10 min)

```bash
cd ~/environment/cdf-core/source

./infrastructure/bundle-core.bash
```

#### Approach 1 - deploy CDF and CMS separately
10. Prep Env Vars

```bash
export env_name=development
export aws_profile=default
export region='us-east-1'
export kms_key_owner=$(aws iam get-user --query 'User.UserName' --output text)
```

```bash
export cms_admin_email=PASTE YOUR EMAIL HERE
```

11. CDF
* create Deployment Bucket
```bash
export acct_id=$(aws sts get-caller-identity --query 'Account' --output text)

export s3_bucket_name=$(aws s3api create-bucket --bucket cms-demo-refactored-$acct_id | jq '.Location' | tr -d "\"" | tr -d "/")
```

* create EC2 keypair
```bash
export keypair_name=myDemoKP
rm -f ~/.ssh/$keypair_name.pem

aws ec2 create-key-pair --key-name $keypair_name --query 'KeyMaterial' --output text >~/.ssh/$keypair_name.pem
chmod 400 ~/.ssh/$keypair_name.pem
```

**DEPLOY**
```bash
cd ~/environment/cdf-core/source
./infrastructure/deploy-core.bash -e $env_name -b $s3_bucket_name -p $keypair_name -R $region -P $aws_profile -B -y s3://$s3_bucket_name/template-snippets/ -i 0.0.0.0/0 -K $kms_key_owner
```

**IMPORTANT: Wait for the stack to complete before proceeding**
Monitor the Stack creation in the CloudFormation Console -- about 30 minutes.

```bash
# change of directory missing from QUIP dev guide
export cdf_core_stack_name=cdf-core-$env_name

cd ~/environment/cdf-auto-solution/source
./infrastructure/deploy.bash -e $env_name -b $s3_bucket_name -h $cms_admin_email -P $aws_profile -l $cdf_core_stack_name -B -R $region -K $kms_key_owner 
```
Await completion -- again about 30 minutes
The email given above should receive the activation email for FleetManager UI.

12. Run Simulation Manager

* Fetch some parameters
```bash
export simulation_manager_base_url=$(aws cloudformation list-exports --query "Exports[?Name=='cdf-core-$env_name-simulationManager-apiGatewayUrl'].Value" --output text)
export certificateId=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-certificateId'].Value" --output text)
export facadeApiFunctionName=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-facade-restApiFunctionName'].Value" --output text)

echo $simulation_manager_base_url
echo $certificateId
echo $facadeApiFunctionName
```

* Copy/Paste these values VERY CAREFULLY into Postman

* Login to the FleetManager app and capture the cognito id token
    * open debugger
    * inspect "Local Storage" from the "Application" tab
    * look for "CognitoIdentity....idToken" and copy the Value -- be sure to "Select All" and Copy, otherwise, intermediate word breaks may copy only part of the token.

_Tokens are generally only good for 60 minutes, if you receive an authorization error in calls, refresh this token._

* Inspect the body of the Postman request and adjust `deviceCount` and other parameters as needed.

* Send request by Postman and wait at least 5 minutes for simulations to be provisioned. Meanwhile, copy the simulationId from the response headers and paste into the postman environment.  You can also monitor the ECS tasks, IoT messages, and the UI itself.

* inspect the body of the Run Simulations request and adjust deviceCount as needed.

* Send the 'start' simulations request by postman. It may take a few minutes for simulations to start running. The above methods can be used to monitor progress.


### Troubleshooting and problems
* can't log in to ui -- check window.appVariables in debugger console and verify values

* SIM provisioning not completing?  Check cached Postman MAPBOX token, FacadeApiFunctionName, and other params to ensure correctness. Failures are often not surfaced other than with non-function.

* Failures after CREATE COMPLETE on sed? Check the sed calls at the end of `cdf-auto-solution/source/infrastructure/deploy.bash`, you may need to remove the superfluous default arg `''`

* Don't request MORE threads than you request devices. Could lead to errors.
