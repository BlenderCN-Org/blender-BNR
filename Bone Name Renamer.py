bl_info = {
    "name": "Bone Name Rangler (BNR)",
    "author": "birdd",
    "version": (1, 0),
    "blender": (2, 75, 0),
    "location": "View3D > Properties > Bone Name Rangler",
    "description": "Set of tools for quickly renaming bones.",
    "warning": "",
    "wiki_url": "",
    "category": "Rigging",
    }

import bpy

print("Loading BNR")

def BNR_import_list(context, filepath, opt_clear):
    f = open(filepath, 'r', encoding='utf-8')
    data = f.read()
    f.close()

    data = data.splitlines()
    
    if opt_clear:
        context.scene.BNR_bone_list.clear()
    for line in data:
        print(line)
        bpy.types.Scene.BNR_bone_list.append(line)
    print(data)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class BoneRenameImportList(Operator, ImportHelper):
    """Opens a .txt file containing a list of bones separated by new lines"""
    bl_idname = "bone_rename.import_list"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Bone List"

    # ImportHelper mixin class uses this
    filename_ext = ".txt"

    filter_glob = StringProperty(
            default="*.txt",
            options={'HIDDEN'},
            maxlen=255,  # Max internal buffer length, longer would be clamped.
            )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    opt_clear = BoolProperty(
            name="Clear Bone List",
            description="Clear the current list of bones on import",
            default=True,
            )

    """type = EnumProperty(
            name="Example Enum",
            description="Choose between two items",
            items=(('OPT_A', "First Option", "Description one"),
                   ('OPT_B', "Second Option", "Description two")),
            default='OPT_A',
            )"""

    def execute(self, context):
        return BNR_import_list(context, self.filepath, self.opt_clear)


def rename_bone(self, context, bone_name):
    bone = get_selected_bone()
    if bone:
        if context.scene.BNR_replaceDuplicate == True:
            duplicate_bone = None
            for b in context.object.data.bones:
                if b.name == bone_name:
                    duplicate_bone = b
                    break
            if duplicate_bone and bone.name != duplicate_bone.name:
                duplicate_bone.name = bone_name + ".replaced"
                bone.name = bone_name
            else:
                bone.name = bone_name
        else:
            bone.name = bone_name

            
                
        next_bone = get_next_bone()
        if next_bone and context.scene.BNR_followChainBool == True:
            bone.select = False
            next_bone.select = True

def get_selected_bone():
    context = bpy.context
    selected_bones = context.selected_bones    
    if selected_bones is not None:
        if len(selected_bones) > 0:
            return selected_bones[0]

    selected_pose_bones = bpy.context.selected_pose_bones
    if selected_pose_bones is not None:
        if len(selected_pose_bones) > 0:
            return context.object.data.bones[selected_pose_bones[0].name]

    return None

def get_next_bone():
    current_bone = get_selected_bone()
    next_bone = current_bone.children
    if next_bone:
        return next_bone[0]
    return None
     
     
class BNR_ClearList(bpy.types.Operator):
    """Clears the bone list"""
    bl_idname = "bone_rename.clearlist"
    bl_label = "Clear List"
    bl_icon = "ERROR"
    bl_options = {"UNDO"}

    def execute(self, context):
        
        context.scene.BNR_bone_list.clear()
        return {"FINISHED"}

class BNR_AddBoneName(bpy.types.Operator):
    """Add a name to the bone list below"""
    bl_idname = "bone_rename.addname"
    bl_label = "Add Bone Name"
    
    def execute(self, context):
        print("self.user_inputted_value:", context.scene.BNR_addBoneString)
        bpy.types.Scene.BNR_bone_list.append(context.scene.BNR_addBoneString)
        return {"FINISHED"}


class BNR_RenameBone(bpy.types.Operator):
    """Rename bone to current button's name"""
    bl_idname = "bone_rename.renamebone"
    bl_label = "Rename Bone"
    bl_options = {"UNDO"}
    
    bone_name = bpy.props.StringProperty(name="Bone")
    
    def execute(self, context):
        current_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode="EDIT")
        
        rename_bone(self, context, self.bone_name)
        
        bpy.ops.object.mode_set(mode=current_mode)
        return {"FINISHED"}

