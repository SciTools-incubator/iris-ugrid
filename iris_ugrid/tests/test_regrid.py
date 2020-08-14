# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test ESMF regridding.
"""

import os
import numpy as np
from numpy import ma
from iris_ugrid.regrid import MeshInfo, GridInfo, Regridder
import scipy.sparse


def make_small_mesh_args():
    ugrid_node_coords = np.array([[0, 0], [0, 1], [1, 0], [1, 1], [1, 2]])
    ugrid_face_node_connectivity = ma.array(
        [[0, 2, 3, -1], [3, 0, 1, 4]],
        mask=np.array([[0, 0, 0, 1], [0, 0, 0, 0]]),
    )
    return ugrid_node_coords, ugrid_face_node_connectivity


def make_small_grid_args():
    small_x = 2
    small_y = 3
    small_grid_lon = np.array(range(small_x)) / (small_x + 1)
    small_grid_lat = np.array(range(small_y)) * 2 / (small_y + 1)

    small_grid_lon_bounds = np.array(range(small_x + 1)) / (small_x + 1)
    small_grid_lat_bounds = np.array(range(small_y + 1)) * 2 / (small_y + 1)
    return (
        small_grid_lon,
        small_grid_lat,
        small_grid_lon_bounds,
        small_grid_lat_bounds,
    )


def expected_weights():
    weight_list = np.array(
        [
            0.3333836384685291,
            0.6666163615314712,
            1.0,
            0.3335106008404508,
            0.9167189586203999,
            0.0832810413795998,
            0.08339316630404843,
            0.9166068336959516,
            0.9168310094376751,
        ]
    )
    rows = np.array([0, 0, 1, 2, 3, 3, 4, 4, 5])
    columns = np.array([0, 1, 1, 1, 0, 1, 0, 1, 1])

    shape = (6, 2)

    weights = scipy.sparse.csr_matrix(
        (weight_list, (rows, columns)), shape=shape
    )
    return weights


def test_make_mesh():
    coords, nodes = make_small_mesh_args()
    mesh = MeshInfo(coords, nodes, 0)
    esmf_mesh_0 = mesh.make_esmf_field()
    esmf_mesh_0.data[:] = 0

    relative_path = os.path.join("results", "test_regrid", "small_mesh.txt")
    abs_path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(abs_path) as file:
        expected_repr = file.read()

    one_indexed_nodes = nodes + 1
    mesh = MeshInfo(coords, one_indexed_nodes, 1)
    esmf_mesh_1 = mesh.make_esmf_field()
    esmf_mesh_1.data[:] = 0

    assert esmf_mesh_0.__repr__() == esmf_mesh_1.__repr__() == expected_repr

    # TODO: make sure this ESMF object behaves as expected, requires understanding
    #  how such objects ought to behave


def test_make_grid():
    lon, lat, lon_bounds, lat_bounds = make_small_grid_args()
    grid = GridInfo(lon, lat, lon_bounds, lat_bounds)
    esmf_grid = grid.make_esmf_field()
    esmf_grid.data[:] = 0

    relative_path = os.path.join("results", "test_regrid", "small_grid.txt")
    abs_path = os.path.join(os.path.dirname(__file__), relative_path)
    with open(abs_path) as file:
        expected_repr = file.read()

    assert esmf_grid.__repr__() == expected_repr

    # TODO: make sure this ESMF object behaves as expected, requires understanding
    #  how such objects ought to behave


def test_Regridder_init():
    node_coords, face_node_connectivity = make_small_mesh_args()
    mesh = MeshInfo(node_coords, face_node_connectivity, 0)

    lon, lat, lon_bounds, lat_bounds = make_small_grid_args()
    grid = GridInfo(lon, lat, lon_bounds, lat_bounds)

    rg = Regridder(mesh, grid)

    result = rg.weight_matrix
    expected = expected_weights()

    assert np.allclose(result.toarray(), expected.toarray())


def test_Regridder_regrid():
    coords, nodes = make_small_mesh_args()
    mesh = MeshInfo(coords, nodes, 0)

    lon, lat, lon_bounds, lat_bounds = make_small_grid_args()
    grid = GridInfo(lon, lat, lon_bounds, lat_bounds)

    rg = Regridder(mesh, grid, precomputed_weights=expected_weights())

    exprected = ma.array(
        [
            [2.333383638468529, 2.0, 2.0],
            [2.9167189586204008, 2.083393166304049, 2.0],
        ]
    )
    result = rg.regrid([3, 2])
    assert np.allclose(exprected, result)

    half_mdtol_expected = ma.array(exprected, mask=[[0, 0, 1], [0, 0, 0]])
    half_mdtol_result = rg.regrid([3, 2], mdtol=0.5)
    assert np.allclose(half_mdtol_expected, half_mdtol_result)

    min_mdtol_expected = ma.array(exprected, mask=[[0, 0, 1], [0, 0, 1]])
    min_mdtol_result = rg.regrid([3, 2], mdtol=0)
    assert np.allclose(min_mdtol_expected, min_mdtol_result)


# TODO: Add testing for regridding with user provided weights, a better
#  understanding of how weights affect ESMF regridding is required
#  before deciding which results are appropriate
