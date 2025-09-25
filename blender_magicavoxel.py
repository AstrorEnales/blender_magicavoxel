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
    "version": (1, 5, 6),
    "blender": (3, 0, 0),
    "location": "File > Import-Export",
    "description": "Importer for MagicaVoxel VOX files",
    "category": "Import-Export",
    "doc_url": "https://github.com/AstrorEnales/blender_magicavoxel",
    "tracker_url": "https://github.com/AstrorEnales/blender_magicavoxel/issues",
    "support": "COMMUNITY",
}

DEFAULT_PALETTE: List[int] = [
    0xffffffff, 0xffffccff, 0xffff99ff, 0xffff66ff, 0xffff33ff, 0xffff00ff,
    0xffccffff, 0xffccccff, 0xffcc99ff, 0xffcc66ff, 0xffcc33ff, 0xffcc00ff,
    0xff99ffff, 0xff99ccff, 0xff9999ff, 0xff9966ff, 0xff9933ff, 0xff9900ff,
    0xff66ffff, 0xff66ccff, 0xff6699ff, 0xff6666ff, 0xff6633ff, 0xff6600ff,
    0xff33ffff, 0xff33ccff, 0xff3399ff, 0xff3366ff, 0xff3333ff, 0xff3300ff,
    0xff00ffff, 0xff00ccff, 0xff0099ff, 0xff0066ff, 0xff0033ff, 0xff0000ff,
    0xccffffff, 0xccffccff, 0xccff99ff, 0xccff66ff, 0xccff33ff, 0xccff00ff,
    0xccccffff, 0xccccccff, 0xcccc99ff, 0xcccc66ff, 0xcccc33ff, 0xcccc00ff,
    0xcc99ffff, 0xcc99ccff, 0xcc9999ff, 0xcc9966ff, 0xcc9933ff, 0xcc9900ff,
    0xcc66ffff, 0xcc66ccff, 0xcc6699ff, 0xcc6666ff, 0xcc6633ff, 0xcc6600ff,
    0xcc33ffff, 0xcc33ccff, 0xcc3399ff, 0xcc3366ff, 0xcc3333ff, 0xcc3300ff,
    0xcc00ffff, 0xcc00ccff, 0xcc0099ff, 0xcc0066ff, 0xcc0033ff, 0xcc0000ff,
    0x99ffffff, 0x99ffccff, 0x99ff99ff, 0x99ff66ff, 0x99ff33ff, 0x99ff00ff,
    0x99ccffff, 0x99ccccff, 0x99cc99ff, 0x99cc66ff, 0x99cc33ff, 0x99cc00ff,
    0x9999ffff, 0x9999ccff, 0x999999ff, 0x999966ff, 0x999933ff, 0x999900ff,
    0x9966ffff, 0x9966ccff, 0x996699ff, 0x996666ff, 0x996633ff, 0x996600ff,
    0x9933ffff, 0x9933ccff, 0x993399ff, 0x993366ff, 0x993333ff, 0x993300ff,
    0x9900ffff, 0x9900ccff, 0x990099ff, 0x990066ff, 0x990033ff, 0x990000ff,
    0x66ffffff, 0x66ffccff, 0x66ff99ff, 0x66ff66ff, 0x66ff33ff, 0x66ff00ff,
    0x66ccffff, 0x66ccccff, 0x66cc99ff, 0x66cc66ff, 0x66cc33ff, 0x66cc00ff,
    0x6699ffff, 0x6699ccff, 0x669999ff, 0x669966ff, 0x669933ff, 0x669900ff,
    0x6666ffff, 0x6666ccff, 0x666699ff, 0x666666ff, 0x666633ff, 0x666600ff,
    0x6633ffff, 0x6633ccff, 0x663399ff, 0x663366ff, 0x663333ff, 0x663300ff,
    0x6600ffff, 0x6600ccff, 0x660099ff, 0x660066ff, 0x660033ff, 0x660000ff,
    0x33ffffff, 0x33ffccff, 0x33ff99ff, 0x33ff66ff, 0x33ff33ff, 0x33ff00ff,
    0x33ccffff, 0x33ccccff, 0x33cc99ff, 0x33cc66ff, 0x33cc33ff, 0x33cc00ff,
    0x3399ffff, 0x3399ccff, 0x339999ff, 0x339966ff, 0x339933ff, 0x339900ff,
    0x3366ffff, 0x3366ccff, 0x336699ff, 0x336666ff, 0x336633ff, 0x336600ff,
    0x3333ffff, 0x3333ccff, 0x333399ff, 0x333366ff, 0x333333ff, 0x333300ff,
    0x3300ffff, 0x3300ccff, 0x330099ff, 0x330066ff, 0x330033ff, 0x330000ff,
    0x00ffffff, 0x00ffccff, 0x00ff99ff, 0x00ff66ff, 0x00ff33ff, 0x00ff00ff,
    0x00ccffff, 0x00ccccff, 0x00cc99ff, 0x00cc66ff, 0x00cc33ff, 0x00cc00ff,
    0x0099ffff, 0x0099ccff, 0x009999ff, 0x009966ff, 0x009933ff, 0x009900ff,
    0x0066ffff, 0x0066ccff, 0x006699ff, 0x006666ff, 0x006633ff, 0x006600ff,
    0x0033ffff, 0x0033ccff, 0x003399ff, 0x003366ff, 0x003333ff, 0x003300ff,
    0x0000ffff, 0x0000ccff, 0x000099ff, 0x000066ff, 0x000033ff, 0xee0000ff,
    0xdd0000ff, 0xbb0000ff, 0xaa0000ff, 0x880000ff, 0x770000ff, 0x550000ff,
    0x440000ff, 0x220000ff, 0x110000ff, 0x00ee00ff, 0x00dd00ff, 0x00bb00ff,
    0x00aa00ff, 0x008800ff, 0x007700ff, 0x005500ff, 0x004400ff, 0x002200ff,
    0x001100ff, 0x0000eeff, 0x0000ddff, 0x0000bbff, 0x0000aaff, 0x000088ff,
    0x000077ff, 0x000055ff, 0x000044ff, 0x000022ff, 0x000011ff, 0xeeeeeeff,
    0xddddddff, 0xbbbbbbff, 0xaaaaaaff, 0x888888ff, 0x777777ff, 0x555555ff,
    0x444444ff, 0x222222ff, 0x111111ff, 0xff000000,
]

