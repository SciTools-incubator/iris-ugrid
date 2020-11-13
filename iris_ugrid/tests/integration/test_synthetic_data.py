# Copyright Iris contributors
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
import shutil
import tempfile
import iris.tests as tests
from gridded.pyugrid.ugrid import UGrid
from iris import Constraint
from iris_ugrid.ugrid_cf_reader import CubeUgrid, load_cubes
from iris_ugrid.tests.synthetic_data_generator import create_synthetic_data_file

@tests.skip_data
class TestUgrid(tests.IrisTest):

    @classmethod
    def setUpClass(cls):
        # Create a temp directory for transient test files.
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        # Destroy the temp directory.
        shutil.rmtree(cls.temp_dir)

    def test_basic_load(self):
        file_path = create_synthetic_data_file(temp_file_dir=self.temp_dir, dataset_name='mesh')
#         file_path = '/project/avd/ng-vat/data/r25376_lfric_atm_files/lfric_ngvat_2D_1t_face_half_levels_main_conv_rain.nc'

        # cube = iris.load_cube(file_path, "theta")
        # Note: cannot use iris.load, as merge can not yet handle UCubes

        # Here's a thing that at least works.
        loaded_cubes = list(load_cubes(file_path))

        # Just check some expected details.
        self.assertEqual(len(loaded_cubes), 1)

        cube, = loaded_cubes

        # Check the primary cube.
        self.assertEqual(cube.var_name, "conv_rain")
        self.assertEqual(cube.long_name, "surface_convective_rainfall_rate")
        self.assertEqual(cube.shape, (2, 866))
        self.assertEqual(
            cube.coord_dims(cube.coord("time", dim_coords=True)), (0,)
        )
        self.assertEqual(cube.coord_dims("levels"), (1,))
        self.assertEqual(cube.coords(dimensions=2), [])

        # Check the cube.ugrid object.
        cubegrid = cube.ugrid
        self.assertIsInstance(cubegrid, CubeUgrid)
        self.assertEqual(cubegrid.cube_dim, 2)
        self.assertEqual(cubegrid.mesh_location, "node")
        self.assertEqual(cubegrid.topology_dimension, 2)
        self.assertEqual(cubegrid.node_coordinates, ["latitude", "longitude"])

        # Check cube.ugrid.grid : a gridded Grid type.
        ugrid = cubegrid.grid
        self.assertIsInstance(ugrid, UGrid)
        self.assertEqual(ugrid.mesh_name, "Mesh0")


if __name__ == "__main__":
    tests.main()
