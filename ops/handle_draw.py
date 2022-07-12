import bpy
import gpu
from bpy.app.handlers import persistent
from bpy.types import SpaceView3D
from .draw_utils.shader import CameraMotionPath, CameraThumb
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, BoolProperty, EnumProperty

C_HANDLE_CURVE = None
C_HANDLE_CAM_PV = None

C_INST_CURVE = None
C_INST_CAM_PV = None


class CameraPV(PropertyGroup):
    enable: BoolProperty(name="Enable", default=False, options={'HIDDEN'})
    pin: BoolProperty(name="Pin Selected Camera", default=False, description='Pin Selected Camera',
                      update=lambda self, context: setattr(context.scene.camhp_pv, 'pin_cam', context.object),
                      options={'HIDDEN'})
    pin_cam: PointerProperty(name="Pinned Camera", type=bpy.types.Object, description='Pinned Camera')

    show_overlay: BoolProperty(name="Show Overlay", default=False,
                               description='Show Overlay', options={'HIDDEN'})


class pop_cam_panel(bpy.types.Panel):
    """Properties"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'


class CAMHP_PT_pop_cam_pv_panel(pop_cam_panel):
    bl_label = "Preview"
    bl_idname = 'CAMHP_PT_pop_cam_pv_panel'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.active = context.scene.camhp_pv.enable
        layout.prop(context.scene.camhp_pv, 'enable')
        layout.prop(context.scene.camhp_pv, 'pin')
        layout.operator('camhp.pv_snap_shot')
        # layout.prop(context.scene.camhp_pv, 'show_overlay')


class CAMHP_OT_campv_popup(bpy.types.Operator):
    """Preview"""
    bl_idname = "camhp.campv_popup"
    bl_label = "Preview"

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'VIEW_3D'

    def invoke(self, context, event):
        def pop_up(cls, context):
            layout = cls.layout
            layout.popover("CAMHP_PT_pop_cam_pv_panel")

        context.window_manager.popup_menu(pop_up, icon='CAMERA_DATA', title='Preview')

        return {'INTERFACE'}


def clear_handle():
    global C_HANDLE_CURVE, C_HANDLE_CAM_PV
    global C_INST_CURVE, C_INST_CAM_PV

    if C_INST_CURVE:
        try:
            SpaceView3D.draw_handler_remove(C_HANDLE_CURVE, 'WINDOW')
        except Exception:
            print("Handle C_HANDLE_CURVE already removed")

        C_HANDLE_CURVE = None
        C_INST_CURVE = None

    if C_INST_CAM_PV and not bpy.context.scene.camhp_pv.pin:
        try:
            SpaceView3D.draw_handler_remove(C_HANDLE_CAM_PV, 'WINDOW')
        except Exception:
            print("Handle C_HANDLE_CAM_PV already removed")

        C_HANDLE_CAM_PV = None
        C_INST_CAM_PV = None


def is_select_obj(context):
    return context and context.object and (
            context.object.type in {'CAMERA', 'EMPTY'})


@persistent
def draw_handle(scene, depsgraph):
    global C_HANDLE_CURVE, C_HANDLE_CAM_PV
    global C_INST_CURVE, C_INST_CAM_PV

    context = bpy.context

    if is_select_obj(context):

        if C_HANDLE_CURVE is None:
            C_INST_CURVE = CameraMotionPath(context, depsgraph)
            C_HANDLE_CURVE = SpaceView3D.draw_handler_add(C_INST_CURVE, (context,), 'WINDOW', 'POST_VIEW')

        if C_HANDLE_CAM_PV is None:
            C_INST_CAM_PV = CameraThumb(context, depsgraph)
            C_HANDLE_CAM_PV = SpaceView3D.draw_handler_add(C_INST_CAM_PV, (context,), 'WINDOW', 'POST_PIXEL')

    else:
        clear_handle()


class CAMHP_OT_pv_snap_shot(bpy.types.Operator):
    """Snap Shot"""
    bl_idname = "camhp.pv_snap_shot"
    bl_label = "Snap Shot"

    @classmethod
    def poll(cls, context):
        return C_INST_CAM_PV is not None

    def execute(self, context):

        cam = C_INST_CAM_PV.cam
        self.width = C_INST_CAM_PV.width
        self.height = C_INST_CAM_PV.height
        buffer = C_INST_CAM_PV.buffer

        if buffer:
            context.scene.camhp_snap_shot_image = True

            if f'_SnapShot_{cam.name}' in bpy.data.images:
                img = bpy.data.images[f'_SnapShot_{cam.name}']
            else:
                img = bpy.data.images.new(name=f'_SnapShot_{cam.name}',
                                          width=self.width,
                                          height=self.height)

            img.scale(self.width, self.height)
            img.pixels.foreach_set(buffer)

            bpy.ops.render.view_show('INVOKE_DEFAULT')
            if context.window.screen.areas[0].type == 'IMAGE_EDITOR':
                # set img as area active image
                context.window.screen.areas[0].spaces[0].image = img

        context.scene.camhp_snap_shot_image = False

        return {'FINISHED'}


def register():
    bpy.utils.register_class(CameraPV)
    bpy.utils.register_class(CAMHP_PT_pop_cam_pv_panel)
    bpy.utils.register_class(CAMHP_OT_campv_popup)
    bpy.utils.register_class(CAMHP_OT_pv_snap_shot)

    bpy.types.Scene.camhp_pv = PointerProperty(type=CameraPV)
    bpy.types.Scene.camhp_snap_shot_image = BoolProperty(name='Snap Shot', default=False)

    bpy.app.handlers.depsgraph_update_post.append(draw_handle)


def unregister():
    clear_handle()
    bpy.app.handlers.depsgraph_update_post.remove(draw_handle)

    del bpy.types.Scene.camhp_pv
    del bpy.types.Scene.camhp_snap_shot_image

    bpy.utils.unregister_class(CAMHP_PT_pop_cam_pv_panel)
    bpy.utils.unregister_class(CAMHP_OT_pv_snap_shot)
    bpy.utils.unregister_class(CAMHP_OT_campv_popup)
    bpy.utils.unregister_class(CameraPV)
