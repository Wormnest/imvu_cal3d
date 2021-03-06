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
from .logger_class import Logger, get_logger

class Skeleton:
    def __init__(self, name, matrix, anim_scale, xml_version, write_ambient_color):
        self.name = name
        self.anim_scale = anim_scale.copy()
        self.matrix = matrix
        self.xml_version = xml_version
        self.bones = []
        self.next_bone_id = 0
        # define default scene ambient color as used on KatsBits website
        self.scene_ambient_color = [0.525176, 0.555059, 0.545235]
        self.write_ambient_color = write_ambient_color
        #DEBUG :
        #print("armature, matrice :", matrix)

        
    def to_cal3d_xml(self):
        s = "<HEADER MAGIC=\"XSF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
        if self.write_ambient_color:
            s += "<SKELETON NUMBONES=\"{0}\" SCENEAMBIENTCOLOR=\"{1:0.6f} {2:0.6f} {3:0.6f}\">\n".format(len(self.bones), 
                self.scene_ambient_color[0],
                self.scene_ambient_color[1],
                self.scene_ambient_color[2])
        else:
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
    def __init__(self, skeleton, parent, name, loc, rot, lights):
        '''
        loc is the translation from the parent coordinate frame to the tail of the bone
        rot is the rotation from the parent coordinate frame to the tail of the bone
        '''
        
        # Initialize our logger
        self.LogMessage = get_logger()
        
        # jgb debug var (0=off)
        self.debug_bone = 0
        
        self.parent = parent
        self.name = name
        self.children = []
        self.xml_version = skeleton.xml_version
        
        # jgb Add light support
        self.is_light = False
        self.light_type = 0
        
        # See if we can determine if Bone is meant to be a light (name should start with either omni or spot)
        testname = self.name.lower()    # lowercase
        if str(testname).startswith("omni"):
            self.is_light = True
            self.light_type = 1
            self.LogMessage.log_message("    Omni light found: " + self.name)
        elif str(testname).startswith("spot"):
            self.is_light = True
            self.light_type = 3
            self.LogMessage.log_message("    Spot light found: " + self.name)
        if self.is_light:
            self.light_color = self.get_light_color(name, lights)
            self.LogMessage.log_message("    Light color: " + str(self.light_color))
        else:
            self.light_color = [0.0, 0.0, 0.0]

        self.child_loc = loc.copy()

        self.quat = rot.copy()
        self.loc = loc.copy()
        self.matrix = self.quat.to_matrix().to_4x4()
        self.matrix[0][3] += self.loc[0]
        self.matrix[1][3] += self.loc[1]
        self.matrix[2][3] += self.loc[2]
        if self.debug_bone > 0:
            self.LogMessage.log_debug("Calculated matrix for bone "+self.name)
            self.LogMessage.log_debug(self.matrix)

        if parent:
            self.matrix = parent.matrix * self.matrix
            parent.children.append(self)

        lmatrix = self.matrix.inverted()
        self.lloc = lmatrix.to_translation()
        self.lquat = lmatrix.to_quaternion()
        if self.debug_bone > 0:
            self.LogMessage.log_debug("lloc, lquat:")
            self.LogMessage.log_debug(self.lloc)
            self.LogMessage.log_debug(self.lquat)

        self.skeleton = skeleton
        self.index = skeleton.next_bone_id
        skeleton.next_bone_id += 1
        skeleton.bones.append(self)

    # Get the light color for the current light.
    # If a light with name "name" exists then take the color from that, else set default color
    def get_light_color(self, name, lights):
        if lights:
            #light = lights[name]
            light_index = lights.find(name)
            if light_index > -1:
            #if light:
                light = lights[light_index]
                return light.color

        # Set default color if no light with same name as light bone present
        self.LogMessage.log_warning ("No light called " + name + " found, setting default light color.")
        return [0.5, 0.5, 0.5]


    def to_cal3d_xml(self):
        s = "  <BONE NAME=\"{0}\" NUMCHILDS=\"{1}\" ID=\"{2}\"".format(
            self.name, 
            len(self.children),
            self.index)
        if self.is_light == True:
            s += " LIGHTTYPE=\"{0}\" LIGHTCOLOR=\"{1:0.6f} {2:0.6f} {3:0.6f}\">\n".format(self.light_type,
                self.light_color[0],
                self.light_color[1],
                self.light_color[2])
        else:
            s += ">\n"

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
