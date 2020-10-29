# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test basic :class:`iris_ugrid.ucube.Ucube` object.
"""

import iris.tests as tests

from iris import Constraint
from iris.tests import IrisTest, get_data_path

from iris.cube import CubeList

from iris_ugrid.ugrid_cf_reader import load_cubes


class Test_cube_representations(IrisTest):
    def setUp(self):
        file_path = get_data_path(
            ("NetCDF", "unstructured_grid", "theta_nodal_xios.nc")
        )
        loaded_cubes = CubeList(load_cubes(file_path))
        (cube,) = loaded_cubes.extract(Constraint("theta"))
        # Prune the attributes, just because there are a lot.
        keep_attrs = ['timeStamp', 'Conventions']
        cube.attributes = {key: value
                           for key, value in cube.attributes.items()
                           if key in keep_attrs}
        self.ucube = cube

    def test_cube_summary_short(self):
        result = self.ucube.summary(shorten=True)
        expected = ('Potential Temperature / (K)         '
                    '(time: 1; levels: 6; *-- : 866)')
        self.assertEqual(result, expected)

    def test_cube_summary_long(self):
        result = str(self.ucube)
        expected = """\
Potential Temperature / (K)         (time: 1; levels: 6; *-- : 866)
     Dimension coordinates:
          time                           x          -        -
          levels                         -          x        -
     Auxiliary coordinates:
          time                           x          -        -
     Unstructured mesh:
          Mesh0.node                     -          -        x
              topology_dimension "2" :
              node_coordinates "latitude longitude" :
              <unprintable mesh>
     Attributes:
          Conventions: UGRID
          timeStamp: 2016-Oct-24 15:16:48 BST
     Cell methods:
          point: time\
"""
        self.assertEqual(result, expected)


if __name__ == "__main__":
    tests.main()
