# Changelog

## [v1.2.4](https://github.com/AstrorEnales/blender_magicavoxel/releases/tag/v1.2.4)

  * **[change]** Material modes with additional material properties moved to checkbox
  * **[fix]** Fix small greedy meshing issue
  * **[fix]** Fix material per color mode
  * **[feature]** New material mode "Textured Models (UV unwrap)"

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