class BNR_RenameBoneConfirmOperator(bpy.types.Operator):
    """TEST QUOTES"""
    bl_idname = "bnr.rename_panel"
    bl_label = "Rename Bone"
    bl_options = {"UNDO"}
    
    type = bpy.props.StringProperty(default="", options={'SKIP_SAVE'})
    #bpy.types.Scene.BNR_addBoneString = bpy.props.StringProperty(default="Bone")
    
    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        rename_bone(self, context, self.type)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        bone = get_selected_bone()
        if bone:
            bone_name = bone.name
            return context.window_manager.invoke_props_dialog(self, width=400)
        
    def draw(self, context):
        self.layout.prop(self, "type", text="")
        
    
bpy.data.window_managers[0].keyconfigs.active.keymaps['Armature'].keymap_items.new('bnr.rename_panel',value='PRESS',type='E',ctrl=True,alt=False,shift=False,oskey=False)
bpy.data.window_managers[0].keyconfigs.active.keymaps['Pose'].keymap_items.new('bnr.rename_panel',value='PRESS',type='E',ctrl=True,alt=False,shift=False,oskey=False)
    
class BNR_RenameChain(bpy.types.Operator):
    """Rename a chain of bones up to when the chain forks based on bone list structure"""
    bl_idname = "bnr.rename_chain"
    bl_label = "Rename Chain"
    bl_options = {"UNDO"}
    
    ##TODO: Add "replace old" check and replace old if true
    def execute(self, context):
        current_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode="EDIT")
        
        bones = context.selected_bones
        if bones:
            if len(bones) > 0:
                index = -1
                bones = bones[0]
                for count in range(0, len(context.scene.BNR_bone_list)):
                    bone_list_name = context.scene.BNR_bone_list[count]
                    print(bones.name, bone_list_name)
                    if bones.name == bone_list_name:
                        print("Matching bone found")
                        index = count
                        break
                if index > -1:
                    count = 1
                    if len(bones.children) == 1:
                        while len(bones.children) == 1 and index + count < len(context.scene.BNR_bone_list):
                            bones = bones.children[0]
                            bones.select = False
                            print("{0}/{1}".format(index + count, len(context.scene.BNR_bone_list) - 1))
                            print(bones.name)
                            bones.name = context.scene.BNR_bone_list[index + count]
                            count += 1
                            
                        bones.select = True
            elif len(bones) > 1:
                print("test")
                
        bpy.ops.object.mode_set(mode=current_mode)
        return {"FINISHED"}
        
        
#### PIE NEXT IN CHAIN SELECTOR ######
class BNR_PieChainMenu(bpy.types.Operator):

    bl_idname = "bnr.pie_chain_menu"
    bl_label = "Add Quick Node"
    
    bone_name = bpy.props.StringProperty()
    @classmethod
    def poll(cls, context):
        if get_selected_bone():
            return True
        return False
        
    def execute(self, context):
        #TODO: Optimize this, and getting current bone
        context.object.data.bones[get_selected_bone().name].select = False
        context.object.data.bones[self.bone_name].select = True
        return {'FINISHED'}
    
class BNR_piechain_template(bpy.types.Menu):
    # label is displayed at the center of the pie menu.
    bl_label = "Select Bone"
    
    @classmethod
    def poll(cls, context):
        if get_selected_bone():
            return True
        return False
    
    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()        
        bones = get_selected_bone().children
        for b in bones:
            pie.operator("bnr.pie_chain_menu", b.name).bone_name = b.name
########################################

