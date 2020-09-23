# Bringing up CMS from a mixed guide so capturing steps

## Repos

| repo/dir | url | branch |
| ----- | ---- | --- |
| cdf-core | https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-core | `refactor_solution_builder` |
| cdf-auto-solution | https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-auto-solution | master |
| cdf-infrastructure-demo | https://git-codecommit.us-west-2.amazonaws.com/v1/repos/cdf-infrastructure-demo | master |

## setup

Run `chkDeps.sh` to verify dependencies

install python modules
```bash
./chkDeps.sh

pip3 install -r cdf-auto-solution/source/packages/cdf-auto-fleetmanager-backend/requirements.txt 
```

Set some ENV vars and create a build bucket

```bash
export REGION=$(aws configure get region)
export ACCT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export BUILD_BUCKET=build-cms-$ACCT_ID

aws s3api create-bucket --bucket $BUILD_BUCKET
```

Create a KeyPair

```bash
export KEY_PAIR=cms-build-keys
rm -f ~/.ssh/$KEY_PAIR.pem

aws ec2 create-key-pair --key-name $KEY_PAIR --query 'KeyMaterial' --output text >~/.ssh/$KEY_PAIR.pem
chmod 400 ~/.ssh/$KEY_PAIR.pem
```

## BUILD -- CDF

1. 
```bash
cd cdf-core/source

./infrastructure/bundle-core.bash 
```

**BUG**
it is common to get errors with `cb.apply` in polyfill.  Comment out lines 61 -63 in ~/.nvm/versions/node/v12.18.3/lib/node_modules/pnpm/lib/node_modules/graceful-fs/polyfills.js
**You may need to repeat this in othe modules as well**
Because of the interelationships of various stacks, you may need multiple runs of delete to fully clean up the stacks.


2. 
using the ENV vars setup above.  You may want to modify the profile passed with `-P`
```bash
./infrastructure/package-core.bash -b $BUILD_BUCKET -R $REGION -P default
```

3. 
may want to modify the environment with `-e` to 'production' or other
be sure to use the full path for `cdf-infrastructure-demo` with `-c`
```bash
export USER=$(aws iam get-user --query 'User.UserName' --output text) 
export ENV_NAME=dev

./infrastructure/deploy-core.bash -e $ENV_NAME -b $BUILD_BUCKET -p $KEY_PAIR -R $REGION -P default -B -y s3://$BUILD_BUCKET/template-snippets/ -i 0.0.0.0/0 -c /home/ubuntu/environment/CMS/cdf-infrastructure-demo -K $USER
```

**ERRORS**
you may need to delete all the stacks or attempted deployments of stacks before retrying the deployments

**RACE CONDITIONS**
it is normal for the script to indicate an error about the stack `cdf-core-development` not existing -- CF

You may find it helpful to turn on 'View Nested' stacks to monitor creation as there are a number of nested stacks.


```
An error occurred (ValidationError) when calling the DescribeStacks operation: Stack with id cdf-core-development does not exist
```
Before proceeding, it is advised to monitor the stack creation in the CloudFormation console as this stack can take some time to complete.


## BUILD -- CMS

1.
```bash
cd cdf-auto-solution/source

./bundle.bash 
```

## DEPLOY - CMS

_ensure env vars are set as above_


```bash
export REGION=$(aws configure get region)
export ACCT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
export BUILD_BUCKET=build-cms-$ACCT_ID
export KEY_PAIR={cms-build-keys}
export USER=$(aws iam get-user --query 'User.UserName' --output text)
```

2. Package and Deploy
```bash
export ADMIN_EMAIL='scofranc@amazon.com'

#STACK_NAME=$(aws cloudformation describe-stacks --query "Stacks[].StackName" | grep "cdf-core-development-Shared-.*-Networking-" | tr -d "\", " ) 
#OUTPUTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --query 'Stacks[].Outputs[]')
#export VPC_ID=$(echo $OUTPUTS | jq '.[] | select(.OutputKey=="VpcId") | .OutputValue')
#export SECURITY_GROUP=$(echo $OUTPUTS | jq '.[] | select(.OutputKey=="CDFSecurityGroup") | .OutputValue' )
#export SUBNETS=$(echo $OUTPUTS | jq '.[] | select(.OutputKey=="PrivateSubnets") | .OutputValue' | sed -r 's/,/\\\\,/g')


./infrastructure/package.bash -b $BUILD_BUCKET -R $REGION -P default
```

DO need full stack name for cdf
The format for the subnets is odd...

need to edit `infrastructure/cloudformation/cfn-cms-core.yaml` to supply the $SUBNETS for the private subnets field due to a bug

UPDATE:

some options no longer needed.  NEW COMMAND:
```bash
export CDF_CORE_STACK_NAME=cdf-core-$ENV_NAME

./infrastructure/deploy.bash -e $ENV_NAME -b $BUILD_BUCKET -h $ADMIN_EMAIL -P default -l $CDF_CORE_STACK_NAME -B -R $REGION -K $USER
```
trying to work around a stuck elastic search deployment by making environment 'dev' instead of 'development'

.. AND ANOTHER UPDATE:
```bash
cd cdf-auto-solution/source

./infrastructure/deploy-full.bash -b $BUILD_BUCKET -h $ADMIN_EMAIL -B -R $REGION -K $KEY_OWNER -e $ENV_NAME -P default -p $KEY_PAIR
```

## Rollback and undoing

1. Delete the CMS and CDF root stacks -- they should delete all components
2. Delete the S3 bucket you created
3. Delete the keypair from both EC2 console and the local build machine `rm ~/.ssh/$KEY_PAIR*`
4. there are also some cloudfront distributions and S3 origin buckets that seem to accummulate. might want to delete those too
