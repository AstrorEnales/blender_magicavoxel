if 'bpy' in locals():
    import importlib
    if "blender_magicavoxel" in locals():
        # noinspection PyUnresolvedReferences,PyUnboundLocalVariable
        importlib.reload(blender_magicavoxel)


def register():
    from .blender_magicavoxel import register as _register
    _register()


def unregister():
    from .blender_magicavoxel import unregister as _unregister
    _unregister()


if __name__ == '__main__':
    register()
