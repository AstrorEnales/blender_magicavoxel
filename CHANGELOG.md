# Changelog

## [v1.5.6](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.6)

  * **[fix]** #14 Fix textured models material texture creation
  * **[change]** Compatibility with the blender extensions registry

## [v1.5.5](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.5)

  * **[fix]** #12 Fix and optimize UV unwrap mode

## [v1.5.4](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.4)

  * **[fix]** #11 Fix shader nodes and their inputs/outputs not being found when blender is set to a non-english language

## [v1.5.3](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.3)

  * **[change]** #10 Always add mesh UV layers to prevent lighting issues when exporting to obj and importing in Godot

## [v1.5.2](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.2)

  * **[fix]** Fix CCL optimization

## [v1.5.0](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.5.0)

  * **[feature]** Speedup greedy meshing
  * **[feature]** Add join models option to create a single mesh

## [v1.4.3](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.4.3)

  * **[fix]** Fix missing voxels regression after introducing octrees

## [v1.4.2](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.4.2)

  * **[fix]** Fix BDSF input keys for Blender 4

## [v1.4.1](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.4.1)

  * **[change]** #7 Populate model material slots with defaults before loading
  * **[feature]** #8 Improve performance by moving from sparse array to octree

## [v1.3.0](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.3.0)

  * **[change]** Material modes with additional material properties moved to checkbox
  * **[fix]** Fix small greedy meshing issue
  * **[fix]** Fix material per color mode
  * **[feature]** New material mode "Textured Models (UV unwrap)"
  * **[feature]** Use scene graph name properties for group and model names
  * **[feature]** Basic camera import

## [v1.2.3](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.2.3)

  * **[feature]** Performance improvements

## [v1.2.2](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.2.2)

  * **[change]** Change default voxel size to 0.1 meters
  * **[fix]** Fix face vertex order
  * **[fix]** Fix meshing edge case where the voxel hull splits the grid area
  * **[feature]** #1 Limit material per color creation to only include used colors
  * **[feature]** #1 Load remaining material properties in blender compatible ranges
  * **[feature]** Significantly improve memory footprint using sparse arrays (for unfilled grids)
  * **[feature]** Improve overall import performance

## [v1.2.1](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.2.1)

 * **[fix]** Fix read_dict for python versions < 3.8
 * **[fix]** Fix vertex color materials if ShaderNodeVertexColor does not exist in older blender versions

## [v1.2.0](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.2.0)

  * **[feature]** Implemented different material modes
  * **[change]** Vertex color material mode now automatically assigns a material

## [v1.1.1](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.1.1)

  * **[fix]** Fix transform rotation matrix parsing
  * **[change]** Change default meshing mode to `SIMPLE_QUADS` as it is probably more usable in most circumstances
  * **[feature]** Implemented vertex deduplication without the need for Blender edit mode

## [v1.0.0](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.0.0)

  * Initial commit