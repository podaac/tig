# TIG - Tool for Image Generation

# Table of contents

- [Overview](#overview)
- [Install poetry](#install-poetry-python-dependency-manager)
- [Build](#build)
- [How to load and use tig module](#how-to-load-and-use-tig-module)
  - [tig Input](#tig-input)
  - [tig Output](#tig-output)
- [CLI Commands](#cli-commands)

## Overview
   tig is built to be used within Cumulus ecosystem.  It is depending on cumulus CMA ([Cumulus Documentation](https://nasa.github.io/cumulus)).
   Please refer to the [Usage](#usage) section for inputs and outputs. TIG itself is a lambda function which runs on top of CMA as its lambda layer.

## Install poetry (python dependency manager)
   Install poetry following the directions here: https://python-poetry.org/docs/#installation

   - Be sure to install poetry in an isolated environment from the rest of your system.
   - Be sure to use with a python version less than 3.12

## Build
* Jenkins pipeline template is applied to this project.
* development is based on poetry python environment.  
  * poetry run pytest   // to run unit test
  * poetry install      // to install all dependencies defined in toml file
  * poetry shell        //to enter the poetry shell
  * poetry build        // to build the wheel


Unit Test can be run using the command
```shell script
poetry run pytest
```

## CLI Commands
- [Generate Thumbnails](#generate-thumbnails)
- [Generate Config File](#generate-config-file)
- [Run Tig](#run-tig)

### Generate Thumbnails
Use cli helper script to generate thumbnails for each collection (NOTE: This automatically generates the config file and runs tig)
```
Go to dir `podaac/tig` and look at generate_thumbnails.sh script.  Follow directions at top to setup.
```

### Generate Config File
Use cli to create a tig configuration for collections 
```
generate_hitide_config --granule <granule_file> -dataset-id <collection short name> --include-image-variables <csv file image variables> --longitude <lon variable> --latitude <lat variable> --time <time variable> --footprint_strategy <footprint strategy>
```

granule: a sample granule file to generate the configuration for
datset-id: collection short name 
include-image-variables: csv file of with image variable names and min max setting for each variable
longitude: longitude variable include the group if they're in group defaults to longitude
latitude: latitude variable include the group if they're in a group defaults to latitude
time: time variable include the group if they're in a group defaults to time
footprint_strategy: strategy to generate footprint will default to None options should be ["periodic", "linestring", "polar", "swot_linestring", "polarsides", "smap"]

### Run Tig
Use cli to test thumbnail image generation for a granule with configuration file and palettes

```
tig --input_file <granule> --output_dir <output_dir> --config_file <config_file> --palette_dir <palette_dir>
```

Use cli to create a tig configuration for collections 
```
generate_hitide_config --granule <granule_file> -dataset-id <collection short name> --include-image-variables <csv file image variables> --longitude <lon variable> --latitude <lat variable> --time <time variable> --footprint_strategy <footprint strategy>
```

granule: a sample granule file to generate the configuration for
datset-id: collection short name 
include-image-variables: csv file of with image variable names and min max setting for each variable
longitude: longitude variable include the group if they're in group defaults to longitude
latitude: latitude variable include the group if they're in a group defaults to latitude
time: time variable include the group if they're in a group defaults to time
footprint_strategy: strategy to generate footprint will default to None options should be ["periodic", "linestring", "polar", "swot_linestring", "polarsides", "smap"]

### Regression Test

** IN DEVELOPMENT **

Currently there is a regression test in the regression_test folder to run please use this command

Note palettes folder needs to be downloaded and included in the regression_test folder
Were not clearing out any data after test future improvement to make it an option to clear or retain data
as granules take awhile to download

```
pytest regression.py
```

### CSV Columns

variable: name of variable
min: min value for variable
max: max value for variable
palette (optional): the palette to be used for the variable
fill_missing (optional): if the generated images have missing pixel in images most likely resolution is to big, either lower resolution or we can fill in the pixels with surrounding pixel
ppd (optional): resolution of the variable, must be an integer


## How to load and use tig module
Project using tig can include/use the tig as following:
```shell script
    module "tig_module" {
      source = "https://cae-artifactory.jpl.nasa.gov/artifactory/general/gov/nasa/podaac/cumulus/tig-terraform/tig-terraform-0.3.0.zip"
      // Lambda variables
      prefix = var.prefix
      image = var.tig_image
      role = module.cumulus.lambda_processing_role_arn
      cmr_environment = var.cmr_environment
      subnet_ids = var.subnet_ids
      security_group_ids = [aws_security_group.no_ingress_all_egress.id]
      task_logs_retention_in_days = var.task_logs_retention_in_days
      config_url = "https://hitide.podaac.earthdatacloud.nasa.gov/dataset-configs"
      palette_url = "https://hitide.podaac.earthdatacloud.nasa.gov/palettes"
      memory_size = var.tig_memory_size
}

```
and the module input variables explained as below.

| field name | type | default | values | description
| ---------- | ---- | ------- | ------ | -----------
| prefix | string | (required) | | A prefix string of lambda function. Ex. prefix = "sample" , created lambda : sample-tig
| region | string | (required) | | AWS region where tig lambda is running upon.  Ex. us-west-2
| cmr_environment | string | (required) | | dev, sit, ops
| config_bucket | string | (required) | | bucket where dataset config resides
| config_dir | string | (required) | | directory where dataset config file resides. dataset-config file follows the collection_shortname.cfg pattern. Ex. MODIS_A-JPL-L2P-v2019.0.cfg
| tig_output_bucket | string | (required) | | bucket where tig file is created and written
| tig_output_dir | string | (required) | | output directory of created tig(fp) file. file will be created as s3://tig_output_bucket/tig_output_dir/collection_short_name/granule_id.png. ex. s3://my-cumulus-internaldataset-tig/ MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.png
| lambda_role | string | (required) | | aws user role to run tig lambda
| layers | list(string) | (required) | | list of layers' arn where tig runs upon.
| security_group_ids | list(string) | (required) | | security group ids
| subnet_ids | list(string) | (required) | | subnet ids where tig runs within
|config_url | string | | | the url of where to retrieve configurations
|palette_url | string | | | the url of where to retrieve palettes

ECS input variables optional

| field name | type | default | values | description
| ---------- | ---- | ------- | ------ | -----------
|tig_ecs | bool | false | | boolean to deploy ecs task
|cluster_arn | string | | | cumulus cluster arn
|desired_count | number | 1 | | number of ecs tig task to run
|log_destination_arn | string | | | A shared AWS:Log:Destination that receives logs in log_groups
|ecs_cpu | number | 700 | |cpu unit to allocate to a tig task
|ecs_memory_reservation | number | 1024 | | memory unit to allocate to tig task


Fargate input variables optional

| field name | type | default | values | description
| ---------- | ---- | ------- | ------ | -----------
|tig_fargate | bool | false | | boolean to deploy fargate task
|fargate_memory | number | 2048 | | amount of memory to allocate for a single fargate task
|fargate_cpu | number | 1024 | | amount of cpu to allocate for a single fargate task
|fargate_desired_count | number | 1 | | desired count of how many fargate task
|fargate_min_capacity | number | 1 | | minimum number of fargate task when scaling
|fargate_max_capacity | number | 1 | | maximum number of fargate task when scaling
|scale_dimensions | map(string) | null | | cloudwatch dimensions to scale on
|scale_up_cooldown | number | 60 | | seconds before able to scaling up again
|scale_down_cooldown | number | 120 | | seconds before able to scaling down again
|comparison_operator_scale_up | string | GreaterThanOrEqualToThreshold | | The arithmetic operation to use when comparing the specified Statistic and Threshold
|evaluation_periods_scale_up | number | 1 | | The number of periods over which data is compared to the specified threshold
|metric_name_scale_up | string | CPUUtilization | | name of the metric
|namespace_scale_up | string | AWS/ECS | | namespace for the alarm's associated metric
|period_scale_up | number | 60 | | period in seconds over which the specified statistic is applied
|statistic_scale_up | string | Average | | statistic to apply to the metric
|threshold_scale_up | number | 50 | | threshold for statistic to compare against to trigger step
|scale_up_step_adjustment | list | | | step adjustment to make when scaling up fargate
|comparison_operator_scale_down | string 
|evaluation_periods_scale_down | number | 1 | | The number of periods over which data is compared to the specified threshold
|metric_name_scale_down | string | CPUUtilization | | name of the metric
|namespace_scale_down | string | AWS/ECS | | namespace for the alarm's associated metric
|period_scale_down | number | 60 | | period in seconds over which the specified statistic is applied
|statistic_scale_down | string | Average | | statistic to apply to the metric
|threshold_scale_down | number | 50 | | threshold for statistic to compare against to trigger step
|scale_down_step_adjustment | list | | | step adjustment to make when scaling down fargate
|fargate_iam_role | string | | | iam arn role for fargate

module output variables

| field name | type | default | values | description
| ---------- | ---- | ------- | ------ | -----------
| tig_function_name | string | (required) | | The name of deployed tig lambda function
| tig_task_arn | string | (required) | | tig lambda aws arn

### tig Input
   Cumulus message with granules payload.  Example below
```json
{
  "granules": [
    {
      "files": [
        {
          "filename": "s3://bucket/file/with/checksum.dat",
          "checksumType": "md5",
          "checksum": "asdfdsa"
        },
        {
          "filename": "s3://bucket/file/without/checksum.dat",
        }
      ]
    }
  ]
}
```

### tig Output
   * A tig file will be created under configured tig_output_bucket and tig-output-dir.  filename as granuleId.png. Ex. s3://my-cumulus-internaldataset-tig/ MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.png
   * A file object will be appended to the files[] of processed granule. Example:
```json
{
  "granules": [
    {
      "granuleId": "20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0",
      "dataType": "MODIS_A-JPL-L2P-v2019.0",
      "sync_granule_duration": 2603,
      "files": [
        {
          "bucket": "my-protected",
          "path": "MODIS_A-JPL-L2P-v2019.0/2020/001",
          "filename": "s3://my-protected/MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc",
          "size": 18232098,
          "name": "20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc",
          "checksumType": "md5",
          "checksum": "aa5204f125ae83847b3b80fa2e571b00",
          "type": "data",
          "url_path": "{cmrMetadata.CollectionReference.ShortName}",
          "filepath": "MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc",
          "duplicate_found": true
        },
        {
          "bucket": "my-public",
          "path": "MODIS_A-JPL-L2P-v2019.0/2020/001",
          "filename": "s3://my-public/MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc.md5",
          "size": 98,
          "name": "20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc.md5",
          "type": "metadata",
          "url_path": "{cmrMetadata.CollectionReference.ShortName}",
          "filepath": "MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.nc.md5",
          "duplicate_found": true
        },
        {
          "bucket": "my-public",
          "filename": "s3://my-public/MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.cmr.json",
          "size": 1617,
          "name": "20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.cmr.json",
          "type": "metadata",
          "url_path": "{cmrMetadata.CollectionReference.ShortName}",
          "filepath": "MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.cmr.json",
          "etag": "\"3e5b9259c5ee7eae5fe71467f151498b\""
        },
        {
          "bucket": "my-internal",
          "filename": "s3://my-internal/dataset-tig/MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.png",
          "filepath": "dataset-tig/MODIS_A-JPL-L2P-v2019.0/20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.png",
          "size": 452,
          "name": "20200101000000-JPL-L2P_GHRSST-SSTskin-MODIS_A-D-v02.0-fv01.0.png",
          "type": "metadata"
        }
      ],
}