DEBUG_OUTPUT = False


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
        leaves_packing_area = (rectangle_x < 0
                               or rectangle_y < 0
                               or rectangle_x + rectangle_width > tested_packing_area_width
                               or rectangle_y + rectangle_height > tested_packing_area_height)
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

    def try_pack(self, rectangle_width: int, rectangle_height: int) -> Tuple[int, int] or None:
        """
        Tries to allocate space for a rectangle in the packing area.
        """
        # Try to find an anchor where the rectangle fits in, enlarging the packing area and repeating the search
        # recursively until it fits or the maximum allowed size is exceeded.
        anchor_index = self.select_anchor_recursive(rectangle_width, rectangle_height, self.actual_packing_area_width,
                                                    self.actual_packing_area_height)
        # No anchor could be found at which the rectangle did fit in
        if anchor_index == -1:
            return None
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
        return placement


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
        return (x >= self.size_half or x < -self.size_half or y >= self.size_half or y < -self.size_half
                or z >= self.size_half or z < -self.size_half)

    def is_inside(self, x: int, y: int, z: int) -> bool:
        # noinspection PyChainedComparisons
        return (x < self.size_half and x >= -self.size_half and y < self.size_half and y >= -self.size_half
                and z < self.size_half and z >= -self.size_half)

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
        while (self.size > 8
               and self._root.is_child_contractible(ChildXnYnZn, ChildXpYpZp)
               and self._root.is_child_contractible(ChildXpYpZn, ChildXnYnZp)
               and self._root.is_child_contractible(ChildXnYpZp, ChildXpYnZn)
               and self._root.is_child_contractible(ChildXpYpZp, ChildXnYnZn)):
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
                OctreeBranchNode(self.parent, pos_x, pos_y, pos_z, self.size_half, self.default_value)
                if self.size_half > SideLength else
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
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))

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
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))
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
        leaf_bounds = [leaf.not_empty_bounds for leaf in voxels.leafs if leaf.is_not_empty]
        leaf_bounds = [(b[0] - 1, b[1] - 1, b[2] - 1, b[3] + 1, b[4] + 1, b[5] + 1) for b in leaf_bounds]
        count = -1
        while count != len(leaf_bounds):
            count = len(leaf_bounds)
            for i in range(len(leaf_bounds) - 1, 0, -1):
                b1 = leaf_bounds[i]
                for j in range(i - 1, -1, -1):
                    b2 = leaf_bounds[j]
                    if not (b1[3] < b2[0] or b1[0] > b2[3] or b1[4] < b2[1] or b1[1] > b2[4] or b1[5] < b2[2]
                            or b1[2] > b2[5]):
                        leaf_bounds[j] = (
                            min(b1[0], b2[0]), min(b1[1], b2[1]), min(b1[2], b2[2]),
                            max(b1[3], b2[3]), max(b1[4], b2[4]), max(b1[5], b2[5])
                        )
                        del leaf_bounds[i]
                        break
        for bounds in leaf_bounds:
            for z in range(bounds[2], bounds[5]):
                for y in range(bounds[1], bounds[4]):
                    for x in range(bounds[0], bounds[3]):
                        if voxels.get_value(x, y, z) is not None:
                            labels.add(x, y, z, -1)
                            continue
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
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))
        return labels


class Quad:
    def __init__(self,
                 p1: Tuple[int, int, int] = (0, 0, 0),
                 p2: Tuple[int, int, int] = (0, 0, 0),
                 p3: Tuple[int, int, int] = (0, 0, 0),
                 p4: Tuple[int, int, int] = (0, 0, 0),
                 normal: Tuple[int, int, int] = (0, 0, 0),
                 color: int = 0,
                 width: int = 1,
                 height: int = 1,
                 vertex_indices: Tuple[int, int, int, int] = (3, 2, 0, 1)
                 ):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.normal = normal
        self.color = color
        self.width = width
        self.height = height
        self.vertex_indices = vertex_indices  # tl,tr,bl,br

    def __getitem__(self, i):
        if i == 0:
            return self.p1
        if i == 1:
            return self.p2
        if i == 2:
            return self.p3
        return self.p4


