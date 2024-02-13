# MIT License
#
# Copyright (c) 2024 https://github.com/AstrorEnales
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
import io
import time
import bpy
import os
import math
import mathutils
import struct
from functools import cmp_to_key
from typing import IO, List, Dict, Tuple, Set
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    IntProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
)

bl_info = {
    "name": "MagicaVoxel VOX format",
    "author": "AstrorEnales",
    "version": (1, 4, 3),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Importer for MagicaVoxel VOX files",
    "category": "Import-Export",
    "doc_url": "https://github.com/AstrorEnales/blender_magicavoxel",
    "tracker_url": "https://github.com/AstrorEnales/blender_magicavoxel/issues",
    "support": "COMMUNITY",
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

DEBUG_OUTPUT = False
READ_INT_UNPACK = struct.Struct('<i').unpack
READ_FLOAT_UNPACK = struct.Struct('<f').unpack


class RectanglePacker:
    """
    Rectangle packer translated from Javier Arevalo
    https://www.flipcode.com/archives/Rectangle_Placement.shtml
    """

    def __init__(self, packing_area_width: int, packing_area_height: int):
        self.packed_rectangles: List[Tuple[int, int, int, int]] = []
        self.anchors: List[Tuple[int, int]] = [(0, 0)]
        self.packing_area_width = packing_area_width
        self.packing_area_height = packing_area_height
        self.actual_packing_area_width = 1
        self.actual_packing_area_height = 1

    @staticmethod
    def compare_anchor_rank(a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return a[0] + a[1] - (b[0] + b[1])

    def insert_anchor(self, anchor: Tuple[int, int]):
        """
        Inserts a new anchor point into the anchor list.
        This method tries to keep the anchor list ordered by ranking the anchors depending on the distance from the top
        left corner in the packing area.
        """
        # Find out where to insert the new anchor based on its rank (which is calculated based on the anchor's distance
        # to the top left corner of the packing area).
        self.anchors.append(anchor)
        self.anchors.sort(key=cmp_to_key(RectanglePacker.compare_anchor_rank))

    @staticmethod
    def rectangles_intersect(a_x: int, a_y: int, a_width: int, a_height: int,
                             b_x: int, b_y: int, b_width: int, b_height: int) -> bool:
        return b_x < a_x + a_width and a_x < b_x + b_width and b_y < a_y + a_height and a_y < b_y + b_height

    def is_free(self, rectangle_x: int, rectangle_y: int, rectangle_width: int, rectangle_height: int,
                tested_packing_area_width: int, tested_packing_area_height: int) -> bool:
        leaves_packing_area = rectangle_x < 0 or \
                              rectangle_y < 0 or \
                              rectangle_x + rectangle_width > tested_packing_area_width or \
                              rectangle_y + rectangle_height > tested_packing_area_height
        if leaves_packing_area:
            return False
        # Brute-force search whether the rectangle touches any of the other rectangles already in the packing area
        for index in range(0, len(self.packed_rectangles)):
            other = self.packed_rectangles[index]
            if self.rectangles_intersect(other[0], other[1], other[2], other[3], rectangle_x, rectangle_y,
                                         rectangle_width, rectangle_height):
                return False
        return True

    def find_first_free_anchor(self, rectangle_width: int, rectangle_height: int, tested_packing_area_width: int,
                               tested_packing_area_height: int) -> int:
        # Walk over all anchors (which are ordered by their distance to the upper left corner of the packing area) until
        # one is discovered that can house the new rectangle.
        for index in range(0, len(self.anchors)):
            if self.is_free(self.anchors[index][0], self.anchors[index][1], rectangle_width, rectangle_height,
                            tested_packing_area_width, tested_packing_area_height):
                return index
        return -1

    def select_anchor_recursive(self, rectangle_width: int, rectangle_height: int,
                                tested_packing_area_width: int, tested_packing_area_height: int) -> int:
        """
        Searches for a free anchor and recursively enlarges the packing area if none can be found.
        """
        # Try to locate an anchor point where the rectangle fits in
        free_anchor_index = self.find_first_free_anchor(rectangle_width, rectangle_height, tested_packing_area_width,
                                                        tested_packing_area_height)
        # If the rectangle fits without resizing packing area (any further in case of a recursive call), take over the
        # new packing area size and return the anchor at which the rectangle can be placed.
        if free_anchor_index != -1:
            self.actual_packing_area_width = tested_packing_area_width
            self.actual_packing_area_height = tested_packing_area_height
            return free_anchor_index
        # If we reach this point, the rectangle did not fit in the current packing area and our only choice is to try
        # and enlarge the packing area. For readability, determine whether the packing area can be enlarged any further
        # in its width and in its height
        can_enlarge_width = tested_packing_area_width < self.packing_area_width
        can_enlarge_height = tested_packing_area_height < self.packing_area_height
        should_enlarge_height = not can_enlarge_width or tested_packing_area_height < tested_packing_area_width
        # Try to enlarge the smaller of the two dimensions first (unless the smaller dimension is already at its maximum
        # size). 'shouldEnlargeHeight' is true when the height was the smaller dimension or when the width is maxed out.
        if can_enlarge_height and should_enlarge_height:
            # Try to double the height of the packing area
            return self.select_anchor_recursive(rectangle_width, rectangle_height, tested_packing_area_width,
                                                min(tested_packing_area_height * 2, self.packing_area_height))
        if can_enlarge_width:
            # Try to double the width of the packing area
            return self.select_anchor_recursive(rectangle_width, rectangle_height,
                                                min(tested_packing_area_width * 2, self.packing_area_width),
                                                tested_packing_area_height)
        return -1

    def optimize_placement(self, placement: Tuple[int, int], rectangle_width: int, rectangle_height: int) \
            -> Tuple[int, int]:
        """
        Optimizes the rectangle's placement by moving it either left or up to fill any gaps resulting from rectangles
        blocking the anchors of the most optimal placements.
        """
        test_coordinate = placement[0]
        # Try to move the rectangle to the left as far as possible
        left_most = placement[0]
        while self.is_free(test_coordinate, placement[1], rectangle_width, rectangle_height, self.packing_area_width,
                           self.packing_area_height):
            left_most = test_coordinate
            test_coordinate -= 1
        # Reset rectangle to original position
        test_coordinate = placement[1]
        # Try to move the rectangle upwards as far as possible
        top_most = placement[1]
        while self.is_free(placement[0], test_coordinate, rectangle_width, rectangle_height, self.packing_area_width,
                           self.packing_area_height):
            top_most = test_coordinate
            test_coordinate -= 1
        # Use the dimension in which the rectangle could be moved farther
        if placement[0] - left_most > placement[1] - top_most:
            return left_most, placement[1]
        else:
            return placement[0], top_most

    def try_pack(self, rectangle_width: int, rectangle_height: int) -> Tuple[bool, Tuple[int, int]]:
        """
        Tries to allocate space for a rectangle in the packing area.
        """
        # Try to find an anchor where the rectangle fits in, enlarging the packing area and repeating the search
        # recursively until it fits or the maximum allowed size is exceeded.
        anchor_index = self.select_anchor_recursive(rectangle_width, rectangle_height, self.actual_packing_area_width,
                                                    self.actual_packing_area_height)
        # No anchor could be found at which the rectangle did fit in
        if anchor_index == -1:
            return False, (0, 0)
        anchor = self.anchors[anchor_index]
        # Move the rectangle either to the left or to the top until it collides with a neighbouring rectangle. This is
        # done to combat the effect of lining up rectangles with gaps to the left or top of them because the anchor that
        # would allow placement there has been blocked by another rectangle
        placement = self.optimize_placement((anchor[0], anchor[1]), rectangle_width, rectangle_height)
        # Remove the used anchor and add new anchors at the upper right and lower left positions of the new rectangle.
        # The anchor is only removed if the placement optimization didn't move the rectangle so far that the anchor
        # isn't blocked anymore
        blocks_anchor = placement[0] + rectangle_width > anchor[0] and placement[1] + rectangle_height > anchor[1]
        if blocks_anchor:
            del self.anchors[anchor_index]
        # Add new anchors at the upper right and lower left coordinates of the rectangle
        self.insert_anchor((placement[0] + rectangle_width, placement[1]))
        self.insert_anchor((placement[0], placement[1] + rectangle_height))
        # Finally, we can add the rectangle to our packed rectangles list
        self.packed_rectangles.append((placement[0], placement[1], rectangle_width, rectangle_height))
        return True, placement


ChildXnYnZn = 0
ChildXpYnZn = 1
ChildXnYpZn = 2
ChildXpYpZn = 3
ChildXnYnZp = 4
ChildXpYnZp = 5
ChildXnYpZp = 6
ChildXpYpZp = 7
SideLength = 4
LeafIndexXMap = [
    0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2,
    3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3
]
LeafIndexYMap = [
    0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1,
    1, 2, 2, 2, 2, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3
]
LeafIndexZMap = [
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3
]
SideLengthTwice = SideLength * SideLength
GridLength = SideLength * SideLength * SideLength


class Octree:
    def __init__(self, size: int = 8, default_value: any = None):
        self.size = 2 ** (max(8, size) - 1).bit_length()
        self.size_half = self.size >> 1
        self.default_value = default_value
        self._root = OctreeBranchNode(self, -self.size_half, -self.size_half, -self.size_half, self.size,
                                      self.default_value)
        self.leafs: List[OctreeLeafNode] = []

    @property
    def is_full(self) -> bool:
        return self._root.is_full

    @property
    def is_empty(self) -> bool:
        return self._root.is_empty

    @property
    def is_not_empty(self) -> bool:
        return self._root.is_not_empty

    @property
    def count(self) -> int:
        return self._root.count

    @property
    def not_empty_bounds(self) -> Tuple[int, int, int, int, int, int]:
        return self._root.not_empty_bounds

    def get_value(self, x: int, y: int, z: int) -> any:
        return self.default_value if self.is_outside(x, y, z) else self._root.get_value(x, y, z)

    def contains(self, x: int, y: int, z: int) -> bool:
        return self.is_inside(x, y, z) and self._root.contains(x, y, z)

    def is_outside(self, x: int, y: int, z: int) -> bool:
        return (x >= self.size_half or x < -self.size_half or y >= self.size_half or y < -self.size_half or
                z >= self.size_half or z < -self.size_half)

    def is_inside(self, x: int, y: int, z: int) -> bool:
        # noinspection PyChainedComparisons
        return (x < self.size_half and x >= -self.size_half and y < self.size_half and y >= -self.size_half and
                z < self.size_half and z >= -self.size_half)

    def add(self, x: int, y: int, z: int, value: any):
        while self.is_outside(x, y, z):
            self._expand()
        self._root.add(x, y, z, value)

    def _expand(self):
        self.size_half <<= 1
        self.size <<= 1
        total_count = 0
        new_root = OctreeBranchNode(self, -self.size_half, -self.size_half, -self.size_half, self.size,
                                    self.default_value)
        # Y+
        child = self._root.child_nodes[ChildXpYpZp]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x, child.start_position_y, child.start_position_z,
                                         child.size * 2, self.default_value)
            new_child.child_nodes[ChildXnYnZn] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXpYpZp] = new_child

        child = self._root.child_nodes[ChildXpYpZn]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x, child.start_position_y,
                                         child.start_position_z - child.size, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXnYnZp] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXpYpZn] = new_child

        child = self._root.child_nodes[ChildXnYpZp]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x - child.size, child.start_position_y,
                                         child.start_position_z, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXpYnZn] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXnYpZp] = new_child

        child = self._root.child_nodes[ChildXnYpZn]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x - child.size, child.start_position_y,
                                         child.start_position_z - child.size, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXpYnZp] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXnYpZn] = new_child

        # Y-
        child = self._root.child_nodes[ChildXpYnZp]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x, child.start_position_y - child.size,
                                         child.start_position_z, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXnYpZn] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXpYnZp] = new_child

        child = self._root.child_nodes[ChildXpYnZn]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x, child.start_position_y - child.size,
                                         child.start_position_z - child.size, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXnYpZp] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXpYnZn] = new_child

        child = self._root.child_nodes[ChildXnYnZp]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x - child.size, child.start_position_y - child.size,
                                         child.start_position_z, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXpYpZn] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXnYnZp] = new_child

        child = self._root.child_nodes[ChildXnYnZn]
        if child is not None:
            new_child = OctreeBranchNode(self, child.start_position_x - child.size, child.start_position_y - child.size,
                                         child.start_position_z - child.size, child.size * 2, self.default_value)
            new_child.child_nodes[ChildXpYpZp] = child
            new_child._count = child.count
            total_count += child.count
            new_child.bounds_set = child.bounds_set
            new_child.min_x = child.min_x
            new_child.min_y = child.min_y
            new_child.min_z = child.min_z
            new_child.max_x = child.max_x
            new_child.max_y = child.max_y
            new_child.max_z = child.max_z
            new_root.child_nodes[ChildXnYnZn] = new_child

        new_root._count = total_count
        new_root.update_not_empty_bounds()
        self._root = new_root

    def _contract(self):
        while (self.size > 8 and
               self._root.is_child_contractible(ChildXnYnZn, ChildXpYpZp) and
               self._root.is_child_contractible(ChildXpYpZn, ChildXnYnZp) and
               self._root.is_child_contractible(ChildXnYpZp, ChildXpYnZn) and
               self._root.is_child_contractible(ChildXpYpZp, ChildXnYnZn)):
            self.size >>= 1
            self.size_half >>= 1
            new_root = OctreeBranchNode(self, -self.size_half, -self.size_half, -self.size_half, self.size,
                                        self.default_value)
            if self._root.child_nodes[ChildXpYpZp] is not None:
                # noinspection PyUnresolvedReferences
                new_root.child_nodes[ChildXpYpZp] = self._root.child_nodes[ChildXpYpZp].child_nodes[ChildXnYnZn]
            if self._root.child_nodes[ChildXpYpZn] is not None:
                # noinspection PyUnresolvedReferences
                new_root.child_nodes[ChildXpYpZn] = self._root.child_nodes[ChildXpYpZn].child_nodes[ChildXnYnZp]
            if self._root.child_nodes[ChildXnYpZp] is not None:
                # noinspection PyUnresolvedReferences
                new_root.child_nodes[ChildXnYpZp] = self._root.child_nodes[ChildXnYpZp].child_nodes[ChildXpYnZn]
            if self._root.child_nodes[ChildXnYnZn] is not None:
                # noinspection PyUnresolvedReferences
                new_root.child_nodes[ChildXnYnZn] = self._root.child_nodes[ChildXnYnZn].child_nodes[ChildXpYpZp]
            new_root.update_not_empty_bounds()
            self._root = new_root

    def remove(self, x: int, y: int, z: int):
        if self.is_inside(x, y, z):
            self._root.remove(x, y, z)
            self._contract()


