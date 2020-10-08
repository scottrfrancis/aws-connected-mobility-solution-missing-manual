# Data Flow Design in CMS/CDF

This document is a post-build description of how data flows in the AWS Connectect Mobililty Solution (built on the Connected Device Framework). The intent of this document is to describe the general flow of data so that developers building from this solution can debug issues and identify customization points.

_References_
* [Internal Draft Implementation Guide](https://drive.corp.amazon.com/documents/AWS%20SA%20PMO/SA%20wiki%20files/Solution%20Implementation%20Guide%20Template.docx)

## Device Provisioning

TBD

See (create_vehicle.md) guide for instructions to setup the asset library and enroll a new `deviceid` in the Facade. This action will bind a `deviceid` and a `VIN` among other associations. 

## Telemetry Data

CMS will ingest telemetry from IoT Topic `dt/cvra/{deviceid}/cardata` for the associated VIN (which is repeated in the body of the telemetry document). The rule `cdf_auto_fleetmanager_iot_car_data` will route these telemetry document messages to the lambda `cms-development-CMS-<id>-Fle-TelemetryRule-<id>` (or similar).

The lambda source code is in [fleetmanager-backend](cdf-auto-solution/source/packages/fleetmanager-backend/src/cdf_auto_fleetmanager_telemetry_rule.py) and makes use of JSON Schema validation in `cdf-auto-solution/source/packages/fleetmanager-backend/src/validators/telemetry_rule_validator.py`.

This 'telemetry rule' lambda flattens and filters the telemetry document then adds the document to the Elasticsearch indices `cardata` and `latest_telemetry`. (NB- this processing also pulls some attributes like trouble codes, anomalies, etc from the `shared_cardata` index -- keyed by VIN.)

The `cardata` index is ever-growing while `latest_telemetry` only holds current samples for each VIN and deviceid. (It is not clear how or where this limitation happens nor why entries seem to be 'doubled' -- one for VIN and one for deviceid.)

Fleet Manager UI does not call Elasticsearch directly, but is fronted (backed?) by Fleet Manager Backend API Gateway lambda layers application collection. This application stack is built with the Chalice libraries which require some special care in building/deploying incremental fixes.

The main function of the backend (with respect to data flow) is to respond to queries for vehicle information. Generally the UI will call `/vehicles/filter` (for a collection of vehicles defined by the filter -- in effect, a query) and `/vehicles/{vin}`.  The various queries and routes can be read from `@app.route` declarations in `cdf-auto-solution/source/packages/fleetmanager-backend/app.py`, which generally dispatches to the handlers in `cdf-auto-solution/source/packages/fleetmanager-backend/chalicelib/apis`.

These handlers query Elasticsearch for the relevant data (`latest_telemetry` index) and then call functions in `cdf-auto-solution/source/pacakges/fleetmanager-backend/chalicelib/utils/cdf_auto_fleetmanager_vehicle_data_util.py` which performs the ETL (and key changes) to convert the ES doc data to the data format for the UI.  See the `build_vehicle_list()` method to check the incoming keys (extraction), the transformation (generally unit changes), and the load (into new keys! which are generally 'flatter').

Fleet Manager UI: the component `cdf-auto-solution/source/packages/fleetmanager-ui/src/components/vehicles/VehicleDetails.jsx` hooks `useEffect()` (Fleetmanager is a React app) to call the backend API for telemetry (there may be other calls too).

Telemetry fields are selected in `components/vehicles/VehicleDetails.jsx` through inclusion of the mappings in `assets/mappings/vehicleMappings.js` which also applies some label and unit decorations to the fields.

#### Example

Suppose you wanted to add a new telemetry field -- say Battery State of Charge -- follow this general procedure (working from UI backwards):

1. modify `vehicleMappings.js` with your desired datum key, label, and units:
e.g.

```python
    ,"telemetry.batterySOC": { label: "Battery Charge", unit: "%" }
```

This will add a line "Battery Charge" to the VehicleDetails component and populate it with the data from the backend response with key 'telemetry.batterySOC' (NB- dot notation -- this is actually a nested dict).

2. modify `cdf_auto_fleetmanager_vehicle_data_util.py#build_vehicle_list()` to set the `['telemetry']['batterySOC']` key from the `incoming_obj` (TIP- use `dict#get` to set a default if the key doesn't exist).
e.g.

```python
    battery_soc = incoming_obj['_source'].get('battery_soc', 50.0)

    vehicle_template['telemetry']['batterySOC'] = round(battery_soc, 2)
```

Note the mapping from IoT Message structure (`battery_soc`) to UI structure (`['telemetry']['batterySOC']`) and the rounding as a simple transform.

3. add validation to the schema in `telemetry_rule_validator.py` to accept a new field
e.g.

```python
    battery_soc = fields.Decimal()
```

This will (optional) that a decimal (float) field with label `battery_soc` exists in every message.

4. Publish messages to `dt/cvra/{deviceid}/cardata` with the `battery_soc` field populated with a number (not enclosed in a string).

5. Sit back, observe the field in the UI and enjoy a beverage of your preference.