class BonePanel(bpy.types.Panel):
    bl_idname = "DATA_PT_bone_rangler"
    bl_label = "Bone Name Rangler"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "data"
    bpy.types.Scene.BNR_addBoneString = bpy.props.StringProperty(default="Bone")
    bpy.types.Scene.BNR_followChainBool = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.BNR_hideMatching = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.BNR_replaceDuplicate = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.BNR_bone_list = []
        
    def draw(self, context):
        if context.object.mode in { 'POSE', 'EDIT' }:
            layout = self.layout
            
            ##TEMP
            layout.operator("wm.call_menu_pie", "BNR_piechain_template").name = "BNR_piechain_template"
            ###############
            
            bone = get_selected_bone()
            if bone is not None:
                layout.prop(bone, "name", "", icon="BONE_DATA")
            else:
                layout.label("No bone selected")            
            
            add_name_row = layout.row()
            add_name_row.prop(context.scene, "BNR_addBoneString", "")
            add_name_row.alignment = "RIGHT"
            add_name_row.operator("bone_rename.addname", "Add Name")
            
            layout.operator("bone_rename.import_list", icon="FILE")
            option_col = layout.column(align=True)
            
            t = option_col.row()
            t.alignment = "CENTER"
            t.label("Armature Options")
            
            option_armature_col = option_col.column()
            t = option_armature_col.row()
            t.prop(context.object.data, "layers", "")
            t = option_armature_col.row()
            t.prop(context.object.data, "show_names")
            t.prop(context.object, "show_x_ray")
            
            t = option_col.row()
            t.alignment = "CENTER"
            t.label("Bone Name Replacement Options")
            
            t = option_col.row()
            t.prop(context.scene, "BNR_followChainBool", "Follow Chain")
            t.prop(context.scene, "BNR_hideMatching", "Hide Matching")
            
            t = option_col.row()
            t.prop(context.scene, "BNR_replaceDuplicate", "Replace Old")
            
            bl_col = layout.column()
            bl_inner_col = bl_col.column()

            if len(bpy.types.Scene.BNR_bone_list) > 0:
                
                t = option_col.row()
                t.operator("bnr.rename_chain")
                
                qbl_row = bl_inner_col.row()
                qbl_row.label("Quick Bone List:")
                qbl_row.alignment = "RIGHT"
                qbl_row.operator("bone_rename.clearlist", "Clear List", icon="X")
                qbl_row.alignment = "EXPAND"

                
                #Begin drawing defined bone list buttons
                a_bone_list = []
                if context.scene.BNR_hideMatching == True:
                    armature_bones = context.object.data.bones
                    for b in armature_bones:
                        a_bone_list.append(b.name)
                hidden_count = 0
                bone_count = 0
                for b in bpy.types.Scene.BNR_bone_list:
                    if context.scene.BNR_hideMatching == True:
                        if b not in a_bone_list:
                            bl_col.operator("bone_rename.renamebone", b).bone_name = b
                        else:
                            hidden_count += 1
                    elif bone is None:
                        bl_col.operator("bone_rename.renamebone", b).bone_name = b
                    else:
                        if bone.name == b:
                            bl_col.operator("bone_rename.renamebone", b, icon="TRIA_RIGHT").bone_name = b
                        elif bone.parent is None:
                            bl_col.operator("bone_rename.renamebone", b).bone_name = b
                        elif bone.parent.name == b:
                            bl_col.operator("bone_rename.renamebone", b, icon="GROUP_BONE").bone_name = b
                        else:
                            bl_col.operator("bone_rename.renamebone", b).bone_name = b

                    bone_count += 1
                if context.scene.BNR_hideMatching == True:
                    bl_inner_col.label("({0}/{1} Hidden due to matching)".format(hidden_count, bone_count))


bnr_class_list = [
    BNR_RenameChain,
    BNR_ClearList,
    BoneRenameImportList,
    BNR_RenameBone,
    BNR_RenameBoneConfirmOperator,
    BNR_AddBoneName,
    BNR_PieChainMenu,
    BNR_piechain_template,
    BonePanel
]

def register():
    for c in bnr_class_list:
        bpy.utils.register_class(c)
        
def unregister():
    for c in bnr_class_list:
        bpy.utils.unregister_class(c)
        
if __name__ == "__main__":
    register()
    