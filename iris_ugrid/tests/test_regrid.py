# Copyright Iris-ugrid contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Test ESMF regridding.
"""

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

    expected_repr = """Field:
    name = None
    type = <TypeKind.R8: 6>
    rank = 1
    extra dimensions = 0
    staggerloc = 1
    lower bounds = array([0], dtype=int32)
    upper bounds = array([2], dtype=int32)
    extra bounds = None
    data = array([0., 0.])
    grid = 
Mesh:
    rank = 1
    size = [5, 2]
    size_owned = [5, 2]
    coords = [[array([0., 0., 1., 1., 1.]), array([0., 1., 0., 1., 2.])], [None, None]]

)"""

    one_indexed_nodes = nodes + 1
    mesh = MeshInfo(coords, one_indexed_nodes, 1)
    esmf_mesh_1 = mesh.make_esmf_field()

    assert esmf_mesh_0.__repr__() == esmf_mesh_1.__repr__() == expected_repr

    # TODO: make sure this ESMF object behaves as expected, requires understanding
    #  how such objects ought to behave


def test_make_grid():
    lon, lat, lon_bounds, lat_bounds = make_small_grid_args()
    grid = GridInfo(lon, lat, lon_bounds, lat_bounds)
    esmf_grid = grid.make_esmf_field()
    expected_repr = """Field:
    name = None
    type = <TypeKind.R8: 6>
    rank = 2
    extra dimensions = 0
    staggerloc = <StaggerLoc.CENTER: 0>
    lower bounds = array([0, 0], dtype=int32)
    upper bounds = array([3, 2], dtype=int32)
    extra bounds = None
    data = array([[0.00000000e+000, 0.00000000e+000],
       [4.24399158e-314, 0.00000000e+000],
       [0.00000000e+000, 0.00000000e+000]])
    grid = 
Grid:
    type = <TypeKind.R8: 6>    areatype = <TypeKind.R8: 6>    rank = 2    num_peri_dims = 0    periodic_dim = None    pole_dim = None    pole_kind = array([1, 1], dtype=int32)    coord_sys = None    staggerloc = [False, False, False, True]    lower bounds = [None, None, None, array([0, 0], dtype=int32)]    upper bounds = [None, None, None, array([4, 3], dtype=int32)]    coords = [[None, None], [None, None], [None, None], [array([[0.        , 0.33333333, 0.66666667],
       [0.        , 0.33333333, 0.66666667],
       [0.        , 0.33333333, 0.66666667],
       [0.        , 0.33333333, 0.66666667]]), array([[0. , 0. , 0. ],
       [0.5, 0.5, 0.5],
       [1. , 1. , 1. ],
       [1.5, 1.5, 1.5]])]]    mask = [None, None, None, None]    area = [None, None, None, None]
)"""
    print(esmf_grid.__repr__())
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
