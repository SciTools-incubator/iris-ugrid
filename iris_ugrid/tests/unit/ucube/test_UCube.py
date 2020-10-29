# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test basic :class:`iris_ugrid.ucube.Ucube` object.
"""
import iris.tests as tests

import re

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
        keep_attrs = ["timeStamp", "Conventions"]
        cube.attributes = {
            key: value
            for key, value in cube.attributes.items()
            if key in keep_attrs
        }
        self.ucube = cube

    def test_summary_short(self):
        # Check the short-form of a UCube summary.
        # This the same as what will appear in a CubeList string repr.
        result = self.ucube.summary(shorten=True)
        expected = (
            "Potential Temperature / (K)         "
            "(time: 1; levels: 6; *-- : 866)"
        )
        self.assertEqual(result, expected)

    def test_summary_long(self):
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

    def test__repr_html_(self):
        result = self.ucube._repr_html_()
        # Check for some key pieces of html, which indicate that it includes
        # a summary of the unstructured dimension, and mesh details.
        str_dim = '<th class="iris iris-word-cell">*--</th>'
        self.assertIn(str_dim, result)
        str_section = \
            '<td class="iris-title iris-word-cell">Unstructured mesh</td>'
        self.assertIn(str_section, result)
        re_mesh = (r'<td class="iris-word-cell iris-subheading-cell">'
                   r'\s*Mesh0\s*</td>'
                   r'\s*<td class="iris-inclusion-cell">node</td>')
        self.assertIsNotNone(re.search(re_mesh, result))


if __name__ == "__main__":
    tests.main()
