"""
================
tig.py
================

Main module for the Tool for Image Generation (TIG)
"""
import os
import logging
import json
import matplotlib.colors as col
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import xarray as xr
import pygeogrids.grids as grids

# One degree in meters
DEG_M = 111319.490793274


class TIG():
    """
    TIG is a class used for image generation. It must be initialized
    with an input NetCDF file, output directory, a config file, and
    a palette file. The actual image generation is handled by the
    generate_images function. Resulting images will be written to the
    output directory.
    """

    def __init__(self, input_file, output_dir, config_file, palette_dir, variables=None, logger=logging):
        self.input_file = input_file
        self.output_dir = output_dir
        self.palette_dir = palette_dir
        self.config = read_config(config_file)
        self.ppd = int(self.config['image']['ppd'])
        self.rows = 0
        self.cols = 0
        self.region = Region([-90, 90, -180, 180])
        self.logger = logger
        self.variables = variables

    def _crosses(self, lons):
        prev = None
        result = False
        for x_val in lons.flatten():
            if prev is None:
                prev = x_val
                continue
            if prev > 0 > x_val and prev - x_val > 200:
                self.logger.debug("prev, x: %s, %s", prev, x_val)
                result = True
            elif x_val > 0 > prev and x_val - prev > 200:
                self.logger.debug("prev, x: %s, %s", prev, x_val)
                result = True
        return result

    def crosses_antimeridian(self, lons):
        """
        Checks if an array of longitudinal values crosses the antimeridian
        Parameters
        ----------
        lons : numpy.ndarray
            An array of longitudinal values
        Returns
        -------
        bool
            True if data crosses antimeridian.
        """
        if len(lons.shape) == 1:
            if self._crosses(lons):
                return True
        else:
            for x_val in range(lons.shape[0]):
                if ma.any(lons[x_val, :]):
                    if self._crosses(lons[x_val, :]):
                        return True
                    break
            if self._crosses(lons[:, 0]):
                return True
            if self._crosses(lons[lons.shape[0]-1, :]):
                return True
            if self._crosses(lons[:, lons.shape[1]-1]):
                return True
        return False

    def get_lon_lat_grids(self):
        """
        Returns longitude and latitude grids based on extents and specified number of rows and cols
        Returns
        -------
        tuple
            Tuple containing a lon_grid and lat_grid
        """
        lons = np.arange(self.region.min_lon, self.region.max_lon, (self.region.max_lon-self.region.min_lon)/self.cols)
        lats = np.arange(self.region.min_lat, self.region.max_lat, (self.region.max_lat-self.region.min_lat)/self.rows)

        # arrage function can create an array slightly larger than cols and rows so we want to cut it
        exact_lons = lons[:self.cols]
        exact_lats = lats[:self.rows]

        lon_grid, lat_grid = np.meshgrid(exact_lons, exact_lats)
        return(lon_grid, lat_grid)

    def get_lon_lat(self):
        """
        Function to get the longitude masked array and latatiude masked array

        Returns
        -------
            return a longitude and latitude masked array
        """

        group, _, lon_var = self.config['lonVar'].rpartition('/')
        _, _, lat_var = self.config['latVar'].rpartition('/')
        local_dataset = xr.open_dataset(self.input_file, group=group, decode_times=False)

        lon_array = local_dataset[lon_var].to_masked_array()
        lat_array = local_dataset[lat_var].to_masked_array()

        # Need to check if the array crosses the antimeridian
        if 'is360' in self.config:
            is360 = self.config['is360']
        else:
            self.logger.debug("Calculating is 360")
            lon_scale = local_dataset[lon_var].encoding['scale_factor']
            lon_offset = local_dataset[lon_var].encoding['add_offset']
            is360 = is_360(local_dataset[lon_var], lon_scale, lon_offset)
        if is360:
            self.logger.debug("Is 360")
            lon_array = ((lon_array + 180) % 360.0) - 180
        lon_array = ma.masked_where(abs(lon_array) > 180, lon_array)
        lat_array = ma.masked_where(abs(lat_array) > 90, lat_array)

        local_dataset.close()
        return lon_array, lat_array

    def generate_images(self, image_format='png', nearest=False, world_file=False, granule_id=""):
        """
        Generates images for each configured variable in a NetCDF file.
        Parameters
        ----------
        image_format : string
            Any output image formatted supported by matplotlib
        nearest : bool
            Fill in values from the nearest grid cell to match pixel resolution
        world_file : bool
            Output an Esri world file for each image that can be used by GIS tools
        Returns
        -------
        list
            List of output image file locations
        """

        self.logger.info("\nProcessing %s", self.input_file)

        # Only use alpha channel with PNGs
        if image_format == 'png':
            alpha = True
        else:
            self.logger.debug("No alpha channel")
            alpha = False

        lon_array, lat_array = self.get_lon_lat()

        # Get Bounds of the dataset
        eastern = lon_array.max()
        western = lon_array.min()
        northern = lat_array.max()
        southern = lat_array.min()

        # Calculate output dimensions
        if not self.crosses_antimeridian(lon_array):
            self.logger.debug("Region does not crosses 180/-180")
            region = (southern, northern, western, eastern)
        else:
            # Image spans antimeridian, wrap it.
            self.logger.debug("Region crosses 180/-180")
            region = (southern, northern, -180, 180)
        self.logger.info("region: %s", str(region))
        height_deg = region[1] - region[0]
        width_deg = region[3] - region[2]
        self.region = Region(region)

        output_dimensions = (int(height_deg * self.ppd), int(width_deg * self.ppd))
        (self.rows, self.cols) = output_dimensions

        # Process each variable configured for the dataset
        output_images = []

        if self.variables is None:
            self.variables = self.config.get("imgVariables", [])

        for var in self.variables:
            output_image_file = self.process_variable(var,
                                                      lon_array,
                                                      lat_array,
                                                      alpha,
                                                      image_format,
                                                      nearest,
                                                      world_file,
                                                      granule_id)
            if output_image_file is not None:
                output_images.append(output_image_file)

        self.logger.info("Finished processing variables")
        return output_images

    def process_variable(self,
                         var,
                         lon_array,
                         lat_array,
                         alpha,
                         image_format='png',
                         nearest=False,
                         world_file=False,
                         granule_id=""):
        """
        Processes an invidual variable to generate an image
        Parameters
        ----------
        var : dict
            A dictionary object containing configuration parameters for a variable
        lon_array : numpy.ndarray
            An array of longitudinal values
        lat_array : numpy.ndarray
            An array of latitude values
        alpha : bool
            Whether or not the image should contain an alpha channel
        image_format : string
            Any output image formatted supported by imageio
        nearest : bool
            Fill in values from the nearest grid cell to match pixel resolution
        world_file : bool
            Output an Esri world file for each image that can be used by GIS tools
        Returns
        -------
        list
            List of output image file locations
        """

        # Get variable name
        config_variable = var['id']
        self.logger.info('variable: %s', config_variable)

        group, _, variable = config_variable.rpartition('/')
        local_dataset = xr.open_dataset(self.input_file, group=group, decode_times=False)

        # Get variable array and fill value
        var_array = local_dataset[variable].to_masked_array().flatten()

        try:
            fill_value = local_dataset[variable].encoding['_FillValue']
        except KeyError:
            # if no fill value get fill value from configuration if defined
            fill_value = var.get('fill_value')
            if fill_value is None:
                raise Exception(f'There is no fill value for variable {variable}') from KeyError
        local_dataset.close()

        # Get palette info
        self.logger.info('palette: %s', var['palette'])
        colormap = load_json_palette(self.palette_dir, var['palette'], alpha)

        # Set the output location
        group_string = group.strip('/').replace('/', '.')
        file_name = '.'.join(x for x in [granule_id, group_string, variable, image_format] if x)
        output_location = "{}/{}".format(self.output_dir, file_name)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        try:
            # Generate an array to populate data for image output
            output_vals = self.generate_image_output(var_array,
                                                     lon_array,
                                                     lat_array,
                                                     fill_value,
                                                     nearest)
            output_vals[output_vals == fill_value] = np.nan
            out_array = np.flip(output_vals.flatten().reshape(self.rows, self.cols), 0)
            # Color the image output array and save to a file
            plt.imsave(output_location,
                       out_array,
                       vmin=float(var['min']),
                       vmax=float(var['max']),
                       cmap=colormap,
                       format=image_format)
            self.logger.info("Wrote %s", output_location)

            # Create world file if specified
            if world_file:
                output_wld = output_location.replace(image_format, 'wld')
                wld_string = create_world_file((self.region.max_lon-self.region.min_lon)/self.cols,
                                               (self.region.max_lat-self.region.min_lat)/self.rows,
                                               self.region.max_lat,
                                               self.region.min_lon)
                with open(output_wld, 'w') as wld:
                    wld.write(wld_string)
                self.logger.info("Wrote %s", output_wld)

        except grids.GridDefinitionError:
            self.logger.warning("Could not grid variable %s", variable.split('/')[-1], exc_info=True)
            raise
        except (ValueError, IndexError):
            self.logger.warning("Could not image variable %s", variable.split('/')[-1], exc_info=True)
            raise

        # Return output image location
        return output_location

    def generate_image_output(self,
                              var_array,
                              lon_array,
                              lat_array,
                              fill_value,
                              nearest=False):
        """
        Generates output that matches image extents using discrete global grids
        Parameters
        ----------
        var_array : numpy.ndarray
            An array of variable values
        lon_array : numpy.ndarray
            An array of longitudinal values
        lat_array : numpy.ndarray
            An array of latitude values
        fill_value : float
            The fill value used in the variable array
        nearest : bool
            Fill in values from the nearest grid cell to match pixel resolution
        Returns
        -------
        numpy.ndarray
            An array of values that matches image output dimensions
        """

        # Generate a grid matching the output image
        image_grid = grids.BasicGrid(self.get_lon_lat_grids()[0].flatten(),
                                     self.get_lon_lat_grids()[1].flatten(),
                                     shape=(self.rows, self.cols))

        # Generate a grid matching the dataset
        data_grid = grids.BasicGrid(lon_array.flatten(), lat_array.flatten())

        # Generate a look-up table between the image and data grid
        lut = data_grid.calc_lut(image_grid)

        # Generate an array for output values
        output_vals = np.full(self.rows * self.cols, fill_value, dtype=np.float64)

        # Use values nearest to grid cells within max_dist
        if nearest:
            # Get grid points
            gpis, gridlons, gridlats = image_grid.get_grid_points()

            max_dist = DEG_M/self.ppd
            for i, idx in enumerate(gpis):
                ngpi, distance = data_grid.find_nearest_gpi(gridlons[idx],
                                                            gridlats[idx])
                if distance <= max_dist:
                    value = var_array[ngpi]
                    if value != np.isnan:
                        if output_vals[i] == fill_value:
                            output_vals[i] = value
                        else:
                            # average two values if they fall in the same grid cell
                            output_vals[i] = (output_vals[i] + value) / 2
                    else:
                        output_vals[i] = fill_value
        # Use values only within grid cells
        else:
            # remove nan values
            lut = lut[~(np.isnan(var_array))]
            var_array = var_array[~(np.isnan(var_array))]
            for i, val in enumerate(var_array):
                idx = lut[i]
                try:
                    if output_vals[idx] == fill_value:
                        output_vals[idx] = val
                    else:
                        # average two values if they fall in the same grid cell
                        output_vals[idx] = (output_vals[idx] + val) / 2
                # skip rare situations where we encounter nan location values
                except IndexError:
                    continue

        # Return output values
        return output_vals


