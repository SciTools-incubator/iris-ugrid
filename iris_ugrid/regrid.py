# Copyright Iris contributors
#
# This file is part of Iris and is released under the LGPL license.
# See COPYING and COPYING.LESSER in the root of the repository for full
# licensing details.
"""
Provides ESMF representations of grids/UGRID meshes and a modified regridder.
"""
import ESMF
import numpy as np
from numpy import ma
import scipy.sparse
import cartopy.crs as ccrs


class MeshInfo:
    """
    This class holds information about Meshes in a form similar to UGRID.
    It contains methods for translating this information into ESMF objects.
    """

    def __init__(
        self,
        node_coords,
        face_node_connectivity,
        node_start_index,
        elem_start_index=0,
        areas=None,
    ):
        """
        Creates a MeshInfo object describing the geometry/topology of a UGRID
        mesh.

        Args:

        * node_coords
            An Nx2 numpy array describing the location of the nodes of the mesh.
            node_coords[:,0] describes the longitudes in degrees and
            node_coords[:,1] describes the latitides in degrees
        * face_node_connectivity
            A numpy masked array describing the face node connectivity of the
            mesh. The unmasked points of face_node_connectivity[i] describe
            which nodes are connected to the i'th face.
        * node_start_index
            An integer describing which index is considered the initial index
            by face_node_connectivity. UGRID supports both 0 based and 1 based
            indexing, so both must be accounted for here

        Kwargs:

        * elem_start_index
            An integer describing what index should be considered by ESMF to be
            the start index for describing its elements. This makes no
            difference to the regridding calculation and will only affect the
            intermediate ESMF objects, should the user need access to them.
        * areas
            either None or a numpy array describing the areas associated with
            each face. If None, then ESMF will use its own calculated areas.
        """
        self.node_coords = node_coords
        self.fnc = face_node_connectivity
        self.nsi = node_start_index
        self.esi = elem_start_index
        self.areas = areas

    def _as_esmf_info(self):
        # ESMF uses a slightly different format to UGRID,
        # the data must be translated into a form ESMF understands
        num_node = self.node_coords.shape[0]
        num_elem = self.fnc.shape[0]
        nodeId = np.array(range(self.nsi, self.nsi + num_node))
        nodeCoord = self.node_coords.flatten()
        nodeOwner = np.zeros([num_node])  # regridding currently serial
        elemId = np.array(range(self.esi, self.esi + num_elem))
        elemType = self.fnc.count(axis=1)
        # Experiments seem to indicate that ESMF is using 0 indexing here
        elemConn = self.fnc.compressed() - self.nsi
        result = (
            num_node,
            num_elem,
            nodeId,
            nodeCoord,
            nodeOwner,
            elemId,
            elemType,
            elemConn,
            self.areas,
        )
        return result

    def _make_esmf_mesh(self):
        info = self._as_esmf_info()
        (
            num_node,
            num_elem,
            nodeId,
            nodeCoord,
            nodeOwner,
            elemId,
            elemType,
            elemConn,
            areas,
        ) = info
        # ESMF can handle other dimensionalities, but we are unlikely
        # to make such a use of ESMF
        emesh = ESMF.Mesh(
            parametric_dim=2, spatial_dim=2, coord_sys=ESMF.CoordSys.SPH_DEG
        )

        emesh.add_nodes(num_node, nodeId, nodeCoord, nodeOwner)
        emesh.add_elements(
            num_elem, elemId, elemType, elemConn, element_area=areas
        )
        return emesh

    def make_esmf_field(self):
        mesh = self._make_esmf_mesh()
        field = ESMF.Field(mesh, meshloc=ESMF.MeshLoc.ELEMENT)
        return field

    def size(self):
        return self.fnc.shape[0]

    def _index_offset(self):
        return self.esi

    def _flatten_array(self, array):
        return array

    def _unflatten_array(self, array):
        return array


