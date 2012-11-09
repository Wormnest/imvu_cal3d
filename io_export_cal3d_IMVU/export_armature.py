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

import os
from math import *

import bpy
from mathutils import *

from . import armature_classes
from .armature_classes import *


def treat_bone(b, scale, parent, skeleton):
	# skip bones that start with _
	# also skips children of that bone so be careful
	if len(b.name) == 0 or  b.name[0] == '_':
		return

	name = b.name
	bone_matrix = b.matrix.copy()

	#not used :
	bone_head = b.head.copy()
	bone_tail = b.tail.copy()

	if parent:
		# Compute the translation from the parent bone's head to the child
		# bone's head, in the parent bone coordinate system.
		# in 2.49 :
		#b.parent.matrix['ARMATURESPACE'].rotationPart() * (b.matrix['ARMATURESPACE'].translationPart() - b.parent.matrix['ARMATURESPACE'].translationPart())
		bone_trans = (b.matrix_local.to_translation()-b.parent.matrix_local.to_translation())*(b.parent.matrix_local.to_quaternion()).to_matrix()
		#Debug :
		#print("loc, bone :", name, bone_trans)
		#matrix2 = b.matrix_local.copy()
		#print("parent, matrice :", matrix2)
		bone_trans = (b.matrix_local.to_translation()-b.parent.matrix_local.to_translation())*(b.parent.matrix_local.to_quaternion()).to_matrix()
		bone_quat = bone_matrix.to_quaternion()
		bone = Bone(skeleton, parent, name, bone_trans, bone_quat)
	else:
		# Here, the translation is simply the head vector
		bone = Bone(skeleton, parent, name,
					(b.matrix_local * skeleton.matrix).to_translation(),
					b.matrix.to_quaternion())
		#Debug :
		#trans = skeleton.matrix.to_translation()
		#print("root bone :", trans)
		#matrix2 = b.matrix_local* skeleton.matrix
		#print("local, matrice :", matrix2)

	for child in b.children:
		treat_bone(child, scale, bone, skeleton)
	


def create_cal3d_skeleton(arm_obj, arm_data,
						  base_rotation,
						  base_translation,
						  base_scale,
						  xml_version):

	#not used
	base_matrix = Matrix.Scale(base_scale, 4)          * \
	              base_rotation.to_4x4()               * \
	              Matrix.Translation(base_translation) * \
	              arm_obj.matrix_world

	#not used
	(total_translation, total_rotation, total_scale) = arm_obj.matrix_world.decompose()

	skeleton = Skeleton(arm_obj.name, arm_obj.matrix_world, total_scale, xml_version)

	#not used
	scalematrix = Matrix()
	scalematrix[0][0] = total_scale.x
	scalematrix[1][1] = total_scale.y
	scalematrix[2][2] = total_scale.z

	for bone in arm_data.bones.values():
		if not bone.parent and bone.name[0] != "_":
			treat_bone(bone, scalematrix, None, skeleton)

	return skeleton

