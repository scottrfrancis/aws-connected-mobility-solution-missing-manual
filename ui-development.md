# Developing Fleet Manager UI

Notes and setup for developing on the Fleet Manager UI.

### Resources

Project root is in the `cdf-auto-solution` project in the `source/packages/fleetmanager-ui` folder.

### Set up

These notes were written using WebStorm on MacOS targeting an existing CMS installation.

#### appVariable.js

The file `public/assets/appVariables.js`  provides deployment-specific variables and bindings for the UI. These values can be discovered from a deployment using scripts or inspecting cloudformation outputs. Or simply copied from the deployment S3 bucket. Or, from the deployed ui, extract them from the debug console with `window.appVariables`.

```bash
export user_pool_id=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-userPoolId'].Value" --output text)
export user_pool_client_id=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-userPoolClientId'].Value" --output text)
export cdf_auto_endpoint=$(aws cloudformation list-exports --query "Exports[?Name=='cms-$env_name-fleetmanager-apiGatewayUrl'].Value" --output text)

echo $user_pool_id
echo $user_pool_client_id
echo $cdf_auto_endpoint
```

Paste or replace values in the local file. DO NOT COMMIT THESE CHANGES TO GIT. Instead... create a named stash for the project, so you can remove/apply the variables when needed.

```bash
git add <the changed files>
git commit 

git stash save <project name>

... do other things ...

git stash apply <project name>
```

#### Install modules

```bash
cd cdf-auto-solution/source/packages/fleetmanager-ui

npm install

npm install @material-ui/styles
npm install mapbox-gl
npm install viewport-mercator-project
```

#### set the appVariables

Normally this is done as part of the bundling process.  But for local dev, use the script `setVars.sh` ONCE after changing a deployment. DO NOT COMMIT the changed appVariables. Instead stash or checkout or otherwise don't override.


#### Start and debug

```bash
npm start
```

will start the dev server and open the browser.  Log in as normal.


## Files of interest

`src/assets/appConfig.js` - some constants for timing and updates of the UI

**fleetmanager-backend**
`chalicelib/utils/cdf_auto_fleetmanager_vehicle_data_util.py` - handles the mapping from raw telemetry to the UI telemetry (expected by the UI mapping)

## Updating Chalice Apps

Chalice libraries are used extensively for Fleetmanager Backend (API gateway, other lambdae). This setup uses Lambda layers and other techniques that make direct update of function code, etc. a bit more complex.

General approach:
- run bundle.bash from the backend dir
- upload (replace) the zip file from the build dir

 