class GridInfo:
    """
    This class holds information about lat-lon type grids.
    It contains methods for translating this information into ESMF objects.
    """

    def __init__(
        self,
        lons,
        lats,
        lonbounds,
        latbounds,
        crs=ccrs.Geodetic(),
        circular=False,
        areas=None,
    ):
        """
        Creates a GridInfo object describing the a grid.

        Args:

        * lons
            A numpy array describing the longitudes of the grid points.
        * lats
            A numpy array describing the latitudes of the grid points.
        * lonbounds
            A numpy array describing the longitude bounds of the grid.
            Should have length one greater than lons
        * latbounds
            A numpy array describing the latitude bounds of the grid.
            Should have length one greater than lats

        Kwargs:

        * crs
            A cartopy.crs projection describing how to interpret the above
            arguments. Defaults to Geodetic().
        * circular
            A boolean value describing if the final longitude bounds should
            be considered contiguous with the first. Defaults to False.
        * areas
            either None or a numpy array describing the areas associated with
            each face. If None, then ESMF will use its own calculated areas.
        """
        self.lons = lons
        self.lats = lats
        self.lonbounds = lonbounds
        self.latbounds = latbounds
        self.crs = crs
        self.circular = circular
        self.areas = areas

    def _as_esmf_info(self):
        size = np.array([len(self.lats), len(self.lons)])

        if self.circular:
            adjustedlonbounds = self.lonbounds[:-1]
        else:
            adjustedlonbounds = self.lonbounds

        centerlons, centerlats = np.meshgrid(self.lons, self.lats)
        cornerlons, cornerlats = np.meshgrid(adjustedlonbounds, self.latbounds)

        truecenters = ccrs.Geodetic().transform_points(
            self.crs, centerlons, centerlats
        )
        truecorners = ccrs.Geodetic().transform_points(
            self.crs, cornerlons, cornerlats
        )

        # The following note in xESMF suggests that the arrays passed to ESMPy ought to
        # be fortran ordered:
        # https://xesmf.readthedocs.io/en/latest/internal_api.html#xesmf.backend.warn_f_contiguous
        # It is yet to be determined what effect this has on performance.
        truecenterlons = np.asfortranarray(truecenters[..., 0])
        truecenterlats = np.asfortranarray(truecenters[..., 1])
        truecornerlons = np.asfortranarray(truecorners[..., 0])
        truecornerlats = np.asfortranarray(truecorners[..., 1])

        info = (
            size,
            truecenterlons,
            truecenterlats,
            truecornerlons,
            truecornerlats,
            self.circular,
            self.areas,
        )
        return info

    def _make_esmf_grid(self):
        info = self._as_esmf_info()
        (
            size,
            truecenterlons,
            truecenterlats,
            truecornerlons,
            truecornerlats,
            circular,
            areas,
        ) = info

        if circular:
            grid = ESMF.Grid(size, num_peri_dims=1)
        else:
            grid = ESMF.Grid(size)

        grid.add_coords(staggerloc=ESMF.StaggerLoc.CORNER)
        grid_corner_x = grid.get_coords(0, staggerloc=ESMF.StaggerLoc.CORNER)
        grid_corner_x[:] = truecornerlons
        grid_corner_y = grid.get_coords(1, staggerloc=ESMF.StaggerLoc.CORNER)
        grid_corner_y[:] = truecornerlats

        # Grid center points would be added here, this is not necessary for
        # conservative area weighted regridding
        # grid.add_coords(staggerloc=ESMF.StaggerLoc.CENTER)
        # grid_center_x = grid.get_coords(0, staggerloc=ESMF.StaggerLoc.CENTER)
        # grid_center_x[:] = truecenterlons
        # grid_center_y = grid.get_coords(1, staggerloc=ESMF.StaggerLoc.CENTER)
        # grid_center_y[:] = truecenterlats

        if areas is not None:
            grid.add_item(
                ESMF.GridItem.AREA, staggerloc=ESMF.StaggerLoc.CENTER
            )
            grid_areas = grid.get_item(
                ESMF.GridItem.AREA, staggerloc=ESMF.StaggerLoc.CENTER
            )
            grid_areas[:] = areas.T

        return grid

    def make_esmf_field(self):
        grid = self._make_esmf_grid()
        field = ESMF.Field(grid, staggerloc=ESMF.StaggerLoc.CENTER)
        return field

    def size(self):
        return len(self.lons) * len(self.lats)

    def _index_offset(self):
        return 1

    def _flatten_array(self, array):
        return array.flatten()

    def _unflatten_array(self, array):
        return array.reshape((len(self.lons), len(self.lats)))


def _get_regrid_weights_dict(src_field, tgt_field):
    regridder = ESMF.Regrid(
        src_field,
        tgt_field,
        ignore_degenerate=True,
        regrid_method=ESMF.RegridMethod.CONSERVE,
        unmapped_action=ESMF.UnmappedAction.IGNORE,
        # Choosing the norm_type DSTAREA allows for mdtol type operations
        # to be performed using the weights information later on.
        norm_type=ESMF.NormType.DSTAREA,
        factors=True,
    )
    # Without specifying deep_copy=true, the information in weights_dict
    # would be corrupted when the ESMF regridder is destoyed.
    weights_dict = regridder.get_weights_dict(deep_copy=True)
    # The weights_dict contains all the information needed for regridding,
    # the ESMF objects can be safely removed.
    regridder.destroy()
    return weights_dict