class SimpleQuadsMeshing:
    @staticmethod
    def generate_mesh(voxels: Octree, outside: Octree, ignore_neighbours: bool) -> List[Quad]:
        if DEBUG_OUTPUT:
            print('[DEBUG] SimpleQuadsMeshing generate_mesh')
        timer_start = time.time()
        quads: List[Quad] = []
        iterator = OctreeIterator(voxels)
        while iterator.move_next():
            (x, y, z, color_index) = iterator.current
            xn, xp, yn, yp, zn, zp = x - 1, x + 1, y - 1, y + 1, z - 1, z + 1
            # Left
            if ignore_neighbours or outside.get_value(xn, y, z):
                quads.append(Quad((x, yp, z), (x, y, z), (x, y, zp), (x, yp, zp), (-1, 0, 0), color_index, 1, 1))
            # Right
            if ignore_neighbours or outside.get_value(xp, y, z):
                quads.append(Quad((xp, y, z), (xp, yp, z), (xp, yp, zp), (xp, y, zp), (1, 0, 0), color_index, 1, 1))
            # Back
            if ignore_neighbours or outside.get_value(x, yn, z):
                quads.append(Quad((x, y, z), (xp, y, z), (xp, y, zp), (x, y, zp), (0, -1, 0), color_index, 1, 1))
            # Front
            if ignore_neighbours or outside.get_value(x, yp, z):
                quads.append(Quad((xp, yp, z), (x, yp, z), (x, yp, zp), (xp, yp, zp), (0, 1, 0), color_index, 1, 1))
            # Bottom
            if ignore_neighbours or outside.get_value(x, y, zn):
                quads.append(Quad((xp, y, z), (x, y, z), (x, yp, z), (xp, yp, z), (0, 0, -1), color_index, 1, 1))
            # Top
            if ignore_neighbours or outside.get_value(x, y, zp):
                quads.append(Quad((x, y, zp), (xp, y, zp), (xp, yp, zp), (x, yp, zp), (0, 0, 1), color_index, 1, 1))
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))
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
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))
        return quads

    @staticmethod
    def mesh_axis(bounds: Tuple[int, int, int, int, int, int], voxels: Octree, outside: Octree, ignore_color: bool,
                  axis_index: int, quads: List[Quad]):
        axis1_index = {0: 1, 1: 0, 2: 0}[axis_index]
        axis2_index = {0: 2, 1: 2, 2: 1}[axis_index]
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
                                            iter_voxel is None
                                            # ...or already visited...
                                            or visited[visited_index][iter_visited_index]
                                            # ...or different color...
                                            or (not ignore_color and start_voxel != iter_voxel)
                                            # ... or not connected to the outside space
                                            or (has_offset[visited_index]
                                                and not outside.get_value(*get_vector(a_back, i, c)))
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
                                                iter_voxel is None
                                                # ...or already visited...
                                                or visited[visited_index][iter_visited_index]
                                                # ...or different color...
                                                or (not ignore_color and start_voxel != iter_voxel)
                                                # ... or not connected to the outside space
                                                or (has_offset[visited_index]
                                                    and not outside.get_value(*get_vector(a_back, i, j)))
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
                                p1 = get_vector(a_visited, b, c)
                                p2 = get_vector(a_visited, end_index_axis1 + 1, c)
                                p3 = get_vector(a_visited, b, end_index_axis2 + 1)
                                p4 = get_vector(a_visited, end_index_axis1 + 1, end_index_axis2 + 1)
                                if axis_index == 1:
                                    if visited_index == 0:
                                        quad.p1 = p1
                                        quad.p2 = p2
                                        quad.p3 = p4
                                        quad.p4 = p3
                                    else:
                                        quad.p1 = p2
                                        quad.p2 = p1
                                        quad.p3 = p3
                                        quad.p4 = p4
                                else:
                                    if visited_index == 0:
                                        quad.p1 = p2
                                        quad.p2 = p1
                                        quad.p3 = p3
                                        quad.p4 = p4
                                    else:
                                        quad.p1 = p1
                                        quad.p2 = p2
                                        quad.p3 = p4
                                        quad.p4 = p3
                                quad.width = end_index_axis1 + 1 - b
                                quad.height = end_index_axis2 + 1 - c
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
        return ("VoxMaterial {type: %s, roughness: %s, metallic: %s, specular: %s, ior: %s, emission: %s, "
                + "flux: %s, ldr: %s, transmission: %s, media_type: %s, density: %s, phase: %s}") % (
            self.type, self.roughness, self.metallic, self.specular, self.ior, self.emission, self.flux,
            self.ldr,
            self.transmission, self.media_type, self.density, self.phase)


class VoxMesh:
    def __init__(self, model_id: int, width: int, depth: int, height: int):
        self.model_id = model_id
        self.num_voxels = 0
        self.grid: VoxelGrid = VoxelGrid(width, depth, height)
        self.voxel_data = None
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
        self.color_palette = DEFAULT_PALETTE.copy()
        self.index_map = None
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
        return (color & 0xff) / 255.0, (color >> 8 & 0xff) / 255.0, (color >> 16 & 0xff) / 255.0, (color >> 24 & 0xff) / 255.0

    def is_layer_hidden(self, layer_id: int):
        return layer_id in self.layers and '_hidden' in self.layers[layer_id] and \
            self.layers[layer_id]['_hidden'] == '1'