class OctreeNode:
    def __init__(self, parent: Octree, start_position_x: int, start_position_y: int, start_position_z: int, size: int,
                 default_value: any):
        self.parent = parent
        self.start_position_x = start_position_x
        self.start_position_y = start_position_y
        self.start_position_z = start_position_z
        self.size = size
        self.size_half = size >> 1
        self.default_value = default_value

        self.bounds_set = False
        self.max_x = -1
        self.max_y = -1
        self.max_z = -1
        self.min_x = -1
        self.min_y = -1
        self.min_z = -1

    @property
    def not_empty_bounds(self) -> Tuple[int, int, int, int, int, int]:
        return (0, 0, 0, 1, 1, 1) if self.is_empty else \
            (self.min_x, self.min_y, self.min_z, self.max_x, self.max_y, self.max_z)

    @property
    def is_leaf(self) -> bool:
        return False

    @property
    def is_full(self) -> bool:
        return False

    @property
    def count(self) -> int:
        return -1

    @property
    def is_empty(self) -> bool:
        return not self.bounds_set

    @property
    def is_not_empty(self) -> bool:
        return self.bounds_set

    def get_value(self, x: int, y: int, z: int) -> any:
        pass

    def contains(self, x: int, y: int, z: int) -> bool:
        pass

    def add(self, x: int, y: int, z: int, value: any) -> bool:
        pass

    def remove(self, x: int, y: int, z: int) -> bool:
        pass


class OctreeBranchNode(OctreeNode):
    def __init__(self, parent: Octree, start_position_x: int, start_position_y: int, start_position_z: int, size: int,
                 default_value: any):
        OctreeNode.__init__(self, parent, start_position_x, start_position_y, start_position_z, size, default_value)
        self._max_count = ((SideLength * 2) ** (math.log2(size) - 2)) * GridLength
        self._center_x = start_position_x + self.size_half
        self._center_y = start_position_y + self.size_half
        self._center_z = start_position_z + self.size_half
        self._count = 0
        self.child_nodes: List[OctreeNode | None] = [None] * 8

    @property
    def is_leaf(self) -> bool:
        return False

    @property
    def is_full(self) -> bool:
        return self._count == self._max_count

    @property
    def count(self) -> int:
        return self._count

    def _get_index(self, x: int, y: int, z: int) -> int:
        return (x >= self._center_x) + (y >= self._center_y) * 2 + (z >= self._center_z) * 4

    def get_value(self, x: int, y: int, z: int) -> any:
        child = self.child_nodes[self._get_index(x, y, z)]
        return child.get_value(x, y, z) if child is not None else self.default_value

    def contains(self, x: int, y: int, z: int) -> bool:
        child = self.child_nodes[self._get_index(x, y, z)]
        return child is not None and child.contains(x, y, z)

    def add(self, x: int, y: int, z: int, value: any) -> bool:
        node_index = self._get_index(x, y, z)
        node = self.child_nodes[node_index]
        if node is None:
            pos_x = self.start_position_x if x < self._center_x else self._center_x
            pos_y = self.start_position_y if y < self._center_y else self._center_y
            pos_z = self.start_position_z if z < self._center_z else self._center_z
            node = (
                OctreeBranchNode(self.parent, pos_x, pos_y, pos_z, self.size >> 1, self.default_value)
                if self.size > SideLength else
                OctreeLeafNode(self.parent, pos_x, pos_y, pos_z, self.default_value)
            )
            self.child_nodes[node_index] = node

        if not node.add(x, y, z, value):
            return False
        self._count += 1
        if not self.bounds_set:
            self.min_x = x
            self.min_y = y
            self.min_z = z
            self.max_x = x + 1
            self.max_y = y + 1
            self.max_z = z + 1
        else:
            if x < self.min_x:
                self.min_x = x
            if y < self.min_y:
                self.min_y = y
            if z < self.min_z:
                self.min_z = z
            if x >= self.max_x:
                self.max_x = x + 1
            if y >= self.max_y:
                self.max_y = y + 1
            if z >= self.max_z:
                self.max_z = z + 1

        self.bounds_set = True
        return True

    def remove(self, x: int, y: int, z: int) -> bool:
        node_index = self._get_index(x, y, z)
        node = self.child_nodes[node_index]
        success = False
        if node is not None:
            success = node.remove(x, y, z)
            if node.is_empty:
                if node.is_leaf:
                    # noinspection PyTypeChecker
                    self.parent.leafs.remove(node)
                self.child_nodes[node_index] = None
        if success:
            self._count -= 1
            self.update_not_empty_bounds()
        return success

    def update_not_empty_bounds(self):
        if self._count == self._max_count:
            self.min_x = self.start_position_x
            self.min_y = self.start_position_y
            self.min_z = self.start_position_z
            self.max_x = self.start_position_x + self.size - 1
            self.max_y = self.start_position_y + self.size - 1
            self.max_z = self.start_position_z + self.size - 1
            self.bounds_set = True
        else:
            self.min_x = -1
            self.max_x = -1
            self.min_y = -1
            self.max_y = -1
            self.min_z = -1
            self.max_z = -1
            self.bounds_set = False
            for i in range(0, len(self.child_nodes)):
                child = self.child_nodes[i]
                if child is None or child.is_empty:
                    continue
                if not self.bounds_set:
                    self.min_x = child.min_x
                    self.min_y = child.min_y
                    self.min_z = child.min_z
                    self.max_x = child.max_x
                    self.max_y = child.max_y
                    self.max_z = child.max_z
                else:
                    if child.min_x < self.min_x:
                        self.min_x = child.min_x
                    if child.min_y < self.min_y:
                        self.min_y = child.min_y
                    if child.min_z < self.min_z:
                        self.min_z = child.min_z
                    if child.max_x > self.max_x:
                        self.max_x = child.max_x
                    if child.max_y > self.max_y:
                        self.max_y = child.max_y
                    if child.max_z > self.max_z:
                        self.max_z = child.max_z
                self.bounds_set = True

    def is_child_contractible(self, child_index: int, remaining_child_child_index: int) -> bool:
        child = self.child_nodes[child_index]
        if child is not None:
            if isinstance(child, OctreeBranchNode):
                for i in range(0, len(child.child_nodes)):
                    if i != remaining_child_child_index and child.child_nodes[i] is not None:
                        return False
            else:
                return False
        return True


class OctreeLeafNode(OctreeNode):
    def __init__(self, parent: Octree, start_position_x: int, start_position_y: int, start_position_z: int,
                 default_value: any):
        OctreeNode.__init__(self, parent, start_position_x, start_position_y, start_position_z, SideLength,
                            default_value)
        parent.leafs.append(self)
        self._index_offset = start_position_x + start_position_y * SideLength + start_position_z * SideLengthTwice
        self._count = 0
        self._x_axis_counts: List[int] = [0] * SideLength
        self._y_axis_counts: List[int] = [0] * SideLength
        self._z_axis_counts: List[int] = [0] * SideLength
        self.grid: List[any] = [None] * GridLength
        self.grid_taken: List[bool] = [False] * GridLength

    def _get_index(self, x: int, y: int, z: int) -> int:
        return x + y * SideLength + z * SideLengthTwice - self._index_offset

    @staticmethod
    def _get_index_local(x: int, y: int, z: int) -> int:
        return x + y * SideLength + z * SideLengthTwice

    @property
    def is_leaf(self) -> bool:
        return True

    @property
    def is_full(self) -> bool:
        return self._count == GridLength

    @property
    def count(self) -> int:
        return self._count

    def get_value(self, x: int, y: int, z: int) -> any:
        index = self._get_index(x, y, z)
        return self.grid[index] if self.grid_taken[index] else self.default_value

    def contains(self, x: int, y: int, z: int) -> bool:
        return self.grid_taken[self._get_index(x, y, z)]

    def add(self, x: int, y: int, z: int, value: any) -> bool:
        if not self.bounds_set:
            self.min_x = x
            self.min_y = y
            self.min_z = z
            self.max_x = x + 1
            self.max_y = y + 1
            self.max_z = z + 1
        else:
            if x < self.min_x:
                self.min_x = x
            if y < self.min_y:
                self.min_y = y
            if z < self.min_z:
                self.min_z = z
            if x >= self.max_x:
                self.max_x = x + 1
            if y >= self.max_y:
                self.max_y = y + 1
            if z >= self.max_z:
                self.max_z = z + 1

        self.bounds_set = True
        x -= self.start_position_x
        y -= self.start_position_y
        z -= self.start_position_z
        index = self._get_index_local(x, y, z)
        if not self.grid_taken[index]:
            self._count += 1
            self.grid_taken[index] = True
            self.grid[index] = value
            self._x_axis_counts[x] += 1
            self._y_axis_counts[y] += 1
            self._z_axis_counts[z] += 1
            return True

        self.grid[index] = value
        return False

    def remove(self, x: int, y: int, z: int) -> bool:
        x -= self.start_position_x
        y -= self.start_position_y
        z -= self.start_position_z
        index = self._get_index_local(x, y, z)
        if not self.grid_taken[index]:
            return False
        self._count -= 1
        self._x_axis_counts[x] -= 1
        self._y_axis_counts[y] -= 1
        self._z_axis_counts[z] -= 1
        self.grid_taken[index] = False
        self.grid[index] = self.default_value
        self._update_not_empty_bounds()
        return True

    def _update_not_empty_bounds(self):
        self.bounds_set = False
        # X axis
        for i in range(0, SideLength):
            if self._x_axis_counts[i] > 0:
                self.min_x = i + self.start_position_x
                self.bounds_set = True
                break

        for i in range(SideLength - 1, -1, -1):
            if self._x_axis_counts[i] > 0:
                self.max_x = i + self.start_position_x + 1
                self.bounds_set = True
                break

        # Y axis
        for i in range(0, SideLength):
            if self._y_axis_counts[i] > 0:
                self.min_y = i + self.start_position_y
                self.bounds_set = True
                break

        for i in range(SideLength - 1, -1, -1):
            if self._y_axis_counts[i] > 0:
                self.max_y = i + self.start_position_y + 1
                self.bounds_set = True
                break

        # Z axis
        for i in range(0, SideLength):
            if self._z_axis_counts[i] > 0:
                self.min_z = i + self.start_position_z
                self.bounds_set = True
                break

        for i in range(SideLength - 1, -1, -1):
            if self._z_axis_counts[i] > 0:
                self.max_z = i + self.start_position_z + 1
                self.bounds_set = True
                break


