# Copyright Iris contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Provides synthetic data generation capability in order to test ugrid loading and regridding.
"""
import pathlib
import subprocess
import numpy as np
import netCDF4


def make_my_datafile(n_horiz=100, n_time=2000):
    # Create test data of a particular type, with size scaling.
#    nc_filepath = target_cache_filepath(
#        basename='datafile_1', params={'nxy': n_horiz, 'nt': n_time})
#    if pathlib.Path(filename).exists():
#        # already in the cache
#        return nc_filepath
    # Create the file from scratch

    nc_filepath = '/home/h03/agemmell/AVD/ng-vat/synthetic_data_generation/test.nc'
    cdl_filepath = '/home/h03/agemmell/AVD/ng-vat/synthetic_data_generation/test.cdl'

    cdl = f"""
        netcdf {nc_filepath} {{
        dimensions:
            time = {n_time} ;
            west_east = {n_horiz * 2} ;
            south_north = {n_horiz} ;
        variables:
            double time(time) ;
                time:standard_name = "time" ;
                time:units = "hours since 1997-1-1 0:0:0" ;
            float airtemp(time, south_north, west_east) ;
                airtemp:long_name = "air_temperature" ;
                airtemp:units = "K" ;
            float lat(south_north) ;
                lat:standard_name = "latitude" ;
                lat:units = "degrees_north" ;
            float lon(west_east) ;
                lon:standard_name = "longitude" ;
                lon:units = "degrees_east" ;
        }}
    """

    with open(cdl_filepath, 'w') as filehandle:
        filehandle.write(cdl)

    completed_process = subprocess.run(
        ['ncgen', '-o'+nc_filepath, cdl_filepath])

    #subprocess.check_call(['ncgen', '-o', nc_filepath, cdl])

    print(completed_process)

    # Post-modify to define the variable data contents.
    # We could probably have another standard utility routine to do this.
    ds = netCDF4.Dataset(nc_filepath, 'r+')
    ds.variables['time'] = np.arange(n_time)
    ds.variables['lon'] = np.linspace(0., 180., n_horiz * 2)
    ds.variables['lat'] = np.linspace(-30., 70., n_horiz)
    ds.variables['airtemp'] = np.random.uniform(
        0., 35., size=(n_horiz, n_horiz))
    ds.close()

    return nc_filepath


def main():
    make_my_datafile()


if __name__ == "__main__":
    main()
