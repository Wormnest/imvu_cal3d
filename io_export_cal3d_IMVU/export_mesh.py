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

import bpy
import mathutils

from . import mesh_classes
from . import armature_classes
from .mesh_classes import *
from .armature_classes import *

# for debugging (0=off)
debug_export = 0

def create_cal3d_materials(cal3d_dirname, imagepath_prefix, xml_version, copy_images):
	cal3d_materials = []
	for material in bpy.data.materials:
		material_index = len(cal3d_materials)
		material_name = material.name
		maps_filenames = []
		tsi = 0
		for texture_slot in material.texture_slots:
			if texture_slot:
				if texture_slot.texture:
					if texture_slot.texture.type == "IMAGE":
						# Test if image is valid (can be None!)
						if texture_slot.texture.image:
							imagename = bpy.path.basename(texture_slot.texture.image.filepath)
						else:
							print("WARNING: no image data available in texture slot {0} for material {1}".format(tsi, material_name))
							# Give it a dummy name, we don't need it for imvu anyway
							imagename = "MATERIAL_{0}_TEXTURE_{1:03d}.JPG".format(material_name, tsi)
						
						# jgb 2012-11-11 Only copy images if that's what we want
						if copy_images:
							filepath = os.path.abspath(bpy.path.abspath(texture_slot.texture.image.filepath))
							texturePath = os.path.join(cal3d_dirname, imagepath_prefix + imagename)
							# jgb 2012-11-03 debugging info
							if debug_export > 0:
								print ("----------")
								print( "material: " + material_name + " index: " + str(material_index))
								print("image: " + imagename + " filepath: " + filepath)
							
							if not os.path.exists(os.path.dirname(texturePath)):
								os.mkdir(os.path.dirname(texturePath))
							if os.path.exists(filepath):
								import shutil
								try:
									shutil.copy(filepath, texturePath)
									print("Copied texture to " + texturePath)
								except Exception as e:
									print("Error copying texture " + str(e))
						maps_filenames.append(imagepath_prefix + imagename)
						#maps_filenames.append(texture_slot.texture.image.filepath[2:]) #remove the double slash
			tsi += 1
		if len(maps_filenames) > 0:
			cal3d_material = Material(material_name, material_index, xml_version)
			cal3d_material.maps_filenames = maps_filenames
			cal3d_materials.append(cal3d_material)
	# jgb 2012-11-08 get some info for testing in case there are no materials
	if len(cal3d_materials) == 0:
		print("Sorry but you need to add materials to you meshes and add the images there in order to be able to export your mesh!")
		print("Currently these images are known:")
		for img in bpy.data.images:
			print(img.filepath)
		
	return cal3d_materials


def get_vertex_influences(vertex, mesh_obj, cal3d_skeleton, use_groups, use_envelopes, armature_obj):
	if not cal3d_skeleton:
		return []

	influences = []
	
	if use_groups:
		for group in vertex.groups:
			group_index = group.group
			group_name = mesh_obj.vertex_groups[group_index].name
			# jgb debug
			if debug_export > 0:
				print( "group name " + group_name + ", group weight: " + str(group.weight))
			weight = group.weight
			if weight > 0.0001:
				for bone in cal3d_skeleton.bones:
					if (bone.name == group_name):
						influence = Influence(bone.index, weight)
						influences.append(influence)
						break

	# XXX BROKEN (jgb: use_envelopes always set to False in __init__.py, dont know what the intention of this value is)
	if use_envelopes and not (len(influences) > 0):
		for bone in armature_obj.data.bones:
			weight = bone.evaluate_envelope(armature_obj.matrix_world.copy().inverted() * (mesh_obj.matrix_world * vertex.co))
			if weight > 0:
				for cal3d_bone in cal3d_skeleton.bones:
					if bone.name == cal3d_bone.name:
						influence = Influence(cal3d_bone.index, weight)
						influences.append(influence)
						break

	return influences