class OctreeIterator:
    def __init__(self, octree: Octree):
        self._leafs = octree.leafs.copy()
        self._has_current = False
        self._next_inside_leaf_index = 0
        self._next_leaf_index = 0
        self._current: Tuple[int, int, int, any] = (0, 0, 0, None)

    @property
    def current(self):
        return self._current if self._has_current else None

    def move_next(self) -> bool:
        self._has_current = False
        while self._next_leaf_index < len(self._leafs):
            current_leaf = self._leafs[self._next_leaf_index]
            while self._next_inside_leaf_index < GridLength:
                if current_leaf.grid_taken[self._next_inside_leaf_index]:
                    self._current = (
                        LeafIndexXMap[self._next_inside_leaf_index] + current_leaf.start_position_x,
                        LeafIndexYMap[self._next_inside_leaf_index] + current_leaf.start_position_y,
                        LeafIndexZMap[self._next_inside_leaf_index] + current_leaf.start_position_z,
                        current_leaf.grid[self._next_inside_leaf_index]
                    )
                    self._has_current = True
                    self._next_inside_leaf_index += 1
                    break
                self._next_inside_leaf_index += 1
            if self._has_current:
                break
            self._next_leaf_index += 1
            self._next_inside_leaf_index = 0
        return self._has_current

    def reset(self):
        self._has_current = False
        self._next_inside_leaf_index = 0
        self._next_leaf_index = 0


class VoxelGrid:
    width: int
    depth: int
    height: int

    def __init__(self, width: int, depth: int, height: int):
        self.width = width
        self.depth = depth
        self.height = height

    @staticmethod
    def reduce_voxel_grid_to_hull(voxels: Octree, outside: Octree):
        if DEBUG_OUTPUT:
            print('[DEBUG] reduce_voxel_grid_to_hull')
        timer_start = time.time()
        iterator = OctreeIterator(voxels)
        while iterator.move_next():
            (x, y, z, _) = iterator.current
            # Left
            if outside.get_value(x - 1, y, z):
                continue
            # Right
            if outside.get_value(x + 1, y, z):
                continue
            # Down
            if outside.get_value(x, y - 1, z):
                continue
            # Up
            if outside.get_value(x, y + 1, z):
                continue
            # Back
            if outside.get_value(x, y, z - 1):
                continue
            # Front
            if outside.get_value(x, y, z + 1):
                continue
            # If not connected to the outside space, delete the voxel(inside hull)
            voxels.remove(x, y, z)
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))

    @staticmethod
    def create_outside_grid(voxels: Octree) -> Octree:
        if DEBUG_OUTPUT:
            print('[DEBUG] create_outside_grid')
        timer_start = time.time()
        outside = Octree(default_value=True)
        if voxels.is_not_empty:
            distinct_areas = VoxelGrid.find_distinct_areas(voxels)
            distinct_areas_iterator = OctreeIterator(distinct_areas)
            while distinct_areas_iterator.move_next():
                (x, y, z, _) = distinct_areas_iterator.current
                if distinct_areas.get_value(x, y, z) != 0:
                    outside.add(x, y, z, False)
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))
        return outside

    @staticmethod
    def find_distinct_areas(voxels: Octree) -> Octree:
        """
        connected-component labeling (CCL) with the Hoshen–Kopelman algorithm
        modified to label all voxels -1 as we're only interested in non-voxel labels
        """
        if DEBUG_OUTPUT:
            print('[DEBUG] find_distinct_areas')
        timer_start = time.time()
        labels = Octree(voxels.size, default_value=0)
        label_equivalence: Dict[int, Set[int]] = {0: set()}
        next_label = 1
        leafs = sorted([leaf for leaf in voxels.leafs if not leaf.is_empty],
                       key=lambda l: (l.start_position_z, l.start_position_y, l.start_position_x))
        for leaf in leafs:
            bounds = leaf.not_empty_bounds
            for z in range(bounds[2] - 1, bounds[5] + 1):
                for y in range(bounds[1] - 1, bounds[4] + 1):
                    for x in range(bounds[0] - 1, bounds[3] + 1):
                        if voxels.get_value(x, y, z) is None:
                            possible_labels: Set[int] = set()
                            if voxels.get_value(x - 1, y, z) is None:
                                possible_labels.add(labels.get_value(x - 1, y, z))
                            if voxels.get_value(x, y - 1, z) is None:
                                possible_labels.add(labels.get_value(x, y - 1, z))
                            if voxels.get_value(x, y, z - 1) is None:
                                possible_labels.add(labels.get_value(x, y, z - 1))
                            if len(possible_labels) == 0:
                                labels.add(x, y, z, next_label)
                                label_equivalence[next_label] = set()
                                next_label += 1
                            elif len(possible_labels) == 1:
                                labels.add(x, y, z, next(iter(possible_labels)))
                            elif len(possible_labels) == 2:
                                min_label = min(possible_labels)
                                if min_label > 0:
                                    labels.add(x, y, z, min_label)
                                tmp = list(possible_labels)
                                if tmp[0] != tmp[1]:
                                    label_equivalence[tmp[0]].add(tmp[1])
                                    label_equivalence[tmp[1]].add(tmp[0])
                            else:
                                min_label = min(possible_labels)
                                if min_label > 0:
                                    labels.add(x, y, z, min_label)
                                tmp = list(possible_labels)
                                if tmp[0] != tmp[1]:
                                    label_equivalence[tmp[0]].add(tmp[1])
                                    label_equivalence[tmp[1]].add(tmp[0])
                                if tmp[0] != tmp[2]:
                                    label_equivalence[tmp[0]].add(tmp[2])
                                    label_equivalence[tmp[2]].add(tmp[0])
                                if tmp[1] != tmp[2]:
                                    label_equivalence[tmp[1]].add(tmp[2])
                                    label_equivalence[tmp[2]].add(tmp[1])
                        else:
                            labels.add(x, y, z, -1)
        # Collapse all overlapping sets until nothing changes anymore
        count = 0
        while count != len(label_equivalence):
            count = len(label_equivalence)
            for label in range(0, next_label):
                if label in label_equivalence:
                    connections = label_equivalence[label]
                    if len(connections) > 0:
                        min_label = min(connections)
                        if min_label < label:
                            del label_equivalence[label]
                            for connected_label in connections:
                                if connected_label in label_equivalence:
                                    next_connections = label_equivalence[connected_label]
                                    for other_label in connections:
                                        if other_label != connected_label:
                                            next_connections.add(other_label)
        # Change all labels to the minimum of the equivalence set they belong to
        label_map = {}
        for key in label_equivalence:
            for connection in label_equivalence[key]:
                label_map[connection] = key
        iterator = OctreeIterator(labels)
        while iterator.move_next():
            if iterator.current[3] in label_map:
                value = label_map[iterator.current[3]]
                if value > 0:
                    labels.add(iterator.current[0], iterator.current[1], iterator.current[2], value)
                else:
                    labels.remove(iterator.current[0], iterator.current[1], iterator.current[2])
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))
        return labels


class Quad:
    def __init__(self,
                 p1: Tuple[int, int, int] = (0, 0, 0),
                 p2: Tuple[int, int, int] = (0, 0, 0),
                 p3: Tuple[int, int, int] = (0, 0, 0),
                 p4: Tuple[int, int, int] = (0, 0, 0),
                 normal: Tuple[int, int, int] = (0, 0, 0),
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
    def generate_mesh(voxels: Octree) -> List[Quad]:
        quads: List[Quad] = []
        iterator = OctreeIterator(voxels)
        while iterator.move_next():
            (x, y, z, color_index) = iterator.current
            # Left
            quads.append(Quad((x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1), (-1, 0, 0), color_index))
            # Right
            quads.append(Quad((x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z), (1, 0, 0),
                              color_index))
            # Back
            quads.append(Quad((x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z), (0, -1, 0), color_index))
            # Front
            quads.append(Quad((x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1), (0, 1, 0),
                              color_index))
            # Bottom
            quads.append(Quad((x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z), (0, 0, -1), color_index))
            # Top
            quads.append(Quad((x, y, z + 1), (x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y, z + 1), (0, 0, 1),
                              color_index))
        return quads


class SimpleQuadsMeshing:
    @staticmethod
    def generate_mesh(voxels: Octree, outside: Octree) -> List[Quad]:
        if DEBUG_OUTPUT:
            print('[DEBUG] SimpleQuadsMeshing generate_mesh')
        timer_start = time.time()
        quads: List[Quad] = []
        iterator = OctreeIterator(voxels)
        while iterator.move_next():
            (x, y, z, color_index) = iterator.current
            # Left
            if outside.get_value(x - 1, y, z):
                quads.append(Quad((x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1), (x, y, z), (-1, 0, 0), color_index))
            # Right
            if outside.get_value(x + 1, y, z):
                quads.append(Quad((x + 1, y, z), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x + 1, y + 1, z), (1, 0, 0),
                                  color_index))
            # Back
            if outside.get_value(x, y - 1, z):
                quads.append(Quad((x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z), (0, -1, 0), color_index))
            # Front
            if outside.get_value(x, y + 1, z):
                quads.append(Quad((x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1), (x, y + 1, z), (0, 1, 0),
                                  color_index))
            # Bottom
            if outside.get_value(x, y, z - 1):
                quads.append(Quad((x, y + 1, z), (x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (0, 0, -1), color_index))
            # Top
            if outside.get_value(x, y, z + 1):
                quads.append(Quad((x, y, z + 1), (x, y + 1, z + 1), (x + 1, y + 1, z + 1), (x + 1, y, z + 1), (0, 0, 1),
                                  color_index))
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))
        return quads


