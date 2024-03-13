"""Python script used to generate hitide config for forge and tig"""

import json
import csv
import click
import netCDF4 as nc

# sample = {
#   "shortName": "CYGNSS_L3_V3.0",
#   "latVar": "lat",
#   "lonVar": "lon",
#   "timeVar": "time",
#   "is360": true,
#   "tiles": {
#     "steps": [
#       30,
#       14
#     ]
#   },
#   "footprint": {
#     "findValid": true,
#     "strategy": "fixed",
#     "geospatial_lat_min": -43,
#     "geospatial_lat_max": 43,
#     "geospatial_lon_min": -180,
#     "geospatial_lon_max": 180,
#     "t": "0:*",
#     "s1": "0:*",
#     "b": "0:*",
#     "s2": "0:*"
#   },
#   "imgVariables": [
#     {
#       "id": "wind_speed",
#       "title": "Wind speed",
#       "units": "m s-1",
#       "min": "-5.0",
#       "max": "100.0",
#       "palette": "paletteMedspirationIndexed"
#     }
#   ],
#   "image": {
#     "ppd": 4,
#     "res": 8
#   },
#   "variables": [
#     "time"
#   ]
# }


def get_variables_with_paths(group, current_path=""):
    """Function to recursively get variables with group paths"""

    variables_with_paths = []
    for var_name, var_obj in group.variables.items():  # pylint: disable=unused-variable
        variable_path = current_path + "/" + var_name if current_path else var_name
        variables_with_paths.append(variable_path)
    for subgroup_name, subgroup in group.groups.items():
        subgroup_path = current_path + "/" + subgroup_name if current_path else subgroup_name
        subgroup_variables = get_variables_with_paths(subgroup, subgroup_path)
        variables_with_paths.extend(subgroup_variables)
    return variables_with_paths


def read_min_max_csv(filename):
    """ Function to read csv with variables, min, max values """

    data = {}
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Read the column headers
        for row in reader:
            key = row[0].replace("'", "").replace(",", "")  # Use the first column as the key
            values = {}
            for i in range(1, len(headers)):
                values[headers[i]] = row[i]
            data[key] = values
    return data