# Collect all normals for all ShapeKeys so we can use them when we need them and don't
# have to iterate over it every time
# jgb 2012-11-24 When matrix world scale <> 1.0 we are restoring scale to 1.0 in create mesh. However for
# some reason the ShapeKey vertex data there is off and for now I can't figure out how to compute the right values
# Therefore we take the easy route and store and return the ShapeKey vertices from here too
def collect_shapekey_normals(mesh_obj, scene, mesh_matrix, shape_keys):
	# Save original values and set to our wanted values
	save_frame = scene.frame_current
	save_show = mesh_obj.show_only_shape_key
	save_val = mesh_obj.active_shape_key.value
	save_active = mesh_obj.active_shape_key_index

	# Init our data where we gonna store all the ShapeKey normals.
	sk_normals = []
	sk_vertices = []

	# Now change to the values we need
	scene.frame_set(scene.frame_start)	# Make sure we are at the first frame of animation
	mesh_obj.show_only_shape_key = True	# We want to be in the keyshape visibe state

	# Go over all ShapeKeys except the first Basis one
	for si in range(1,len(shape_keys.key_blocks)):
		#Update to the correct ShapeKey
		mesh_obj.active_shape_key_index = si
		# Note: for now we always assume a MAX value of 1.0. Should we allow for other max (and min)?
		# Do we need to set this within the loop?
		mesh_obj.active_shape_key.value = 1.0	# Set KeyShape to its full setting
		#scene.update()	# Data still correct without this line

		# Get mesh in our wanted ShapeKey state
		keymesh_data = mesh_obj.to_mesh(scene, True, "PREVIEW")	# True = apply modifiers
		keymesh_data.transform(mesh_matrix)

		# Store all the normals for this ShapeKey
		sk_normals.append([])	# Add empty slot for ShapeKey normals
		sk_vertices.append([])	# Add empty slot for ShapeKey vertices
		for vx in range(len(keymesh_data.vertices)):
			# Get the normal for this vertex and store it in our list at list index sk_normals[si-1][vx]
			if vx == 0 and debug_export > 0:
				print("ShapeKey {0} [{1}] has normal {2} and vertex {3}".format(si-1, vx,
					keymesh_data.vertices[vx].normal, keymesh_data.vertices[vx].co))
			sk_normal = keymesh_data.vertices[vx].normal.copy()
			sk_normals[si-1].append(sk_normal)
			sk_vert = keymesh_data.vertices[vx].co.copy()
			sk_vertices[si-1].append(sk_vert)

		# Finished with this ShapeKey now remove the temp mesh for this ShapeKey state
		bpy.data.meshes.remove(keymesh_data)

	# Reset to original values and remove keymesh_data after use
	scene.frame_set(save_frame)
	mesh_obj.active_shape_key.value = save_val
	mesh_obj.show_only_shape_key = save_show
	#bpy.data.meshes.remove(keymesh_data)

	# Return the collected ShapeKey normals
	return sk_normals, sk_vertices