class GreedyMeshing:
    @staticmethod
    def generate_mesh(voxels: Octree, outside: Octree, ignore_color: bool = False) -> List[Quad]:
        if DEBUG_OUTPUT:
            print('[DEBUG] GreedyMeshing generate_mesh')
        timer_start = time.time()
        quads: List[Quad] = []
        bounds = voxels.not_empty_bounds
        GreedyMeshing.mesh_axis(bounds, voxels, outside, ignore_color, 0, quads)
        GreedyMeshing.mesh_axis(bounds, voxels, outside, ignore_color, 1, quads)
        GreedyMeshing.mesh_axis(bounds, voxels, outside, ignore_color, 2, quads)
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))
        return quads

    @staticmethod
    def mesh_axis(bounds: Tuple[int, int, int, int, int, int], voxels: Octree, outside: Octree, ignore_color: bool,
                  axis_index: int, quads: List[Quad]):
        axis1_index = {0: 1, 1: 2, 2: 0}[axis_index]
        axis2_index = {0: 2, 1: 0, 2: 1}[axis_index]
        axis_sizes = {0: bounds[3] - bounds[0], 1: bounds[4] - bounds[1], 2: bounds[5] - bounds[2]}
        axis_size = axis_sizes[axis_index]
        axis1_size = axis_sizes[axis1_index]
        axis2_size = axis_sizes[axis2_index]

        get_vector = GreedyMeshing.get_vector_func(bounds, axis_index, axis1_index, axis2_index)
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
        for a in range(0, axis_size):
            has_offset = [a > 0, a < axis_size - 1]
            visited = [
                [False] * axis1_size * axis2_size,
                [False] * axis1_size * axis2_size
            ]
            for b in range(0, axis1_size):
                for c in range(0, axis2_size):
                    visited_start_index = b * axis2_size + c
                    start_voxel = voxels.get_value(*get_vector(a, b, c))
                    if start_voxel is None:
                        visited[0][visited_start_index] = True
                        visited[1][visited_start_index] = True
                    else:
                        # Handle both directions separately as the visited pattern
                        # might be different, and we gather only the outer shell
                        for visited_index in range(0, 2):
                            if not visited[visited_index][visited_start_index]:
                                a_back = a + normal_offsets[visited_index]
                                if has_offset[visited_index] and not outside.get_value(*get_vector(a_back, b, c)):
                                    visited[visited_index][visited_start_index] = True
                                    continue
                                # Move first axis until end or voxel mismatch
                                end_index_axis1 = b
                                found_end_axis1 = False
                                for i in range(b + 1, axis1_size):
                                    iter_visited_index = i * axis2_size + c
                                    iter_voxel = voxels.get_value(*get_vector(a, i, c))
                                    if (
                                            # No voxel found...
                                            iter_voxel is None or
                                            # ...or already visited...
                                            visited[visited_index][iter_visited_index] or
                                            # ...or different color...
                                            (not ignore_color and start_voxel != iter_voxel) or
                                            # ... or not connected to the outside space
                                            (has_offset[visited_index] and
                                             not outside.get_value(*get_vector(a_back, i, c)))
                                    ):
                                        end_index_axis1 = i - 1
                                        found_end_axis1 = True
                                        break
                                if not found_end_axis1:
                                    end_index_axis1 = axis1_size - 1
                                # Move second axis until end or voxel row mismatch
                                end_index_axis2 = c
                                found_end_axis2 = False
                                for j in range(c + 1, axis2_size):
                                    any_mismatch_in_row = False
                                    for i in range(b, end_index_axis1 + 1):
                                        iter_visited_index = i * axis2_size + j
                                        iter_voxel = voxels.get_value(*get_vector(a, i, j))
                                        if (
                                                # No voxel found...
                                                iter_voxel is None or
                                                # ...or already visited...
                                                visited[visited_index][iter_visited_index] or
                                                # ...or different color...
                                                (not ignore_color and start_voxel != iter_voxel) or
                                                # ... or not connected to the outside space
                                                (has_offset[visited_index] and
                                                 not outside.get_value(*get_vector(a_back, i, j)))
                                        ):
                                            any_mismatch_in_row = True
                                            break
                                    if any_mismatch_in_row:
                                        end_index_axis2 = j - 1
                                        found_end_axis2 = True
                                        break
                                if not found_end_axis2:
                                    end_index_axis2 = axis2_size - 1
                                # Mark area as visited
                                for i in range(b, end_index_axis1 + 1):
                                    for j in range(c, end_index_axis2 + 1):
                                        visited[visited_index][i * axis2_size + j] = True
                                # Store quad
                                a_visited = a if visited_index == 0 else a + 1
                                quad = Quad()
                                quad.normal = normals[visited_index]
                                quad.color = start_voxel
                                quad.p1 = get_vector(a_visited, b, c)
                                quad.p2 = (get_vector(a_visited, end_index_axis1 + 1, c) if visited_index == 0 else
                                           get_vector(a_visited, b, end_index_axis2 + 1))
                                quad.p3 = get_vector(a_visited, end_index_axis1 + 1, end_index_axis2 + 1)
                                quad.p4 = (get_vector(a_visited, b, end_index_axis2 + 1) if visited_index == 0 else
                                           get_vector(a_visited, end_index_axis1 + 1, c))
                                quads.append(quad)

    @staticmethod
    def get_vector_func(bounds: Tuple[int, int, int, int, int, int], axis_index: int, axis1_index: int,
                        axis2_index: int):
        if axis_index == 0 and axis1_index == 1 and axis2_index == 2:
            return lambda x, y, z: (bounds[0] + x, bounds[1] + y, bounds[2] + z)
        if axis_index == 1 and axis1_index == 0 and axis2_index == 2:
            return lambda y, x, z: (bounds[0] + x, bounds[1] + y, bounds[2] + z)
        if axis_index == 1 and axis1_index == 2 and axis2_index == 0:
            return lambda y, z, x: (bounds[0] + x, bounds[1] + y, bounds[2] + z)
        if axis_index == 0 and axis1_index == 2 and axis2_index == 1:
            return lambda x, z, y: (bounds[0] + x, bounds[1] + y, bounds[2] + z)
        if axis_index == 2 and axis1_index == 0 and axis2_index == 1:
            return lambda z, x, y: (bounds[0] + x, bounds[1] + y, bounds[2] + z)
        # 2, 1, 0
        return lambda z, y, x: (bounds[0] + x, bounds[1] + y, bounds[2] + z)


class VoxMaterial:
    TYPE_DIFFUSE = ""
    TYPE_METAL = "_metal"
    TYPE_GLASS = "_glass"
    TYPE_BLEND = "_blend"
    TYPE_MEDIA = "_media"  # Cloud in MV UI
    TYPE_EMIT = "_emit"
    MEDIA_TYPE_ABSORB = ""
    MEDIA_TYPE_SCATTER = "_scatter"
    MEDIA_TYPE_EMIT = "_emit"  # Emissive
    MEDIA_TYPE_SSS = "_sss"  # Subsurface Scattering

    def __init__(self, data: Dict[str, str]):
        self.data = data
        self.type = VoxMaterial.TYPE_DIFFUSE
        if "_type" in data and data["_type"] in [
            VoxMaterial.TYPE_METAL, VoxMaterial.TYPE_GLASS, VoxMaterial.TYPE_BLEND, VoxMaterial.TYPE_MEDIA,
            VoxMaterial.TYPE_EMIT
        ]:
            self.type = data["_type"]
        # _rough --> Roughness [0-1] float, default: 0.1 | 0.1 --> UI 10
        # Multiply by 0.5 as the max roughness of MV roughly matches a value of 0.5
        self.roughness = 1.0 if self.type == VoxMaterial.TYPE_DIFFUSE else \
            (float(data["_rough"]) if "_rough" in data else 0.1) * 0.5
        has_metal = self.type in [VoxMaterial.TYPE_METAL, VoxMaterial.TYPE_BLEND]
        # _metal --> Metallic [0-1] float, default: 0.0
        self.metallic = float(data["_metal"]) if "_metal" in data and has_metal else 0
        # _sp --> Specular [1-2] float, default 1.0
        self.specular = float(data["_sp"]) if "_sp" in data and has_metal else 1
        # data["_ior"] = (data["_ri"] - 1), MV shows _ri in UI and Blender uses _ri value range as well for IOR
        # default 0.3 / 1.3
        self.ior = float(data["_ri"]) if "_ri" in data else 1.3
        # _flux --> Power {0, 1, 2, 3, 4}, default 0
        # We calculate +1 to the power as we handle it just as a multiplier
        self.flux = float(data["_flux"]) + 1 if "_flux" in data and self.type == "_emit" else 0
        has_emission = self.type == VoxMaterial.TYPE_EMIT
        # _emit --> Emission [0-1] float, default: 0.0
        self.emission = float(data["_emit"]) * self.flux if "_emit" in data and has_emission else 0
        # _ldr --> LDR [0-1] float, default: 0.0 | 0.8 --> UI 80
        self.ldr = float(data["_ldr"]) if "_ldr" in data and has_emission else 0
        has_transmission = self.type in [VoxMaterial.TYPE_GLASS, VoxMaterial.TYPE_BLEND]
        # _alpha == _trans --> Transparency [0-1] float, default: 0.0 | 0.5 --> UI 50
        self.transmission = float(data["_trans"]) if "_trans" in data and has_transmission else 0
        has_media = self.type in [VoxMaterial.TYPE_GLASS, VoxMaterial.TYPE_BLEND, VoxMaterial.TYPE_MEDIA]
        # _media_type [
        #   None --> Absorb, (Volume Absorption node)
        #   "_scatter" --> Scatter, (Volume Scatter node)
        #   "_emit" --> Emissive, (Emission node)
        #   "_sss" --> Subsurface Scattering
        # ]
        # _media [None --> Absorb, 1 --> Scatter, 2 --> Emissive, 3 --> Subsurface Scattering]
        self.media_type = VoxMaterial.MEDIA_TYPE_ABSORB
        if has_media and "_media_type" in data and data["_media_type"] in [
            VoxMaterial.MEDIA_TYPE_SCATTER, VoxMaterial.MEDIA_TYPE_EMIT, VoxMaterial.MEDIA_TYPE_SSS
        ]:
            self.media_type = data["_media_type"]
        # _d --> Density [0-1], default: 0.05 | 0.025 --> UI 25 | 0.050 --> UI 50
        self.density = float(data["_d"]) if "_d" in data and has_media else 0
        # _g --> Phase [-0.9-0.9] float, default: 0.0
        self.phase = float(data["_g"]) if "_g" in data and has_media else 0

    @staticmethod
    def get_default():
        return VoxMaterial({"_rough": "0.1", "_ior": "0.3", "_ri": "1.3", "_d": "0.05"})

    def __str__(self):
        return ("VoxMaterial {type: %s, roughness: %s, metallic: %s, specular: %s, ior: %s, emission: %s, " +
                "flux: %s, ldr: %s, transmission: %s, media_type: %s, density: %s, phase: %s}") % (
            self.type, self.roughness, self.metallic, self.specular, self.ior, self.emission, self.flux,
            self.ldr,
            self.transmission, self.media_type, self.density, self.phase)


class VoxMesh:
    def __init__(self, model_id: int, width: int, depth: int, height: int):
        self.model_id = model_id
        self.num_voxels = 0
        self.grid: VoxelGrid = VoxelGrid(width, depth, height)
        self.voxels = Octree()
        self.used_color_indices: Set[int] = set()

    def get_voxel_color_index(self, x: int, y: int, z: int) -> int or None:
        return self.voxels.get_value(x, y, z)


