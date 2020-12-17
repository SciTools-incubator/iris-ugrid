# Copyright Iris contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Provides synthetic data generation capability in order to test ugrid loading and regridding.
"""
from pathlib import Path
from string import Template
import subprocess

import netCDF4
import numpy as np


def create_file(
    temp_file_dir,
    dataset_name,
    dataset_type,
    n_faces=866,
    n_times=1,
    n_levels=39,
):
    """Create a synthetic NetCDF file with XIOS-like content.

    Starts from a template CDL headers string, modifies to the input dimensions
    then adds data of the correct size.

    Parameters
    ----------
    temp_file_dir : str or pathlib.Path
        The directory in which to place the created file.
    dataset_name : str
        The name for the NetCDF dataset and also the created file.
    dataset_type : str
        Name of the type of dataset to write to the file. The name = the name
        of the template CDL string file to fetch from the `mesh_headers/`
        directory.
    n_faces, n_times, n_levels : int
        Descriptors for the desired dimensions of the file's dataset.

    Returns
    -------
    str
        Path of the created NetCDF file.

    """

    # Fetch the specified CDL template type, modify the placeholders for the
    # specified dimensions.
    templates_dir = Path(__file__).parent / "mesh_headers"
    template_filepath = templates_dir.joinpath(dataset_type).with_suffix(
        ".txt"
    )
    with open(template_filepath) as file:
        template_string = Template(file.read())
    cdl = template_string.substitute(
        DATASET_NAME=dataset_name,
        NUM_NODES=n_faces + 2,
        NUM_FACES=n_faces,
        NUM_LEVELS=n_levels,
    )

    # Spawn an "ncgen" command to create an actual netcdf file from the cdl string.
    nc_filepath = Path(temp_file_dir).joinpath(dataset_name).with_suffix(".nc")
    subprocess.run(
        ["ncgen", "-o" + str(nc_filepath)],
        input=cdl,
        encoding="ascii",
        check=True,
    )

    # Load the netcdf file and post-modify it to define the variable data contents.
    ds = netCDF4.Dataset(nc_filepath, "r+")

    # Fill all data variables (both mesh and phenomenon vars) with zeros.
    for var in ds.variables.values():
        shape = list(var.shape)
        dims = var.dimensions
        # Where vars use the time dim, which is unlimited (=0), fill that with the desired length.
        shape = [
            n_times if dim == "time_counter" else size
            for dim, size in zip(dims, shape)
        ]
        data = np.zeros(shape, dtype=var.dtype)
        if len(var.dimensions) == 1 and var.dimensions[0] == var.name:
            # Fill the var with ascending values (not all zeroes), so it can be a dim-coord.
            data = np.arange(data.size, dtype=data.dtype).reshape(data.shape)
        var[:] = data

    ds.close()

    return str(nc_filepath)


def create_file__xios_half_levels_faces(
    temp_file_dir, dataset_name, n_faces=866, n_times=1
):
    """2020-12-14: still used downstream, now deprecated in favour of `create_file()`"""

    return create_file(
        temp_file_dir=temp_file_dir,
        dataset_name=dataset_name,
        dataset_type="xios_2D_face_half_levels",
        n_faces=n_faces,
        n_times=n_times,
    )
