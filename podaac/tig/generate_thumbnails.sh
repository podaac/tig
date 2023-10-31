#!/usr/bin/env bash

# Prerequisites
#
# 1. Clone forge-tig-configuration into the parent dir of this repo
# 2. Setup poetry and run poetry install

# HOW-TO Use
#
# Setup Collection Short Name Directories
#
#  1. Create a directory in the tig root dir named "configs"
#  2. Create directories under "configs" dir with the collection short name
#  3. Copy this script to each short name dir
#  4. Copy file "example_vars.csv" (in repo root dir) to a file called "vars.csv" in each short name dir
#  5. Update vars.csv file in each collection short name specifically for that collection (i.e. update var names and min/maxes)
#  6. Download a "representative" .nc granule file for that collection short name and move it into each short name dir
#  7. Update this script in each short name dir specifically for its collection short name (e.g. update input parameters)

# Run Script
#
#  1. Change dir to the configs/<shortname> dir
#  2. Run command "./generate_thumbnails.sh" to automatically generate the config, run tig, and open the thumbnails
#  3. The collection <shortname>.cfg file will be saved in each short name dir
#  4. Verify .cfg file and all thumbnail images in each short name dir
#  5. Tweak var.csv or this script in short name dir if needed and re-run
#
#  NOTE: In rare cases, the generate_hitide_config.py file may need tweaking to generate a correct config file

#  Publish config files to forge-tig-configuration repo
#
#  1. Copy each short name .cfg file to the forge-tig-configuration repo under "config-files"
#  2. Commit the new cfg files in forge-tig-configuration to a new branch named "feature/<name>"
#  3. Open a PR in forge-tig-configuration for this new branch

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