class Region():
    """
    Object that stores the extents of a given region
    """

    def __init__(self, region):
        self._min_lat = region[0]
        self._max_lat = region[1]
        self._min_lon = region[2]
        self._max_lon = region[3]

    @property
    def min_lat(self):
        """Minimum latitude"""
        return self._min_lat

    @property
    def max_lat(self):
        """Maximum latitude"""
        return self._max_lat

    @property
    def min_lon(self):
        """Minimum longitude"""
        return self._min_lon

    @property
    def max_lon(self):
        """Maximum longitude"""
        return self._max_lon


def create_world_file(x_size, y_size, max_lat, min_lon):
    """
    Creates an Esri world file for georeferencing.
    Parameters
    ----------
    x_size : float
        Pixel size in the x direction
    y_size : float
        Pixel size in the y direction
    max_lat : float
        The maximum latitude or y value
    min_lon : float
        The maximum longitude or x value
    Returns
    -------
    string
        An Esri world file string
    """
    wld_string = str(x_size)
    wld_string += '\n0.00000000000000' + '\n0.00000000000000'
    wld_string += '\n' + str(y_size * -1)
    wld_string += '\n' + str(min_lon + 0.5 * x_size)
    wld_string += '\n' + str(max_lat + 0.5 * (y_size * -1))
    return wld_string


