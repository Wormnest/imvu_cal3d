# ##### BEGIN GPL LICENSE BLOCK #####
#
# This file is part of the Blender 2.63+ to Cal3d exporter targeted
# primarily for IMVU compatibility.
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = \
{
  "name": "IMVU Cal3D export",
  "author": "Jean-Baptiste Lamy (Jiba), " \
            "Chris Montijin, "            \
            "Damien McGinnes, "           \
            "David Young, "               \
            "Alexey Dorokhov, "           \
            "Matthias Ferch, "             \
            "Peter Amstutz, "                \
            "Etory, "                \
            "Jacob Boerema",
  "version": (1, 1, 1),
  "blender": (2, 6, 3),
  "location": "File > Export > IMVU Cal3D (.cfg)",
  "description": "Export mesh geometry, armature, "   \
                 "materials and animations to Cal3D "  \
                 "for IMVU",
  "warning": "You must have Blender 2.6.3 or higher to run this script." \
            "Assigning material(s) to your mesh is required for the exporter to work.",
  "wiki_url": "https://bitbucket.org/jacobb/imvu_cal3d",
  "tracker_url": "",
  "category": "Import-Export"
}

# To support reload properly, try to access a package var, 
# if it's there, reload everything
print("")
print("Initializing IMVU Cal3D export version " + str(bl_info['version'][0])+"."+str(bl_info['version'][1])+"."+str(bl_info['version'][2]))
if "bpy" in locals():
	import imp
	print("reloading script classes")

	if "mesh_classes" in locals():
		#print("reload mesh_classes")
		imp.reload(mesh_classes)

	if "export_mesh" in locals():
		#print("reload export_mesh")
		imp.reload(export_mesh)

	if "armature_classes" in locals():
		#print("reload armature_classes")
		imp.reload(armature_classes)

	if "export_armature" in locals():
		#print("reload export_armature")
		imp.reload(export_armature)

	if "action_classes" in locals():
		#print("reload action_classes")
		imp.reload(action_classes)

	if "export_action" in locals():
		#print("reload export_action")
		imp.reload(export_action)


import bpy
from bpy import ops
from bpy import context
from bpy.props import BoolProperty,			\
                      EnumProperty,			\
                      CollectionProperty,	\
                      FloatProperty,		\
                      StringProperty,		\
                      FloatVectorProperty,	\
                      IntProperty


import bpy_extras
from bpy_extras.io_utils import ExportHelper, ImportHelper

import mathutils

import os.path
import sys
import traceback

