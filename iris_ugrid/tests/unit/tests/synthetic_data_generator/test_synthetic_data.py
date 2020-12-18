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
    create_file__xios_2d_face_half_levels,
    create_file__xios_3d_face_half_levels,
    create_file__xios_3d_face_full_levels,
)


class Create_file_mixin(tests.IrisTest):
    @classmethod
    def setUpClass(cls):
        # Create a temp directory for transient test files.
        cls.temp_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        # Destroy the temp directory.
        shutil.rmtree(cls.temp_dir)

    def create_synthetic_file(self, **create_kwargs):
        # Placeholder that will be overridden by sub-classes.
        return create_file__xios_2d_face_half_levels(
            temp_file_dir=self.temp_dir, dataset_name="mesh", **create_kwargs
        )

    def create_synthetic_testcube(self, **create_kwargs):
        file_path = self.create_synthetic_file(**create_kwargs)

        # cube = iris.load_cube(file_path, "theta")
        # Note: cannot use iris.load, as merge can not yet handle UCubes.
        # Here's a thing that at least works.
        loaded_cubes = list(load_cubes(file_path))

        # We expect just 1 cube.
        self.assertEqual(len(loaded_cubes), 1)

        (cube,) = loaded_cubes
        return cube

    def check_ucube(self, cube, shape, location, level):
        # Basic checks on the primary data cube.
        self.assertEqual(cube.var_name, "thing")
        self.assertEqual(cube.long_name, "thingness")
        self.assertEqual(cube.shape, shape)

        # Also a few checks on the attached grid information.
        last_dim = cube.ndim - 1
        self.assertIsInstance(cube, UCube)
        cubegrid = cube.ugrid
        self.assertIsInstance(cubegrid, CubeUgrid)
        self.assertEqual(cubegrid.cube_dim, last_dim)
        self.assertEqual(cubegrid.mesh_location, location)
        self.assertEqual(cubegrid.topology_dimension, 2)
        self.assertEqual(cubegrid.node_coordinates, ["latitude", "longitude"])
        ugrid = cubegrid.grid
        self.assertIsInstance(ugrid, UGrid)
        self.assertEqual(ugrid.mesh_name, f"Mesh2d_{level}_levels")
        self.assertIsNotNone(ugrid.face_coordinates)
        self.assertEqual(ugrid.face_coordinates.shape, (shape[last_dim], 2))


class Test_create_file__xios_2d_face_half_levels(Create_file_mixin):
    def create_synthetic_file(self, **create_kwargs):
        return create_file__xios_2d_face_half_levels(
            temp_file_dir=self.temp_dir, dataset_name="mesh", **create_kwargs
        )

    def test_basic_load(self):
        cube = self.create_synthetic_testcube()
        self.check_ucube(cube, shape=(1, 866), location="face", level="half")

    def test_scale_mesh(self):
        cube = self.create_synthetic_testcube(n_faces=10)
        self.check_ucube(cube, shape=(1, 10), location="face", level="half")

    def test_scale_time(self):
        cube = self.create_synthetic_testcube(n_times=3)
        self.check_ucube(cube, shape=(3, 866), location="face", level="half")


class Test_create_file__xios_3d_face_half_levels(Create_file_mixin):
    def create_synthetic_file(self, **create_kwargs):
        return create_file__xios_3d_face_half_levels(
            temp_file_dir=self.temp_dir, dataset_name="mesh", **create_kwargs
        )

    def test_basic_load(self):
        cube = self.create_synthetic_testcube()
        self.check_ucube(
            cube, shape=(1, 38, 866), location="face", level="half"
        )

    def test_scale_mesh(self):
        cube = self.create_synthetic_testcube(n_faces=10)
        self.check_ucube(
            cube, shape=(1, 38, 10), location="face", level="half"
        )

    def test_scale_time(self):
        cube = self.create_synthetic_testcube(n_times=3)
        self.check_ucube(
            cube, shape=(3, 38, 866), location="face", level="half"
        )

    def test_scale_levels(self):
        cube = self.create_synthetic_testcube(n_levels=10)
        self.check_ucube(
            cube, shape=(1, 10, 866), location="face", level="half"
        )


class Test_create_file__xios_3d_face_full_levels(Create_file_mixin):
    def create_synthetic_file(self, **create_kwargs):
        return create_file__xios_3d_face_full_levels(
            temp_file_dir=self.temp_dir, dataset_name="mesh", **create_kwargs
        )

    def test_basic_load(self):
        cube = self.create_synthetic_testcube()
        self.check_ucube(
            cube, shape=(1, 39, 866), location="face", level="full"
        )

    def test_scale_mesh(self):
        cube = self.create_synthetic_testcube(n_faces=10)
        self.check_ucube(
            cube, shape=(1, 39, 10), location="face", level="full"
        )

    def test_scale_time(self):
        cube = self.create_synthetic_testcube(n_times=3)
        self.check_ucube(
            cube, shape=(3, 39, 866), location="face", level="full"
        )

    def test_scale_levels(self):
        cube = self.create_synthetic_testcube(n_levels=10)
        self.check_ucube(
            cube, shape=(1, 10, 866), location="face", level="full"
        )


if __name__ == "__main__":
    tests.main()
