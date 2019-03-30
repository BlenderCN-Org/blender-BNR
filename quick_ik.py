##TODO:// Add Color groups automatically
##TODO:// Use enumerator property instead of int for target
##TODO:// Add direction picking for IK handle

#pylint: disable=import-error
import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy_extras.object_utils import AddObjectHelper
#pylint: enable=import-error

symmetry_map = {
    "L" : "R",
    "l" : "r",
    "LEFT" : "RIGHT",
    "Left" : "Right"
}

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
    ikh.tail = (x, abs(y - fk_ik.tail[1]) + self.ik_size, z)

    parent_list = fk_ik.parent_recursive
    par_length = len(parent_list)
    if self.pole_target >= par_length:
        self.pole_target = par_length-1
    if self.chain_length > par_length:
        self.chain_length = par_length

    self.pole_target_name = fk_pt.name
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

    fk_ik_pose = arm.pose.bones[fk_ik.name]
    ## ADD CONSTRAINTS
    ik_constraint = fk_ik_pose.constraints.new("IK")
    ik_constraint.target = arm
    ik_constraint.subtarget = ikh.name
    ik_constraint.pole_target = arm
    ik_constraint.pole_subtarget = ikp.name
    ik_constraint.chain_count = self.chain_length
    ik_constraint.use_tail = self.use_tail
    ik_constraint.pole_angle = pole_angle

    if self.use_rotation:
        cr_constraint = fk_ik_pose.constraints.new("COPY_ROTATION")
        cr_constraint.target = arm
        cr_constraint.subtarget = ikh.name
        cr_constraint.owner_space = "LOCAL_WITH_PARENT"
        cr_constraint.target_space = "LOCAL"

    bpy.ops.object.mode_set(mode=cur_mode)

#region     /# Operators #/
class BNR_QIK_OT_add_simple_ik(Operator, AddObjectHelper):
    bl_idname = "bnr_qik.add_simple_ik"
    bl_label = "Add Simple IK"
    bl_options = { "REGISTER", "UNDO", "PRESET" }

    ik_size : FloatProperty(name="IK Size", default=0.0)
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
    bl_label       = "BNR Quick IK"
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