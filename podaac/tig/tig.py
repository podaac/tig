"""
================
tig.py
================

Main module for the Tool for Image Generation (TIG)
"""
# pylint: disable=invalid-name, too-many-lines

import os
import logging
import json
import matplotlib.colors as col
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
import xarray as xr
import pygeogrids.grids as grids
from scipy.optimize import leastsq

# One degree in meters
DEG_M = 111319.490793274


def distance_between_points(lon0, lons, lat0, lats):
    """
    Calculate the distance between two points on the Earth's surface
    using the haversine formula.

    Parameters:
    lon0 (float): The longitude of the first point in decimal degrees
    lons (float): The longitudes of the second point(s) in decimal degrees.
                  This can be a single value or an array-like object.
    lat0 (float): The latitude of the first point in decimal degrees
    lats (float): The latitudes of the second point(s) in decimal degrees.
                  This can be a single value or an array-like object.

    Returns:
    float or numpy.ndarray: The distance(s) between the two points in meters.

    """

    # Convert latitude and longitude to spherical coordinates in radians.
    degrees_to_radians = np.pi/180.0

    # phi = 90 - latitude
    phi1 = lat0*degrees_to_radians
    phi2 = lats*degrees_to_radians
    dphi = phi1-phi2

    # theta = longitude
    theta1 = lon0*degrees_to_radians
    theta2 = lons*degrees_to_radians
    dtheta = theta1-theta2

    # The haversine formula
    co = np.sqrt(np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dtheta/2.0)**2)
    arc = 2 * np.arcsin(co)
    dist = arc*6371.0e3

    return dist


