# Copyright Iris contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Unit tests for the
:mod:`iris.fileformats.tests.synthetic_data_generator` module.

"""

# Import iris.tests first so that some things can be initialised before
# importing anything else.
import shutil
import tempfile
import iris.tests as tests
from gridded.pyugrid.ugrid import UGrid
from iris_ugrid.ucube import UCube
from iris_ugrid.ugrid_cf_reader import CubeUgrid, load_cubes
from iris_ugrid.tests.synthetic_data_generator import (
    create_file__xios_half_levels_faces,
)


class Test_create_file__xios_half_levels_faces(tests.IrisTest):
    @classmethod
    def setUpClass(cls):
        # Create a temp directory for transient test files.
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        # Destroy the temp directory.
        shutil.rmtree(cls.temp_dir)

    def create_synthetic_testcube(self, **create_kwargs):

        file_path = create_file__xios_half_levels_faces(
            temp_file_dir=self.temp_dir, dataset_name="mesh", **create_kwargs
        )

        # cube = iris.load_cube(file_path, "theta")
        # Note: cannot use iris.load, as merge can not yet handle UCubes.
        # Here's a thing that at least works.
        loaded_cubes = list(load_cubes(file_path))

        # We expect just 1 cube.
        self.assertEqual(len(loaded_cubes), 1)

        (cube,) = loaded_cubes
        return cube

    def check_ucube(self, cube, expected_shape):
        # Basic checks on the primary data cube.
        self.assertEqual(cube.var_name, "thing")
        self.assertEqual(cube.long_name, "thingness")
        self.assertEqual(cube.shape, expected_shape)

        # Also a few checks on the attached grid information.
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
        self.assertIsNotNone(ugrid.face_coordinates)
        self.assertEqual(ugrid.face_coordinates.shape, (expected_shape[1], 2))

    def test_basic_load(self):
        cube = self.create_synthetic_testcube()
        self.check_ucube(cube, expected_shape=(1, 866))

    def test_scale_mesh(self):
        cube = self.create_synthetic_testcube(n_faces=10)
        self.check_ucube(cube, expected_shape=(1, 10))

    def test_scale_time(self):
        cube = self.create_synthetic_testcube(n_times=3, n_faces=10)
        self.check_ucube(cube, expected_shape=(3, 10))


if __name__ == "__main__":
    tests.main()
