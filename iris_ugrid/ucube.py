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

    def _summary_dim_name(self, dim):
        """
        Add an identifying "*" prefix to the mesh dimension.

        This specialises the labelling of dims in cube summaries.

        """
        name = super()._summary_dim_name(dim)
        if self.ugrid is not None and dim == self.ugrid.cube_dim:
            name = "*" + name
        return name

    def _summary_vector_sections_info(self):
        """
        Build the "vector summary sections" list.  This has the standard form,
        plus one extra section to contain the mesh.

        This extends cube summaries with a row showing the mesh as for a
        coordinate, showing which cube dims it maps to.

        """
        specs = super()._summary_vector_sections_info()
        if self.ugrid:
            Spec = Cube._VectorSectionSpec
            specs.append(
                Spec(
                    title="Unstructured mesh",
                    elements=[self.ugrid],
                    add_extra_lines=True,
                )
            )
        return specs

    def summary(self, shorten=False, *args, **kwargs):
        """
        Provide cube summaries, extended to include mesh information.

        """
        summary = super().summary(shorten=shorten, *args, **kwargs)
        if self.ugrid and not shorten:
            # Get a mesh description : as it prints itself.
            detail_lines = str(self.ugrid).split("\n")
            # Use only certain parts: which happens to be the last N lines.
            (i_wanted_line,) = [
                i
                for i, line in enumerate(detail_lines)
                if "topology_dimension" in line
            ]
            # Cut out end portion, strip lines and discard blank ones.
            detail_lines = detail_lines[i_wanted_line:]
            detail_lines = [line.strip() for line in detail_lines]
            detail_lines = [line for line in detail_lines if line]

            # Find the section that shows the grid info.
            summary_lines = summary.split("\n")
            ugrid_section_title = "Unstructured mesh"
            (i_ugrid_line,) = [
                i
                for i, line in enumerate(summary_lines)
                if line.strip().startswith(ugrid_section_title)
            ]

            # Get the indent of the line below (the grid variable dims).
            next_line = summary_lines[i_ugrid_line + 1]
            indent_number = [
                ind for ind, char in enumerate(next_line) if char != " "
            ][0]

            # Indent the mesh details 4 spaces more than that.
            indent_string = " " * (indent_number + 4)
            detail_lines = [indent_string + line for line in detail_lines]

            # Splice in the detail lines after that, indenting to match.
            i_next_section = i_ugrid_line + 2
            summary_lines[i_next_section:i_next_section] = detail_lines

            summary = "\n".join(summary_lines)

        return summary
