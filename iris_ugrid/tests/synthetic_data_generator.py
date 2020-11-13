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
import os


def create_file__xios_half_levels_faces(temp_file_dir, dataset_name, n_faces=866, n_times=1):
    # Create a synthetic netcdf file with XIOS-like content.
    # Contains a single data variable, on mesh faces.
    # For now : omits all optional information (on edges + connectivity), *except* for face locations.
    nc_filepath = os.path.join(temp_file_dir, dataset_name + '.nc')
    cdl_filepath = os.path.join(temp_file_dir, dataset_name + '.cdl')

    cdl = f"""
        netcdf {dataset_name} {{
        dimensions:
            axis_nbounds = 2 ;
            Two = 2 ;
            nMesh2d_half_levels_node = {n_faces + 2} ;
            nMesh2d_half_levels_face = {n_faces} ;
            nMesh2d_half_levels_vertex = 4 ;
            time_counter = UNLIMITED ; // (1 currently)
        variables:
            int Mesh2d_half_levels ;
                Mesh2d_half_levels:cf_role = "mesh_topology" ;
                Mesh2d_half_levels:long_name = "Topology data of 2D unstructured mesh" ;
                Mesh2d_half_levels:topology_dimension = 2 ;
                Mesh2d_half_levels:node_coordinates = "Mesh2d_half_levels_node_x Mesh2d_half_levels_node_y" ;
                Mesh2d_half_levels:face_coordinates = "Mesh2d_half_levels_face_x Mesh2d_half_levels_face_y" ;
                Mesh2d_half_levels:face_node_connectivity = "Mesh2d_half_levels_face_nodes" ;
            float Mesh2d_half_levels_node_x(nMesh2d_half_levels_node) ;
                Mesh2d_half_levels_node_x:standard_name = "longitude" ;
                Mesh2d_half_levels_node_x:long_name = "Longitude of mesh nodes." ;
                Mesh2d_half_levels_node_x:units = "degrees_east" ;
            float Mesh2d_half_levels_node_y(nMesh2d_half_levels_node) ;
                Mesh2d_half_levels_node_y:standard_name = "latitude" ;
                Mesh2d_half_levels_node_y:long_name = "Latitude of mesh nodes." ;
                Mesh2d_half_levels_node_y:units = "degrees_north" ;
            float Mesh2d_half_levels_face_x(nMesh2d_half_levels_face) ;
                Mesh2d_half_levels_face_x:standard_name = "longitude" ;
                Mesh2d_half_levels_face_x:long_name = "Characteristic longitude of mesh faces." ;
                Mesh2d_half_levels_face_x:units = "degrees_east" ;
            float Mesh2d_half_levels_face_y(nMesh2d_half_levels_face) ;
                Mesh2d_half_levels_face_y:standard_name = "latitude" ;
                Mesh2d_half_levels_face_y:long_name = "Characteristic latitude of mesh faces." ;
                Mesh2d_half_levels_face_y:units = "degrees_north" ;
            int Mesh2d_half_levels_face_nodes(nMesh2d_half_levels_face, nMesh2d_half_levels_vertex) ;
                Mesh2d_half_levels_face_nodes:cf_role = "face_node_connectivity" ;
                Mesh2d_half_levels_face_nodes:long_name = "Maps every face to its corner nodes." ;
                Mesh2d_half_levels_face_nodes:start_index = 0 ;
            double time_instant(time_counter) ;
                time_instant:standard_name = "time" ;
                time_instant:long_name = "Time axis" ;
                time_instant:calendar = "gregorian" ;
                time_instant:units = "seconds since 2016-01-01 15:00:00" ;
                time_instant:time_origin = "2016-01-01 15:00:00" ;
                time_instant:bounds = "time_instant_bounds" ;
            double time_instant_bounds(time_counter, axis_nbounds) ;
            double conv_rain(time_counter, nMesh2d_half_levels_face) ;
                conv_rain:long_name = "surface_convective_rainfall_rate" ;
                conv_rain:units = "kg m-2 s-1" ;
                conv_rain:mesh = "Mesh2d_half_levels" ;
                conv_rain:location = "face" ;
                conv_rain:online_operation = "instant" ;
                conv_rain:interval_operation = "300 s" ;
                conv_rain:interval_write = "21600 s" ;
                conv_rain:cell_methods = "time: point (interval: 300 s)" ;
                conv_rain:coordinates = "time_instant Mesh2d_half_levels_face_y Mesh2d_half_levels_face_x" ;
        
        // global attributes:
                :name = "lfric_ngvat_2D_1t_face_half_levels_main_conv_rain" ;
                :Conventions = "UGRID" ;
        }}
    """

    with open(cdl_filepath, 'w') as filehandle:
        filehandle.write(cdl)

    completed_process = subprocess.run(
        ['ncgen', '-o'+nc_filepath, cdl_filepath])

    print(completed_process)

    # Post-modify to define the variable data contents.
    # We could probably have another standard utility routine to do this.
    ds = netCDF4.Dataset(nc_filepath, 'r+')

    # Fill all the data variables (both mesh and phenomenon vars) with zeros.
    for var in ds.variables.values():
        shape = list(var.shape)
        dims = var.dimensions
        # Where vars use the time dim, which is unlimited = 0, fill that with the desired length.
        shape = [n_times if dim == 'time_counter' else size
                 for dim, size in zip(dims, shape)]
        data = np.zeros(shape, dtype=var.dtype)
        if 'time_instant' in var.name:
            # Fill the time + time-bounds vars with ascending values (not all zeroes), so it can be a dim-coord.
            data = np.arange(data.size, dtype=data.dtype).reshape(data.shape)
        var[:] = data

    ds.close()

    return nc_filepath