def load_json_palette(palette_dir, palette_name, alpha):
    """
    Parses and registers a JSON color palette file.
    Parameters
    ----------
    palette_dir : string
        Path to directory with palette files
    palette_name : string
        The name of the colormap
    alpha : bool
        Whether or not the image should contain an alpha channel
    Returns
    -------
    Colormap
    """

    palette_file = f'{palette_dir}/{palette_name}.json'
    with open(palette_file) as cmap_file:
        palette = json.load(cmap_file)

    if alpha:
        # pylint: disable=R1728
        colors = [tuple([int(x)/255 for x in (str(y['color']+',255')).split(',')])
                  for y in palette['Palette']['values']['value']]
    else:
        # pylint: disable=R1728
        colors = [tuple([int(x) for x in y['color'].split(',')])
                  for y in palette['Palette']['values']['value']]

    cmap = col.ListedColormap(colors, palette_name)
    cm.register_cmap(cmap=cmap)

    return cm.get_cmap(palette_name)


def vals_to_rgba(vals, min_val, max_val, colormap, transparency=True, no_data=None):
    """
    Converts data values to RGBA values based on colormap.
    Parameters
    ----------
    vals : numpy.ndarray
        A list of data values
    min_val : float
        The minimum data value for the colormap
    max_val : float
        The maximum data value for the colormap
    colormap : Colormap
        A registered matplotlib Colormap to be used
    transparency: bool
        Whether or not the alpha channel should be included
    no_data: float
        Optional no data value that will be transparent
    Returns
    -------
    list
        List of values as Red, Green, Blue, and Alpha (if true)
    """
    cmap = plt.get_cmap(colormap)
    max_val = float(max_val)
    min_val = float(min_val)
    drange = max_val - min_val
    output = np.zeros((vals.size, 4 if transparency else 3), dtype=np.uint8)
    for i, val in enumerate(vals):
        val = float(val)
        if no_data is not None:
            no_data = float(no_data)
        if val > max_val:
            val = max_val
        if val < min_val and no_data != val:
            val = min_val

        if val == no_data:
            alpha = 0
        else:
            alpha = 255

        norm_val = (val - min_val) / (drange)
        (float_r, float_g, float_b, _float_a) = cmap(norm_val)

        int_r = int(round(float_r * 255))
        int_g = int(round(float_g * 255))
        int_b = int(round(float_b * 255))
        if transparency:
            output[i] = [int_r, int_g, int_b, alpha]
        else:
            output[i] = [int_r, int_g, int_b]
    return output


