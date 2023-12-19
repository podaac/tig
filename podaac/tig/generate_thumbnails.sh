#!/usr/bin/env bash

# Prerequisites
#
# 1. Clone forge-tig-configuration into the parent dir of this repo
# 2. Install poetry using this: https://python-poetry.org/docs/#installation
# 3. In a shell, cd to the tig root dir
# 4. Make sure poetry is setup to use python less than 3.12.
#    Run commands:
#      poetry env list
#      poetry env remove <env id>  (<< this is the environment id returned from 'poetry env list', need to remove only if it's version > 3.10)
#      poetry env use python3.10
# 5. Run command "poetry install"

# HOW-TO Use
#
# Setup Collection Short Name Directories
#
#  1. Create a directory in the tig root dir named "configs"
#  2. For each collection, create a directory under "configs" dir with the collection short name
#     e.g. in repo dir: configs/ASCATA_ESDR_L2_WIND_STRESS_V1.1
#  3. Copy this script to each short name dir
#  4. Copy file "example_vars.csv" (in repo root dir) to a file called "vars.csv" in each short name dir
#  5. Update vars.csv file in each collection short name dir specifically for that collection (i.e. update var names and min/maxes)
#  6. Download a "representative" .nc granule file for that collection short name and move it into each short name dir
#  7. Update this script in each short name dir specifically for its collection short name
#     e.g. Update the input variable names or paths:  --latitude lat  TO  --latitude data_01/ku/latitude
#     e.g. Remove --time argument if the collection doesn't have a time dimension (i.e. it will just default to "time" but won't be used)
#     e.g. Change footprint-strategy parameter
#     e.g. Change tig's palette-dir parameter

# Run Script
#
#  1. Change dir to the configs/<shortname> dir
#  2. Run command "./generate_thumbnails.sh" to automatically generate the config, run tig, and open the thumbnails
#  3. The collection <shortname>.cfg file will be saved in each short name dir
#  4. Verify <shortname>.cfg file and all thumbnail images in each short name dir
#  5. Tweak var.csv or this script in short name dir if needed and re-run
#
#  NOTE: In rare cases, the generate_hitide_config.py file may need tweaking to generate a correct config file

#  Publish config files to forge-tig-configuration repo
#
#  1. Copy each short name .cfg file to the forge-tig-configuration repo under "config-files"
#  2. Update the CHANGELOG.md in forge-tig-configuration listing your changes
#  3. Commit and push the new updates in forge-tig-configuration to a new branch named "feature/<name>"
#     NOTE: The <name> can be anything you want to describe the collection you are adding
#  4. Open a PR in forge-tig-configuration for this new branch
#  5. In the PR, include reviewers James Wood and Simon Liu, and let us know it's ready in Slack

collection=$(basename "$(pwd)")

echo Generating configuration for collection $collection...

if [ -e "$collection.cfg" ]; then
    rm "$collection.cfg"
    echo "Removed existing $collection.cfg"
fi

if [ -d "images" ]; then
    rm -rf "images"
    echo "Removed existing 'images' directory"
fi

cd ../..

poetry run generate_hitide_config -g configs/$collection/*.nc -d $collection -i configs/$collection/vars.csv --latitude lat --longitude lon --time time --footprint-strategy periodic

echo "Running tig to generate thumbnail images..."

poetry run tig --input_file configs/$collection/*.nc --output_dir configs/$collection/images --config_file "$collection".cfg --palette_dir ../forge-tig-configuration/palettes

mv "$collection".cfg configs/$collection

cd configs/$collection
open images/*
