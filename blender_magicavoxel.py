# MIT License
#
# Copyright (c) 2022 https://github.com/AstrorEnales
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
This script imports a MagicaVoxel VOX file to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired VOX file.

Repository:
https://github.com/AstrorEnales/blender_magicavoxel

File format info:
https://github.com/ephtracy/voxel-model/blob/master/MagicaVoxel-file-format-vox.txt
https://github.com/ephtracy/voxel-model/blob/master/MagicaVoxel-file-format-vox-extension.txt
"""

import bpy
import os
import math
import mathutils
import struct
from typing import IO, List, Dict, Tuple, Set
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
)

bl_info = {
    "name": "MagicaVoxel VOX format",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Importer for MagicaVoxel VOX files",
    "category": "Import-Export",
}


def abgr_int_to_rgba_tuple(color: int) -> Tuple[int, int, int, int]:
    return (
        (color >> 24) & 0xff,
        (color >> 16) & 0xff,
        (color >> 8) & 0xff,
        color & 0xff
    )


DEFAULT_PALETTE: List[Tuple[int, int, int, int]] = [
    abgr_int_to_rgba_tuple(x) for x in [
        0x00000000, 0xffffffff, 0xffccffff, 0xff99ffff, 0xff66ffff, 0xff33ffff,
        0xff00ffff, 0xffffccff, 0xffccccff, 0xff99ccff, 0xff66ccff, 0xff33ccff,
        0xff00ccff, 0xffff99ff, 0xffcc99ff, 0xff9999ff, 0xff6699ff, 0xff3399ff,
        0xff0099ff, 0xffff66ff, 0xffcc66ff, 0xff9966ff, 0xff6666ff, 0xff3366ff,
        0xff0066ff, 0xffff33ff, 0xffcc33ff, 0xff9933ff, 0xff6633ff, 0xff3333ff,
        0xff0033ff, 0xffff00ff, 0xffcc00ff, 0xff9900ff, 0xff6600ff, 0xff3300ff,
        0xff0000ff, 0xffffffcc, 0xffccffcc, 0xff99ffcc, 0xff66ffcc, 0xff33ffcc,
        0xff00ffcc, 0xffffcccc, 0xffcccccc, 0xff99cccc, 0xff66cccc, 0xff33cccc,
        0xff00cccc, 0xffff99cc, 0xffcc99cc, 0xff9999cc, 0xff6699cc, 0xff3399cc,
        0xff0099cc, 0xffff66cc, 0xffcc66cc, 0xff9966cc, 0xff6666cc, 0xff3366cc,
        0xff0066cc, 0xffff33cc, 0xffcc33cc, 0xff9933cc, 0xff6633cc, 0xff3333cc,
        0xff0033cc, 0xffff00cc, 0xffcc00cc, 0xff9900cc, 0xff6600cc, 0xff3300cc,
        0xff0000cc, 0xffffff99, 0xffccff99, 0xff99ff99, 0xff66ff99, 0xff33ff99,
        0xff00ff99, 0xffffcc99, 0xffcccc99, 0xff99cc99, 0xff66cc99, 0xff33cc99,
        0xff00cc99, 0xffff9999, 0xffcc9999, 0xff999999, 0xff669999, 0xff339999,
        0xff009999, 0xffff6699, 0xffcc6699, 0xff996699, 0xff666699, 0xff336699,
        0xff006699, 0xffff3399, 0xffcc3399, 0xff993399, 0xff663399, 0xff333399,
        0xff003399, 0xffff0099, 0xffcc0099, 0xff990099, 0xff660099, 0xff330099,
        0xff000099, 0xffffff66, 0xffccff66, 0xff99ff66, 0xff66ff66, 0xff33ff66,
        0xff00ff66, 0xffffcc66, 0xffcccc66, 0xff99cc66, 0xff66cc66, 0xff33cc66,
        0xff00cc66, 0xffff9966, 0xffcc9966, 0xff999966, 0xff669966, 0xff339966,
        0xff009966, 0xffff6666, 0xffcc6666, 0xff996666, 0xff666666, 0xff336666,
        0xff006666, 0xffff3366, 0xffcc3366, 0xff993366, 0xff663366, 0xff333366,
        0xff003366, 0xffff0066, 0xffcc0066, 0xff990066, 0xff660066, 0xff330066,
        0xff000066, 0xffffff33, 0xffccff33, 0xff99ff33, 0xff66ff33, 0xff33ff33,
        0xff00ff33, 0xffffcc33, 0xffcccc33, 0xff99cc33, 0xff66cc33, 0xff33cc33,
        0xff00cc33, 0xffff9933, 0xffcc9933, 0xff999933, 0xff669933, 0xff339933,
        0xff009933, 0xffff6633, 0xffcc6633, 0xff996633, 0xff666633, 0xff336633,
        0xff006633, 0xffff3333, 0xffcc3333, 0xff993333, 0xff663333, 0xff333333,
        0xff003333, 0xffff0033, 0xffcc0033, 0xff990033, 0xff660033, 0xff330033,
        0xff000033, 0xffffff00, 0xffccff00, 0xff99ff00, 0xff66ff00, 0xff33ff00,
        0xff00ff00, 0xffffcc00, 0xffcccc00, 0xff99cc00, 0xff66cc00, 0xff33cc00,
        0xff00cc00, 0xffff9900, 0xffcc9900, 0xff999900, 0xff669900, 0xff339900,
        0xff009900, 0xffff6600, 0xffcc6600, 0xff996600, 0xff666600, 0xff336600,
        0xff006600, 0xffff3300, 0xffcc3300, 0xff993300, 0xff663300, 0xff333300,
        0xff003300, 0xffff0000, 0xffcc0000, 0xff990000, 0xff660000, 0xff330000,
        0xff0000ee, 0xff0000dd, 0xff0000bb, 0xff0000aa, 0xff000088, 0xff000077,
        0xff000055, 0xff000044, 0xff000022, 0xff000011, 0xff00ee00, 0xff00dd00,
        0xff00bb00, 0xff00aa00, 0xff008800, 0xff007700, 0xff005500, 0xff004400,
        0xff002200, 0xff001100, 0xffee0000, 0xffdd0000, 0xffbb0000, 0xffaa0000,
        0xff880000, 0xff770000, 0xff550000, 0xff440000, 0xff220000, 0xff110000,
        0xffeeeeee, 0xffdddddd, 0xffbbbbbb, 0xffaaaaaa, 0xff888888, 0xff777777,
        0xff555555, 0xff444444, 0xff222222, 0xff111111,
    ]
]


class VoxelGrid:
    width: int
    half_width: float
    depth: int
    half_depth: float
    height: int
    half_height: float
    size: int
    last_index_x: int
    last_index_y: int
    last_index_z: int
    y_multiplier: int
    z_multiplier: int

    def __init__(self, width: int, depth: int, height: int):
        self.width = width
        self.depth = depth
        self.height = height
        self.half_width = width * 0.5
        self.half_height = height * 0.5
        self.half_depth = depth * 0.5
        self.size = width * height * depth
        self.last_index_x = width - 1
        self.last_index_y = depth - 1
        self.last_index_z = height - 1
        self.y_multiplier = width
        self.z_multiplier = depth * width

    def get_index(self, x: int, y: int, z: int) -> int:
        return z * self.z_multiplier + y * self.y_multiplier + x

    def get_index_func(self,
                       axis1_index: int,
                       axis2_index: int,
                       axis3_index: int
                       ):
        if axis1_index == 0 and axis2_index == 1 and axis3_index == 2:
            return lambda x, y, z: z * self.z_multiplier + y * self.y_multiplier + x
        if axis1_index == 1 and axis2_index == 0 and axis3_index == 2:
            return lambda y, x, z: z * self.z_multiplier + y * self.y_multiplier + x
        if axis1_index == 1 and axis2_index == 2 and axis3_index == 0:
            return lambda y, z, x: z * self.z_multiplier + y * self.y_multiplier + x
        if axis1_index == 0 and axis2_index == 2 and axis3_index == 1:
            return lambda x, z, y: z * self.z_multiplier + y * self.y_multiplier + x
        if axis1_index == 2 and axis2_index == 0 and axis3_index == 1:
            return lambda z, x, y: z * self.z_multiplier + y * self.y_multiplier + x
        # 2, 1, 0
        return lambda z, y, x: z * self.z_multiplier + y * self.y_multiplier + x

    def get_axis(self, axis_index: int) -> int:
        return self.width if axis_index == 0 else (
            self.depth if axis_index == 1 else self.height
        )

    def reduce_voxel_grid_to_hull(self, voxels: List[int or None], outside: List[bool]):
        for z in range(0, self.height):
            last_z = z == self.last_index_z
            first_z = z == 0
            for y in range(0, self.depth):
                last_y = y == self.last_index_y
                first_y = y == 0
                for x in range(0, self.width):
                    index = self.get_index(x, y, z)
                    if voxels[index] is not None:
                        # Left
                        if x == 0 or outside[self.get_index(x - 1, y, z)]:
                            continue
                        # Right
                        if x == self.last_index_x or outside[self.get_index(x + 1, y, z)]:
                            continue
                        # Down
                        if first_y or outside[self.get_index(x, y - 1, z)]:
                            continue
                        # Up
                        if last_y or outside[self.get_index(x, y + 1, z)]:
                            continue
                        # Back
                        if first_z or outside[self.get_index(x, y, z - 1)]:
                            continue
                        # Front
                        if last_z or outside[self.get_index(x, y, z + 1)]:
                            continue
                        # If not connected to the outside space, delete the voxel(inside hull)
                        voxels[index] = None

    def create_outside_grid(self, voxels: List[int or None]) -> List[int or None]:
        distinct_areas = self.find_distinct_areas(voxels)
        outside_index = self.find_outside_index(voxels)
        if outside_index is None:
            # All is marked as outside to prevent any faces to be removed
            return [False] * self.size
        outside_label = distinct_areas[outside_index]
        return [label == outside_label for label in distinct_areas]

    def find_distinct_areas(self, voxels: List[int or None]) -> List[int]:
        """
        connected-component labeling (CCL) with the Hoshen–Kopelman algorithm
        """
        labels: List[int] = []
        label_equivalence: Dict[int, Set[int]] = {}
        next_label = 0
        for z in range(0, self.height):
            for y in range(0, self.depth):
                for x in range(0, self.width):
                    index = self.get_index(x, y, z)
                    value = voxels[index] is not None
                    left_index = self.get_index(x - 1, y, z)
                    left_value = voxels[left_index] is not None if x > 0 else -1
                    back_index = self.get_index(x, y - 1, z)
                    back_value = voxels[back_index] is not None if y > 0 else -1
                    down_index = self.get_index(x, y, z - 1)
                    down_value = voxels[down_index] is not None if z > 0 else -1
                    possible_labels: Set[int] = set()
                    if value == left_value:
                        possible_labels.add(labels[left_index])
                    if value == back_value:
                        possible_labels.add(labels[back_index])
                    if value == down_value:
                        possible_labels.add(labels[down_index])
                    if len(possible_labels) == 0:
                        labels.append(next_label)
                        next_label += 1
                    elif len(possible_labels) == 1:
                        labels.append(list(possible_labels)[0])
                    else:
                        min_label = min(possible_labels)
                        labels.append(min_label)
                        for label in possible_labels:
                            if label not in label_equivalence:
                                label_equivalence[label] = set()
                            for other_label in possible_labels:
                                if other_label != label:
                                    label_equivalence[label].add(other_label)
        count = 0
        while count != len(label_equivalence):
            count = len(label_equivalence)
            for label in [i for i in label_equivalence.keys()]:
                connections = [x for x in label_equivalence[label]]
                min_label = min(connections)
                if min_label < label:
                    del label_equivalence[label]
                    for connected_label in connections:
                        if connected_label in label_equivalence:
                            next_connections = label_equivalence[connected_label]
                            for j in range(0, len(connections)):
                                if connections[j] != connected_label:
                                    next_connections.add(connections[j])
        label_map: Dict[int, int] = {}
        for label in range(0, next_label):
            if label in label_equivalence:
                for connection in label_equivalence[label]:
                    label_map[connection] = label
        for z in range(0, self.height):
            for y in range(0, self.depth):
                for x in range(0, self.width):
                    index = self.get_index(x, y, z)
                    if labels[index] in label_map:
                        labels[index] = label_map[labels[index]]
        return labels

    def find_outside_index(self, voxels: List[int or None]) -> int or None:
        for z in range(0, self.height):
            for x in range(0, self.width):
                index = self.get_index(x, 0, z)
                if voxels[index] is None:
                    return index
                index = self.get_index(x, self.last_index_y, z)
                if voxels[index] is None:
                    return index
        for y in range(0, self.depth):
            for x in range(0, self.width):
                index = self.get_index(x, y, 0)
                if voxels[index] is None:
                    return index
                index = self.get_index(x, y, self.last_index_z)
                if voxels[index] is None:
                    return index
        for y in range(0, self.depth):
            for z in range(0, self.height):
                index = self.get_index(0, y, z)
                if voxels[index] is None:
                    return index
                index = self.get_index(self.last_index_x, y, z)
                if voxels[index] is None:
                    return index
        return None


class Quad:
    def __init__(self,
                 p1: Tuple[float, float, float] = (0, 0, 0),
                 p2: Tuple[float, float, float] = (0, 0, 0),
                 p3: Tuple[float, float, float] = (0, 0, 0),
                 p4: Tuple[float, float, float] = (0, 0, 0),
                 normal: Tuple[float, float, float] = (0, 0, 0),
                 color: int = 0
                 ):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.normal = normal
        self.color = color


class SimpleCubesMeshing:
    @staticmethod
    def generate_mesh(grid: VoxelGrid, voxels: List[int or None]) -> List[Quad]:
        quads: List[Quad] = []
        for x in range(0, grid.width):
            for y in range(0, grid.depth):
                for z in range(0, grid.height):
                    color_index = voxels[grid.get_index(x, y, z)]
                    if color_index is not None:
                        # Left
                        quads.append(Quad(
                            (x, y, z),
                            (x, y + 1, z),
                            (x, y + 1, z + 1),
                            (x, y, z + 1),
                            (-1, 0, 0),
                            color_index
                        ))
                        # Right
                        quads.append(Quad(
                            (x + 1, y, z),
                            (x + 1, y, z + 1),
                            (x + 1, y + 1, z + 1),
                            (x + 1, y + 1, z),
                            (1, 0, 0),
                            color_index
                        ))
                        # Back
                        quads.append(Quad(
                            (x, y, z),
                            (x, y, z + 1),
                            (x + 1, y, z + 1),
                            (x + 1, y, z),
                            (0, -1, 0),
                            color_index
                        ))
                        # Front
                        quads.append(Quad(
                            (x, y + 1, z),
                            (x + 1, y + 1, z),
                            (x + 1, y + 1, z + 1),
                            (x, y + 1, z + 1),
                            (0, 1, 0),
                            color_index
                        ))
                        # Bottom
                        quads.append(Quad(
                            (x, y, z),
                            (x + 1, y, z),
                            (x + 1, y + 1, z),
                            (x, y + 1, z),
                            (0, 0, -1),
                            color_index
                        ))
                        # Top
                        quads.append(Quad(
                            (x, y, z + 1),
                            (x, y + 1, z + 1),
                            (x + 1, y + 1, z + 1),
                            (x + 1, y, z + 1),
                            (0, 0, 1),
                            color_index
                        ))
        return quads


class SimpleQuadsMeshing:
    @staticmethod
    def generate_mesh(grid: VoxelGrid, voxels: List[int or None],
                      outside: List[bool]) -> List[Quad]:
        quads: List[Quad] = []
        for x in range(0, grid.width):
            for y in range(0, grid.depth):
                for z in range(0, grid.height):
                    color_index = voxels[grid.get_index(x, y, z)]
                    if color_index is not None:
                        # Left
                        if x == 0 or outside[grid.get_index(x - 1, y, z)]:
                            quads.append(Quad(
                                (x, y, z),
                                (x, y + 1, z),
                                (x, y + 1, z + 1),
                                (x, y, z + 1),
                                (-1, 0, 0),
                                color_index
                            ))
                        # Right
                        if x == grid.last_index_x or outside[grid.get_index(x + 1, y, z)]:
                            quads.append(Quad(
                                (x + 1, y, z),
                                (x + 1, y, z + 1),
                                (x + 1, y + 1, z + 1),
                                (x + 1, y + 1, z),
                                (1, 0, 0),
                                color_index
                            ))
                        # Back
                        if y == 0 or outside[grid.get_index(x, y - 1, z)]:
                            quads.append(Quad(
                                (x, y, z),
                                (x, y, z + 1),
                                (x + 1, y, z + 1),
                                (x + 1, y, z),
                                (0, -1, 0),
                                color_index
                            ))
                        # Front
                        if y == grid.last_index_y or outside[grid.get_index(x, y + 1, z)]:
                            quads.append(Quad(
                                (x, y + 1, z),
                                (x + 1, y + 1, z),
                                (x + 1, y + 1, z + 1),
                                (x, y + 1, z + 1),
                                (0, 1, 0),
                                color_index
                            ))
                        # Bottom
                        if z == 0 or outside[grid.get_index(x, y, z - 1)]:
                            quads.append(Quad(
                                (x, y, z),
                                (x + 1, y, z),
                                (x + 1, y + 1, z),
                                (x, y + 1, z),
                                (0, 0, -1),
                                color_index
                            ))
                        # Top
                        if z == grid.last_index_z or outside[grid.get_index(x, y, z + 1)]:
                            quads.append(Quad(
                                (x, y, z + 1),
                                (x, y + 1, z + 1),
                                (x + 1, y + 1, z + 1),
                                (x + 1, y, z + 1),
                                (0, 0, 1),
                                color_index
                            ))
        return quads


class GreedyMeshing:
    @staticmethod
    def generate_mesh(grid: VoxelGrid, voxels: List[int or None],
                      outside: List[bool]) -> List[Quad]:
        quads: List[Quad] = []
        GreedyMeshing.mesh_axis(grid, voxels, outside, 0, quads)
        GreedyMeshing.mesh_axis(grid, voxels, outside, 1, quads)
        GreedyMeshing.mesh_axis(grid, voxels, outside, 2, quads)
        return quads

    @staticmethod
    def mesh_axis(grid: VoxelGrid, voxels: List[int or None],
                  outside: List[bool], axis_index: int, quads: List[Quad]):
        axis1_index = 1 if axis_index == 0 else (2 if axis_index == 1 else 0)
        axis2_index = 2 if axis_index == 0 else (0 if axis_index == 1 else 1)
        get_index = grid.get_index_func(axis_index, axis1_index, axis2_index)
        get_vector = GreedyMeshing.get_vector_func(axis_index, axis1_index, axis2_index)
        normals: List[Tuple[float, float, float]] = [
            (
                -1 if axis_index == 0 else 0,
                -1 if axis_index == 1 else 0,
                -1 if axis_index == 2 else 0,
            ),
            (
                1 if axis_index == 0 else 0,
                1 if axis_index == 1 else 0,
                1 if axis_index == 2 else 0,
            )
        ]
        normal_offsets = [-1, 1]
        for a in range(0, grid.get_axis(axis_index)):
            has_offset = [a > 0, a < grid.get_axis(axis_index) - 1]
            visited = [
                [False] * grid.get_axis(axis1_index) * grid.get_axis(axis2_index),
                [False] * grid.get_axis(axis1_index) * grid.get_axis(axis2_index)
            ]
            for b in range(0, grid.get_axis(axis1_index)):
                for c in range(0, grid.get_axis(axis2_index)):
                    visited_start_index = b * grid.get_axis(axis2_index) + c
                    grid_start_index = get_index(a, b, c)
                    start_voxel = voxels[grid_start_index]
                    if start_voxel is None:
                        visited[0][visited_start_index] = True
                        visited[1][visited_start_index] = True
                    else:
                        # Handle both directions separately as the visited pattern
                        # might be different, and we gather only the outer shell
                        for visited_index in range(0, 2):
                            if not visited[visited_index][visited_start_index]:
                                if has_offset[visited_index] and \
                                        not outside[get_index(a + normal_offsets[visited_index], b, c)]:
                                    visited[visited_index][visited_start_index] = True
                                    continue
                                # Move first axis until end or voxel mismatch
                                end_index_axis1 = b
                                for i in range(b + 1, grid.get_axis(axis1_index)):
                                    iter_visited_index = i * grid.get_axis(axis2_index) + c
                                    iter_index = get_index(a, i, c)
                                    iter_voxel = voxels[iter_index]
                                    if (
                                            # No voxel found...
                                            iter_voxel is None or
                                            # ...or already visited...
                                            visited[visited_index][iter_visited_index] or
                                            # ...or different color...
                                            start_voxel != iter_voxel or
                                            # ... or not connected to the outside space
                                            (has_offset[visited_index] and
                                             not outside[
                                                 get_index(a + normal_offsets[visited_index], i, c)
                                             ])
                                    ):
                                        end_index_axis1 = i - 1
                                        break
                                # Move second axis until end or voxel row mismatch
                                end_index_axis2 = c
                                for j in range(c + 1, grid.get_axis(axis2_index)):
                                    any_mismatch_in_row = False
                                    for i in range(b, end_index_axis1 + 1):
                                        iter_visited_index = i * grid.get_axis(axis2_index) + j
                                        iter_index = get_index(a, i, j)
                                        iter_voxel = voxels[iter_index]
                                        if (
                                                # No voxel found...
                                                iter_voxel is None or
                                                # ...or already visited...
                                                visited[visited_index][iter_visited_index] or
                                                # ...or different color...
                                                start_voxel != iter_voxel or
                                                # ... or not connected to the outside space
                                                (has_offset[visited_index] and
                                                 not outside[
                                                     get_index(a + normal_offsets[visited_index], i, j)
                                                 ])
                                        ):
                                            any_mismatch_in_row = True
                                            break
                                    if any_mismatch_in_row:
                                        end_index_axis2 = j - 1
                                        break
                                # Mark area as visited
                                for i in range(b, end_index_axis1 + 1):
                                    for j in range(c, end_index_axis2 + 1):
                                        visited[visited_index][i * grid.get_axis(axis2_index) + j] = True
                                # Store quad
                                quad = Quad()
                                quad.p1 = get_vector(a, b, c) \
                                    if visited_index == 0 \
                                    else get_vector(a + 1, b, c)
                                quad.p2 = get_vector(a, end_index_axis1 + 1, c) \
                                    if visited_index == 0 \
                                    else get_vector(a + 1, b, end_index_axis2 + 1)
                                quad.p3 = get_vector(a, end_index_axis1 + 1, end_index_axis2 + 1) \
                                    if visited_index == 0 \
                                    else get_vector(a + 1, end_index_axis1 + 1, end_index_axis2 + 1)
                                quad.p4 = get_vector(a, b, end_index_axis2 + 1) \
                                    if visited_index == 0 \
                                    else get_vector(a + 1, end_index_axis1 + 1, c)
                                quad.color = start_voxel
                                quad.normal = normals[visited_index]
                                quads.append(quad)

    @staticmethod
    def get_vector_func(axis_index: int, axis1_index: int, axis2_index: int):
        if axis_index == 0 and axis1_index == 1 and axis2_index == 2:
            return lambda x, y, z: (x, y, z)
        if axis_index == 1 and axis1_index == 0 and axis2_index == 2:
            return lambda y, x, z: (x, y, z)
        if axis_index == 1 and axis1_index == 2 and axis2_index == 0:
            return lambda y, z, x: (x, y, z)
        if axis_index == 0 and axis1_index == 2 and axis2_index == 1:
            return lambda x, z, y: (x, y, z)
        if axis_index == 2 and axis1_index == 0 and axis2_index == 1:
            return lambda z, x, y: (x, y, z)
        # 2, 1, 0
        return lambda z, y, x: (x, y, z)


class VoxMesh:
    def __init__(self, model_id: int, width: int, depth: int, height: int):
        self.model_id = model_id
        self.grid: VoxelGrid = VoxelGrid(width, depth, height)
        self.voxels: List[int or None] = [None] * width * depth * height

    def set_voxel_color_index(self, x: int, y: int, z: int, color_index: int):
        index = self.grid.get_index(x, y, z)
        self.voxels[index] = color_index

    def get_voxel_color_index(self, x: int, y: int, z: int) -> int or None:
        index = self.grid.get_index(x, y, z)
        return self.voxels[index]


class VoxNode:
    def __init__(self):
        self.type = "TRN"  # "TRN" or "GRP" or "SHP"
        self.node_id = -1
        self.layer_id = -1
        self.node_attributes: Dict[str, str] = {}
        self.frame_attributes: Dict[int, Dict[str, str]] = {}
        self.meshes: Dict[int, Dict[str, str]] = {}

    def get_transform(self, frame: int):
        matching_attributes_by_frame_key = [
            x for x in self.frame_attributes.values()
            if "_f" in x and x["_f"] == frame
        ]
        return matching_attributes_by_frame_key[0] \
            if len(matching_attributes_by_frame_key) > 0 \
            else self.frame_attributes[0]

    def get_transform_translation(self, frame: int, voxel_size: float):
        transform = self.get_transform(frame)
        if "_t" in transform:
            t_parts = transform["_t"].split(" ")
            return mathutils.Matrix.Translation(
                mathutils.Vector((
                    int(t_parts[0]) * voxel_size,
                    int(t_parts[1]) * voxel_size,
                    int(t_parts[2]) * voxel_size
                ))
            )
        else:
            return mathutils.Matrix()

    def get_transform_rotation(self, frame: int):
        transform = self.get_transform(frame)
        rotation = mathutils.Matrix()
        if "_r" in transform:
            rotation_byte = int(transform["_r"])
            first_row_index = rotation_byte & 3
            second_row_index = (rotation_byte >> 2) & 3
            third_row_index = [0, 1, 2]
            third_row_index.remove(first_row_index)
            third_row_index.remove(second_row_index)
            third_row_index = third_row_index[0]
            first_row_sign = (rotation_byte >> 3) & 1
            second_row_sign = (rotation_byte >> 4) & 1
            third_row_sign = (rotation_byte >> 5) & 1
            rotation.zero()
            rotation[0][first_row_index] = 1 if first_row_sign == 0 else -1
            rotation[1][second_row_index] = 1 if second_row_sign == 0 else -1
            rotation[2][third_row_index] = 1 if third_row_sign == 0 else -1
            rotation[3][3] = 1
        return rotation


class VoxModel:
    def __init__(self, version: int):
        self.version = version
        self.next_model_id: int = 0
        self.color_palette = [x for x in DEFAULT_PALETTE]
        self.color_palette_lookup: Dict[int, int] = {i: i for i in range(256)}
        self.materials: Dict[int, Dict[str, str]] = {}
        self.layers: Dict[int, Dict[str, str]] = {}
        self.cameras: Dict[int, Dict[str, str]] = {}
        self.rendering_attributes: List[Dict[str, str]] = []
        self.meshes: List[VoxMesh] = []
        self.nodes: Dict[int, VoxNode] = {}
        self.node_parent_relations: Dict[int, int] = {}

    def get_color(self, color_index: int) -> Tuple[float, float, float, float]:
        # Map color index using IMAP
        color_index = self.color_palette_lookup[color_index]
        color = self.color_palette[color_index]
        return color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0


def voxels_as_cubes_on_update(self, _context):
    if self.convert_to_mesh is self.voxels_as_cubes:
        self.convert_to_mesh = not self.voxels_as_cubes


def convert_to_mesh_on_update(self, _context):
    if self.voxels_as_cubes is self.convert_to_mesh:
        self.voxels_as_cubes = not self.convert_to_mesh
    if self.convert_to_mesh:
        self.voxel_hull = True


class ImportVOX(bpy.types.Operator, ImportHelper):
    """Load a MagicaVoxel VOX File"""
    bl_idname = "import_scene.vox"
    bl_label = "Import VOX"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".vox"
    filter_glob: StringProperty(
        default="*.vox",
        options={'HIDDEN'},
    )

    import_cameras: BoolProperty(
        name="Import Cameras",
        description="Import camera definitions from MagicaVoxel",
        default=False,
    )

    import_materials: BoolProperty(
        name="Import Materials",
        description="Import material definitions from MagicaVoxel",
        default=False,
    )

    import_hierarchy: BoolProperty(
        name="Import Hierarchy",
        description="Import hierarchy from MagicaVoxel as collections",
        default=False,
    )

    voxel_size: FloatProperty(
        name="Voxel Size",
        description="Size of the imported voxels",
        min=0.0001,
        soft_min=0.0001,
        default=1.0,
    )

    meshing_type: EnumProperty(
        name="Meshing Type",
        items=[
            ("CUBES_AS_OBJ", "Voxel as Models", "Each Voxel as an individual cube object"),
            ("SIMPLE_CUBES", "Simple Cubes", "Each Voxel as a cube in one mesh"),
            ("SIMPLE_QUADS", "Simple Quads", "Outside facing Voxel faces as quads in one mesh"),
            ("GREEDY", "Greedy", "Outside facing Voxel faces greedy optimized in one mesh")
        ],
        description="",
        default="SIMPLE_QUADS"
    )

    voxel_hull: BoolProperty(
        name="Reduce Voxels to Hull",
        description="",
        default=True,
    )

    merge_models: BoolProperty(
        name="Merge Models",
        description="",
        default=False,
    )

    def execute(self, context):
        keywords = self.as_keywords(
            ignore=(
                "filter_glob",
                "import_cameras",
                "import_materials",
                "voxel_size",
                "voxel_hull",
                "meshing_type",
                "merge_models",
            ),
        )
        filepath = keywords['filepath']
        result = self.load_vox(filepath)
        if result is not None:
            collection_name = os.path.basename(filepath)
            view_layer = context.view_layer
            active_collection = view_layer.active_layer_collection.collection
            voxel_collection = context.blend_data.collections.new(name=collection_name)
            active_collection.children.link(voxel_collection)
            # context.view_layer.active_layer_collection = voxel_collection
            if self.import_cameras:
                for camera_id in result.cameras:
                    camera = result.cameras[camera_id]
                    camera_data = bpy.data.cameras.new(name="camera_%s" % camera_id)
                    if "_fov" in camera:
                        camera_data.angle = math.radians(float(camera["_fov"]))
                    if "_mode" in camera:
                        mode = camera["_mode"]
                        if mode == "sg":
                            self.report({"WARNING"},
                                        "Camera %s mode 'sg' is not supported, fallback to 'pers'" % camera_id)
                        camera_data.type = "PANO" if mode == "pano" else "PERSP"
                    # TODO: {'_focus': '0 0 0', '_angle': '0 0 0', '_radius': '0', '_frustum': '0.414214'}
                    #  (_mode : string)
                    #  (_focus : vec(3))
                    #  (_angle : vec(3))
                    #  (_radius : int)
                    #  (_frustum : float)
                    camera_object = bpy.data.objects.new("camera_%s" % camera_id, camera_data)
                    voxel_collection.objects.link(camera_object)
            if self.import_materials:
                for material_id in result.materials:
                    material = result.materials[material_id]
                    # TODO: {'_rough': '0.1', '_ior': '0.3', '_ri': '1.3', '_d': '0.05'}
                    #  (_type : str) _diffuse, _metal, _glass, _emit
                    #  (_weight : float) range 0 ~ 1
                    #  (_rough : float)
                    #  (_spec : float)
                    #  (_ior : float)
                    #  (_att : float)
                    #  (_flux : float)
                    #  (_plastic)
            node_id_empty_lookup = {}
            if self.import_hierarchy:
                for node_id in result.nodes:
                    node = result.nodes[node_id]
                    if node.type == "GRP":
                        transform_node = result.nodes[result.node_parent_relations[node_id]]
                        # TODO: frame
                        translation = transform_node.get_transform_translation(0, self.voxel_size)
                        rotation = transform_node.get_transform_rotation(0)
                        group_data = bpy.data.objects.new("grp_%s" % node_id, None)
                        group_data.empty_display_size = 1
                        group_data.empty_display_type = 'PLAIN_AXES'
                        group_data.matrix_local = translation @ rotation
                        voxel_collection.objects.link(group_data)
                        node_id_empty_lookup[node_id] = group_data
                for node_id in node_id_empty_lookup:
                    current_node_id = node_id
                    while current_node_id in result.node_parent_relations:
                        current_node_id = result.node_parent_relations[current_node_id]
                        next_node = result.nodes[current_node_id]
                        if next_node.type == "GRP":
                            node_id_empty_lookup[node_id].parent = node_id_empty_lookup[next_node.node_id]
                            break
            mesh_index = -1
            for mesh in result.meshes:
                generated_mesh_models = []
                mesh_index += 1
                outside = mesh.grid.create_outside_grid(mesh.voxels)
                if self.meshing_type == "CUBES_AS_OBJ":
                    if self.voxel_hull:
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                    for x in range(0, mesh.grid.width):
                        for y in range(0, mesh.grid.depth):
                            for z in range(0, mesh.grid.height):
                                color_index = mesh.get_voxel_color_index(x, y, z)
                                if color_index is not None:
                                    vertices = []
                                    faces = []
                                    vertices.append(self.get_vertex_pos((x, y, z), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x + 1, y, z), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x, y + 1, z), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x + 1, y + 1, z), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x, y, z + 1), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x + 1, y, z + 1), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x, y + 1, z + 1), mesh.grid))
                                    vertices.append(self.get_vertex_pos((x + 1, y + 1, z + 1), mesh.grid))
                                    faces.append([0, 2, 3, 1])
                                    faces.append([4, 5, 7, 6])
                                    faces.append([0, 1, 5, 4])
                                    faces.append([2, 6, 7, 3])
                                    faces.append([0, 4, 6, 2])
                                    faces.append([1, 3, 7, 5])
                                    new_mesh = bpy.data.meshes.new("mesh_%s_voxel_%s_%s_%s" % (mesh_index, x, y, z))
                                    new_mesh.from_pydata(vertices, [], faces)
                                    new_mesh.update()
                                    new_mesh.vertex_colors.new()
                                    vertex_colors = new_mesh.vertex_colors[0].data
                                    color = result.get_color(color_index)
                                    for i in range(len(faces) * 4):
                                        vertex_colors[i].color = color
                                    new_object = bpy.data.objects.new("model_%s_voxel_%s_%s_%s" % (mesh_index, x, y, z),
                                                                      new_mesh)
                                    voxel_collection.objects.link(new_object)
                                    generated_mesh_models.append(new_object)
                else:
                    if self.meshing_type == "GREEDY":
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = GreedyMeshing.generate_mesh(mesh.grid, mesh.voxels, outside)
                    elif self.meshing_type == "SIMPLE_QUADS":
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = SimpleQuadsMeshing.generate_mesh(mesh.grid, mesh.voxels, outside)
                    elif self.meshing_type == "SIMPLE_CUBES":
                        if self.voxel_hull:
                            mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = SimpleCubesMeshing.generate_mesh(mesh.grid, mesh.voxels)
                    else:
                        self.report({"WARNING"}, "Unknown meshing type %s" % self.meshing_type)
                        quads = []
                    vertices = []
                    faces = []
                    offset = 0
                    for quad in quads:
                        vertices.append(self.get_vertex_pos(quad.p1, mesh.grid))
                        vertices.append(self.get_vertex_pos(quad.p2, mesh.grid))
                        vertices.append(self.get_vertex_pos(quad.p3, mesh.grid))
                        vertices.append(self.get_vertex_pos(quad.p4, mesh.grid))
                        faces.append([offset, offset + 1, offset + 2, offset + 3])
                        offset += 4
                    new_mesh = bpy.data.meshes.new("mesh_%s" % mesh_index)
                    new_mesh.from_pydata(vertices, [], faces)
                    new_mesh.update()
                    new_mesh.vertex_colors.new()
                    vertex_colors = new_mesh.vertex_colors[0].data
                    for i in range(len(quads)):
                        vertex_offset = i * 4
                        color = result.get_color(quads[i].color)
                        vertex_colors[vertex_offset].color = color
                        vertex_colors[vertex_offset + 1].color = color
                        vertex_colors[vertex_offset + 2].color = color
                        vertex_colors[vertex_offset + 3].color = color
                    new_object = bpy.data.objects.new('model_%s' % mesh_index, new_mesh)
                    voxel_collection.objects.link(new_object)
                    generated_mesh_models.append(new_object)
                    # Remove duplicate vertices
                    bpy.context.view_layer.objects.active = new_object
                    bpy.ops.object.editmode_toggle()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.remove_doubles(
                        threshold=0.0001,
                        use_unselected=True,
                        use_sharp_edge_from_normals=True
                    )
                    bpy.ops.object.editmode_toggle()

                # Translate generated meshes and associate if requested with node hierarchy
                parent_nodes = [n for n in result.nodes.values() if n.type == "SHP" and mesh.model_id in n.meshes]
                if len(parent_nodes) > 0:
                    parent_node = parent_nodes[0]
                    if self.import_hierarchy:
                        current_node_id = parent_node.node_id
                        while current_node_id in result.node_parent_relations:
                            current_node_id = result.node_parent_relations[current_node_id]
                            next_node = result.nodes[current_node_id]
                            if next_node.type == "GRP":
                                for generated_mesh_model in generated_mesh_models:
                                    generated_mesh_model.parent = node_id_empty_lookup[next_node.node_id]
                                break
                    mesh_attributes = parent_node.meshes[mesh.model_id]
                    mesh_frame = mesh_attributes["_f"] if "_f" in mesh_attributes else 0
                    current_node_id = parent_node.node_id
                    while current_node_id in result.node_parent_relations:
                        current_node_id = result.node_parent_relations[current_node_id]
                        next_node = result.nodes[current_node_id]
                        if next_node.type == 'TRN':
                            translation = next_node.get_transform_translation(mesh_frame, self.voxel_size)
                            rotation = next_node.get_transform_rotation(mesh_frame)
                            for generated_mesh_model in generated_mesh_models:
                                if self.import_hierarchy:
                                    generated_mesh_model.matrix_local = translation @ rotation
                                else:
                                    matrix_world = generated_mesh_model.matrix_world
                                    matrix_world = translation @ rotation @ matrix_world
                                    generated_mesh_model.matrix_world = matrix_world
                            if self.import_hierarchy:
                                # If we import the hierarchy, we only need to apply the
                                # nearest transform node as all other transforms are applied
                                # by the object parent hierarchy
                                break

        return {"CANCELLED"} if result is None else {'FINISHED'}

    def get_vertex_pos(self, p: Tuple[float, float, float], grid: VoxelGrid) -> Tuple[float, float, float]:
        return (
            (p[0] - math.floor(grid.width * 0.5)) * self.voxel_size,
            (p[1] - math.floor(grid.depth * 0.5)) * self.voxel_size,
            (p[2] - math.floor(grid.height * 0.5)) * self.voxel_size
        )

    def load_vox(self, filepath: str) -> VoxModel or None:
        with open(filepath, "rb") as f:
            if ImportVOX.read_riff_id(f) != "VOX ":
                self.report({"WARNING"}, "File is not in VOX format")
                return None
            version = ImportVOX.read_int32(f)
            model = VoxModel(version)
            print('MagicaVoxel vox file version %s' % version)
            while f.tell() < os.fstat(f.fileno()).st_size:
                ImportVOX.read_next_chunk(f, model)
        return model

    @staticmethod
    def read_riff_id(f: IO) -> str:
        return "".join(map(chr, f.read(4)))

    @staticmethod
    def read_int32(f: IO) -> int:
        return struct.unpack('<i', f.read(4))[0]

    @staticmethod
    def read_float32(f: IO) -> int:
        return struct.unpack('<f', f.read(4))[0]

    @staticmethod
    def read_uint8(f: IO) -> int:
        return struct.unpack('B', f.read(1))[0]

    @staticmethod
    def read_string(f: IO) -> str:
        length = ImportVOX.read_int32(f)
        return "".join(map(chr, f.read(length))) if length > 0 else ""

    @staticmethod
    def read_dict(f: IO) -> Dict[str, str]:
        num_pairs = ImportVOX.read_int32(f)
        return {
            ImportVOX.read_string(f): ImportVOX.read_string(f)
            for _ in range(0, num_pairs)
        }

    @staticmethod
    def read_next_chunk(f: IO, model: VoxModel):
        riff_id = ImportVOX.read_riff_id(f)
        content_byte_length = ImportVOX.read_int32(f)
        ImportVOX.read_int32(f)  # children_byte_length
        current_position = f.tell()
        if riff_id == 'PACK':
            ImportVOX.read_int32(f)  # num_models
        elif riff_id == 'SIZE':
            mesh = VoxMesh(
                model.next_model_id,
                ImportVOX.read_int32(f),
                ImportVOX.read_int32(f),
                ImportVOX.read_int32(f)
            )
            model.next_model_id += 1
            model.meshes.append(mesh)
        elif riff_id == 'XYZI':
            num_voxels = ImportVOX.read_int32(f)
            for i in range(0, num_voxels):
                model.meshes[-1].set_voxel_color_index(
                    ImportVOX.read_uint8(f),
                    ImportVOX.read_uint8(f),
                    ImportVOX.read_uint8(f),
                    ImportVOX.read_uint8(f)
                )
        elif riff_id == 'rCAM':
            camera_id = ImportVOX.read_int32(f)
            model.cameras[camera_id] = ImportVOX.read_dict(f)
        elif riff_id == 'rOBJ':
            model.rendering_attributes.append(ImportVOX.read_dict(f))
        elif riff_id == 'nTRN':
            node = VoxNode()
            node.type = "TRN"
            node.node_id = ImportVOX.read_int32(f)
            node.node_attributes = ImportVOX.read_dict(f)
            child_node_id = ImportVOX.read_int32(f)
            ImportVOX.read_int32(f)  # reserved id, must be -1
            node.layer_id = ImportVOX.read_int32(f)
            num_frames = ImportVOX.read_int32(f)
            node.frame_attributes = {i: ImportVOX.read_dict(f) for i in range(0, num_frames)}
            model.nodes[node.node_id] = node
            model.node_parent_relations[child_node_id] = node.node_id
        elif riff_id == 'nGRP':
            node = VoxNode()
            node.type = "GRP"
            node.node_id = ImportVOX.read_int32(f)
            node.node_attributes = ImportVOX.read_dict(f)
            num_child_ids = ImportVOX.read_int32(f)
            for i in range(0, num_child_ids):
                child_node_id = ImportVOX.read_int32(f)
                model.node_parent_relations[child_node_id] = node.node_id
            model.nodes[node.node_id] = node
        elif riff_id == 'nSHP':
            node = VoxNode()
            node.type = "SHP"
            node.node_id = ImportVOX.read_int32(f)
            node.node_attributes = ImportVOX.read_dict(f)
            num_models = ImportVOX.read_int32(f)
            for i in range(0, num_models):
                model_id = ImportVOX.read_int32(f)
                model_attributes = ImportVOX.read_dict(f)
                node.meshes[model_id] = model_attributes
            model.nodes[node.node_id] = node
        elif riff_id == 'MATL':
            material_id = ImportVOX.read_int32(f)
            model.materials[material_id] = ImportVOX.read_dict(f)
            # print('MATL', material_id, model.materials[material_id])
        elif riff_id == 'MATT':  # Legacy material
            material_id = ImportVOX.read_int32(f)
            # 0: diffuse, 1: metal, 2: glass, 3: emissive
            material_type = ImportVOX.read_int32(f)
            type_keys = ['_diffuse', '_metal', '_glass', '_emit']
            # diffuse:   1.0
            # metal:    (0.0 - 1.0] : blend between metal and diffuse material
            # glass:    (0.0 - 1.0] : blend between glass and diffuse material
            # emissive: (0.0 - 1.0] : self-illuminated material
            material_weight = ImportVOX.read_float32(f)
            # set if value is saved in next section
            # bit(0) : Plastic
            # bit(1) : Roughness
            # bit(2) : Specular
            # bit(3) : IOR
            # bit(4) : Attenuation
            # bit(5) : Power
            # bit(6) : Glow
            # bit(7) : isTotalPower (*no value)
            property_bits = ImportVOX.read_int32(f)
            # TODO: translate rest of keys
            bit_keys = ['_plastic', '_rough', '_spec', '_ior', '_att', 'power', 'glow', 'isTotalPower']
            # TODO: normalized property value: (0.0 - 1.0], need to map to real range
            property_values = {bit_keys[i]: 1 if i == 7 else ImportVOX.read_float32(f) for i in range(8) if
                               (1 << i) & property_bits != 0}
            property_values['_weight'] = material_weight
            if 0 <= material_type < len(type_keys):
                property_values['_type'] = type_keys[material_type]
            else:
                property_values['_type'] = type_keys[0]
            model.materials[material_id] = property_values
            # print('MATT', material_id, model.materials[material_id])
        elif riff_id == 'LAYR':
            layer_id = ImportVOX.read_int32(f)
            model.layers[layer_id] = ImportVOX.read_dict(f)
            _ = ImportVOX.read_int32(f)  # reserved id, must be -1
        elif riff_id == 'RGBA':
            custom_palette: List[Tuple[int, int, int, int]] = [(0, 0, 0, 255)]
            for i in range(256):
                r = ImportVOX.read_uint8(f)
                g = ImportVOX.read_uint8(f)
                b = ImportVOX.read_uint8(f)
                a = ImportVOX.read_uint8(f)
                color = (r, g, b, a)
                if i == 255:
                    custom_palette[0] = color
                else:
                    custom_palette.append(color)
            model.color_palette = custom_palette
        elif riff_id == 'IMAP':
            _ = {ImportVOX.read_uint8(f): (i + 1) % 256 for i in range(256)}  # model.color_palette_lookup
            # TODO: IMAP seems to collide with custom palette. Needs further investigation
        elif riff_id == 'NOTE':
            num_color_names = ImportVOX.read_int32(f)
            _ = [ImportVOX.read_string(f) for _ in range(num_color_names)]  # color_names
            # TODO
        # Skip unknown data
        if current_position + content_byte_length > f.tell():
            f.seek(current_position + content_byte_length)

    def draw(self, context):
        pass


class VOX_PT_import_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_vox"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        # layout.prop(operator, "import_cameras")
        # layout.prop(operator, "import_materials")
        layout.prop(operator, "import_hierarchy")


class VOX_PT_import_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "IMPORT_SCENE_OT_vox"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "voxel_size")
        # layout.row().prop(operator, "merge_models")
        layout.row().prop(operator, "meshing_type")
        if operator.meshing_type in ["CUBES_AS_OBJ", "SIMPLE_CUBES"]:
            layout.row().prop(operator, "voxel_hull")


def menu_func_import(self, _context):
    self.layout.operator(ImportVOX.bl_idname, text="MagicaVoxel (.vox)")


classes = (
    ImportVOX,
    VOX_PT_import_include,
    VOX_PT_import_geometry,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