def voxels_as_cubes_on_update(self, _context):
    if self.convert_to_mesh is self.voxels_as_cubes:
        self.convert_to_mesh = not self.voxels_as_cubes


def convert_to_mesh_on_update(self, _context):
    if self.voxels_as_cubes is self.convert_to_mesh:
        self.voxels_as_cubes = not self.convert_to_mesh
    if self.convert_to_mesh:
        self.voxel_hull = True


class ShaderNodeProxy:
    @staticmethod
    def get_node_input_key(node, key, alternatives=None):
        translated_key = bpy.app.translations.pgettext(key)
        if translated_key in node.inputs:
            return translated_key
        if key in node.inputs:
            return key
        if alternatives is not None:
            for alternative in alternatives:
                translated_key = bpy.app.translations.pgettext(alternative)
                if translated_key in node.inputs:
                    return translated_key
                if alternative in node.inputs:
                    return alternative
        print("[WARN] Failed to find shader node input key '%s' or any alternative %s" % (key, alternatives))
        return None

    @staticmethod
    def get_node_output_key(node, key, alternatives=None):
        translated_key = bpy.app.translations.pgettext(key)
        if translated_key in node.outputs:
            return translated_key
        if key in node.outputs:
            return key
        if alternatives is not None:
            for alternative in alternatives:
                translated_key = bpy.app.translations.pgettext(alternative)
                if translated_key in node.outputs:
                    return translated_key
                if alternative in node.outputs:
                    return alternative
        print("[WARN] Failed to find shader node output key '%s' or any alternative %s" % (key, alternatives))
        return None


class SeparateColorNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        try:
            self.node = nodes.new("ShaderNodeSeparateColor")
            self.input_key = self.get_node_input_key(self.node, "Color")
            self.output_red_key = self.get_node_output_key(self.node, "Red")
            self.output_green_key = self.get_node_output_key(self.node, "Green")
            self.output_blue_key = self.get_node_output_key(self.node, "Blue")
        except RuntimeError:
            self.node = nodes.new("ShaderNodeSeparateRGB")
            self.input_key = self.get_node_input_key(self.node, "Image")
            self.output_red_key = self.get_node_output_key(self.node, "R")
            self.output_green_key = self.get_node_output_key(self.node, "G")
            self.output_blue_key = self.get_node_output_key(self.node, "B")

    def get_input(self):
        return self.node.inputs[self.input_key]

    def get_output_red(self):
        return self.node.outputs[self.output_red_key]

    def get_output_green(self):
        return self.node.outputs[self.output_green_key]

    def get_output_blue(self):
        return self.node.outputs[self.output_blue_key]


class VertexColorNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes, layer_name):
        try:
            self.node = nodes.new("ShaderNodeVertexColor")
            self.node.layer_name = layer_name
        except RuntimeError:
            self.node = nodes.new("ShaderNodeAttribute")
            self.node.attribute_name = layer_name
        self.output_key = self.get_node_output_key(self.node, "Color")

    def get_output(self):
        return self.node.outputs[self.output_key]


class TexImageNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        self.node = nodes.new("ShaderNodeTexImage")
        self.output_key = self.get_node_output_key(self.node, "Color")

    def get_output(self):
        return self.node.outputs[self.output_key]


class VolumeAbsorptionNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        self.node = nodes.new("ShaderNodeVolumeAbsorption")
        self.input_color_key = self.get_node_input_key(self.node, "Color")
        self.input_density_key = self.get_node_input_key(self.node, "Density")
        self.output_key = self.get_node_output_key(self.node, "Volume")

    def get_input_color(self):
        return self.node.inputs[self.input_color_key]

    def get_input_density(self):
        return self.node.inputs[self.input_density_key]

    def get_output(self):
        return self.node.outputs[self.output_key]


class VolumeScatterNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        self.node = nodes.new("ShaderNodeVolumeScatter")
        self.input_color_key = self.get_node_input_key(self.node, "Color")
        self.input_density_key = self.get_node_input_key(self.node, "Density")
        self.input_anisotropy_key = self.get_node_input_key(self.node, "Anisotropy")
        self.output_key = self.get_node_output_key(self.node, "Volume")

    def get_input_color(self):
        return self.node.inputs[self.input_color_key]

    def get_input_density(self):
        return self.node.inputs[self.input_density_key]

    def get_input_anisotropy(self):
        return self.node.inputs[self.input_anisotropy_key]

    def get_output(self):
        return self.node.outputs[self.output_key]


class EmissionNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        self.node = nodes.new("ShaderNodeEmission")
        self.input_color_key = self.get_node_input_key(self.node, "Color")
        self.input_strength_key = self.get_node_input_key(self.node, "Strength")
        self.output_key = self.get_node_output_key(self.node, "Emission")

    def get_input_color(self):
        return self.node.inputs[self.input_color_key]

    def get_input_strength(self):
        return self.node.inputs[self.input_strength_key]

    def get_output(self):
        return self.node.outputs[self.output_key]


class MaterialOutputNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        try:
            self.node = nodes[bpy.app.translations.pgettext("Material Output")]
        except RuntimeError:
            for node in nodes:
                if node.bl_idname == "ShaderNodeOutputMaterial":
                    self.node = node
                    break
        self.input_volume_key = self.get_node_input_key(self.node, "Volume")

    def get_input_volume(self):
        return self.node.inputs[self.input_volume_key]


class PrincipledBSDFNodeProxy(ShaderNodeProxy):
    def __init__(self, nodes):
        try:
            self.node = nodes[bpy.app.translations.pgettext("Principled BSDF")]
        except RuntimeError:
            for node in nodes:
                if node.type == "BSDF_PRINCIPLED" or node.bl_idname == "ShaderNodeBsdfPrincipled":
                    self.node = node
                    break
        self.input_roughness_key = self.get_node_input_key(self.node, "Roughness")
        self.input_metallic_key = self.get_node_input_key(self.node, "Metallic")
        self.input_ior_key = self.get_node_input_key(self.node, "IOR")
        self.input_emission_strength_key = self.get_node_input_key(self.node, "Emission Strength")
        self.input_base_color_key = self.get_node_input_key(self.node, "Base Color")
        self.input_emission_color_key = self.get_node_input_key(self.node, "Emission Color", ["Emission"])
        self.input_transmission_weight_key = self.get_node_input_key(self.node, "Transmission Weight", ["Transmission"])

    def get_input_roughness(self):
        return self.node.inputs[self.input_roughness_key]

    def get_input_metallic(self):
        return self.node.inputs[self.input_metallic_key]

    def get_input_ior(self):
        return self.node.inputs[self.input_ior_key]

    def get_input_emission_strength(self):
        if self.input_emission_strength_key is not None:
            return self.node.inputs[self.input_emission_strength_key]
        else:
            return None

    def set_input_emission_strength_default_value(self, value):
        if self.input_emission_strength_key is not None:
            self.node.inputs[self.input_emission_strength_key].default_value = value

    def get_input_base_color(self):
        return self.node.inputs[self.input_base_color_key]

    def get_input_emission_color(self):
        return self.node.inputs[self.input_emission_color_key]

    def get_input_transmission_weight(self):
        return self.node.inputs[self.input_transmission_weight_key]


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
            ("VERTEX_COLOR", "Vertex Color", "The color palette will be imported and assigned to face "
             + "vertex colors. A simple material is added using the vertex colors as 'Base Color'."),
            ("MAT_PER_COLOR", "Material Per Color", "A material is added per color in the color palette and assigned "
             + "to the faces material index."),
            ("MAT_AS_TEX", "Materials As Texture", "The color palette is created as a 256x1 texture. A simple "
             + "material is added using this texture."),
            ("TEXTURED_MODEL", "Textured Models (UV unwrap)", "Each model is assigned a material and texture with "
             + "UV unwrap. Automatically locks Greedy meshing mode."),
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

    def create_materials_vertex_colors(self, collection_name: str, _: VoxModel):
        vertex_color_mat = bpy.data.materials.new(name=collection_name + " Material")
        vertex_color_mat.use_nodes = True
        nodes = vertex_color_mat.node_tree.nodes
        links = vertex_color_mat.node_tree.links
        bdsf_node = PrincipledBSDFNodeProxy(nodes)
        vertex_color_node = VertexColorNodeProxy(nodes, "Col")
        if self.import_material_props:
            vertex_color_material_node = VertexColorNodeProxy(nodes, "Mat")
            separate_rgb_node = SeparateColorNodeProxy(nodes)
            links.new(vertex_color_material_node.get_output(), separate_rgb_node.get_input())
            links.new(separate_rgb_node.get_output_red(), bdsf_node.get_input_roughness())
            links.new(separate_rgb_node.get_output_green(), bdsf_node.get_input_metallic())
            links.new(separate_rgb_node.get_output_blue(), bdsf_node.get_input_ior())
            bdsf_node.set_input_emission_strength_default_value(0.0)
            links.new(vertex_color_node.get_output(), bdsf_node.get_input_emission_color())
        links.new(vertex_color_node.get_output(), bdsf_node.get_input_base_color())
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
                bdsf_node = PrincipledBSDFNodeProxy(nodes)
                mat_output_node = MaterialOutputNodeProxy(nodes)
                color = model.get_color(color_index)
                bdsf_node.get_input_base_color().default_value = color
                if self.import_material_props:
                    bdsf_node.get_input_roughness().default_value = material.roughness
                    bdsf_node.get_input_metallic().default_value = material.metallic
                    bdsf_node.get_input_ior().default_value = material.ior
                    bdsf_node.set_input_emission_strength_default_value(0.0)
                    bdsf_node.get_input_emission_color().default_value = color
                    if material.type == VoxMaterial.TYPE_EMIT:
                        bdsf_node.set_input_emission_strength_default_value(material.emission)
                    elif material.type in [VoxMaterial.TYPE_MEDIA, VoxMaterial.TYPE_GLASS, VoxMaterial.TYPE_BLEND]:
                        # bdsf_node.get_input_base_color().default_value = (1, 1, 1, 1)
                        bdsf_node.get_input_transmission_weight().default_value = 1.0
                        if material.media_type == VoxMaterial.MEDIA_TYPE_ABSORB:
                            absorb_node = VolumeAbsorptionNodeProxy(nodes)
                            absorb_node.get_input_color().default_value = color
                            absorb_node.get_input_density().default_value = material.density
                            links.new(absorb_node.get_output(), mat_output_node.get_input_volume())
                        elif (material.media_type == VoxMaterial.MEDIA_TYPE_SCATTER
                              or material.media_type == VoxMaterial.MEDIA_TYPE_SSS):  # TODO: own SSS
                            scatter_node = VolumeScatterNodeProxy(nodes)
                            scatter_node.get_input_color().default_value = color
                            scatter_node.get_input_density().default_value = material.density
                            scatter_node.get_input_anisotropy().default_value = material.phase
                            links.new(scatter_node.get_output(), mat_output_node.get_input_volume())
                        elif material.media_type == VoxMaterial.MEDIA_TYPE_EMIT:
                            emission_node = EmissionNodeProxy(nodes)
                            emission_node.get_input_color().default_value = color
                            emission_node.get_input_strength().default_value = material.density
                            links.new(emission_node.get_output(), mat_output_node.get_input_volume())
                materials.append(mat)
        return materials

    def create_materials_as_textures(self, collection_name: str, model: VoxModel):
        color_texture = bpy.data.images.new(collection_name + " Color Texture", width=256, height=1)
        for color_index in range(len(model.color_palette)):
            color = model.get_color(color_index)
            pixel_index = color_index * 4
            color_texture.pixels[pixel_index:pixel_index + 4] = color
        mat = bpy.data.materials.new(name=collection_name + " Material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bdsf_node = PrincipledBSDFNodeProxy(nodes)
        color_texture_node = TexImageNodeProxy(nodes)
        color_texture_node.node.image = color_texture
        color_texture_node.node.interpolation = "Closest"
        links.new(color_texture_node.get_output(), bdsf_node.get_input_base_color())
        if self.import_material_props:
            links.new(color_texture_node.get_output(), bdsf_node.get_input_emission_color())
            bdsf_node.set_input_emission_strength_default_value(0.0)
            mat_texture = bpy.data.images.new(collection_name + " Material Texture", width=256, height=1)
            mat_texture.colorspace_settings.name = "Non-Color"
            for color_index in range(len(model.color_palette)):
                material = model.materials[color_index]
                pixel_index = color_index * 4
                mat_texture.pixels[pixel_index] = material.roughness
                mat_texture.pixels[pixel_index + 1] = material.metallic
                mat_texture.pixels[pixel_index + 2] = material.ior
                mat_texture.pixels[pixel_index + 3] = 1.0
            mat_texture_node = TexImageNodeProxy(nodes)
            mat_texture_node.node.image = mat_texture
            mat_texture_node.node.interpolation = "Closest"
            separate_rgb_node = SeparateColorNodeProxy(nodes)
            links.new(mat_texture_node.get_output(), separate_rgb_node.get_input())
            links.new(separate_rgb_node.get_output_red(), bdsf_node.get_input_roughness())
            links.new(separate_rgb_node.get_output_green(), bdsf_node.get_input_metallic())
            links.new(separate_rgb_node.get_output_blue(), bdsf_node.get_input_ior())
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
        if DEBUG_OUTPUT:
            print('[DEBUG] took %s sec' % (time.time() - timer_start))
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
                                x + 0.5 - math.floor(mesh.grid.width * 0.5),
                                y + 0.5 - math.floor(mesh.grid.depth * 0.5),
                                z + 0.5 - math.floor(mesh.grid.height * 0.5)
                            ))
                            combined_mesh.voxels.add(int(target_position[0] - 0.5), int(target_position[1] - 0.5),
                                                     int(target_position[2] - 0.5), value)
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
                        uv_layer = new_mesh.uv_layers.new(name="UVMap")
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
                        quads = SimpleQuadsMeshing.generate_mesh(mesh.voxels, outside, False)
                    elif self.meshing_type == "SIMPLE_CUBES":
                        if self.voxel_hull:
                            mesh.grid.reduce_voxel_grid_to_hull(mesh.voxels, outside)
                        quads = SimpleQuadsMeshing.generate_mesh(mesh.voxels, outside, True)
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
                            self.get_or_create_vertex(vertices_map, vertices, quad.p2, mesh),
                            self.get_or_create_vertex(vertices_map, vertices, quad.p3, mesh),
                            self.get_or_create_vertex(vertices_map, vertices, quad.p4, mesh)
                        ]
                        for quad in quads
                    ]
                    new_mesh = bpy.data.meshes.new("mesh_%s" % mesh_index)
                    new_mesh.from_pydata(vertices, [], faces)
                    new_mesh.update()
                    uv_layer = new_mesh.uv_layers.new(name="UVMap")
                    if DEBUG_OUTPUT:
                        print('[DEBUG] took %s sec' % (time.time() - timer_start))
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
                        quad_placements: List[Tuple[int, int]] = []
                        if DEBUG_OUTPUT:
                            print('[DEBUG] finding texture space for', len(quads), 'quads')
                        for quad in quads:
                            quad_placement = packer.try_pack(quad.width, quad.height)
                            if quad_placement is None:
                                self.report({"WARNING"}, "Failed to unwrap all mesh faces onto texture")
                                return {"CANCELLED"}
                            quad_placements.append((quad_placement[0], quad_placement[1]))
                        pixel_size = packer.actual_packing_area_width * packer.actual_packing_area_height
                        texture_pixels = [
                            [0.0, 0.0, 0.0, 1.0] * pixel_size
                        ]
                        if self.import_material_props:
                            texture_pixels.append([0.0, 0.0, 0.0, 1.0] * pixel_size)  # metal
                            texture_pixels.append([0.0, 0.0, 0.0, 1.0] * pixel_size)  # roughness
                            texture_pixels.append([0.0, 0.0, 0.0, 1.0] * pixel_size)  # emission
                        uv_x_step = 1.0 / packer.actual_packing_area_width
                        uv_y_step = 1.0 / packer.actual_packing_area_height
                        for i in range(len(quads)):
                            quad = quads[i]
                            x, y = quad_placements[i]
                            vertex_indices = quad.vertex_indices
                            vertex_offset = i * 4
                            uv_x = x * uv_x_step
                            uv_y = y * uv_y_step
                            uv_right = (x + quad.width) * uv_x_step
                            uv_top = (y + quad.height) * uv_y_step
                            uv_layer.data[vertex_offset + vertex_indices[0]].uv = [uv_x, uv_top]
                            uv_layer.data[vertex_offset + vertex_indices[1]].uv = [uv_right, uv_top]
                            uv_layer.data[vertex_offset + vertex_indices[2]].uv = [uv_x, uv_y]
                            uv_layer.data[vertex_offset + vertex_indices[3]].uv = [uv_right, uv_y]
                            for iy in range(0, quad.height):
                                pixel_offset_iy = (y + iy) * packer.actual_packing_area_width
                                for ix in range(0, quad.width):
                                    if quad.normal[0] != 0:
                                        # y, z
                                        vx = quad[vertex_indices[0]][0] - (0 if quad.normal[0] < 0 else 1)
                                        vy = quad[vertex_indices[0]][1] + (ix if quad.normal[0] > 0 else -ix - 1)
                                        vz = quad[vertex_indices[2]][2] + iy
                                        color_index = mesh.get_voxel_color_index(vx, vy, vz)
                                    elif quad.normal[1] != 0:
                                        # x, z
                                        vx = quad[vertex_indices[0]][0] + (ix if quad.normal[1] < 0 else -ix - 1)
                                        vy = quad[vertex_indices[0]][1] - (0 if quad.normal[1] < 0 else 1)
                                        vz = quad[vertex_indices[2]][2] + iy
                                        color_index = mesh.get_voxel_color_index(vx, vy, vz)
                                    else:
                                        # x, y
                                        vx = quad[vertex_indices[0]][0] + (ix if quad.normal[2] > 0 else -ix - 1)
                                        vy = quad[vertex_indices[2]][1] + iy
                                        vz = quad[vertex_indices[0]][2] - (0 if quad.normal[2] < 0 else 1)
                                        color_index = mesh.get_voxel_color_index(vx, vy, vz)
                                    color = result.get_color(color_index)
                                    color_material = result.materials[color_index]
                                    pindex = (pixel_offset_iy + x + ix) * 4
                                    texture_pixels[0][pindex:pindex + 4] = color
                                    if self.import_material_props:
                                        texture_pixels[1][pindex:pindex + 3] = [color_material.metallic] * 3
                                        texture_pixels[2][pindex:pindex + 3] = [color_material.emission] * 3
                                        texture_pixels[3][pindex:pindex + 3] = [color_material.roughness] * 3
                        # Setup model material
                        closest_interpolation_key = "Closest"
                        color_texture = bpy.data.images.new(collection_name + " Color Texture",
                                                            width=packer.actual_packing_area_width,
                                                            height=packer.actual_packing_area_height)
                        color_texture.pixels = texture_pixels[0]
                        mat = bpy.data.materials.new(name="mesh_%s Material" % mesh_index)
                        mat.use_nodes = True
                        nodes = mat.node_tree.nodes
                        links = mat.node_tree.links
                        bdsf_node = PrincipledBSDFNodeProxy(nodes)
                        color_texture_node = TexImageNodeProxy(nodes)
                        color_texture_node.node.image = color_texture
                        color_texture_node.node.interpolation = closest_interpolation_key
                        links.new(color_texture_node.get_output(), bdsf_node.get_input_base_color())
                        if self.import_material_props:
                            metal_mask_texture = bpy.data.images.new(collection_name + " Metal Mask Texture",
                                                                     width=packer.actual_packing_area_width,
                                                                     height=packer.actual_packing_area_height)
                            metal_mask_texture.pixels = texture_pixels[1]
                            metal_mask_texture_node = TexImageNodeProxy(nodes)
                            metal_mask_texture_node.node.image = metal_mask_texture
                            metal_mask_texture_node.node.interpolation = closest_interpolation_key
                            links.new(metal_mask_texture_node.get_output(), bdsf_node.get_input_metallic())
                            roughness_mask_texture = bpy.data.images.new(collection_name + " Roughness Mask Texture",
                                                                         width=packer.actual_packing_area_width,
                                                                         height=packer.actual_packing_area_height)
                            roughness_mask_texture.pixels = texture_pixels[2]
                            roughness_mask_texture_node = TexImageNodeProxy(nodes)
                            roughness_mask_texture_node.node.image = roughness_mask_texture
                            roughness_mask_texture_node.node.interpolation = closest_interpolation_key
                            links.new(roughness_mask_texture_node.get_output(), bdsf_node.get_input_roughness())
                            emission_mask_texture = bpy.data.images.new(collection_name + " Emission Mask Texture",
                                                                        width=packer.actual_packing_area_width,
                                                                        height=packer.actual_packing_area_height)
                            emission_mask_texture.pixels = texture_pixels[3]
                            emission_mask_texture_node = TexImageNodeProxy(nodes)
                            emission_mask_texture_node.node.image = emission_mask_texture
                            emission_mask_texture_node.node.interpolation = closest_interpolation_key
                            if bdsf_node.get_input_emission_strength() is not None:
                                links.new(emission_mask_texture_node.get_output(),
                                          bdsf_node.get_input_emission_strength())
                            links.new(color_texture_node.get_output(), bdsf_node.get_input_emission_color())
                        new_mesh.materials.append(mat)
                    elif self.material_mode == "MAT_PER_COLOR":
                        for i, face in enumerate(new_mesh.polygons):
                            face.material_index = color_index_material_map[quads[i].color]
                    new_object = bpy.data.objects.new('import_tmp_model', new_mesh)
                    generated_mesh_models.append(new_object)
                    if DEBUG_OUTPUT:
                        print('[DEBUG] took %s sec' % (time.time() - timer_start))
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
            if DEBUG_OUTPUT:
                print('[DEBUG] took %s sec' % (time.time() - timer_start))

        if DEBUG_OUTPUT:
            print('[DEBUG] total time %s sec' % (time.time() - total_timer_start))
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
                        translation = next_node.get_transform_translation(mesh_frame, 1)
                        rotation = next_node.get_transform_rotation(mesh_frame)
                        matrix_world = translation @ rotation @ matrix_world
                if model_id not in result:
                    result[model_id] = []
                result[model_id].append(matrix_world)
        for child_id in node.child_ids:
            self.get_model_world_transforms_recursive(nodes, nodes[child_id], path + [node.node_id], result)

    def get_vertex_pos(self, p: Tuple[float, float, float], grid: VoxelGrid) -> Tuple[float, float, float]:
        if self.join_models:
            return p[0] * self.voxel_size, p[1] * self.voxel_size, p[2] * self.voxel_size
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
            ImportVOX.post_process_model(model)
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
        mesh.voxel_data = bytearray(num_voxels * 4)
        f.readinto(mesh.voxel_data)

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
        material_id = ImportVOX.read_int32(f)
        material_id = material_id & 0xff  # incoming material 256 is material 0
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
        model.color_palette = list(struct.unpack('%sI' % 256, f.read(256 * 4)))

    @staticmethod
    def read_imap_chunk(f: IO, model: VoxModel):
        model.index_map = struct.unpack('%sB' % 256, f.read(256))  # imap_data

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

    def post_process_model(model: VoxModel):
        # To support index-level assumptions (eg. artists using top 16 colors for color/palette cycling,
        # other ranges for emissive etc), we must ensure the order of colors that the artist sees in the
        # magicavoxel tool matches the actual index we'll end up using here. Unfortunately, magicavoxel
        # does an unexpected thing when remapping colors in the editor using ctrl+drag within the palette.
        # Instead of remapping all indices in all models, it just keeps track of a display index to actual
        # palette map and uses that to show reordered colors in the palette window. This is how that
        # map works:
        #   displaycolor[k] = paletteColor[index_map[k]]
        # To ensure our indices are in the same order as displayed by magicavoxel within the palette
        # window, we apply the mapping from the IMAP chunk both to the color palette and indices within each
        # voxel model.
        if model.index_map:
            # the imap chunk maps from display index to actual index.
            # generate an inverse index map (maps from actual index to display index)
            index_map_inverse = bytearray(256)
            for i in range(256):
                index_map_inverse[model.index_map[i]] = i

            # reorder colors in the palette so the palette contains colors in display order
            old_palette = model.color_palette.copy()
            for i in range(256):
                remapped_index = (model.index_map[i] + 255) & 0xff
                model.color_palette[i] = old_palette[remapped_index]

            # reorder materials
            old_materials = model.materials.copy()
            for i in range(256):
                remapped_i = (i + 255) & 0xff
                remapped_index = model.index_map[remapped_i]
                model.materials[i] = old_materials[remapped_index]

            # ensure that all models are remapped so they are using display order palette indices.
            for mesh in model.meshes:
                for i in range(3, len(mesh.voxel_data), 4):
                    mesh.voxel_data[i] = 1 + index_map_inverse[mesh.voxel_data[i]]

            model.index_map = None  # Clean index map since it has just been applied

        # Process mesh used color indices and octrees
        for mesh in model.meshes:
            for i in range(0, len(mesh.voxel_data), 4):
                mesh.voxels.add(int(mesh.voxel_data[i]), int(mesh.voxel_data[i + 1]),
                                int(mesh.voxel_data[i + 2]), int(mesh.voxel_data[i + 3]))
            mesh.used_color_indices.update({int(mesh.voxel_data[i]) for i in range(3, len(mesh.voxel_data), 4)})


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
        layout.prop(operator, "join_models")

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
