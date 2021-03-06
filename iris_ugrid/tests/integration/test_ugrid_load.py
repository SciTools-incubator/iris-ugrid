# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Integration tests for the
:mod:`iris.fileformats.ugrid_cf_reader.UGridCFReader` class.

"""

# Import iris.tests first so that some things can be initialised before
# importing anything else.
import iris.tests as tests

from gridded.pyugrid.ugrid import UGrid

from iris import Constraint
from iris.cube import CubeList, Cube

from iris_ugrid.ucube import UCube
from iris_ugrid.ugrid_cf_reader import CubeUgrid, load_cubes


@tests.skip_data
class TestUgrid(tests.IrisTest):
    def test_basic_load(self):
        file_path = tests.get_data_path(
            ("NetCDF", "unstructured_grid", "theta_nodal_xios.nc")
        )

        # cube = iris.load_cube(file_path, "theta")
        # Note: cannot use iris.load, as merge does not yet preserve
        # the cube 'ugrid' properties.

        # Here's a thing that at least works.
        loaded_cubes = CubeList(load_cubes(file_path))

        # Just check some expected details.
        self.assertEqual(len(loaded_cubes), 2)

        (cube_0,) = loaded_cubes.extract(Constraint("theta"))

        # Check the primary cube.
        self.assertIsInstance(cube_0, UCube)
        self.assertEqual(cube_0.var_name, "theta")
        self.assertEqual(cube_0.long_name, "Potential Temperature")
        self.assertEqual(cube_0.shape, (1, 6, 866))
        self.assertEqual(
            cube_0.coord_dims(cube_0.coord("time", dim_coords=True)), (0,)
        )
        self.assertEqual(cube_0.coord_dims("levels"), (1,))
        self.assertEqual(cube_0.coords(dimensions=2), [])

        # Check the cube.ugrid object.
        cubegrid = cube_0.ugrid
        self.assertIsInstance(cubegrid, CubeUgrid)
        self.assertEqual(cubegrid.cube_dim, 2)
        self.assertEqual(cubegrid.mesh_location, "node")
        self.assertEqual(cubegrid.topology_dimension, 2)
        self.assertEqual(cubegrid.node_coordinates, ["latitude", "longitude"])

        # Check cube.ugrid.grid : a gridded Grid type.
        ugrid = cubegrid.grid
        self.assertIsInstance(ugrid, UGrid)
        self.assertEqual(ugrid.mesh_name, "Mesh0")

    def test_nonugrid_load(self):
        # Check that ugrid-load can still return "ordinary" cubes.
        file_path = tests.get_data_path(
            ("NetCDF", "rotated", "xy", "rotPole_landAreaFraction.nc")
        )
        cubes = CubeList(load_cubes(file_path))
        cube = cubes[0]
        self.assertIsInstance(cube, Cube)
        self.assertFalse(isinstance(cube, UCube))


if __name__ == "__main__":
    tests.main()
