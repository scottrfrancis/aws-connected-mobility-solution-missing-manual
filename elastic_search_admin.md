# Some Common Tasks for Elasticsearch Service

In the deployment of CMS, Elasticsearch is commonly put in an isolated subnet of the VPC without any external access. To do things with ES, a python notebook is provided.


### Step 1 - ssh with a tunnel to the Bastion Host 

* ensure you have the keypair for the Bastion host locally
* connect to the bastion, forwarding port `8888`

```bash
ssh -i keypair.pem -L 8888:localhost:8888 ubuntu@<bastionIP>
```

### Step 2 - ONLY DO THIS ONCE

* install jupyterlab on bastion

```bash
pip3 install jupyterlab
```

### Step 3 - start Jupyterlab

```bash 
jupyter-lab
```

* 'command' or 'control' click on the URL in the output. Due to port forwarding, this should open in your local browser to the host

### Step 4 -- only needed once

* copy the notebook `Elasticsearch Tools.ipynb` to the lab space and open it

### Step 5 -- copy credentials

* copy/paste credentials into the notebook under 'Set Access Keys First' and then again in the python block for 'Setup configuration'

**NB-** Be sure to redact or delete credentials when you are done!

### Step 6 - Run the cells to observe

* run all the cells, one-by-one except for the last one, 'delete'
* Note the output that shows all the docs for a given index
* set the 'vin' variable as desired

### Step 7 -- run the delete cell

* as desired to remove documents for a given vin

### Step 8 - remove credentials

* delete credentials and save the doc

## Other notes

You can also use the `rmVin.py` script from the command line or even create new notebooks or tools.  You will need to export credentials as demonstrated though.