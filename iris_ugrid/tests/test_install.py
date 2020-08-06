# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test that the correct iris is installed, including iris-ugrid support.

TODO: remove this when we have other more sensible tests.

"""

def test_iris_installation():
    # Check that iris cf loader includes 'exclude' functionality.
    # Import a ugrid-specific test, that ought to exist on the branch.
    from iris.tests.unit.fileformats.cf.test_CFReader \
        import Test_exclude_vars

    assert hasattr(Test_exclude_vars, 'test_exclude_vars')
