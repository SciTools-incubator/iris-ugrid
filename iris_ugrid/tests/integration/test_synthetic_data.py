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
from iris_ugrid.ucube import UCube
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

        # cube = iris.load_cube(file_path, "theta")
        # Note: cannot use iris.load, as merge can not yet handle UCubes.

        # Here's a thing that at least works.
        loaded_cubes = list(load_cubes(file_path))

        # Just check some expected details.
        self.assertEqual(len(loaded_cubes), 1)

        cube, = loaded_cubes

        # Basic checks on the primary data cube.
        self.assertEqual(cube.var_name, "conv_rain")
        self.assertEqual(cube.long_name, "surface_convective_rainfall_rate")
        self.assertEqual(cube.shape, (1, 866))

        # Also just a few checks on the attached grid information.
        self.assertIsInstance(cube, UCube)
        cubegrid = cube.ugrid
        self.assertIsInstance(cubegrid, CubeUgrid)
        self.assertEqual(cubegrid.cube_dim, 1)
        self.assertEqual(cubegrid.mesh_location, "face")
        self.assertEqual(cubegrid.topology_dimension, 2)
        self.assertEqual(cubegrid.node_coordinates, ["latitude", "longitude"])
        ugrid = cubegrid.grid
        self.assertIsInstance(ugrid, UGrid)
        self.assertEqual(ugrid.mesh_name, "Mesh2d_half_levels")


if __name__ == "__main__":
    tests.main()
