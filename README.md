# Documents and tools for working with CMS

_Resources for working with the old, stable, binary release from April 2020 have been moved to the [deprecated](tree/master/deprecated) folder_

### Background

This project seeks to bridge the gap between the public documentation and resources provided with the _upcoming_ [AWS Connected Mobility Solution](#) and what is needed to really work with the solution.  If you're new to CMS, suggest reviewing the website and documents first. Then, come back here when you're ready to deploy or start developing. 

The AWS Connected Mobility Solution (CMS) is an AWS Solution, that when released, customers and partners may use to build their own workloads. CMS implements a Fleet Management system for connected vehicles that publish telematics. Some of the functions of the system include:

* visualize locations of vehicles on a map in near real time
* manage and command OTA updates to vehicle software
* detect and report anomalies and DTC events

CMS is built on the Connected Device Framework which provides

* a common system for data and event publication over MQTT using AWS IoT Core
* database systems to manage the relationships between assets, owners, users, and data
* a simulation system to help demonstrate and debug the system
* apis, user access management, lambda functions, and other components needed to deliver the system

### Using this helper project

If you need to deploy CMS, start with the [Install Guide](blob/master/Install-from-Source.md). That will lead you through building and deploying the TWO AWS CloudFormation stacks--CDF and CMS--as well as running a basic simulation to verify the deployment. A [script](blob/master/chkDeps.sh) is provided to help ensure the correct versions of tools are present.

Read the [Customization Guide](blob/master/Customization.md) to get an understanding of the options for customization that have been considered as part of putting together this project. (**NB-** the Customization Guide needs updating)

Onboard your own vehicle using the [Create Vehicle Guide](blob/master/create_vehicle.md). A [Postman Collection](blob/master/CMS-Demo.postman_collection.json) is provided to assist with creating Simulations and issuing other API calls when creating vehicles. 

To clean up the UI or otherwise explore data which is stored in Amazon Elasticsearch Service, a [Notebook](blob/master/Elasticsearch+Tools.ipynb) is provided. No instructions for configuring Jupyter, anaconda, or other means for running the notebook, but those are widely available elsewhere. A simple [python script](blob/master/rmVin.sh) is also provided that can be easily read, modified, and used to explore and manipulate Elasticsearch.

### Context Notes

These notes were developed mostly by using a dedicated AWS account with a Cloud 9 instance running as a sort of Bastion box from where various scripts and commands were run. For reference, the instance was set up as t3.xl with Ubuntu 18.04. While nothing is terribly OS-specific or non-portable, you may need to adapt various commands to your environment.