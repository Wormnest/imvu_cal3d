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
from array import array
from math import *

import string

import bpy
from mathutils import *

class Skeleton:
	def __init__(self, name, matrix, anim_scale, xml_version):
		self.name = name
		self.anim_scale = anim_scale.copy()
		self.matrix = matrix
		self.xml_version = xml_version
		self.bones = []
		self.next_bone_id = 0
		#DEBUG :
		#print("armature, matrice :", matrix)

		
	def to_cal3d_xml(self):
		s = "<HEADER MAGIC=\"XSF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
		s += "<SKELETON NUMBONES=\"{0}\">\n".format(len(self.bones))
		s += "".join(map(Bone.to_cal3d_xml, self.bones))
		s += "</SKELETON>\n"
		return s

		
	def to_cal3d_binary(self, file):
		s = b'CSF\0'
		ar = array('b', list(s))
		ar.tofile(file)

		# Etory : downgrade version to 700 for Cal3D 0.11 compatibility
		ar = array('I', [700, len(self.bones)])
		ar.tofile(file)
		
		for bn in self.bones:
			bn.to_cal3d_binary(file)

class Bone:
	def __init__(self, skeleton, parent, name, loc, rot):
		'''
		loc is the translation from the parent coordinate frame to the tail of the bone
		rot is the rotation from the parent coordinate frame to the tail of the bone
		'''
		
		self.parent = parent
		self.name = name
		self.children = []
		self.xml_version = skeleton.xml_version

		self.child_loc = loc.copy()

		self.quat = rot.copy()
		self.loc = loc.copy()
		self.matrix = self.quat.to_matrix().to_4x4()
		self.matrix[0][3] += self.loc[0]
		self.matrix[1][3] += self.loc[1]
		self.matrix[2][3] += self.loc[2]
		print("calculated matrix for bone "+self.name)
		print(self.matrix)

		if parent:
			self.matrix = parent.matrix * self.matrix
			parent.children.append(self)

		lmatrix = self.matrix.inverted()
		self.lloc = lmatrix.to_translation()
		self.lquat = lmatrix.to_quaternion()
		print("lloc, lquat:")
		print(self.lloc)
		print(self.lquat)

		self.skeleton = skeleton
		self.index = skeleton.next_bone_id
		skeleton.next_bone_id += 1
		skeleton.bones.append(self)

 
	def to_cal3d_xml(self):
		s = "  <BONE ID=\"{0}\" NAME=\"{1}\" NUMCHILDS=\"{2}\">\n".format(self.index,
		                                                                  self.name, 
		                                                                  len(self.children))

		s += "    <TRANSLATION>{0:0.6f} {1:0.6f} {2:0.6f}</TRANSLATION>\n".format(self.loc[0],
		                                                         self.loc[1],
		                                                         self.loc[2])

		# Etory : need negate quaternion values
		s += "    <ROTATION>{0:0.6f} {1:0.6f} {2:0.6f} {3:0.6f}</ROTATION>\n".format(-self.quat.inverted().x,
		                                                       -self.quat.inverted().y,
		                                                       -self.quat.inverted().z,
		                                                       -self.quat.inverted().w)

		s += "    <LOCALTRANSLATION>{0:0.6f} {1:0.6f} {2:0.6f}</LOCALTRANSLATION>\n".format(self.lloc[0],
		                                                                   self.lloc[1],
		                                                                   self.lloc[2])

		# Etory : need negate quaternion values
		s += "    <LOCALROTATION>{0:0.6f} {1:0.6f} {2:0.6f} {3:0.6f}</LOCALROTATION>\n".format(-self.lquat.inverted().x,
		                                                                 -self.lquat.inverted().y,
		                                                                 -self.lquat.inverted().z,
		                                                                 -self.lquat.inverted().w)

		if self.parent:
			s += "    <PARENTID>{0}</PARENTID>\n".format(self.parent.index)
		else:
			s += "    <PARENTID>{0}</PARENTID>\n".format(-1)
		s += "".join(map(lambda bone: "    <CHILDID>{0}</CHILDID>\n".format(bone.index),
		             self.children))
		s += "  </BONE>\n"
		return s

		
	def to_cal3d_binary(self, file):
		name = self.name
		name += '\0'
		ar = array('I', [len(name)])
		ar.tofile(file)
		
		ar = array('b', list(name.encode("utf8")))
		ar.tofile(file)

        
		ar = array('f', [self.loc[0],
						 self.loc[1],
						 self.loc[2],
						 -self.quat.inverted().x, # Etory : need negate quaternion values
						 -self.quat.inverted().y,
						 -self.quat.inverted().z,
						 -self.quat.inverted().w,

						 self.lloc[0],
						 self.lloc[1],
						 self.lloc[2],
						 -self.lquat.inverted().x, # Etory : need negate quaternion values
						 -self.lquat.inverted().y,
						 -self.lquat.inverted().z,
						 -self.lquat.inverted().w])

		ar.tofile(file)
		
		if self.parent:
			ar = array('I', [self.parent.index])
		else:
			ar = array('i', [-1])
		if self.children:
			ar.append(len(self.children))
			for ch in self.children:
				ar.append(ch.index)
		else:
			ar.append(0)
		ar.tofile(file)