def generate_hitide_config(granule, dataset_id, include_image_variables, longitude, latitude, time, footprint_strategy):  # pylint: disable=too-many-branches
    """Function to generate hitide configuration"""

    dataset_config = {
        'shortName': dataset_id,
        'latVar': latitude,
        'lonVar': longitude,
        'timeVar': time,
        'is360': True,
        'tiles': {'steps': [30, 14]},
        'footprint': {},
        'imgVariables': [],
        'image': {'ppd': 16, 'res': 8},
        'variables': []
    }

    if footprint_strategy:
        if footprint_strategy == "periodic":
            dataset_config['footprint'] = {
                'strategy': footprint_strategy,
                't': '0:0,0:*',
                's1': '0:*,0:0',
                'b': '*:*,0:*',
                's2': '0:*,*:*'
            }
        elif footprint_strategy == "smap":
            dataset_config['footprint'] = {
                'strategy': footprint_strategy,
                "t": "0:0,0:*,0:0",
                "s1": "0:*,0:0,0:0",
                "b": "*:*,0:*,0:0",
                "s2": "0:*,*:*,0:0"
            }
        elif footprint_strategy == "linestring":
            dataset_config['footprint'] = {
                'strategy': footprint_strategy,
                "t": "0:*",
                "s1": "0:*",
                "b": "0:*",
                "s2": "0:*"
            }
        else:
            dataset_config['footprint'] = {
                'strategy': footprint_strategy,
                't': '0:0,0:*',
                's1': '0:*,0:0',
                'b': '*:*,0:*',
                's2': '0:*,*:*'
            }

    vars_data = {}
    if include_image_variables:
        vars_data = read_min_max_csv(include_image_variables)

    with nc.Dataset(granule, 'r') as dataset:  # pylint: disable=no-member

        data_var_names = get_variables_with_paths(dataset)
        dataset_config['variables'] = data_var_names

        try:
            for data_var in data_var_names:
                if vars_data and data_var in vars_data:
                    variable = dataset[data_var]

                    units = variable.units if 'units' in variable.ncattrs() else ''
                    long_name = variable.long_name if 'long_name' in variable.ncattrs() else ''

                    palette = 'paletteMedspirationIndexed'
                    fill_missing = False
                    ppd = 16

                    if data_var in vars_data:
                        min_val = float(vars_data[data_var]['min'])
                        max_val = float(vars_data[data_var]['max'])
                        palette = vars_data[data_var].get('palette')
                        fill_missing = vars_data[data_var].get('fill_missing', False)
                        ppd = vars_data[data_var].get('ppd', 16)
                    else:
                        min_val = variable.valid_min if 'valid_min' in variable.ncattrs() else ''
                        max_val = variable.valid_max if 'valid_max' in variable.ncattrs() else ''

                    if not palette:
                        palette = 'paletteMedspirationIndexed'

                    dataset_dict = {
                        'id': data_var,
                        'title': long_name,
                        'units': units,
                        'min': min_val,
                        'max': max_val,
                        'palette': palette
                    }

                    if fill_missing:
                        fill_missing = fill_missing.lower().strip()
                        dataset_dict['fill_missing'] = fill_missing == "true"

                    if ppd != 16 and ppd.isdigit():
                        dataset_dict['ppd'] = int(ppd)

                    dataset_config['imgVariables'].append(dataset_dict)

        except Exception as ex:  # pylint: disable=broad-exception-caught
            print(f"Error: Failed on variable {data_var}, exception: " + str(ex))

    print(json.dumps(dataset_config, indent=4))

    # Specify the file path where you want to save the JSON data
    file_path = f"{dataset_id}.cfg"

    # Open the file in write mode and write the JSON data to it
    with open(file_path, "w") as json_file:
        json.dump(dataset_config, json_file, indent=4)

    return dataset_config


@click.command()
@click.option('-g', '--granule', help='Sample granule file', required=True)
@click.option('-d', '--dataset-id', help='Collection short name', required=True)
@click.option('-i', '--include-image-variables', help='CSV file with variables, min, max settings', required=False)
@click.option('--longitude', required=False, help='longitude variable', default="longitude")
@click.option('--latitude', required=False, help='latitude variable', default="latitude")
@click.option('--time', required=False, help='time variable', default="time")
@click.option('--footprint-strategy', help='forge footprint strategy', required=False)
def generate_hitide_config_command(granule, dataset_id, include_image_variables, longitude, latitude, time, footprint_strategy):
    """Command call to generate config"""

    generate_hitide_config(granule, dataset_id, include_image_variables, longitude, latitude, time, footprint_strategy)


if __name__ == '__main__':
    generate_hitide_config_command()  # pylint: disable=no-value-for-parameter

# Example runs:
# python gen_dataset_config.py -g SWOT_L2_LR_SSH_Basic_001_001_20160901T000000_20160901T005126_DG10_01.nc -d SWOT_L2_LR_SSH_BASIC_1.0 -i SWOT_L2_LR_SSH_BASIC_1.0.csv
# python gen_dataset_config.py -g SWOT_L2_LR_SSH_WindWave_001_001_20160901T000000_20160901T005126_DG10_01.nc -d SWOT_L2_LR_SSH_WINDWAVE_1.0 -i SWOT_L2_LR_SSH_WINDWAVE_1.0.csv
# python gen_dataset_config.py -g SWOT_L2_LR_SSH_Expert_001_001_20160901T000000_20160901T005126_DG10_01.nc -d SWOT_L2_LR_SSH_EXPERT_1.0 -i SWOT_L2_LR_SSH_EXPERT_1.0.csv
