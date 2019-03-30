#pylint: disable=import-error
import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, IntProperty
from bpy_extras.object_utils import AddObjectHelper
#pylint: enable=import-error

#region     /# Operators #/
class BNR_QIK_OT_add_simple_ik(Operator, AddObjectHelper):
    bl_idname = "bnr_qik.add_simple_ik"
    bl_label = "Add Simple IK"
    bl_options = { "REGISTER", "UNDO", "PRESET" }

    ik_size : FloatProperty(name="IK Size", default=0.0)
    chain_length : IntProperty(name="Chain Length", default=2, min=0)
    use_tail : BoolProperty(name="Use Tail", default=False)
    use_rotation : BoolProperty(name="Copy Rotation", default=True)
    pole_target : IntProperty(name="Pole Target", default=0, min=0)
    pole_angle : FloatProperty(name="Pole Angle", default=-3.14159, min=-3.14159, max=3.14159, subtype="ANGLE", step=15)
    pole_distance : FloatProperty(name="Pole Distance", default=2, step=0.10)

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
        print("testies")
        
        arm = context.object
        cur_mode = context.object.mode
        if arm.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        fk_bone = context.selected_bones[0]
        ikh = arm.data.edit_bones.new("IK." + fk_bone.name)
        ikh.head = fk_bone.head
        ikh.tail = (fk_bone.head[0], abs(fk_bone.head[1] - fk_bone.tail[1]) + self.ik_size, fk_bone.head[2])

        parent_list = fk_bone.parent_recursive
        par_length = len(parent_list)
        if self.pole_target > par_length:
            self.pole_target = par_length-1
        if self.chain_length > par_length:
            self.chain_length = par_length-1
        fk_secondary = parent_list[self.pole_target]
        ikp = arm.data.edit_bones.new("IK.Pole." + fk_secondary.name)
        x = fk_secondary.head[0]
        y = fk_secondary.head[1]
        z = fk_secondary.head[2]
        ikp.head = [x, y - self.pole_distance, z]
        ikp.tail = [x, y - self.pole_distance, z + 0.25]

        ##POSE MODE STUFF
        bpy.ops.object.mode_set(mode="POSE")

        fk_bone = context.selected_pose_bones[0]
        ## ADD CONSTRAINTS
        ik_constraint = fk_bone.constraints.new("IK")
        ik_constraint.target = arm
        ik_constraint.subtarget = ikh.name
        ik_constraint.pole_target = arm
        ik_constraint.pole_subtarget = ikp.name
        ik_constraint.chain_count = self.chain_length
        ik_constraint.use_tail = self.use_tail
        ik_constraint.pole_angle = self.pole_angle

        if self.use_rotation:
            cr_constraint = fk_bone.constraints.new("COPY_ROTATION")
            cr_constraint.target = arm
            cr_constraint.subtarget = ikh.name
            cr_constraint.owner_space = "LOCAL_WITH_PARENT"
            cr_constraint.target_space = "LOCAL"

        bpy.ops.object.mode_set(mode=cur_mode)
        return { "FINISHED" }

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "ik_size")
        layout.prop(self, "chain_length")
        layout.prop(self, "use_tail")
        layout.prop(self, "use_rotation")
        layout.prop(self, "pole_target")
        layout.prop(self, "pole_angle")
        layout.prop(self, "pole_distance")
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