def _weights_dict_to_sparse_array(weights, shape, index_offsets):
    matrix = scipy.sparse.csr_matrix(
        (
            weights["weights"],
            (
                weights["row_dst"] - index_offsets[0],
                weights["col_src"] - index_offsets[1],
            ),
        ),
        shape=shape,
    )
    return matrix


class Regridder:
    def __init__(self, src, tgt, precomputed_weights=None):
        """
        Creates a regridder designed to regrid data from a specified
        source mesh/grid to a specified target mesh/grid.

        Args:

        * src
            A MeshInfo or GridInfo oject describing the source mesh/grid.
            Data supplied to this regridder should be in a numpy array
            whose shape is compatible with src.
        * tgt
            A MeshInfo or GridInfo oject describing the target mesh/grid.
            Data output by this regridder will be a numpy array whose
            shape is compatible with tgt.

        Kwargs:

        * precomputed_weights
            None or a scipy.sparse matrix. If None, ESMF will be used to
            calculate regridding weights. Otherwise, ESMF will be bypassed
            and precomputed_weights will be used as the regridding weights.
        """
        self.src = src
        self.tgt = tgt

        if precomputed_weights is None:
            weights_dict = _get_regrid_weights_dict(
                src.make_esmf_field(), tgt.make_esmf_field()
            )
            self.weight_matrix = _weights_dict_to_sparse_array(
                weights_dict,
                (self.tgt.size(), self.src.size()),
                (self.tgt._index_offset(), self.src._index_offset()),
            )
        else:
            if not scipy.sparse.isspmatrix(precomputed_weights):
                raise ValueError(
                    "Precomputed weights must be given as a sparse matrix."
                )
            if precomputed_weights.shape != (self.tgt.size(), self.src.size()):
                msg = "Expected precomputed weights to have shape {}, got shape {} instead."
                raise ValueError(
                    msg.format(
                        (self.tgt.size(), self.src.size()),
                        precomputed_weights.shape,
                    )
                )
            self.weight_matrix = precomputed_weights

    def regrid(self, src_array, mdtol=1):
        """
        Perform regridding on an array of data.

        Args:

        * src_array
            A numpy array whose shape is compatible with self.src

        Kwargs:

        * mdtol
            A number between 0 and 1 describing the missing data tolerance.
            Depending on the value of mdtol, if an element in the target mesh/grid
            is not sufficiently covered by elements of the source mesh/grid, then
            the corresponding data point will be masked. An mdtol of 1 means that
            only target elements which are completely uncovered will be masked,
            an mdtol of 0 means that only target elements which are completely
            covered will be unmasked and an mdtol of 0.5 means that target elements
            whose area is at least half uncovered by source elements will be masked.

        Returns:
            A numpy array whose shape is compatible with self.tgt.
        """
        # A rudimentary filter is applied to mask data which is mapped from an
        # insufficiently large source. This currently only accounts for discrepancies
        # between the source and target grid/mesh geometries and does not account for
        # masked data, though it ought to be possible to extend the functionality to
        # handle masked data.
        #
        # Note that ESMPy is also able to handle masked data. It is worth investigating
        # how this affects the mathematics and if it can be replicated after the fact
        # using just the weights or if ESMF is doing something we want access to.
        weight_sums = np.array(self.weight_matrix.sum(axis=1)).flatten()
        # Set the minimum mdtol to be slightly higher than 0 to account for rounding
        # errors.
        mdtol = max(mdtol, 1e-8)
        tgt_mask = weight_sums >= 1 - mdtol
        masked_weight_sums = weight_sums * tgt_mask.astype(int)
        normalisations = np.where(
            masked_weight_sums == 0, 0, 1 / masked_weight_sums
        )
        normalisations = ma.array(
            normalisations, mask=np.logical_not(tgt_mask)
        )

        flat_src = self.src._flatten_array(src_array)
        flat_tgt = self.weight_matrix * flat_src
        flat_tgt = flat_tgt * normalisations
        tgt_array = self.tgt._unflatten_array(flat_tgt)
        return tgt_array