class VoxNode:
    def __init__(self, type: str):
        self.type = type
        self.node_id = -1
        self.layer_id = -1
        self.node_attributes: Dict[str, str] = {}
        self.frame_attributes: Dict[int, Dict[str, str]] = {}
        self.meshes: Dict[int, Dict[str, str]] = {}
        self.child_ids = []

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

    # noinspection PyUnresolvedReferences
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
            first_row_sign = (rotation_byte >> 4) & 1
            second_row_sign = (rotation_byte >> 5) & 1
            third_row_sign = (rotation_byte >> 6) & 1
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
        self.materials: Dict[int, VoxMaterial] = {i: VoxMaterial.get_default() for i in range(0, 256)}
        self.layers: Dict[int, Dict[str, str]] = {}
        self.cameras: Dict[int, Dict[str, str]] = {}
        self.rendering_attributes: List[Dict[str, str]] = []
        self.meshes: List[VoxMesh] = []
        self.nodes: Dict[int, VoxNode] = {}

    def get_all_used_color_indices(self) -> Set[int]:
        used_color_indices: Set[int] = set()
        for mesh in self.meshes:
            used_color_indices.update(mesh.used_color_indices)
        return used_color_indices

    def get_used_color_indices_material_map(self) -> Dict[int, int]:
        result: Dict[int, int] = {}
        used_color_indices = sorted(self.get_all_used_color_indices())
        material_slot_index = 0
        for color_index in used_color_indices:
            result[color_index] = material_slot_index
            material_slot_index += 1
        return result

    def get_color(self, color_index: int) -> Tuple[float, float, float, float]:
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

    import_hierarchy: BoolProperty(
        name="Import Hierarchy",
        description="Import hierarchy from MagicaVoxel as collections",
        default=False,
    )

    voxel_size: FloatProperty(
        name="Voxel Size (m)",
        description="Size of the imported voxels in meters",
        min=0.0001,
        soft_min=0.0001,
        default=0.1,
    )

    max_texture_size: IntProperty(
        name="Max Texture Size (px)",
        description="Maximum size (width and height) of generated textures",
        min=256,
        soft_min=256,
        max=8192,
        soft_max=8192,
        default=4096,
    )

    import_material_props: BoolProperty(
        name="Import Material Properties",
        description="Import additional material properties such as metal and emission",
        default=False,
    )

    material_mode: EnumProperty(
        name="Material Mode",
        items=[
            ("NONE", "Ignore", "Neither colors nor materials are imported."),
            ("VERTEX_COLOR", "Vertex Color", "The color palette will be imported and assigned to face " +
             "vertex colors. A simple material is added using the vertex colors as 'Base Color'."),
            ("MAT_PER_COLOR", "Material Per Color", "A material is added per color in the color palette and assigned " +
             "to the faces material index."),
            ("MAT_AS_TEX", "Materials As Texture", "The color palette is created as a 256x1 texture. A simple " +
             "material is added using this texture."),
            ("TEXTURED_MODEL", "Textured Models (UV unwrap)", "Each model is assigned a material and texture with " +
             "UV unwrap. Automatically locks Greedy meshing mode."),
        ],
        description="",
        default="VERTEX_COLOR"
    )

    meshing_type: EnumProperty(
        name="Meshing Type",
        items=[
            ("CUBES_AS_OBJ", "Voxel as Models (Slow)", "Each Voxel as an individual cube object"),
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

    join_models: BoolProperty(
        name="Join Models",
        description="",
        default=False,
    )

    def create_vertex_color_node(self, nodes, layer_name: str):
        try:
            n = nodes.new("ShaderNodeVertexColor")
            n.layer_name = layer_name
            return n
        except:
            n = nodes.new("ShaderNodeAttribute")
            n.attribute_name = layer_name
            return n

    def create_materials_vertex_colors(self, collection_name: str, _: VoxModel):
        vertex_color_mat = bpy.data.materials.new(name=collection_name + " Material")
        vertex_color_mat.use_nodes = True
        nodes = vertex_color_mat.node_tree.nodes
        links = vertex_color_mat.node_tree.links
        bdsf_node = nodes["Principled BSDF"]
        vertex_color_node = self.create_vertex_color_node(nodes, "Col")
        if self.import_material_props:
            vertex_color_material_node = self.create_vertex_color_node(nodes, "Mat")
            separate_rgb_node = nodes.new("ShaderNodeSeparateRGB")
            links.new(vertex_color_material_node.outputs["Color"], separate_rgb_node.inputs["Image"])
            links.new(separate_rgb_node.outputs["R"], bdsf_node.inputs["Roughness"])
            links.new(separate_rgb_node.outputs["G"], bdsf_node.inputs["Metallic"])
            links.new(separate_rgb_node.outputs["B"], bdsf_node.inputs["IOR"])
            bdsf_node.inputs["Emission Strength"].default_value = 0
            emission_color_input = (bdsf_node.inputs["Emission Color"] if "Emission Color" in bdsf_node.inputs else
                                    bdsf_node.inputs["Emission"])
            links.new(vertex_color_node.outputs["Color"], emission_color_input)
        links.new(vertex_color_node.outputs["Color"], bdsf_node.inputs["Base Color"])
        return [vertex_color_mat]

    def create_materials_per_color(self, collection_name: str, model: VoxModel,
                                   color_index_material_map: Dict[int, int]):
        materials = []
        for color_index in range(len(model.color_palette)):
            if color_index in color_index_material_map:
                material = model.materials[color_index]
                mat = bpy.data.materials.new(name="%s Material %s" % (collection_name, color_index))
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                bdsf_node = nodes["Principled BSDF"]
                mat_output_node = nodes["Material Output"]
                color = model.get_color(color_index)
                bdsf_node.inputs["Base Color"].default_value = color
                if self.import_material_props:
                    bdsf_node.inputs["Roughness"].default_value = material.roughness
                    bdsf_node.inputs["Metallic"].default_value = material.metallic
                    bdsf_node.inputs["IOR"].default_value = material.ior
                    bdsf_node.inputs["Emission Strength"].default_value = 0
                    if "Emission Color" in bdsf_node.inputs:
                        bdsf_node.inputs["Emission Color"].default_value = color
                    else:
                        bdsf_node.inputs["Emission"].default_value = color
                    if material.type == VoxMaterial.TYPE_EMIT:
                        bdsf_node.inputs["Emission Strength"].default_value = material.emission
                    elif material.type in [VoxMaterial.TYPE_MEDIA, VoxMaterial.TYPE_GLASS, VoxMaterial.TYPE_BLEND]:
                        bdsf_node.inputs["Base Color"].default_value = (1, 1, 1, 1)
                        if "Transmission Weight" in bdsf_node.inputs:
                            bdsf_node.inputs["Transmission Weight"].default_value = 1.0
                        else:
                            bdsf_node.inputs["Transmission"].default_value = 1.0
                        if material.media_type == VoxMaterial.MEDIA_TYPE_ABSORB:
                            absorb_node = nodes.new("ShaderNodeVolumeAbsorption")
                            absorb_node.inputs["Color"].default_value = color
                            absorb_node.inputs["Density"].default_value = material.density
                            links.new(absorb_node.outputs["Volume"], mat_output_node.inputs["Volume"])
                        elif material.media_type == VoxMaterial.MEDIA_TYPE_SCATTER:
                            scatter_node = nodes.new("ShaderNodeVolumeScatter")
                            scatter_node.inputs["Color"].default_value = color
                            scatter_node.inputs["Density"].default_value = material.density
                            scatter_node.inputs["Anisotropy"].default_value = material.phase
                            links.new(scatter_node.outputs["Volume"], mat_output_node.inputs["Volume"])
                        elif material.media_type == VoxMaterial.MEDIA_TYPE_EMIT:
                            emission_node = nodes.new("ShaderNodeEmission")
                            emission_node.inputs["Color"].default_value = color
                            emission_node.inputs["Strength"].default_value = material.density
                            links.new(emission_node.outputs["Emission"], mat_output_node.inputs["Volume"])
                materials.append(mat)
        return materials

    def create_materials_as_textures(self, collection_name: str, model: VoxModel):
        color_texture = bpy.data.images.new(collection_name + " Color Texture", width=256, height=1)
        for color_index in range(len(model.color_palette)):
            color = model.get_color(color_index)
            pixel_index = color_index * 4
            color_texture.pixels[pixel_index] = color[0]
            color_texture.pixels[pixel_index + 1] = color[1]
            color_texture.pixels[pixel_index + 2] = color[2]
            color_texture.pixels[pixel_index + 3] = color[3]
        mat = bpy.data.materials.new(name=collection_name + " Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bdsf_node = nodes["Principled BSDF"]
        color_texture_node = nodes.new("ShaderNodeTexImage")
        color_texture_node.image = color_texture
        links.new(color_texture_node.outputs["Color"], bdsf_node.inputs["Base Color"])
        if self.import_material_props:
            links.new(color_texture_node.outputs["Color"], bdsf_node.inputs["Emission"])
            bdsf_node.inputs["Emission Strength"].default_value = 0
            mat_texture = bpy.data.images.new(collection_name + " Material Texture", width=256, height=1)
            mat_texture.colorspace_settings.name = 'Non-Color'
            for color_index in range(len(model.color_palette)):
                material = model.materials[color_index]
                pixel_index = color_index * 4
                mat_texture.pixels[pixel_index] = material.roughness
                mat_texture.pixels[pixel_index + 1] = material.metallic
                mat_texture.pixels[pixel_index + 2] = material.ior
                mat_texture.pixels[pixel_index + 3] = 1.0
            mat_texture_node = nodes.new("ShaderNodeTexImage")
            mat_texture_node.image = mat_texture
            separate_rgb_node = nodes.new("ShaderNodeSeparateRGB")
            links.new(mat_texture_node.outputs["Color"], separate_rgb_node.inputs["Image"])
            links.new(separate_rgb_node.outputs["R"], bdsf_node.inputs["Roughness"])
            links.new(separate_rgb_node.outputs["G"], bdsf_node.inputs["Metallic"])
            links.new(separate_rgb_node.outputs["B"], bdsf_node.inputs["IOR"])
        return [mat]

    def execute(self, context):
        keywords = self.as_keywords(
            ignore=(
                "filter_glob",
                "import_cameras",
                "material_mode",
                "voxel_size",
                "voxel_hull",
                "meshing_type",
                "join_models",
                "max_texture_size",
                "import_material_props",
            ),
        )

        if self.material_mode == "TEXTURED_MODEL" and self.meshing_type not in ["GREEDY"]:
            self.report({"WARNING"}, "Selected 'Textured Models (UV unwrap)' material mode without greedy meshing.")
            self.meshing_type = "SIMPLE_QUADS"

        total_timer_start = time.time()
        filepath = keywords['filepath']
        if DEBUG_OUTPUT:
            print('[DEBUG] load raw data')
        timer_start = time.time()
        result = self.load_vox(filepath)
        timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (timer_end - timer_start))
        if result is not None:
            collection_name = os.path.basename(filepath)
            view_layer = context.view_layer
            active_collection = view_layer.active_layer_collection.collection
            voxel_collection = context.blend_data.collections.new(name=collection_name)
            active_collection.children.link(voxel_collection)
            if self.import_cameras:
                for camera_id in result.cameras:
                    camera = result.cameras[camera_id]
                    mode = camera["_mode"] if "_mode" in camera else "pers"
                    blender_modes = {
                        "pers": "PERSP",
                        "free": "PERSP",
                        "pano": "PANO",
                        "orth": "ORTHO",
                        "iso": "ORTHO"
                    }
                    if mode not in blender_modes:
                        self.report({"WARNING"}, "Camera %s mode '%s' is not supported, skipping" % (camera_id, mode))
                        continue
                    camera_data = bpy.data.cameras.new(name="camera_%s" % camera_id)
                    camera_data.type = blender_modes[mode]
                    if "_fov" in camera:
                        camera_data.angle = math.radians(float(camera["_fov"]))
                    camera_object = bpy.data.objects.new("camera_%s" % camera_id, camera_data)
                    rotation = mathutils.Vector((0, 0, 0))
                    roll = 0
                    target = mathutils.Vector((0, 0, 0))
                    radius = 1
                    # Camera target
                    if "_focus" in camera:
                        target = mathutils.Vector(
                            (float(x.strip()) * self.voxel_size for x in camera["_focus"].split(" ")))
                    # Camera distance
                    if "_radius" in camera:
                        radius = float(camera["_radius"])
                    # Camera orientation: pitch, yaw, roll
                    if "_angle" in camera:
                        pitch, yaw, roll = (float(x.strip()) for x in camera["_angle"].split(" "))
                        pitch = math.radians(pitch)
                        yaw = -math.radians(-yaw if yaw <= 180 else (360 - yaw))
                        roll = -math.radians(-roll if roll <= 180 else (360 - roll))
                        rotation = mathutils.Vector((pitch, 0, yaw))
                    rotation_matrix = mathutils.Euler(rotation).to_matrix()
                    rotation_matrix.resize_4x4()
                    position = target + (rotation_matrix @ mathutils.Matrix.Translation(
                        mathutils.Vector((0, -radius * self.voxel_size, 0)))).to_translation()
                    camera_object.rotation_euler = rotation + mathutils.Vector((math.pi * 0.5, 0, 0))
                    camera_object.rotation_euler.rotate_axis("Z", roll)
                    camera_object.location = position
                    voxel_collection.objects.link(camera_object)
            # Create materials depending on the selected material mode
            materials = []
            color_index_material_map = result.get_used_color_indices_material_map()
            if self.material_mode == "VERTEX_COLOR":
                materials = self.create_materials_vertex_colors(collection_name, result)
            elif self.material_mode == "MAT_PER_COLOR":
                materials = self.create_materials_per_color(collection_name, result, color_index_material_map)
            elif self.material_mode == "MAT_AS_TEX":
                materials = self.create_materials_as_textures(collection_name, result)
            # =========================================================================================================
            # Join models
            if self.join_models:
                combined_mesh = VoxMesh(0, -1, -1, -1)
                for mesh in result.meshes:
                    combined_mesh.used_color_indices.update(mesh.used_color_indices)
                model_id_transforms_map = {}
                self.get_model_world_transforms_recursive(result.nodes, result.nodes[0], [], model_id_transforms_map)
                for model_id in model_id_transforms_map:
                    mesh = result.meshes[model_id]
                    for world_matrix in model_id_transforms_map[model_id]:
                        voxel_iterator = OctreeIterator(mesh.voxels)
                        while voxel_iterator.move_next():
                            (x, y, z, value) = voxel_iterator.current
                            target_position = world_matrix @ mathutils.Vector((
                                x - math.floor(mesh.grid.width * 0.5),
                                y - math.floor(mesh.grid.height * 0.5),
                                z - math.floor(mesh.grid.depth * 0.5)
                            ))
                            combined_mesh.voxels.add(int(target_position[0]), int(target_position[1]),
                                                     int(target_position[2]), value)
                bounds = combined_mesh.voxels.not_empty_bounds
                combined_mesh.width = bounds[3] - bounds[0]
                combined_mesh.height = bounds[4] - bounds[1]
                combined_mesh.depth = bounds[5] - bounds[2]
                combined_mesh.num_voxels = combined_mesh.voxels.count
                result.meshes = [combined_mesh]
                root_trn = VoxNode("TRN")
                root_trn.node_id = 0
                root_trn.frame_attributes[0] = {}
                root_trn.child_ids.append(1)
                root_grp = VoxNode("GRP")
                root_grp.node_id = 1
                root_grp.child_ids.append(2)
                shape_trn = VoxNode("TRN")
                shape_trn.node_id = 2
                shape_trn.frame_attributes[0] = {}
                shape_trn.child_ids.append(3)
                shape_shp = VoxNode("SHP")
                shape_shp.node_id = 3
                shape_shp.meshes[0] = {}
                result.nodes = {root_trn.node_id: root_trn, root_grp.node_id: root_grp, shape_trn.node_id: shape_trn,
                                shape_shp.node_id: shape_shp}
            # =========================================================================================================
            # Create models
            model_id_object_lookup = {}
            mesh_index = -1
            for mesh in result.meshes:
                if DEBUG_OUTPUT:
                    bounds = mesh.voxels.not_empty_bounds
                    print('[DEBUG] Generate model %s with size [%s, %s, %s]' % (
                        mesh.model_id, bounds[3] - bounds[0], bounds[4] - bounds[1], bounds[5] - bounds[2]))
                generated_mesh_models = []
                mesh_index += 1
                # Skip empty models
                if mesh.num_voxels == 0:
                    model_id_object_lookup[mesh_index] = []
                    continue
                outside = mesh.grid.create_outside_grid(mesh.voxels)
                # =====================================================
                # CUBES_AS_OBJ
                # =====================================================
                if self.meshing_type == "CUBES_AS_OBJ":
                    if self.voxel_hull:
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                    faces = [[0, 2, 3, 1], [4, 5, 7, 6], [0, 1, 5, 4], [2, 6, 7, 3], [0, 4, 6, 2], [1, 3, 7, 5]]
                    voxel_iterator = OctreeIterator(mesh.voxels)
                    while voxel_iterator.move_next():
                        (x, y, z, color_index) = voxel_iterator.current
                        new_mesh = bpy.data.meshes.new("mesh_%s_voxel_%s_%s_%s" % (mesh_index, x, y, z))
                        vertices = [
                            self.get_vertex_pos((x, y, z), mesh.grid),
                            self.get_vertex_pos((x + 1, y, z), mesh.grid),
                            self.get_vertex_pos((x, y + 1, z), mesh.grid),
                            self.get_vertex_pos((x + 1, y + 1, z), mesh.grid),
                            self.get_vertex_pos((x, y, z + 1), mesh.grid),
                            self.get_vertex_pos((x + 1, y, z + 1), mesh.grid),
                            self.get_vertex_pos((x, y + 1, z + 1), mesh.grid),
                            self.get_vertex_pos((x + 1, y + 1, z + 1), mesh.grid)
                        ]
                        new_mesh.from_pydata(vertices, [], faces)
                        new_mesh.update()
                        if self.material_mode == "VERTEX_COLOR":
                            new_mesh.materials.append(materials[0])
                            new_mesh.vertex_colors.new()
                            vertex_colors = new_mesh.vertex_colors[0].data
                            color = result.get_color(color_index)
                            for i in range(len(faces) * 4):
                                vertex_colors[i].color = color
                            if self.import_material_props:
                                new_mesh.vertex_colors.new()
                                new_mesh.vertex_colors[1].name = "Mat"
                                vertex_colors_mat = new_mesh.vertex_colors[1].data
                                material = result.materials[color_index]
                                mat_color = (material.roughness, material.metallic, material.ior, 0.0)
                                for i in range(len(faces) * 4):
                                    vertex_colors_mat[i].color = mat_color
                        elif self.material_mode == "MAT_AS_TEX":
                            new_mesh.materials.append(materials[0])
                            uv_layer = new_mesh.uv_layers.new(name="UVMap")
                            # Color index as pixel x position + 0.5 offset for the center of the pixel
                            uv_x = (color_index + 0.5) / 256.0
                            for i in range(len(faces) * 4):
                                uv_layer.data[i].uv = [uv_x, 0.5]
                        elif self.material_mode == "MAT_PER_COLOR":
                            material_index = color_index_material_map[color_index]
                            new_mesh.materials.append(materials[material_index])
                            for i, face in enumerate(new_mesh.polygons):
                                face.material_index = 1
                        new_object = bpy.data.objects.new("model_%s_voxel_%s_%s_%s" % (mesh_index, x, y, z),
                                                          new_mesh)
                        voxel_collection.objects.link(new_object)
                        generated_mesh_models.append(new_object)
                # =====================================================
                # Other meshing types
                # =====================================================
                else:
                    if self.meshing_type == "GREEDY":
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        ignore_color = self.material_mode in ["NONE", "TEXTURED_MODEL"]
                        quads = GreedyMeshing.generate_mesh(mesh.voxels, outside, ignore_color)
                    elif self.meshing_type == "SIMPLE_QUADS":
                        mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = SimpleQuadsMeshing.generate_mesh(mesh.voxels, outside)
                    elif self.meshing_type == "SIMPLE_CUBES":
                        if self.voxel_hull:
                            mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = SimpleCubesMeshing.generate_mesh(mesh.voxels)
                    else:
                        self.report({"WARNING"}, "Unknown meshing type %s" % self.meshing_type)
                        quads = []
                    if DEBUG_OUTPUT:
                        print('[DEBUG] generate mesh from faces')
                    timer_start = time.time()
                    vertices_map: Dict[Tuple[int, int, int], int] = {}
                    vertices: List[Tuple[float, float, float]] = []
                    faces = [
                        [
                            self.get_or_create_vertex(vertices_map, vertices, quad.p1, mesh),
                            self.get_or_create_vertex(vertices_map, vertices, quad.p4, mesh),
                            self.get_or_create_vertex(vertices_map, vertices, quad.p3, mesh),
                            self.get_or_create_vertex(vertices_map, vertices, quad.p2, mesh)
                        ]
                        for quad in quads
                    ]
                    new_mesh = bpy.data.meshes.new("mesh_%s" % mesh_index)
                    new_mesh.from_pydata(vertices, [], faces)
                    new_mesh.update()
                    timer_end = time.time()
                    if DEBUG_OUTPUT:
                        print('[DEBUG] took %s sec' % (timer_end - timer_start))
                    if DEBUG_OUTPUT:
                        print('[DEBUG] assign material data')
                    timer_start = time.time()
                    # Assign the material(s) to the object
                    for material in materials:
                        new_mesh.materials.append(material)
                    if self.material_mode == "VERTEX_COLOR":
                        new_mesh.vertex_colors.new()
                        vertex_colors = new_mesh.vertex_colors[0].data
                        vertex_colors_mat = None
                        if self.import_material_props:
                            new_mesh.vertex_colors.new()
                            new_mesh.vertex_colors[1].name = "Mat"
                            vertex_colors_mat = new_mesh.vertex_colors[1].data
                        for i in range(len(quads)):
                            vertex_offset = i * 4
                            color = result.get_color(quads[i].color)
                            vertex_colors[vertex_offset].color = color
                            vertex_colors[vertex_offset + 1].color = color
                            vertex_colors[vertex_offset + 2].color = color
                            vertex_colors[vertex_offset + 3].color = color
                            if vertex_colors_mat is not None:
                                material = result.materials[quads[i].color]
                                mat_color = (material.roughness, material.metallic, material.ior, 0.0)
                                vertex_colors_mat[vertex_offset].color = mat_color
                                vertex_colors_mat[vertex_offset + 1].color = mat_color
                                vertex_colors_mat[vertex_offset + 2].color = mat_color
                                vertex_colors_mat[vertex_offset + 3].color = mat_color
                    elif self.material_mode == "MAT_AS_TEX":
                        uv_layer = new_mesh.uv_layers.new(name="UVMap")
                        for i in range(len(quads)):
                            vertex_offset = i * 4
                            # Color index as pixel x position + 0.5 offset for the center of the pixel
                            uv_x = (quads[i].color + 0.5) / 256.0
                            uv_layer.data[vertex_offset].uv = [uv_x, 0.5]
                            uv_layer.data[vertex_offset + 1].uv = [uv_x, 0.5]
                            uv_layer.data[vertex_offset + 2].uv = [uv_x, 0.5]
                            uv_layer.data[vertex_offset + 3].uv = [uv_x, 0.5]
                    elif self.material_mode == "TEXTURED_MODEL":
                        packer = RectanglePacker(self.max_texture_size, self.max_texture_size)
                        quad_placements: List[Tuple[int, int, int, int]] = []
                        for i in range(len(quads)):
                            quad = quads[i]
                            if quad.normal[0] != 0:
                                width = max(quad.p1[1], quad.p2[1], quad.p3[1], quad.p4[1]) - \
                                        min(quad.p1[1], quad.p2[1], quad.p3[1], quad.p4[1])
                                height = max(quad.p1[2], quad.p2[2], quad.p3[2], quad.p4[2]) - \
                                         min(quad.p1[2], quad.p2[2], quad.p3[2], quad.p4[2])
                            elif quad.normal[1] != 0:
                                width = max(quad.p1[0], quad.p2[0], quad.p3[0], quad.p4[0]) - \
                                        min(quad.p1[0], quad.p2[0], quad.p3[0], quad.p4[0])
                                height = max(quad.p1[2], quad.p2[2], quad.p3[2], quad.p4[2]) - \
                                         min(quad.p1[2], quad.p2[2], quad.p3[2], quad.p4[2])
                            else:
                                width = max(quad.p1[0], quad.p2[0], quad.p3[0], quad.p4[0]) - \
                                        min(quad.p1[0], quad.p2[0], quad.p3[0], quad.p4[0])
                                height = max(quad.p1[1], quad.p2[1], quad.p3[1], quad.p4[1]) - \
                                         min(quad.p1[1], quad.p2[1], quad.p3[1], quad.p4[1])
                            quad_pack_successful, quad_placement = packer.try_pack(width, height)
                            if not quad_pack_successful:
                                self.report({"WARNING"}, "File is not in VOX format")
                                return {"CANCELLED"}
                            quad_placements.append((quad_placement[0], quad_placement[1], width, height))
                        pixel_size = packer.actual_packing_area_width * packer.actual_packing_area_height
                        pixels = [0.0, 0.0, 0.0, 1.0] * pixel_size
                        metal_mask_pixels = [0.0, 0.0, 0.0, 1.0] * pixel_size
                        roughness_mask_pixels = [0.0, 0.0, 0.0, 1.0] * pixel_size
                        emission_mask_pixels = [0.0, 0.0, 0.0, 1.0] * pixel_size
                        uv_x_step = 1.0 / packer.actual_packing_area_width
                        uv_y_step = 1.0 / packer.actual_packing_area_height
                        uv_layer = new_mesh.uv_layers.new(name="UVMap")
                        for i in range(len(quads)):
                            quad = quads[i]
                            quad_placement = quad_placements[i]
                            vertex_offset = i * 4
                            uv_x = quad_placement[0] * uv_x_step
                            uv_y = quad_placement[1] * uv_y_step
                            uv_right = (quad_placement[0] + quad_placement[2]) * uv_x_step
                            uv_top = (quad_placement[1] + quad_placement[3]) * uv_y_step
                            uv_layer.data[vertex_offset].uv = [uv_x, uv_y]
                            uv_layer.data[vertex_offset + 3].uv = [uv_x, uv_top]
                            uv_layer.data[vertex_offset + 2].uv = [uv_right, uv_top]
                            uv_layer.data[vertex_offset + 1].uv = [uv_right, uv_y]
                            if quad.normal[0] != 0:
                                tx = quad.p1[0] if quad.normal[0] < 0 else quad.p1[0] - 1
                                width = max(quad.p1[1], quad.p4[1]) - min(quad.p1[1], quad.p4[1])
                                height = quad.p2[2] - quad.p1[2]
                                for iz in range(0, height):
                                    pixel_offset_iz = (quad_placement[1] + iz) * packer.actual_packing_area_width
                                    tz = quad.p1[2] + iz
                                    for iy in range(0, width):
                                        ty = quad.p1[1] - 1 - iy if quad.normal[0] < 0 else quad.p1[1] + iy
                                        pixel_index = (pixel_offset_iz + quad_placement[0] + iy) * 4
                                        color_index = mesh.get_voxel_color_index(tx, ty, tz)
                                        color = result.get_color(color_index)
                                        pixels[pixel_index:pixel_index + 4] = color
                                        color_material = result.materials[color_index]
                                        metal_mask_pixels[pixel_index:pixel_index + 3] = [color_material.metallic] * 3
                                        emission_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                color_material.emission] * 3
                                        roughness_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                 color_material.roughness] * 3
                            elif quad.normal[1] != 0:
                                ty = quad.p1[1] if quad.normal[1] < 0 else quad.p1[1] - 1
                                width = max(quad.p1[0], quad.p4[0]) - min(quad.p1[0], quad.p4[0])
                                height = quad.p2[2] - quad.p1[2]
                                for iz in range(0, height):
                                    pixel_offset_iz = (quad_placement[1] + iz) * packer.actual_packing_area_width
                                    tz = quad.p1[2] + iz
                                    for ix in range(0, width):
                                        tx = quad.p1[0] + ix if quad.normal[1] < 0 else quad.p1[0] - 1 - ix
                                        pixel_index = (pixel_offset_iz + quad_placement[0] + ix) * 4
                                        color_index = mesh.get_voxel_color_index(tx, ty, tz)
                                        color = result.get_color(color_index)
                                        pixels[pixel_index:pixel_index + 4] = color
                                        color_material = result.materials[color_index]
                                        metal_mask_pixels[pixel_index:pixel_index + 3] = [color_material.metallic] * 3
                                        emission_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                color_material.emission] * 3
                                        roughness_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                 color_material.roughness] * 3
                            elif quad.normal[2] != 0:
                                tz = quad.p1[2] if quad.normal[2] < 0 else quad.p1[2] - 1
                                width = quad.p4[0] - quad.p1[0]
                                height = max(quad.p1[1], quad.p2[1]) - min(quad.p1[1], quad.p2[1])
                                for ix in range(0, width):
                                    tx = quad.p1[0] + ix
                                    for iy in range(0, height):
                                        ty = quad.p1[1] - 1 - iy if quad.normal[2] < 0 else quad.p1[1] + iy
                                        pixel_offset_iy = (quad_placement[1] + iy) * packer.actual_packing_area_width
                                        pixel_index = (pixel_offset_iy + quad_placement[0] + ix) * 4
                                        color_index = mesh.get_voxel_color_index(tx, ty, tz)
                                        color = result.get_color(color_index)
                                        pixels[pixel_index:pixel_index + 4] = color
                                        color_material = result.materials[color_index]
                                        metal_mask_pixels[pixel_index:pixel_index + 3] = [color_material.metallic] * 3
                                        emission_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                color_material.emission] * 3
                                        roughness_mask_pixels[pixel_index:pixel_index + 3] = [
                                                                                                 color_material.roughness] * 3
                        # Setup model material
                        color_texture = bpy.data.images.new(collection_name + " Color Texture",
                                                            width=packer.actual_packing_area_width,
                                                            height=packer.actual_packing_area_height)
                        color_texture.pixels = pixels
                        mat = bpy.data.materials.new(name="mesh_%s Material" % mesh_index)
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        links = mat.node_tree.links
                        bdsf_node = nodes["Principled BSDF"]
                        color_texture_node = nodes.new("ShaderNodeTexImage")
                        color_texture_node.image = color_texture
                        color_texture_node.interpolation = "Closest"
                        links.new(color_texture_node.outputs["Color"], bdsf_node.inputs["Base Color"])
                        if self.import_material_props:
                            metal_mask_texture = bpy.data.images.new(collection_name + " Metal Mask Texture",
                                                                     width=packer.actual_packing_area_width,
                                                                     height=packer.actual_packing_area_height)
                            metal_mask_texture.pixels = metal_mask_pixels
                            metal_mask_texture_node = nodes.new("ShaderNodeTexImage")
                            metal_mask_texture_node.image = metal_mask_texture
                            metal_mask_texture_node.interpolation = "Closest"
                            links.new(metal_mask_texture_node.outputs["Color"], bdsf_node.inputs["Metallic"])
                            roughness_mask_texture = bpy.data.images.new(collection_name + " Roughness Mask Texture",
                                                                         width=packer.actual_packing_area_width,
                                                                         height=packer.actual_packing_area_height)
                            roughness_mask_texture.pixels = roughness_mask_pixels
                            roughness_mask_texture_node = nodes.new("ShaderNodeTexImage")
                            roughness_mask_texture_node.image = roughness_mask_texture
                            roughness_mask_texture_node.interpolation = "Closest"
                            links.new(roughness_mask_texture_node.outputs["Color"], bdsf_node.inputs["Roughness"])
                            emission_mask_texture = bpy.data.images.new(collection_name + " Emission Mask Texture",
                                                                        width=packer.actual_packing_area_width,
                                                                        height=packer.actual_packing_area_height)
                            emission_mask_texture.pixels = emission_mask_pixels
                            emission_mask_texture_node = nodes.new("ShaderNodeTexImage")
                            emission_mask_texture_node.image = emission_mask_texture
                            emission_mask_texture_node.interpolation = "Closest"
                            links.new(emission_mask_texture_node.outputs["Color"],
                                      bdsf_node.inputs["Emission Strength"])
                            links.new(color_texture_node.outputs["Color"], bdsf_node.inputs["Emission"])
                        new_mesh.materials.append(mat)
                    elif self.material_mode == "MAT_PER_COLOR":
                        for i, face in enumerate(new_mesh.polygons):
                            face.material_index = color_index_material_map[quads[i].color]
                    new_object = bpy.data.objects.new('import_tmp_model', new_mesh)
                    generated_mesh_models.append(new_object)
                    timer_end = time.time()
                    if DEBUG_OUTPUT:
                        print('[DEBUG] took %s sec' % (timer_end - timer_start))
                model_id_object_lookup[mesh_index] = generated_mesh_models

            if DEBUG_OUTPUT:
                print('[DEBUG] recurse hierarchy')
            timer_start = time.time()
            if len(result.nodes) == 0:
                # If we have a file without hierarchy, just add the models to the collection
                for model_objects in model_id_object_lookup.values():
                    for model_object in model_objects:
                        model_object.name = 'model'
                        voxel_collection.objects.link(model_object)
            else:
                # Translate generated meshes and associate if requested with node hierarchy
                self.recurse_hierarchy(voxel_collection, result.nodes, result.nodes[0], [], [], model_id_object_lookup)
                # Remove original objects as the hierarchy creates copies
                for model_objects in model_id_object_lookup.values():
                    for model_object in model_objects:
                        bpy.data.objects.remove(model_object)
            timer_end = time.time()
            if DEBUG_OUTPUT:
                print('[DEBUG] took %s sec' % (timer_end - timer_start))

        total_timer_end = time.time()
        if DEBUG_OUTPUT:
            print('[DEBUG] total time %s sec' % (total_timer_end - total_timer_start))
        return {"CANCELLED"} if result is None else {'FINISHED'}

    def get_or_create_vertex(self, vertices_map: Dict[Tuple[int, int, int], int],
                             vertices: List[Tuple[float, float, float]], vertex: Tuple[int, int, int],
                             mesh: VoxMesh) -> int:
        if vertex in vertices_map:
            return vertices_map[vertex]
        vertices.append(self.get_vertex_pos(vertex, mesh.grid))
        vertices_map[vertex] = len(vertices) - 1
        return len(vertices) - 1

    def recurse_hierarchy(self, voxel_collection, nodes: Dict[int, VoxNode], node: VoxNode, path, path_objects,
                          model_id_object_lookup: Dict):
        next_path = path + [node.node_id]
        next_path_objects = list(path_objects)
        if node.type == 'GRP':
            parent_transform_attributes = nodes[path[-1]].node_attributes
            group_name = parent_transform_attributes[
                '_name'] if '_name' in parent_transform_attributes else 'grp_%s' % node.node_id
            if self.import_hierarchy:
                transform_node = nodes[path[-1]]
                # TODO: frame
                translation = transform_node.get_transform_translation(0, self.voxel_size)
                rotation = transform_node.get_transform_rotation(0)
                group_data = bpy.data.objects.new(group_name, None)
                group_data.empty_display_size = 1
                group_data.empty_display_type = 'PLAIN_AXES'
                group_data.matrix_local = translation @ rotation
                voxel_collection.objects.link(group_data)
                next_path_objects.append(group_data)
                if len(path_objects) > 0:
                    group_data.parent = path_objects[-1]
        elif node.type == 'SHP':
            parent_transform_attributes = nodes[path[-1]].node_attributes
            for model_id in node.meshes:
                model_name = parent_transform_attributes[
                    '_name'] if '_name' in parent_transform_attributes else 'model_%s' % model_id
                shape_objects = [x.copy() for x in model_id_object_lookup[model_id]]
                for shape_object in shape_objects:
                    voxel_collection.objects.link(shape_object)
                    shape_object.name = model_name
                    if self.import_hierarchy:
                        shape_object.parent = next_path_objects[-1]
                    mesh_attributes = node.meshes[model_id]
                    mesh_frame = mesh_attributes["_f"] if "_f" in mesh_attributes else 0
                    for i in range(len(path) - 1, 0, -1):
                        next_node = nodes[path[i]]
                        if next_node.type == 'TRN':
                            translation = next_node.get_transform_translation(mesh_frame, self.voxel_size)
                            rotation = next_node.get_transform_rotation(mesh_frame)
                            if self.import_hierarchy:
                                shape_object.matrix_local = translation @ rotation
                                # If we import the hierarchy, we only need to apply the
                                # nearest transform node as all other transforms are applied
                                # by the object parent hierarchy
                                break
                            else:
                                shape_object.matrix_world = translation @ rotation @ shape_object.matrix_world
        for child_id in node.child_ids:
            self.recurse_hierarchy(voxel_collection, nodes, nodes[child_id], next_path, next_path_objects,
                                   model_id_object_lookup)

    def get_model_world_transforms_recursive(self, nodes: Dict[int, VoxNode], node: VoxNode, path,
                                             result: Dict[int, List[mathutils.Matrix]]):
        if node.type == 'SHP':
            for model_id in node.meshes:
                mesh_attributes = node.meshes[model_id]
                mesh_frame = mesh_attributes["_f"] if "_f" in mesh_attributes else 0
                matrix_world = mathutils.Matrix()
                for i in range(len(path) - 1, 0, -1):
                    next_node = nodes[path[i]]
                    if next_node.type == 'TRN':
                        translation = next_node.get_transform_translation(mesh_frame, self.voxel_size)
                        rotation = next_node.get_transform_rotation(mesh_frame)
                        matrix_world = translation @ rotation @ matrix_world
                if model_id not in result:
                    result[model_id] = []
                result[model_id].append(matrix_world)
        for child_id in node.child_ids:
            self.get_model_world_transforms_recursive(nodes, nodes[child_id], path + [node.node_id], result)

    def get_vertex_pos(self, p: Tuple[float, float, float], grid: VoxelGrid) -> Tuple[float, float, float]:
        return (
            (p[0] - math.floor(grid.width * 0.5)) * self.voxel_size,
            (p[1] - math.floor(grid.depth * 0.5)) * self.voxel_size,
            (p[2] - math.floor(grid.height * 0.5)) * self.voxel_size
        )

    def load_vox(self, filepath: str) -> VoxModel or None:
        with io.FileIO(filepath, "r") as f:
            if ImportVOX.read_riff_id(f) != "VOX ":
                self.report({"WARNING"}, "File is not in VOX format")
                return None
            version = ImportVOX.read_int32(f)
            model = VoxModel(version)
            if DEBUG_OUTPUT:
                print('[DEBUG] MagicaVoxel vox file version %s' % version)
            while f.tell() < os.fstat(f.fileno()).st_size:
                ImportVOX.read_next_chunk(f, model)
        return model

    @staticmethod
    def read_riff_id(f: IO) -> str:
        return "".join(map(chr, f.read(4)))

    @staticmethod
    def read_int32(f: IO) -> int:
        return READ_INT_UNPACK(f.read(4))[0]

    @staticmethod
    def read_float32(f: IO) -> int:
        return READ_FLOAT_UNPACK(f.read(4))[0]

    @staticmethod
    def read_string(f: IO) -> str:
        length = ImportVOX.read_int32(f)
        return "".join(map(chr, f.read(length))) if length > 0 else ""

    @staticmethod
    def read_dict(f: IO) -> Dict[str, str]:
        num_pairs = ImportVOX.read_int32(f)
        # Beware, reading from a file can not be done directly in a dict comprehension as with pep-0572 (python 3.8)
        # the order in which dict comprehension keys and values are evaluated changed. Here we explicitly load key and
        # value in order and only then push them to the dictionary.
        result = {}
        for _ in range(0, num_pairs):
            key = ImportVOX.read_string(f)
            value = ImportVOX.read_string(f)
            result[key] = value
        return result

    @staticmethod
    def read_pack_chunk(f: IO, _: VoxModel):
        ImportVOX.read_int32(f)  # num_models, ignored

    @staticmethod
    def read_size_chunk(f: IO, model: VoxModel):
        # width, depth, height
        mesh = VoxMesh(model.next_model_id, ImportVOX.read_int32(f), ImportVOX.read_int32(f), ImportVOX.read_int32(f))
        model.next_model_id += 1
        model.meshes.append(mesh)

    @staticmethod
    def read_xyzi_chunk(f: io.FileIO, model: VoxModel):
        num_voxels = ImportVOX.read_int32(f)
        mesh = model.meshes[-1]
        mesh.num_voxels = num_voxels
        voxel_data = bytearray(num_voxels * 4)
        f.readinto(voxel_data)
        for i in range(0, len(voxel_data), 4):
            mesh.voxels.add(int(voxel_data[i]), int(voxel_data[i + 1]), int(voxel_data[i + 2]), int(voxel_data[i + 3]))
        mesh.used_color_indices.update({int(voxel_data[i + 3]) for i in range(0, len(voxel_data), 4)})

    @staticmethod
    def read_rcam_chunk(f: IO, model: VoxModel):
        camera_id = ImportVOX.read_int32(f)
        model.cameras[camera_id] = ImportVOX.read_dict(f)

    @staticmethod
    def read_robj_chunk(f: IO, model: VoxModel):
        model.rendering_attributes.append(ImportVOX.read_dict(f))

    @staticmethod
    def read_ntrn_chunk(f: IO, model: VoxModel):
        node = VoxNode("TRN")
        node.node_id = ImportVOX.read_int32(f)
        node.node_attributes = ImportVOX.read_dict(f)
        child_node_id = ImportVOX.read_int32(f)
        node.child_ids.append(child_node_id)
        ImportVOX.read_int32(f)  # reserved id, must be -1
        node.layer_id = ImportVOX.read_int32(f)
        num_frames = ImportVOX.read_int32(f)
        node.frame_attributes = {i: ImportVOX.read_dict(f) for i in range(0, num_frames)}
        model.nodes[node.node_id] = node

    @staticmethod
    def read_ngrp_chunk(f: IO, model: VoxModel):
        node = VoxNode("GRP")
        node.node_id = ImportVOX.read_int32(f)
        node.node_attributes = ImportVOX.read_dict(f)
        num_child_ids = ImportVOX.read_int32(f)
        for i in range(0, num_child_ids):
            child_node_id = ImportVOX.read_int32(f)
            node.child_ids.append(child_node_id)
        model.nodes[node.node_id] = node

    @staticmethod
    def read_nshp_chunk(f: IO, model: VoxModel):
        node = VoxNode("SHP")
        node.node_id = ImportVOX.read_int32(f)
        node.node_attributes = ImportVOX.read_dict(f)
        num_models = ImportVOX.read_int32(f)
        for i in range(0, num_models):
            model_id = ImportVOX.read_int32(f)
            model_attributes = ImportVOX.read_dict(f)
            node.meshes[model_id] = model_attributes
        model.nodes[node.node_id] = node

    @staticmethod
    def read_matl_chunk(f: IO, model: VoxModel):
        material_id = ImportVOX.read_int32(f) % 256
        model.materials[material_id] = VoxMaterial(ImportVOX.read_dict(f))

    @staticmethod
    def read_matt_chunk(f: IO, model: VoxModel):
        material_id = ImportVOX.read_int32(f) % 256
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
        model.materials[material_id] = VoxMaterial(property_values)

    @staticmethod
    def read_layr_chunk(f: IO, model: VoxModel):
        layer_id = ImportVOX.read_int32(f)
        model.layers[layer_id] = ImportVOX.read_dict(f)
        _ = ImportVOX.read_int32(f)  # reserved id, must be -1

    @staticmethod
    def read_rgba_chunk(f: IO, model: VoxModel):
        custom_palette: List[Tuple[int, int, int, int]] = [(0, 0, 0, 255)]
        color_data = struct.unpack('%sB' % 256 * 4, f.read(256 * 4))
        for i in range(256):
            offset = i * 4
            color = (color_data[offset], color_data[offset + 1], color_data[offset + 2], color_data[offset + 3])
            if i == 255:
                custom_palette[0] = color
            else:
                custom_palette.append(color)
        model.color_palette = custom_palette

    @staticmethod
    def read_imap_chunk(f: IO, _: VoxModel):
        _ = struct.unpack('%sB' % 256, f.read(256))  # imap_data
        # _ = {imap_data[i]: (i + 1) % 256 for i in range(256)}
        # IMAP in combination with custom palette is only relevant for showing the palette in MV. Ignored.

    @staticmethod
    def read_note_chunk(f: IO, _: VoxModel):
        num_color_names = ImportVOX.read_int32(f)
        _ = [ImportVOX.read_string(f) for _ in range(num_color_names)]  # color_names
        # color palette names are ignored

    @staticmethod
    def read_next_chunk(f: io.FileIO, model: VoxModel):
        riff_id = ImportVOX.read_riff_id(f)
        content_byte_length = ImportVOX.read_int32(f)
        ImportVOX.read_int32(f)  # children_byte_length
        current_position = f.tell()
        if riff_id == 'PACK':
            ImportVOX.read_pack_chunk(f, model)
        elif riff_id == 'SIZE':
            ImportVOX.read_size_chunk(f, model)
        elif riff_id == 'XYZI':
            ImportVOX.read_xyzi_chunk(f, model)
        elif riff_id == 'rCAM':
            ImportVOX.read_rcam_chunk(f, model)
        elif riff_id == 'rOBJ':
            ImportVOX.read_robj_chunk(f, model)
        elif riff_id == 'nTRN':
            ImportVOX.read_ntrn_chunk(f, model)
        elif riff_id == 'nGRP':
            ImportVOX.read_ngrp_chunk(f, model)
        elif riff_id == 'nSHP':
            ImportVOX.read_nshp_chunk(f, model)
        elif riff_id == 'MATL':
            ImportVOX.read_matl_chunk(f, model)
        elif riff_id == 'MATT':  # Legacy material
            ImportVOX.read_matt_chunk(f, model)
        elif riff_id == 'LAYR':
            ImportVOX.read_layr_chunk(f, model)
        elif riff_id == 'RGBA':
            ImportVOX.read_rgba_chunk(f, model)
        elif riff_id == 'IMAP':
            ImportVOX.read_imap_chunk(f, model)
        elif riff_id == 'NOTE':
            ImportVOX.read_note_chunk(f, model)
        # Skip unknown data
        if current_position + content_byte_length > f.tell():
            f.seek(current_position + content_byte_length)

    def draw(self, context):
        pass


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

        if operator.join_models:
            operator.import_hierarchy = False
            row = layout.row()
            row.enabled = False
            row.prop(operator, "import_hierarchy")
        else:
            layout.prop(operator, "import_hierarchy")
        # layout.prop(operator, "join_models")

        layout.prop(operator, "voxel_size")
        layout.row().prop(operator, "meshing_type")
        if operator.meshing_type in ["CUBES_AS_OBJ", "SIMPLE_CUBES"]:
            layout.row().prop(operator, "voxel_hull")


class VOX_PT_import_materials(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Materials"
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

        layout.row().prop(operator, "material_mode")
        if operator.material_mode != "NONE":
            layout.row().prop(operator, "import_material_props")
        if operator.material_mode == "TEXTURED_MODEL":
            operator.meshing_type = "GREEDY"
            layout.row().label(text="INFO: Locked Greedy meshing for")
            layout.row().label(text="textured models mode.")
            layout.row().prop(operator, "max_texture_size")


class VOX_PT_import_cameras(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Cameras"
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

        layout.prop(operator, "import_cameras")


def menu_func_import(self, _context):
    self.layout.operator(ImportVOX.bl_idname, text="MagicaVoxel (.vox)")


classes = (
    ImportVOX,
    VOX_PT_import_geometry,
    VOX_PT_import_materials,
    VOX_PT_import_cameras,
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