def create_cal3d_mesh(scene, mesh_obj,
                      cal3d_skeleton,
                      cal3d_materials, cal3d_used_materials,
                      base_rotation_orig,
                      base_translation_orig,
                      base_scale,
                      xml_version,
                      use_groups, use_envelopes, armature_obj):

	mesh_matrix = mesh_obj.matrix_world.copy()

	(mesh_translation, mesh_quat, mesh_scale) = mesh_matrix.decompose()
	mesh_rotation = mesh_quat.to_matrix()
	# Check to see if the mesh is scaled, if so give a warning and try to correct it
	if((mesh_scale.x != 1.0) or (mesh_scale.y != 1.0) or (mesh_scale.z != 1.0)):
		print("WARNING: at least one of the matrix world (armature) scale components is not 1.0!\nMesh scale: "+str(mesh_scale))
		print("matrix world: "+str(mesh_matrix))
		print("Trying to correct scale to 1.0")
		# jgb Not sure if this computation will be always correct, see also in armature_export.py for a possible other way to do it
		# 1.  Scale down the translation by the used scale
		mesh_translation.x = mesh_translation.x / mesh_scale.x
		mesh_translation.y = mesh_translation.y / mesh_scale.y
		mesh_translation.z = mesh_translation.z / mesh_scale.z
		# 2. Add scale 1.0 matrix and matrix of the rescaled translation
		mat_scale = mathutils.Matrix.Scale(1.0, 4, (1.0, 1.0, 1.0))
		mat_trans = mathutils.Matrix.Translation(mesh_translation)
		# 3.  Recompute matrix based on new scale, new translation and the old rotation
		mesh_matrix = mat_scale * mat_trans * mesh_quat.to_matrix().to_4x4()
		# 4.  Get the corrected data back
		(mesh_translation, mesh_quat, mesh_scale) = mesh_matrix.decompose()
		mesh_rotation = mesh_quat.to_matrix()
		# For info and checking print out the corrected matrix
		print("Corrected scaled matrix:\n"+str(mesh_matrix))

	if debug_export > 0:
		print("matrix world: "+str(mesh_matrix))
		print("mesh translation: "+str(mesh_translation))
		print("mesh quat: "+str(mesh_quat))
		print("mesh scale: "+str(mesh_scale))

	mesh_data = mesh_obj.to_mesh(scene, False, "PREVIEW")
	mesh_data.transform(mesh_matrix)

	base_translation = base_translation_orig.copy()
	base_rotation = base_rotation_orig.copy()

	total_rotation = base_rotation.copy()
	total_translation = base_translation.copy()

	cal3d_mesh = Mesh(mesh_obj.name, xml_version)
	if cal3d_skeleton:
		print("mesh: " + mesh_obj.name)
	else:
		print("ERROR: mesh: " + mesh_obj.name + " is not attached to a skeleton or skeleton is not selected!")
		# No use going on if we can't assing influences
		return None

	#not compatible with Blender 2.6.3
	#faces = mesh_data.faces
	#For Blender 2.6.3, use tesselation :
	mesh_data.update (calc_tessface=True)
	faces = mesh_data.tessfaces

	# currently 1 material per mesh

	blender_material = None
	if len(mesh_data.materials) > 0:
		blender_material = mesh_data.materials[0]
	
	cal3d_material_index = -1
	# for cal3d_material in cal3d_materials:
		# # jgb 2012-11-03 debug
		# print("material: blender name: " + blender_material.name + " cal3d name: " + cal3d_material.name)
		# if (blender_material != None) and (cal3d_material.name == blender_material.name):
			# cal3d_material_index = cal3d_material.index
			# # jgb debug
			# print("cal3d material index: " + str(cal3d_material_index))
			# # jgb 2012-11-03 As far as I can see these next 2 calls need to go inside the if, and not outside the for loop like they were!!
			# cal3d_submesh = SubMesh(cal3d_mesh, len(cal3d_mesh.submeshes),
				# cal3d_material_index)
			# cal3d_mesh.submeshes.append(cal3d_submesh)

	# jgb 2012-11-03 For IMVU we need to go over all blender materials, try a new double for loop here instead of above
	# Take test for blender_material None out of loop, no need to be tested more than once!
	# if can be replaced by test len(mesh_data.materials) > 0: (see above)
	if blender_material != None:
		bm = 0	# jgb not sure if there is another way in python to get the index of blender_material in materials
		for blender_material in mesh_data.materials:
			for cal3d_material in cal3d_materials:
				# jgb 2012-11-03 debug
				if debug_export > 0:
					print("material: blender name: " + blender_material.name + " cal3d name: " + cal3d_material.name)
				if (cal3d_material.name == blender_material.name):
					cal3d_material_index = cal3d_material.index
					# jgb debug
					if debug_export > 0:
						print("cal3d/mesh material indexes: " + str(cal3d_material_index) + " , " + str(bm))
					# jgb Set this material as being in use when needed:
					if cal3d_material.in_use == False:
						cal3d_material.in_use = True
						cal3d_material.used_index = len(cal3d_used_materials)
						cal3d_used_materials.append(cal3d_material)
					# jgb 2012-11-05 Add mesh_material id relative to mesh to SubMesh
					cal3d_submesh = SubMesh(cal3d_mesh, len(cal3d_mesh.submeshes),
						cal3d_material.used_index, bm)
					cal3d_mesh.submeshes.append(cal3d_submesh)
			bm += 1
	else:
		print("ERROR: this mesh has no materials!")
		# Currently we can't continue without error unless there are materials
		return None

	duplicate_index = len(mesh_data.vertices)

	#Not compatible with Blender 2.6.3
	#for face in mesh_data.faces:
	#For Blender 2.6.3 use tesselation :
	if debug_export > 0:
		print("tess faces: " + str(len(mesh_data.tessfaces)))
	
	# Test for presence of any uv textures
	if not mesh_data.tessface_uv_textures:
		print("ERROR: There are no uv textures assigned!")
		return None

	# Test existence of shape keys for morphing
	# Need more than 1 shape_key because first is the Basis which is the same as our mesh
	if mesh_data.shape_keys and len(mesh_data.shape_keys.key_blocks) > 1:
		if debug_export > 0:
			print("Shape key(s) found in mesh")
		if mesh_data.shape_keys.use_relative:
			do_shape_keys = True
			# Requires same number of vertices in mesh and in each of the shape keys
			vert_count = len(mesh_data.vertices)
			for kb in mesh_data.shape_keys.key_blocks[1:]:
				if len(kb.data) != vert_count:
					do_shape_keys = False
					print("WARNING: shape key "+kb.name+" has a different vertex count as the base mesh."+
						" Morph targets will be ignored and not exported!")
					break
				# Add a morph with this name to all submeshes
				sk_id = 0
				for sm in cal3d_mesh.submeshes:
					cal3d_morph = Morph(kb.name,sk_id)
					if cal3d_morph:
						sm.morphs.append(cal3d_morph)
					sk_id += 1
		else:
			print("WARNING: Only relative ShapeKeys are currently supported! Morph information will not be added to your mesh.")
			do_shape_keys = False
		if do_shape_keys:
			# Get the normals of the ShapeKeys
			if debug_export > 0:
				print("Collecting ShapeKey normals and vertices")
			sk_normals, sk_vertices = collect_shapekey_normals(mesh_obj, scene, mesh_matrix, mesh_data.shape_keys)
	else:
		do_shape_keys = False

	mind = -1
	for face in mesh_data.tessfaces:
		cal3d_vertex1 = None
		cal3d_vertex2 = None
		cal3d_vertex3 = None
		cal3d_vertex4 = None
		
		#jgb 2012-11-4 try to add support for multiple submeshes based on material id
		# Get the submesh that has same material id as the one in tessfaces...
		if mind != face.material_index:
			mind = face.material_index
			if debug_export > 0:
				print("tess material: " + str(face.material_index))
				print("tess verts: " + str(len(face.vertices)))
			cal3d_submesh = cal3d_mesh.get_submesh(face.material_index)
			if cal3d_submesh != None:
				if debug_export > 0:
					print("submesh material: " + str(cal3d_submesh.mesh_material_id))
			else:
				print("ERROR: submesh with correct material id not found!")
				return None

		for vertex_index in face.vertices:
			duplicate = False
			cal3d_vertex = None
			uvs = []

			#Not compatible with Blender 2.6.3
			#for uv_texture in mesh_data.uv_textures:
			#Blender 2.6.3 use tesselation : tessface_uv_textures
			for uv_texture in mesh_data.tessface_uv_textures:
				if not cal3d_vertex1:
					uvs.append(uv_texture.data[face.index].uv1.copy())
				elif not cal3d_vertex2:
					uvs.append(uv_texture.data[face.index].uv2.copy())
				elif not cal3d_vertex3:
					uvs.append(uv_texture.data[face.index].uv3.copy())
				elif not cal3d_vertex4:
					uvs.append(uv_texture.data[face.index].uv4.copy())

			# Etory : Don't flip texture verticaly
			# jgb 2012-11-03 maybe IMVU does need it to be flipped, so uncommented the next 2 lines
			for uv in uvs:
				uv[1] = 1.0 - uv[1]

			if not uvs:
				print("WARNING: no uv texture assigned to face "+str(face.index) + " vertex "+str(vertex_index))
			
			for cal3d_vertex_iter in cal3d_submesh.vertices:
				if cal3d_vertex_iter.index == vertex_index:
					duplicate = True
					if len(cal3d_vertex_iter.maps) != len(uvs):
						break
					
					uv_matches = True
					for i in range(len(uvs)):
						if cal3d_vertex_iter.maps[i].u != uvs[i][0]:
							uv_matches = False
							break

						if cal3d_vertex_iter.maps[i].v != uvs[i][1]:
							uv_matches = False
							break
					
					if uv_matches:
						cal3d_vertex = cal3d_vertex_iter

					break

			# jgb 2012-11-07 try to figure out the vertex colors
			# jgb 2012-11-08 but first test if there are any vertex colors
			if mesh_data.tessface_vertex_colors:
				col = mesh_data.tessface_vertex_colors.active.data[face.index]
				if debug_export > 0:
					print("vertex colors for face" + str(face.index))
					print("colors: " + str(col.color1) + ", "+ str(col.color2) + ", "+ str(col.color3) + ", "+ str(col.color4))
				if not cal3d_vertex1:
					vertex_color = col.color1
				elif not cal3d_vertex2:
					vertex_color = col.color2
				elif not cal3d_vertex3:
					vertex_color = col.color3
				elif not cal3d_vertex4:
					vertex_color = col.color4
				if debug_export > 0:
					print(str(vertex_color))
			else:
				# jgb cal3d v 919 always requires the color tag to be written even if we don't use vertex colors thus set default colors
				vertex_color = (1.0, 1.0, 1.0)

			if debug_export > 0:
				print("vertex, duplicate indexes: "+str(vertex_index)+", "+str(duplicate_index))

			if not cal3d_vertex:
				vertex = mesh_data.vertices[vertex_index]
				if debug_export > 0:
					print("vertex "+str(vertex.co))

				normal = vertex.normal.copy()
				normal *= base_scale
				normal.rotate(total_rotation)
				normal.normalize()
				if debug_export > 0:
					print("vertex normal: "+str(normal))

				coord = vertex.co.copy()
				coord = coord + total_translation
				coord *= base_scale
				coord.rotate(total_rotation)

				# If we have shape keys (morph targets) then also compute their vertex info
				if do_shape_keys:
					sk_id = 0
					# loop over all ShapeKeys
					for kb in mesh_data.shape_keys.key_blocks[1:]:
						# Turn ShapeKey data into a Vector.
						blend_vertex = mathutils.Vector(kb.data[vertex_index].co.copy())
						if debug_export > 0:
							if vertex_index == 0:
								print("vertex 0: {0}\nblend vertex 0: {1}".format(str(vertex.co),str(blend_vertex)))

						# Get the previously collected normal for this ShapeKey and vertex index
						#print("shapekey normal indexes sk, vertex "+str(sk_id)+", "+str(vertex_index))
						# sk_normals index starts at 0 for First non Basis ShapeKey!
						sk_normal = sk_normals[sk_id][vertex_index].copy()
						#print("shapekey normal "+str(sk_normal)+", vert: "+str(blend_vertex))
						sk_normal *= base_scale
						sk_normal.rotate(total_rotation)
						sk_normal.normalize()

						if debug_export > 0:
							print("ShapeKey normal: "+str(sk_normal))

						# Compute ShapeKey position
						# jgb 2012-11-24 Now use the stored ShapeKey vertex instead of the data from the ShapeKey array
						sk_coord = sk_vertices[sk_id][vertex_index].copy()
						#sk_coord = blend_vertex.copy()
						sk_coord = sk_coord + total_translation
						sk_coord *= base_scale
						sk_coord.rotate(total_rotation)

						# Calculate posdiff between vertex and blend vertex
						# posdiff according to cal3d source in saver.cpp is computed as the absolute length of 
						# the difference between the vertex and blend vertex
						vec_posdiff = sk_coord - coord

						# Ignore this Blend Vector when difference is below Tolerance value
						# Note that the Cal3d saver uses different values for the binary saver and the xml saver
						# binary uses 0.01 and xml uses 1.0, We go in the middle with 0.1
						differenceTolerance = 0.1;
						posdiff = abs(vec_posdiff.length)
						if debug_export > 0:
							print("posdiff: "+str(posdiff)+" vec_posdiff: "+str(vec_posdiff))
						
						# Only add this Blend Vertex if there is enough difference with the original Vertex
						if posdiff >= differenceTolerance:
							# BlendVertex index should be same as exportindex for normal Vertex:
							bv_index = len(cal3d_submesh.vertices)
							# Add Blend Vertex
							cal3d_blend_vertex = BlendVertex( bv_index,
								sk_coord, sk_normal, posdiff)
							# For now we always use the same texture coordinates for vertex and blend vertex
							# According to Boris the engineer using different values may not work anyway
							for uv in uvs:
								cal3d_blend_vertex.maps.append(Map(uv[0], uv[1]))
							# Get corresponding morph in submesh
							sk_morph = cal3d_submesh.morphs[sk_id]
							# Add the blend vertex to morph
							sk_morph.blend_vertices.append(cal3d_blend_vertex)

						# Increment the current ShapeKey index
						sk_id += 1

				if duplicate:
					#print("duplicate vertex: "+str(coord))
					cal3d_vertex = Vertex(cal3d_submesh, duplicate_index,
					                      coord, normal, vertex_color)
					duplicate_index += 1

				else:
					cal3d_vertex = Vertex(cal3d_submesh, vertex_index,
					                      coord, normal, vertex_color)

				cal3d_vertex.influences = get_vertex_influences(vertex,
						                                        mesh_obj,
				                                                cal3d_skeleton,
																use_groups, use_envelopes, armature_obj)
				# jgb 2012-11-14 Add warning when vertex has no influences!
				if cal3d_vertex.influences == []:
					print("WARNING: vertex " + str(vertex.co) + " has no influences!")
				
				for uv in uvs:
					cal3d_vertex.maps.append(Map(uv[0], uv[1]))

				cal3d_submesh.vertices.append(cal3d_vertex)

			if not cal3d_vertex1:
				cal3d_vertex1 = cal3d_vertex
			elif not cal3d_vertex2:
				cal3d_vertex2 = cal3d_vertex
			elif not cal3d_vertex3:
				cal3d_vertex3 = cal3d_vertex
			elif not cal3d_vertex4:
				cal3d_vertex4 = cal3d_vertex

		cal3d_face = Face(cal3d_submesh, cal3d_vertex1,
		                  cal3d_vertex2, cal3d_vertex3,
		                  cal3d_vertex4)
		cal3d_submesh.faces.append(cal3d_face)


	bpy.data.meshes.remove(mesh_data)

	return cal3d_mesh