class ExportCal3D(bpy.types.Operator, ExportHelper):
	'''Save Cal3d files for IMVU'''

	# jgb To ease debugging use a class debugging var (0 means off)
	debug_ExportCal3D = 0
	
	bl_idname = "cal3d_model.cfg"
	bl_label = 'Export Cal3D for IMVU'
	bl_options = {'PRESET'}

	filename_ext = ".cfg"
	filter_glob = StringProperty(default="*.cfg;*.xsf;*.xaf;*.xmf;*.xrf;*.csf;*.caf;*.cmf;*.crf",
								 options={'HIDDEN'})

	# List of operator properties, the attributes will be assigned
	# to the class instance from the operator settings before calling.

	# context group
	mesh_prefix = StringProperty(name="Mesh", 
									 default="model_")
									 
	skeleton_prefix = StringProperty(name="Skeleton", 
									 default="")
									 
	anim_prefix = StringProperty(name="Animation",
									  default="")
									  
	material_prefix = StringProperty(name="Material",
									  default="")
	
	imagepath_prefix = StringProperty(name="Image Path",
									  default="")
									  
	base_rotation = FloatVectorProperty(name="Base Rotation (XYZ)", 
										default = (0.0, 0.0, 0.0),
										subtype="EULER")

	base_scale = FloatProperty(name="Base Scale",
								default=1.0)

	# jgb 2012-11-09 IMVU expects 30 fps (ref: http://www.imvu.com/catalog/modules.php?op=modload&name=phpbb2&file=viewtopic.php&t=307460&start=0)
	# While I remember reading that blender default and the value that was here before = 25.
	fps = FloatProperty(name="Frame Rate",
						default=30.0)

	#path_mode = bpy_extras.io_utils.path_reference_mode
	
	use_groups = BoolProperty(name="Vertex Groups", description="Export the meshes using vertex groups.", default=True)
	#use_envelopes = BoolProperty(name="Envelopes", description="Export the meshes using bone envelopes.", default=True)
	
	skeleton_binary_bool = EnumProperty(
            name="Skeleton Filetype",
            items=(('binary', "Binary (.CSF)", "Export a binary skeleton"),
                   ('xml', "XML (.XSF)", "Export an xml skeleton"),
                   ),
			default='xml'
            )
	mesh_binary_bool = EnumProperty(
            name="Mesh Filetype",
            items=(('binary', "Binary (.CMF)", "Export a binary mesh"),
                   ('xml', "XML (.XMF)", "Export an xml mesh"),
                   ),
			default='xml'
            )
	animation_binary_bool = EnumProperty(
            name="Animation Filetype",
            items=(('binary', "Binary (.CAF)", "Export a binary animation"),
                   ('xml', "XML (.XAF)", "Export an xml animation"),
                   ),
			default='xml'
            )
	material_binary_bool = EnumProperty(
            name="Material Filetype",
            items=(('binary', "Binary (.CRF)", "Export a binary material"),
                   ('xml', "XML (.XRF)", "Export an xml material"),
                   ),
			default='xml'
            )
	
	export_xsf = BoolProperty(name="Export skeleton (.XSF)", description="Whether or not to export the skeleton.", default=True)
	export_xmf = BoolProperty(name="Export mesh (.XMF)", description="Whether or not to export the mesh.", default=True)
	export_xaf = BoolProperty(name="Export animation (.XAF)", description="Whether or not to export the animation.", default=True)
	# Since IMVU doesn't use XRF anymore and never used CFG we turn them off by default
	export_xrf = BoolProperty(name="Export materials (.XRF)", description="Whether or not to export the materials.", default=False)
	export_cfg = BoolProperty(name="Export config file (.CFG)", description="Whether or not to export the .CFG file.", default=False)
	copy_img = BoolProperty(name="Copy images", description="Whether or not to copy used material images to export folder.", default=False)
	
	def execute(self, context):
		from . import export_mesh
		from . import export_armature
		from . import export_action
		from .export_armature import create_cal3d_skeleton
		from .export_mesh import create_cal3d_materials
		from .export_mesh import create_cal3d_mesh
		from .export_action import create_cal3d_animation

		# Always add empty line to make it easier to find start of our info
		print("")
		print("ExportCal3D started.")
		
		# jgb Set desired Cal3d xml export version only once and change it from 900 to 919.
		# Which version might possibly be required for animation settings like  
		# TRANSLATIONREQUIRED="0" TRANSLATIONISDYNAMIC="0" HIGHRANGEREQUIRED="1"
		Cal3d_xml_version = 919
		
		cal3d_dirname = os.path.dirname(self.filepath)

		cal3d_skeleton = None
		cal3d_materials = []
		cal3d_meshes = []
		cal3d_animations = []
		armature_obj = None

		# base_translation, base_rotation, and base_scale are user adjustments to the export
		base_translation = mathutils.Vector([0.0, 0.0, 0.0])
		base_rotation = mathutils.Euler([self.base_rotation[0],
		                                 self.base_rotation[1],
		                                 self.base_rotation[2]], 'XYZ').to_matrix()
		base_scale = self.base_scale
		fps = self.fps
		
		#visible_objects = [ob for ob in context.scene.objects if ob.is_visible(context.scene)]
		visible_objects = context.selected_objects
		
		# Export armatures
		# Always read skeleton because both meshes and animations need it.
		if self.debug_ExportCal3D > 0:
			print("ExportCal3D: export armatures.")
		try:
			for obj in visible_objects:
				if obj.type == "ARMATURE":
					if cal3d_skeleton:
						raise RuntimeError("Only one armature is supported per scene")
					armature_obj = obj
					cal3d_skeleton = create_cal3d_skeleton(obj, obj.data,
					                                       base_rotation.copy(),
					                                       base_translation.copy(),
					                                       base_scale, Cal3d_xml_version)
		except Exception as e:
			print("###### ERROR DURING ARMATURE EXPORT ######")
			traceback.print_exc()
			return {"FINISHED"}

		# Export meshes and materials
		# Test for xmf first because that one is the most likely to be set.
		if self.export_xmf or self.export_xrf:
			if self.debug_ExportCal3D > 0:
				print("ExportCal3D: export meshes and materials.")
			try:
				cal3d_materials = create_cal3d_materials(cal3d_dirname, self.imagepath_prefix, Cal3d_xml_version, self.copy_img)

				# jgb 2012-11-09 We currently  can't do the meshes without at least 1 material
				if len(cal3d_materials) > 0:
					for obj in visible_objects:
						if obj.type == "MESH" and obj.is_visible(context.scene):
							cal3d_meshes.append(create_cal3d_mesh(context.scene, obj, 
																  cal3d_skeleton,
																  cal3d_materials,
																  base_rotation,
																  base_translation,
																  base_scale, Cal3d_xml_version,
																  self.use_groups, False, armature_obj))
				else:
					if self.debug_ExportCal3D > 0:
						print("ExportCal3D: no cal3d materials found!")

			except RuntimeError as e:
				print("###### ERROR DURING MESH EXPORT ######")
				print(e)
				return {"FINISHED"}


		if self.export_xaf:
			# Export animations
			if self.debug_ExportCal3D > 0:
				print("ExportCal3D: export animations.")
			try:
				if cal3d_skeleton:
					for action in bpy.data.actions:
						cal3d_animation = create_cal3d_animation(cal3d_skeleton,
																 action, fps, Cal3d_xml_version)
						if cal3d_animation:
							cal3d_animations.append(cal3d_animation)
							
			except RuntimeError as e:
				print("###### ERROR DURING ACTION EXPORT ######")
				print(e)
				return {"FINISHED"}


		if self.debug_ExportCal3D > 0:
			print("ExportCal3D: write files.")

		if self.export_xsf:
			if cal3d_skeleton:
				if self.skeleton_binary_bool == 'binary':
					skeleton_filename = self.skeleton_prefix + cal3d_skeleton.name + ".csf"
					skeleton_filepath = os.path.join(cal3d_dirname, skeleton_filename)
					cal3d_skeleton_file = open(skeleton_filepath, "wb")
					cal3d_skeleton.to_cal3d_binary(cal3d_skeleton_file)
				else:
					skeleton_filename = self.skeleton_prefix + cal3d_skeleton.name + ".xsf"
					skeleton_filepath = os.path.join(cal3d_dirname, skeleton_filename)
					cal3d_skeleton_file = open(skeleton_filepath, "wt")
					cal3d_skeleton_file.write(cal3d_skeleton.to_cal3d_xml())
				cal3d_skeleton_file.close()
				print("Wrote skeleton '%s'" % (skeleton_filename))

		if self.export_xrf:
			i = 0
			for cal3d_material in cal3d_materials:
				if self.material_binary_bool == 'binary':
					material_filename = self.material_prefix + cal3d_material.name + ".crf"
					material_filepath = os.path.join(cal3d_dirname, material_filename)
					cal3d_material_file = open(material_filepath, "wb")
					cal3d_material.to_cal3d_binary(cal3d_material_file)
				else:
					material_filename = self.material_prefix + cal3d_material.name + ".xrf"
					material_filepath = os.path.join(cal3d_dirname, material_filename)
					cal3d_material_file = open(material_filepath, "wt")
					cal3d_material_file.write(cal3d_material.to_cal3d_xml())
				cal3d_material_file.close()
				print("Wrote material '%s' with index %s" % (material_filename, i))
				i += 1

		if self.export_xmf:
			for cal3d_mesh in cal3d_meshes:
				if self.mesh_binary_bool == 'binary':
					mesh_filename = self.mesh_prefix + cal3d_mesh.name + ".cmf"
					mesh_filepath = os.path.join(cal3d_dirname, mesh_filename)
					cal3d_mesh_file = open(mesh_filepath, "wb")
					cal3d_mesh.to_cal3d_binary(cal3d_mesh_file)
				else:
					mesh_filename = self.mesh_prefix + cal3d_mesh.name + ".xmf"
					mesh_filepath = os.path.join(cal3d_dirname, mesh_filename)
					cal3d_mesh_file = open(mesh_filepath, "wt")
					cal3d_mesh_file.write(cal3d_mesh.to_cal3d_xml())
				cal3d_mesh_file.close()
				print("Wrote mesh '%s' with materials %s" % (mesh_filename, [x.material_id for x in cal3d_mesh.submeshes]))
			
		if self.export_xaf:
			for cal3d_animation in cal3d_animations:
				if self.animation_binary_bool == 'binary':
					animation_filename = self.anim_prefix + cal3d_animation.name + ".caf"
					animation_filepath = os.path.join(cal3d_dirname, animation_filename)
					cal3d_animation_file = open(animation_filepath, "wb")
					cal3d_animation.to_cal3d_binary(cal3d_animation_file)
				else:
					animation_filename = self.anim_prefix + cal3d_animation.name + ".xaf"
					animation_filepath = os.path.join(cal3d_dirname, animation_filename)
					cal3d_animation_file = open(animation_filepath, "wt")
					cal3d_animation_file.write(cal3d_animation.to_cal3d_xml())
				cal3d_animation_file.close()
				print("Wrote animation '%s'" % (animation_filename))


		if self.export_cfg:
			# jgb 2012-11-09 We don't want to overwrite a .blend file by accident:
			if not self.filepath.endswith('.cfg'):
				filename = self.filepath + '.cfg'
			else:
				filename = self.filepath
			cal3d_cfg_file = open(filename, "wt")

			if self.debug_ExportCal3D > 0:
				print("ExportCal3D: write cfg.")

			# lolwut?
			#cal3d_cfg_file.write("path={0}\n".format("data\\models\\" + os.path.basename(self.filepath[:-4])+ "\\"))
			#cal3d_cfg_file.write("scale=0.01f\n")
			
			if cal3d_skeleton:
				if self.skeleton_binary_bool == 'binary':
					skeleton_filename = self.skeleton_prefix + cal3d_skeleton.name + ".csf"
				else:
					skeleton_filename = self.skeleton_prefix + cal3d_skeleton.name + ".xsf"
				cal3d_cfg_file.write("skeleton={0}\n".format(skeleton_filename))

			for cal3d_animation in cal3d_animations:
				if self.animation_binary_bool == 'binary':
					animation_filename = self.anim_prefix + cal3d_animation.name + ".caf"
				else:
					animation_filename = self.anim_prefix + cal3d_animation.name + ".xaf"
				cal3d_cfg_file.write("animation={0}\n".format(animation_filename))

			for cal3d_material in cal3d_materials:
				if self.material_binary_bool == 'binary':
					material_filename = self.material_prefix + cal3d_material.name + ".crf"
				else:
					material_filename = self.material_prefix + cal3d_material.name + ".xrf"
				cal3d_cfg_file.write("material={0}\n".format(material_filename))

			for cal3d_mesh in cal3d_meshes:
				if self.mesh_binary_bool == 'binary':
					mesh_filename = self.mesh_prefix + cal3d_mesh.name + ".cmf"
				else:
					mesh_filename = self.mesh_prefix + cal3d_mesh.name + ".xmf"
				cal3d_cfg_file.write("mesh={0}\n".format(mesh_filename))

			cal3d_cfg_file.close()

		print("Export finished.")
		print("")

		return {"FINISHED"}

	def draw(self, context):
		layout = self.layout
		
		row = layout.row(align=True)
		row.label(text="Which files to export:")
		row = layout.row(align=True)
		row.prop(self, "export_xsf")
		row = layout.row(align=True)
		row.prop(self, "export_xmf")
		row = layout.row(align=True)
		row.prop(self, "export_xaf")
		row = layout.row(align=True)
		row.prop(self, "export_xrf")
		row = layout.row(align=True)
		row.prop(self, "export_cfg")
		row = layout.row(align=True)
		row.prop(self, "copy_img")


		row = layout.row(align=True)
		row.label(text="Filename prefixes for:")
		
		row = layout.row(align=True)
		row.prop(self, "skeleton_prefix")
		
		row = layout.row(align=True)
		row.prop(self, "mesh_prefix")
		
		row = layout.row(align=True)
		row.prop(self, "anim_prefix")
		
		row = layout.row(align=True)
		row.prop(self, "material_prefix")
		
		row = layout.row(align=True)
		row.prop(self, "imagepath_prefix")
		
		#row = layout.row(align=True)
		#row.prop(self, "base_rotation")
		
		#row = layout.row(align=True)
		#row.prop(self, "base_scale")
		
		row = layout.row(align=True)
		row.prop(self, "fps")
		
		#row = layout.row(align=True)
		#row.prop(self, "path_mode")
		
		row = layout.row(align=True)
		row.label(text="Export with:")
		row = layout.row(align=True)
		row.prop(self, "use_groups")
		#row.prop(self, "use_envelopes")
		
		# jgb 2012-11-11 Binary not supported on IMVU afaik therefore no need to give a choice
		#row = layout.row(align=True)
		#row.label(text="Skeleton")
		#row.prop(self, "skeleton_binary_bool", expand=True)
		#row = layout.row(align=True)
		#row.label(text="Mesh")
		#row.prop(self, "mesh_binary_bool", expand=True)
		#row = layout.row(align=True)
		#row.label(text="Animation")
		#row.prop(self, "animation_binary_bool", expand=True)
		#row = layout.row(align=True)
		#row.label(text="Material")
		#row.prop(self, "material_binary_bool", expand=True)
		

	def invoke(self, context, event):
		
		self.fps = context.scene.render.fps
		sc = ""
		if len(bpy.data.scenes) > 1:
			sc = context.scene.name + "_"
		pre = os.path.splitext(os.path.basename(bpy.data.filepath))[0] + "_" + sc
		self.mesh_prefix = pre
		self.skeleton_prefix = pre
		self.anim_prefix = pre
		self.material_prefix = pre
		r = super(ExportCal3D, self).invoke(context, event)
		
		#print(bpy.context.active_operator)
		#preset = bpy.utils.preset_find("default", "operator\\cal3d_model.cfg", display_name=False)
		#print("preset is " + preset)
		#orig = context["active_operator"]
		#try:
		#	bpy.context["active_operator"] = self
		#	bpy.ops.script.execute_preset(context_copy, filepath=preset, menu_idname="WM_MT_operator_presets")
		#finally:
		#	context["active_operator"] = orig
		
		return r

def menu_func_export(self, context):
	self.layout.operator(ExportCal3D.bl_idname, text="IMVU Cal3D export")


def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
	register()
