# Copyright Iris contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Defines the UCube : a cube which has an unstructured mesh dimension.

"""
from iris.cube import Cube


class UCube(Cube):
    # Derived 'unstructured' Cube subtype, with a '.ugrid' property.
    def __init__(self, *args, ugrid=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ugrid = ugrid