def is_360(lon_var, scale, offset):
    """
    Determine if given dataset is a '360' dataset or not.
    Parameters
    ----------
    lon_var : xr.DataArray
        The lon variable from the xarray Dataset
    scale : float
        Used to remove scale and offset for easier calculation
    offset : float
        Used to remove scale and offset for easier calculation
    Returns
    -------
    bool
        True if dataset is 360, False if not. Defaults to False.
    """
    valid_min = lon_var.attrs.get('valid_min', None)

    if valid_min is None or valid_min > 0:
        var_min = remove_scale_offset(np.amin(lon_var.values), scale, offset)
        var_max = remove_scale_offset(np.amax(lon_var.values), scale, offset)

        if var_min < 0:
            return False
        if var_max > 180:
            return True

    if valid_min == 0:
        return True
    if valid_min < 0:
        return False

    return False


def read_config(config_file):
    """Parses a JSON dataset config file"""
    config = None
    with open(config_file) as config_f:
        config = json.load(config_f)
    return config


def remove_scale_offset(value, scale, offset):
    """Remove scale and offset from the given value"""
    return (value * scale) - offset


def configure_logging() -> None:
    """
    Sets up basic python logging

    Returns
    -------

    """
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")


def main() -> None:
    """
    Main entry point for the application.

    Returns
    -------

    """
    configure_logging()


if __name__ == '__main__':
    main()