def fit_bias(ssh, cross_track_distance,
             order=2,
             iter_max=20,
             remove_along_track_polynomial=False,
             check_bad_point_threshold=0.6):
    """
    Parameters
    ----------
    ssh : xarray.DataArray
        A 2D array of SSH data.
    cross_track_distance : xarray.DataArray
        A 2D array of cross-track distances
    order : int, optional
        Order of the polynomial to fit to the phase bias, by default 2.
    remove_along_track_polynomial : bool, optional
        Flag to remove the along-track polynomial from the SSH data, by default False.
    check_bad_point_threshold : float, optional
        Threshold for checking the percentage of bad points,
        larger than which the fitting will be skipped, by default 0.6.

    The two arrays must have the same shape. Missing values are filled with NaNs.

    Returns
    -------
    xarray.DataArray
        A 2D array of the phase bias.

    """

    def err(cc, x0, p, order):  # pylint: disable=inconsistent-return-statements
        if order == 2:
            a, b, c = cc
            return p - (a + b*x0 + c*x0**2)
        if order == 3:
            a, b, c, d = cc
            return p - (a + b*x0 + c*x0**2 + d*x0**3)

    def get_anomaly(ssha, distance, order):
        msk = np.isfinite(ssha.flatten())
        if msk.sum() < ssha.size*check_bad_point_threshold:
            return np.zeros_like(ssha)
        x = distance
        xf = x.flatten()[msk]
        pf = ssha.flatten()[msk]

        cc = [0.0]*(order+1)
        coef = leastsq(err, cc, args=(xf, pf, order))[0]
        anomaly = err(coef, x, ssha, order)

        return anomaly

    cdis = np.nanmean(cross_track_distance, axis=0)/1e3

    m1 = cdis > 0
    m2 = cdis < 0

    ano = np.where(np.isfinite(ssh), np.zeros((ssh.shape)), np.nan)
    ano[:, m1] = get_anomaly(ssh[:, m1], cross_track_distance[:, m1], order)
    ano[:, m2] = get_anomaly(ssh[:, m2], cross_track_distance[:, m2], order)

    for i in range(iter_max//2):  # pylint: disable=unused-variable
        ano[:, m1] = get_anomaly(ano[:, m1], cross_track_distance[:, m1], order)
        ano[:, m2] = get_anomaly(ano[:, m2], cross_track_distance[:, m2], order)
        # ano = np.where(np.abs(ano)>6*np.nanstd(ano),np.nan,ano)
    for i in range(iter_max//2):
        ano[:, m1] = get_anomaly(ano[:, m1], cross_track_distance[:, m1], order)
        ano[:, m2] = get_anomaly(ano[:, m2], cross_track_distance[:, m2], order)
        ano = np.where(np.abs(ano-np.nanmean(ano)) > 5*np.nanstd(ano), np.nan, ano)

    ano = np.where(np.isnan(ssh), np.nan, ano)
    # mm = m1|m2
    # ano[:,~mm]=np.nan

    if remove_along_track_polynomial:
        y = np.arange(ssh.shape[0])[:, np.newaxis]*np.ones_like(ssh)
        ano = fit_along_track_polynomial(y, ano)

    return ano


def fit_along_track_polynomial(y, din):
    """
    Computes the best-fit 2D surface of the form
    p = a + by + cy^2 + d y^3

    The best-fit surface is determined by minimizing the sum
    of squared residuals between the functional surface and the input data.

    Parameters
    ----------
    y : numpy.ndarray
        A 2D array or a list of y-coordinates.
    p : numpy.ndarray
        A 2D array or a list of data values on (y) grid.

    Returns


    """

    def err(cc, y0, p):
        a, b, c, d, e = cc
        return p - (a + b*y0 + c*y0**2 + d*y0**3+e*y0**4)

    msk = np.isfinite(din.flatten())
    if msk.sum() < din.size/3:
        return np.zeros_like(din)*np.nan
    yf = y.flatten()[msk]
    dd = din.flatten()[msk]
    cc = [1e-4, 1e-6, 1e-10, 1e-10, 1e-10]

    coef = leastsq(err, cc, args=(yf, dd))[0]

    anomaly = err(coef, y, din)  # mean surface

    return anomaly


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
                self.logger.debug(f"prev, x: {prev}, {x_val}")
                result = True
            elif x_val > 0 > prev and x_val - prev > 200:
                self.logger.debug(f"prev, x: {prev}, {x_val}")
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

    def get_lon_lat_grids(self, rows, cols):
        """
        Returns longitude and latitude grids based on extents and specified number of rows and cols
        Returns
        -------
        tuple
            Tuple containing a lon_grid and lat_grid
        """

        lons = np.arange(self.region.min_lon, self.region.max_lon, (self.region.max_lon-self.region.min_lon)/cols)
        lats = np.arange(self.region.min_lat, self.region.max_lat, (self.region.max_lat-self.region.min_lat)/rows)

        # arrage function can create an array slightly larger than cols and rows so we want to cut it
        exact_lons = lons[:cols]
        exact_lats = lats[:rows]

        lon_grid, lat_grid = np.meshgrid(exact_lons, exact_lats)
        return (lon_grid, lat_grid)

    def get_lon_lat(self, param_group=None):
        """
        Function to get the longitude masked array and latatiude masked array

        Returns
        -------
            return a longitude and latitude masked array
        """

        group, _, lon_var = self.config['lonVar'].rpartition('/')
        _, _, lat_var = self.config['latVar'].rpartition('/')

        if param_group:
            group = param_group
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

    def get_swot_expert_data(self, group):
        """Function to get data for swot expert collection specifically for ssha_karin_2 data."""

        local_dataset = xr.open_dataset(
            self.input_file, group=group, decode_times=False)
        flag = local_dataset.ancillary_surface_classification_flag
        lon = local_dataset.longitude.values
        lat = local_dataset.latitude.values

        cross_track_distance = local_dataset.cross_track_distance.values
        ssha = local_dataset.ssha_karin_2
        ssha_1 = np.where(flag == 0, ssha, np.nan)
        local_dataset.close()

        lon_segments = []
        lat_segments = []
        data_segments = []
        n_segments = 16
        total_num_lines = local_dataset.num_lines.size
        # make sure it is even
        n_per_segment = int(np.ceil(total_num_lines / n_segments))//2*2

        for n in range(n_segments):

            # add buffer to make sure we have enough data to fit
            i0 = n*n_per_segment-n_per_segment//2
            # add buffer to make sure we have enough data to fit
            i1 = (n+1)*n_per_segment + n_per_segment//2
            if n == 0:
                i0 = 0
            elif n == n_segments-1:
                i1 = total_num_lines

            data_modify = ssha_1[i0:i1, :]
            new_distance = cross_track_distance[i0:i1, :]

            ssha_2 = fit_bias(
                data_modify, new_distance,
                check_bad_point_threshold=0.1,
                remove_along_track_polynomial=False
            )

            mask_distance = np.nanmean(new_distance, axis=0)
            msk = (np.abs(mask_distance) < 60e3) & (
                np.abs(mask_distance) > 10e3)
            ssha_2[:, ~msk] = np.nan

            # make index to put the data back
            ii0 = n*n_per_segment
            ii1 = ii0+n_per_segment

            if n == n_segments-1:
                ii1 = total_num_lines

            lon_modify = lon[ii0:ii1, :]
            lat_modify = lat[ii0:ii1, :]

            lon_modify[:, ~msk] = np.nan
            lat_modify[:, ~msk] = np.nan

            if n == 0:
                data_segments.append(ssha_2[0:ii1, :])
            elif n == n_segments-1:
                data_segments.append(ssha_2[n_per_segment//2:, :])
            else:
                data_segments.append(
                    ssha_2[n_per_segment//2:n_per_segment+n_per_segment//2])

            lon_segments.append(lon_modify)
            lat_segments.append(lat_modify)

        lon_array = np.concatenate([segment.flatten()
                                   for segment in lon_segments])
        lat_array = np.concatenate([segment.flatten()
                                   for segment in lat_segments])
        var_array = np.concatenate([segment.flatten()
                                   for segment in data_segments])

        return lon_array, lat_array, var_array

    def generate_images(self, image_format='png', world_file=False, granule_id=""):
        """
        Generates images for each configured variable in a NetCDF file.
        Parameters
        ----------
        image_format : string
            Any output image formatted supported by matplotlib
        world_file : bool
            Output an Esri world file for each image that can be used by GIS tools
       granule_id : string
            The granule_id of the granule file
        Returns
        -------
        list
            List of output image file locations
        """

        self.logger.info(f"\nProcessing {self.input_file}")
        output_images = []
        if self.config.get('multi_lon_lat'):
            for group in self.config.get('multi_groups'):
                output_images += self.generate_images_group(image_format, world_file, granule_id, group=group)
        else:
            output_images = self.generate_images_group(image_format, world_file, granule_id, group=None)
        return output_images

    def generate_images_group(self, image_format='png', world_file=False, granule_id="", group=None):
        """
        Generates images for each configured variable in a NetCDF file.
        Parameters
        ----------
        image_format : string
            Any output image formatted supported by matplotlib
        world_file : bool
            Output an Esri world file for each image that can be used by GIS tools
        granule_id : string
            The granule_id of the granule file
        param_group : string
            The group name in which the dataset file will be open with
        Returns
        -------
        list
            List of dictionary with image_file location, variable and group
        """

        # Only use alpha channel with PNGs
        if image_format == 'png':
            alpha = True
        else:
            self.logger.debug("No alpha channel")
            alpha = False

        lon_array, lat_array = self.get_lon_lat(param_group=group)

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

        if self.config.get('global_grid', False):
            region = (-90, 90, -180, 180)

        self.logger.info(f"region: {region}")
        height_deg = region[1] - region[0]
        width_deg = region[3] - region[2]
        self.region = Region(region)

        if self.are_all_lon_lat_invalid(lon_array, lat_array):
            raise Exception("Can't generate images for empty granule")

        output_dimensions = (int(height_deg * self.ppd), int(width_deg * self.ppd))
        (self.rows, self.cols) = output_dimensions

        # Process each variable configured for the dataset
        output_images = []

        if self.variables is None:
            self.variables = self.config.get("imgVariables", [])

        for var in self.variables:

            override_rows = None
            override_cols = None

            if var.get('ppd'):
                new_dimensions = (int(height_deg * var.get('ppd')), int(width_deg * var.get('ppd')))
                override_rows, override_cols = new_dimensions

            output_image_file = self.process_variable(var,
                                                      lon_array,
                                                      lat_array,
                                                      alpha,
                                                      image_format,
                                                      world_file,
                                                      granule_id,
                                                      group,
                                                      override_rows,
                                                      override_cols)
            if output_image_file is not None:
                output_images.append({'image_file': output_image_file, 'variable': var['id'], 'group': group})

        self.logger.info("Finished processing variables")
        return output_images

    def get_non_black_neighbor_value(self, img, x, y):
        """
        Get the value of a neighboring pixel that isn't black for a given pixel coordinate in an image array.

        Parameters:
        - img: NumPy array representing the image.
        - x: Row coordinate of the pixel.
        - y: Column coordinate of the pixel.

        Returns:
        - Value of a neighboring pixel that isn't black, or None if all neighbors are black.
        """
        height, width = img.shape[:2]

        for i in range(-1, 2):
            for j in range(-1, 2):
                # Skip the central pixel itself
                if i == 0 and j == 0:
                    continue

                # Calculate neighboring pixel coordinates
                neighbor_x = x + i
                neighbor_y = y + j

                # Check if the neighbor is within the image bounds
                if 0 <= neighbor_x < height and 0 <= neighbor_y < width:
                    neighbor_value = img[neighbor_x, neighbor_y]

                    # Check if the neighbor is not black (assuming black is 0)
                    if not np.isnan(neighbor_value):
                        return neighbor_value

        # Return None if all neighbors are black
        return None

    def fill_swath_with_neighboring_pixel(self, output_array):
        """
        This method fills NaN values in the input image with RGB values from neighboring pixels.
        The replacement values are chosen randomly from non-missing pixel portions of the image.
        The probability of selecting a value is inversely proportional to the distance from the NaN position.

        The function uses a helper function `non_nan_neighbors` to check if the neighboring values of a given
        position are not NaN. It then retrieves x and y coordinates of NaN values with at least one non-NaN neighbor
        and fills the NaN values in the copy with values from these neighbors.

        Parameters:
        - output_array (numpy.ndarray): Input image with missing data represented as NaN values.

        Returns:
        numpy.ndarray: (numpy.ndarray): Output image with missing values surrounded by data filled in.
        """

        def non_nan_neighbors(arr, x, y):
            """
            Check if there is at least one non-NaN neighbor for a given position.

            Parameters:
            - arr (numpy.ndarray): Input array.
            - x (int): x-coordinate of the position.
            - y (int): y-coordinate of the position.

            Returns:
            bool: True if there is at least one non-NaN neighbor, False otherwise.
            """
            neighbors = [
                (x-1, y), (x+1, y),  # Left and right neighbors
                (x, y-1), (x, y+1)   # Up and down neighbors
            ]

            return any(0 <= i < arr.shape[0] and 0 <= j < arr.shape[1] and not np.isnan(arr[i, j]) for i, j in neighbors)

        # Get the indices of NaN values
        img_with_neighbor_filled = output_array.copy()
        x_swath, y_swath = zip(*[(x, y) for x, y in zip(*np.where(np.isnan(output_array))) if non_nan_neighbors(output_array, x, y)])

        for index, (x, y) in enumerate(zip(x_swath, y_swath)):  # pylint: disable=unused-variable
            value = self.get_non_black_neighbor_value(output_array, x, y)
            if value is not None:
                img_with_neighbor_filled[x, y] = value

        return img_with_neighbor_filled

    def are_all_lon_lat_invalid(self, lon, lat):
        """
        Checks if all coordinate pairs contain at least one invalid value.

        Parameters:
            lon (array-like): Array of longitude values.
            lat (array-like): Array of latitude values.
        Returns:
            bool: True if all coordinate pairs have at least one invalid value,
                  False if there exists at least one valid coordinate pair.
        """
        try:
            # Define valid ranges
            valid_lon_mask = (lon >= -180) & (lon <= 180)
            valid_lat_mask = (lat >= -90) & (lat <= 90)
            # Check if any pair is completely valid
            valid_pairs = valid_lon_mask & valid_lat_mask
            return not valid_pairs.any()
        except Exception as e:
            raise RuntimeError(f"Error checking longitude/latitude validity: {e}") from e

    def process_variable(self,
                         var,
                         lon_array,
                         lat_array,
                         alpha,
                         image_format='png',
                         world_file=False,
                         granule_id="",
                         param_group=None,
                         override_rows=None,
                         override_cols=None):
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
        world_file : bool
            Output an Esri world file for each image that can be used by GIS tools
        granule_id : string
            The granule_id of the granule file
        param_group : string
            The group name in which the dataset file will be open with
        Returns
        -------
        list
            List of output image file locations
        """

        # Get variable name
        config_variable = var['id']
        self.logger.info(f'variable: {config_variable}')

        group, _, variable = config_variable.rpartition('/')
        if param_group:
            group = param_group
        local_dataset = xr.open_dataset(self.input_file, group=group, decode_times=False)

        # Get variable array and fill value
        var_array = local_dataset[variable].to_masked_array().flatten()

        try:
            fill_value = local_dataset[variable].encoding['_FillValue']
        except KeyError:
            # if no fill value get fill value from configuration if defined
            fill_value = var.get('fill_value')
            if fill_value is None:
                raise KeyError(f'There is no fill value for variable {variable}') from KeyError
        local_dataset.close()

        # Get palette info
        self.logger.info(f"palette: {var['palette']}")
        colormap = load_json_palette(self.palette_dir, var['palette'], alpha)

        # Set the output location
        group_string = group.strip('/').replace('/', '.').replace(" ", "_")
        file_name = '.'.join(x for x in [granule_id, group_string, variable, image_format] if x)
        output_location = "{}/{}".format(self.output_dir, file_name)

        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        rows = override_rows if override_rows else self.rows
        cols = override_cols if override_cols else self.cols

        if var.get('is_swot_expert') and var.get('id') == "ssha_karin_2":
            lon_array, lat_array, var_array = self.get_swot_expert_data(group_string)

        try:
            # Generate an array to populate data for image output
            output_vals = self.generate_image_output(var_array,
                                                     lon_array,
                                                     lat_array,
                                                     fill_value,
                                                     rows,
                                                     cols)
            output_vals[output_vals == fill_value] = np.nan
            out_array = np.flip(output_vals.flatten().reshape(rows, cols), 0)

            if var.get('fill_missing'):
                out_array = self.fill_swath_with_neighboring_pixel(out_array)

            # Color the image output array and save to a file
            plt.imsave(output_location,
                       out_array,
                       vmin=float(var['min']),
                       vmax=float(var['max']),
                       cmap=colormap,
                       format=image_format)

            self.logger.info(f"Wrote {output_location}")

            # Create world file if specified
            if world_file:
                output_wld = output_location.replace(image_format, 'wld')
                wld_string = create_world_file((self.region.max_lon-self.region.min_lon)/cols,
                                               (self.region.max_lat-self.region.min_lat)/rows,
                                               self.region.max_lat,
                                               self.region.min_lon)
                with open(output_wld, 'w') as wld:
                    wld.write(wld_string)
                self.logger.info(f"Wrote {output_wld}")

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
                              rows,
                              cols
                              ):
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
        Returns
        -------
        numpy.ndarray
            An array of values that matches image output dimensions
        """

        # Generate a grid matching the output image
        lon_grid, lat_grid = self.get_lon_lat_grids(rows, cols)
        image_grid = grids.BasicGrid(lon_grid.flatten(),
                                     lat_grid.flatten(),
                                     shape=(rows, cols))

        # Generate a grid matching the dataset
        data_grid = grids.BasicGrid(lon_array.flatten(), lat_array.flatten())

        # Generate a look-up table between the image and data grid
        lut = data_grid.calc_lut(image_grid)

        # Generate an array for output values
        output_vals = np.full(rows * cols, fill_value, dtype=np.float64)

        # Iterate through valid values in var_array, remove nan values
        valid_values = ~np.isnan(var_array)
        lut = lut[valid_values]
        var_array = var_array[valid_values]

        # Find valid indices within the bounds of output_vals
        valid_indices_lut = (0 <= lut) & (lut < len(output_vals))
        # Filter lut to include only valid indices
        lut = lut[valid_indices_lut]

        # Replace the loop with NumPy indexing
        valid_indices = np.where(output_vals[lut] == fill_value)[0]
        output_vals[lut[valid_indices]] = var_array[valid_indices]

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
    try:
        matplotlib.colormaps.register(cmap=cmap)
    except ValueError:
        # palette register via other images
        pass

    return matplotlib.colormaps[palette_name]


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
