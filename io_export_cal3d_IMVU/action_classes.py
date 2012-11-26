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

import bpy
from mathutils import *

class KeyFrame:
	def __init__(self, time, loc, quat):
		self.time = time
		self.loc = loc.copy()
		self.quat = quat.copy()
 
	def to_cal3d_xml(self):
		s = "    <KEYFRAME TIME=\"{0:0.5f}\">\n".format(self.time)
		s += "      <TRANSLATION>{0:0.6f} {1:0.6f} {2:0.6f}</TRANSLATION>\n".format(self.loc[0], self.loc[1], self.loc[2])

		# jgb 2012-11-11 Maybe we need for w: -self.quat.w to get the same negative value as for the mesh.
		s += "      <ROTATION>{0:0.6f} {1:0.6f} {2:0.6f} {3:0.6f}</ROTATION>\n".format(self.quat.copy().x, 
		                                                           self.quat.copy().y, 
		                                                           self.quat.copy().z, 
		                                                           -self.quat.copy().w)
		s += "    </KEYFRAME>\n"
		return s

		
	def to_cal3d_binary(self, file):
		ar = array('f', [self.time,
						 self.loc[0],
						 self.loc[1],
						 self.loc[2],
						 self.quat.copy().x, 
						 self.quat.copy().y,
						 self.quat.copy().z,
						 -self.quat.copy().w])
		ar.tofile(file)



class Track:
	def __init__(self, bone_index):
		self.bone_index = bone_index
		self.keyframes = []
		# jgb 2012-11-14 If I'm reading the Cal3d source correctly (saver.cpp, CalSaver::saveXmlCoreAnimation)
		# Then TRANSLATIONREQUIRED=1 means there will be a TRANSLATION record for the first keyframe
		# The next keyframes don't require a TRANSLATION record, unless TRANSLATIONISDYNAMIC=1, then every keyframe needs it.
		# Therefore we set translationisdynamic to 1 here.
		# Seems highrangerequired also defaults to true (see xmlformat.cpp, CalCoreAnimationPtr CalLoader::loadXmlCoreAnimation)
		# highrangerequired seems to be used to compress animation, when it's off it uses some bits for other purposes, we leave it on for now
		# TODO: We should make this dependent on whether or not we actually need to use the translation record or not.
		self.translationrequired = 1
		self.translationisdynamic = 1
		self.highrangerequired = 1


	def to_cal3d_xml(self):
		s = "  <TRACK BONEID=\"{0}\" TRANSLATIONREQUIRED=\"{1}\" TRANSLATIONISDYNAMIC=\"{2}\" ".format(self.bone_index, self.translationrequired, self.translationisdynamic)
		s += "HIGHRANGEREQUIRED=\"{0}\" NUMKEYFRAMES=\"{1}\">\n".format(self.highrangerequired, len(self.keyframes))
		s += "".join(map(KeyFrame.to_cal3d_xml, self.keyframes))
		s += "  </TRACK>\n"
		return s

		
	def to_cal3d_binary(self, file):
		ar = array('L', [self.bone_index,
						 len(self.keyframes)])
		ar.tofile(file)
		
		for kf in self.keyframes:
			kf.to_cal3d_binary(file)



class Animation:
	def __init__(self, name, xml_version):
		self.name = name
		self.xml_version = xml_version
		self.duration = 0.0
		self.tracks = []


	def to_cal3d_xml(self):
		s = "<HEADER MAGIC=\"XAF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
		s += "<ANIMATION DURATION=\"{0:0.5f}\" NUMTRACKS=\"{1}\">\n".format(self.duration, len(self.tracks))
		s += "".join(map(Track.to_cal3d_xml, self.tracks))
		s += "</ANIMATION>\n"
		return s

		
	def to_cal3d_binary(self, file):
		s = b'CAF\0'
		ar = array('b', list(s))
		ar.tofile(file)
		
		# Etory : downgrade version to 700 for Cal3D 0.11 compatibility
		ar = array('L', [700])
		ar.tofile(file)
		
		ar = array('L', [0]) # this is an unknown value that has to be there
		ar.tofile(file)
		
		ar = array('f', [self.duration])
		ar.tofile(file)
		
		ar = array('L', [len(self.tracks),
						 0]) # flags for tracks      Bit 0: 1 if compressed tracks
		ar.tofile(file)
		
		if ar[1] == 0: # normal uncompressed tracks
			for tr in self.tracks:
				tr.to_cal3d_binary(file)
		else: # compressed tracks
			for tr in self.tracks: # not sure what to do here yet
				tr.to_cal3d_binary(file)


# ====================================
# ========== Morph animations ==========
# ====================================

# Class MorphKeyFrame store a keyframe of a morph animation and allows export to XML only.
class MorphKeyFrame:
	def __init__(self, time, weight):
		self.time = time
		self.weight = weight
 
	def to_cal3d_xml(self):
		s = "    <KEYFRAME TIME=\"{0:0.5f}\">\n".format(self.time)
		s += "      <WEIGHT>{0:0.6f}</WEIGHT>\n".format(self.weight)
		s += "    </KEYFRAME>\n"
		return s


# Class MorphTrack stores Morph Animation tracks and allows XML export only.
class MorphTrack:
	def __init__(self, morph_name):
		self.morph_name = morph_name
		self.keyframes = []


	def to_cal3d_xml(self):
		s = "  <TRACK NUMKEYFRAMES=\"{0}\" MORPHNAME=\"{1}\">\n".format(len(self.keyframes), self.morph_name)
		s += "".join(map(MorphKeyFrame.to_cal3d_xml, self.keyframes))
		s += "  </TRACK>\n"
		return s


# Class MorphAnimation stores morph animation data and allows XML export only.
class MorphAnimation:
	def __init__(self, name, xml_version):
		self.name = name
		self.xml_version = xml_version
		self.duration = 0.0
		self.morph_tracks = []


	def to_cal3d_xml(self):
		s = "<HEADER MAGIC=\"XPF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
		s += "<ANIMATION NUMTRACKS=\"{0}\" DURATION=\"{1:0.5f}\">\n".format(len(self.morph_tracks), self.duration)
		s += "".join(map(MorphTrack.to_cal3d_xml, self.morph_tracks))
		s += "</ANIMATION>\n"
		return s
