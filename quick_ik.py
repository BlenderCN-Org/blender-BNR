##TODO:// Add Color groups automatically
##TODO:// Use enumerator property instead of int for target
##TODO:// Add direction picking for IK handle

#pylint: disable=import-error
import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy_extras.object_utils import AddObjectHelper
import bmesh
import mathutils
#pylint: enable=import-error
import math

symmetry_map = {
    "L" : "R",
    "l" : "r",
    "LEFT" : "RIGHT",
    "Left" : "Right"
}

def create_widget(name, shape_name="CIRCLE", rotation_offset=[0, 0, 0], size=1.0):
    scene_collection = bpy.context.scene.collection
    wgt_col_name = "QIK-WIDGETS"
    wgt_collection = None

    for c in scene_collection.children:
        if wgt_col_name == c.name:
            wgt_collection = c
    
    if not wgt_collection:
        wgt_collection = bpy.data.collections.new(wgt_col_name)
        scene_collection.children.link(wgt_collection)
        
    wgt_obj = None

    if shape_name == "CIRCLE":
        #region WIDGET_CIRCLE
        mesh = bpy.data.meshes.new(name)
        wgt_obj = bpy.data.objects.new(name, mesh)

        bm = bmesh.new()
        bmesh.ops.create_circle(
            bm, 
            radius=size, 
            segments=32)

        bm.to_mesh(mesh)
        bm.free()
        #endregion WIDGET_CIRCLE
    elif shape_name == "POLE_TARGET":
        #region     WIDGET_POLE_TARGET

        # Make a new BMesh
        bm = bmesh.new()

        # Add a circle XXX, should return all geometry created, not just verts.
        bmesh.ops.create_circle(
            bm,
            cap_ends=False,
            radius=1,
            segments=32)
            
        ret = bmesh.ops.duplicate(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
        geom_dupe = ret["geom"]
        verts_dupe = [ele for ele in geom_dupe if isinstance(ele, bmesh.types.BMVert)]
        del ret

        # position the new link
        bmesh.ops.rotate(
            bm,
            verts=verts_dupe,
            cent=(0.0, 0.0, 0.0),
            matrix=mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Y'))
            
        ret = bmesh.ops.duplicate(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:])
        geom_dupe = ret["geom"]
        verts_dupe = [ele for ele in geom_dupe if isinstance(ele, bmesh.types.BMVert)]
        del ret

        bmesh.ops.rotate(
            bm,
            verts=verts_dupe,
            cent=(0.0, 0.0, 0.0),
            matrix=mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Y'))

        bmesh.ops.rotate(
            bm,
            verts=verts_dupe,
            cent=(0.0, 0.0, 0.0),
            matrix=mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Z'))

        bmesh.ops.remove_doubles(
            bm,
            verts=bm.verts[:],
            dist=0.01)

        # Finish up, write the bmesh into a new mesh
        me = bpy.data.meshes.new("Mesh")
        bm.to_mesh(me)
        bm.free()

        wgt_obj = bpy.data.objects.new(name, me)
        #endregion  WIDGET_POLE_TARGET

    wgt_collection.objects.link(wgt_obj)
    wgt_collection.hide_select = True
    wgt_collection.hide_render = True
    wgt_collection.hide_viewport = True
    
    return wgt_obj



def create_bone_group(name="IK", color_set="THEME09"):
    bone_groups = bpy.context.object.pose.bone_groups
    for bg in bone_groups:
        if name == bg.name:
            return bg

    bg = bone_groups.new(name=name)
    bg.color_set = color_set

    return bg

def get_symmetrical_name(name):
    base_name = name.split(".")
    extension = base_name.pop()
    for key, value in symmetry_map.items():
        if extension == key:
            base_name.append(value)
            return ".".join(base_name)
        elif extension == value:
            base_name.append(key)
            return ".".join(base_name)  

    return None

def create_simple_limb_ik(self, arm, fk_ik, fk_pt, pole_angle):
    context = bpy.context

    cur_mode = context.object.mode
    if arm.mode != "EDIT":
        bpy.ops.object.mode_set(mode="EDIT")

    ikh = arm.data.edit_bones.new("IK." + fk_ik.name)
    x = fk_ik.head[0]
    y = fk_ik.head[1]
    z = fk_ik.head[2]
    ikh.head = fk_ik.head
    ikh.tail = (x, abs(y - fk_ik.tail[1]/2) * self.ik_size, z)

    parent_list = fk_ik.parent_recursive
    par_length = len(parent_list)
    if self.pole_target >= par_length:
        self.pole_target = par_length-1
    if self.chain_length > par_length:
        self.chain_length = par_length

    ikp = arm.data.edit_bones.new("IK.PoleTarget." + fk_pt.name)
    x = fk_pt.head[0]
    y = fk_pt.head[1]
    z = fk_pt.head[2]
    ikp.head = [x, y - self.pole_distance, z]
    ikp.tail = [x, y - self.pole_distance, z + 0.25]

    if self.pole_parented:
        ikp.parent = ikh

    ##POSE MODE STUFF
    bpy.ops.object.mode_set(mode="POSE")
    
    #Create IK group
    IK_bone_group = create_bone_group()
    #Set IK bones to group IK
    arm.pose.bones[ikh.name].bone_group = IK_bone_group
    arm.pose.bones[ikp.name].bone_group = IK_bone_group
    fk_ik_pose = arm.pose.bones[fk_ik.name]

    #region     /# ADD CONSTRAINTS #/
    #Inverse Kinematics
    ik_constraint = fk_ik_pose.constraints.new("IK")
    ik_constraint.target = arm
    ik_constraint.subtarget = ikh.name
    ik_constraint.pole_target = arm
    ik_constraint.pole_subtarget = ikp.name
    ik_constraint.chain_count = self.chain_length
    ik_constraint.use_tail = self.use_tail
    ik_constraint.pole_angle = pole_angle
    #Copy Rotation
    if self.use_rotation:
        cr_constraint = fk_ik_pose.constraints.new("COPY_ROTATION")
        cr_constraint.target = arm
        cr_constraint.subtarget = ikh.name
        cr_constraint.owner_space = "LOCAL_WITH_PARENT"
        cr_constraint.target_space = "LOCAL"
    #endregion  /# ADD CONSTRAINTS #/

    #region / ADD CUSTOM SHAPES /
    ## IK HANDLE
    pose_bone = arm.pose.bones[ikh.name]
    widget = create_widget(pose_bone.name)
    pose_bone.custom_shape = widget

    ## IK POLE TARGET
    pose_bone = arm.pose.bones[ikp.name]
    widget = create_widget(pose_bone.name, shape_name="POLE_TARGET")
    pose_bone.custom_shape = widget
    #endregion / ADD CUSTOM SHAPES /

    bpy.ops.object.mode_set(mode=cur_mode)

#region     /# Operators #/
class BNR_QIK_OT_add_simple_ik(Operator, AddObjectHelper):
    bl_idname = "bnr_qik.add_simple_ik"
    bl_label = "Add Simple IK"
    bl_options = { "REGISTER", "UNDO", "PRESET" }

    ik_size : FloatProperty(name="IK Size", default=1.0)
    chain_length : IntProperty(name="Chain Length", default=2, min=0)
    use_tail : BoolProperty(name="Use Tail", default=False)
    use_rotation : BoolProperty(name="Copy Rotation", default=True)
    pole_target : IntProperty(name="Pole Target", default=0, min=0, subtype="NONE")
    pole_target_name : StringProperty(name="Pole Target Name", default="")
    pole_angle : FloatProperty(name="Pole Angle", default=-3.14159, min=-3.14159, max=3.14159, subtype="ANGLE")
    pole_distance : FloatProperty(name="Pole Distance", default=2, step=0.10)
    pole_parented : BoolProperty(name="Parented", default=True)
    symmetrize : BoolProperty(name="Symmetrize", default=True)

    @classmethod
    def poll(self, context):
        if context.selected_bones != None:
            if len(context.selected_bones) > 0:
                if context.selected_bones[0].parent != None:
                    return True
        if context.selected_pose_bones != None:
            if len(context.selected_pose_bones) > 0:
                if context.selected_pose_bones[0].parent != None:
                    return True
        return False

    def execute(self, context):
        arm = context.object

        cur_mode = context.object.mode
        if arm.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
        
        fk_bone = context.selected_bones[0]
        parent_list = fk_bone.parent_recursive
        par_length = len(parent_list)
        if self.pole_target >= par_length:
            self.pole_target = par_length-1
        if self.chain_length > par_length:
            self.chain_length = par_length
        fk_secondary = parent_list[self.pole_target]
        self.pole_target_name = fk_secondary.name

        #Set names to variable cus this changes after the function call for some reason
        fk_ik_name = fk_bone.name
        fk_pt_name = fk_secondary.name

        create_simple_limb_ik(self, arm, fk_bone, fk_secondary, self.pole_angle)

        ##Symmetrize selection
        if self.symmetrize:
            ## IK target target bone
            sym_name = get_symmetrical_name(fk_ik_name)
            if sym_name == None:
                self.symmetrize = False
                bpy.ops.object.mode_set(mode=cur_mode)
                return { "FINISHED" }
            if not sym_name in arm.data.edit_bones:
                self.symmetrize = False
                bpy.ops.object.mode_set(mode=cur_mode)
                return { "FINISHED" }
            fk_bone = arm.data.edit_bones[sym_name]
            
            ## Pole target target bone
            sym_name = get_symmetrical_name(fk_pt_name)
            if sym_name == None:
                self.symmetrize = False
                bpy.ops.object.mode_set(mode=cur_mode)
                return { "FINISHED" }
            if not sym_name in arm.data.edit_bones:
                self.symmetrize = False
                bpy.ops.object.mode_set(mode=cur_mode)
                return { "FINISHED" }
            fk_secondary = arm.data.edit_bones[sym_name]
            #1.570795
            pole_angle = ( (-self.pole_angle + 3.14159 * 2) % (3.14159 * 2) ) - 3.14159
            #Create symmetric ik
            create_simple_limb_ik(self, arm, fk_bone, fk_secondary, pole_angle)
        
        bpy.ops.object.mode_set(mode=cur_mode)
        
        return { "FINISHED" }

    def draw(self, context):
        layout = self.layout

        layout.label(text="IK Options")
        layout.prop(self, "ik_size", text="Size")
        layout.prop(self, "chain_length")
        t = layout.row()
        t.prop(self, "use_tail")
        t.prop(self, "use_rotation", text="Copy Rotation")

        layout.label(text="Pole Options")
        t = layout.row()
        t.prop(self, "pole_target", text=self.pole_target_name)
        t.prop(self, "pole_parented", text="Parented")
        layout.prop(self, "pole_angle", text="Angle")
        layout.prop(self, "pole_distance", text="Distance")
        layout.prop(self, "symmetrize")
#endregion  /# Operators #/

class TOOLS_PT_BNR_Quick_IK(Panel):
    bl_label       = "QIK BNR"
    bl_idname      = "TOOLS_PT_BNR_Quick_IK"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'BNR'
    
    
    @classmethod
    def poll(self, context):
        if context.mode == "POSE" or context.mode == "EDIT_ARMATURE":
            return True
        return False
    
    def draw(self, context):
        layout = self.layout
        layout.operator("bnr_qik.add_simple_ik", text="Add Simple Limb IK")

qik_class_list = [
    BNR_QIK_OT_add_simple_ik,
    TOOLS_PT_BNR_Quick_IK
]