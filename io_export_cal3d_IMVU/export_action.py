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

from . import armature_classes
from .armature_classes import *

from . import action_classes
from .action_classes import *

def get_action_group_fcurve(action_group, data_path, array_index):
	for fcu in action_group.channels:
		if fcu.data_path.find(data_path) != -1 and \
		    fcu.array_index == array_index:
			return fcu

	return None


def get_keyframes_list(fcu):
	keyframes_list = []
	if fcu:
		for keyframe in fcu.keyframe_points:
			keyframes_list.append(keyframe.co[0])
	return keyframes_list


def evaluate_loc(loc_x_fcu, loc_y_fcu, loc_z_fcu, keyframe):
	loc_x = 0.0
	loc_y = 0.0
	loc_z = 0.0

	if loc_x_fcu:
		loc_x = loc_x_fcu.evaluate(keyframe)

	if loc_y_fcu:
		loc_y = loc_y_fcu.evaluate(keyframe)

	if loc_z_fcu:
		loc_z = loc_z_fcu.evaluate(keyframe)

	return mathutils.Vector([loc_x, loc_y, loc_z])


def evaluate_quat(quat_x_fcu, quat_y_fcu, quat_z_fcu, quat_w_fcu, keyframe):
	quat_x = 0.0
	quat_y = 0.0
	quat_z = 0.0
	# jgb 2012-11-11 Blender has a w value of 1.0 when we haven't changed the rotation so try that instead of 0.0
	quat_w = 1.0

	if quat_x_fcu:
		quat_x = quat_x_fcu.evaluate(keyframe)

	if quat_y_fcu:
		quat_y = quat_y_fcu.evaluate(keyframe)

	if quat_z_fcu:
		quat_z = quat_z_fcu.evaluate(keyframe)

	if quat_w_fcu:
		quat_w = quat_w_fcu.evaluate(keyframe)

	# jgb 2012-11-11 I think with quaternions w needs to come first, not last.
	return mathutils.Quaternion([quat_w, quat_x, quat_y, quat_z])


def track_sort_key(track):
	return track.bone_index


def create_cal3d_animation(cal3d_skeleton, action, fps, xml_version):
	cal3d_animation = Animation(action.name, xml_version)

	initialized_borders = False
	last_keyframe = 0
	first_keyframe = 0

	for action_group in action.groups:
		cal3d_bone = None

		for bone in cal3d_skeleton.bones:
			if bone.name == action_group.name:
				cal3d_bone = bone
				break

		if not cal3d_bone:
			print("WARNING: no bone found corresponding to action group "+action_group.name)
			continue

		cal3d_track = Track(cal3d_bone.index)

		loc_x_fcu = get_action_group_fcurve(action_group, "location", 0)
		loc_y_fcu = get_action_group_fcurve(action_group, "location", 1)
		loc_z_fcu = get_action_group_fcurve(action_group, "location", 2)

		# jgb NB: w first instead of last, thus has index 0, not 3!
		quat_w_fcu = get_action_group_fcurve(action_group,
				                             "rotation_quaternion", 0)
		quat_x_fcu = get_action_group_fcurve(action_group, 
				                             "rotation_quaternion", 1)
		quat_y_fcu = get_action_group_fcurve(action_group,
				                             "rotation_quaternion", 2)
		quat_z_fcu = get_action_group_fcurve(action_group,
				                             "rotation_quaternion", 3)

		keyframes_list = []

		keyframes_list.extend(get_keyframes_list(loc_x_fcu))
		keyframes_list.extend(get_keyframes_list(loc_y_fcu))
		keyframes_list.extend(get_keyframes_list(loc_z_fcu))

		keyframes_list.extend(get_keyframes_list(quat_x_fcu))
		keyframes_list.extend(get_keyframes_list(quat_y_fcu))
		keyframes_list.extend(get_keyframes_list(quat_z_fcu))
		keyframes_list.extend(get_keyframes_list(quat_w_fcu))

		# remove duplicates
		keyframes_set = set(keyframes_list)
		keyframes_list = list(keyframes_set)
		keyframes_list.sort()
		
		if len(keyframes_list) == 0:
			print("WARNING: no keyframes in action group "+action_group.name)
			continue

		if initialized_borders:
			first_keyframe = min(keyframes_list[0], first_keyframe)
			last_keyframe = max(keyframes_list[len(keyframes_list) - 1], 
			                    last_keyframe)
		else:
			first_keyframe = keyframes_list[0]
			last_keyframe = keyframes_list[len(keyframes_list) - 1]
			initialized_borders = True

		cal3d_track.keyframes = []

		for keyframe in keyframes_list:
			dloc = evaluate_loc(loc_x_fcu, loc_y_fcu, loc_z_fcu, keyframe)
			dquat = evaluate_quat(quat_x_fcu, quat_y_fcu, 
			                      quat_z_fcu, quat_w_fcu, keyframe)

			quat = dquat.copy()
			quat.rotate(cal3d_bone.quat)
			quat.normalize()

			dloc.x *= cal3d_skeleton.anim_scale.x
			dloc.y *= cal3d_skeleton.anim_scale.y
			dloc.z *= cal3d_skeleton.anim_scale.z

			dloc.rotate(cal3d_bone.quat)
			loc = cal3d_bone.loc + dloc

			cal3d_keyframe = KeyFrame(keyframe, loc, quat)
			cal3d_track.keyframes.append(cal3d_keyframe)

		if len(cal3d_track.keyframes) > 0:
			cal3d_animation.tracks.append(cal3d_track)

	cal3d_animation.duration = ((last_keyframe - first_keyframe) / fps)
	cal3d_animation.tracks.sort(key=track_sort_key)

	for track in cal3d_animation.tracks:
		for keyframe in track.keyframes:
			keyframe.time = (keyframe.time - first_keyframe) / fps


	if len(cal3d_animation.tracks) > 0:
		return cal3d_animation

	return None

def MorphFromDataPath(dataPath):
	if dataPath.startswith("key_blocks["):
		words = dataPath.split('"')
		if len(words) == 3:
			return words[1]
		else:
			print("UNEXPECTED datapath type!")
			#  e.g. location
			return None
	else:
		print("UNEXPECTED datapath type!")
		return None

# jgb: Morph animation export handler based on the normal animation handler
# Note: the shape_keys parameter is currently not used but as I'm not sure whether I won't need it
# in the future here I'm leaving it in
def create_cal3d_morph_animation(shape_keys, action, fps, xml_version):
	cal3d_morph_animation = MorphAnimation(action.name, xml_version)
	print("Morph animation: "+action.name)
	# determine animation duration
	cal3d_morph_animation.duration = ((action.frame_range.y - action.frame_range.x) / fps)


#	last_keyframe = 0
#	first_keyframe = 0

#	for sk in shape_keys:
#		for kb in sk.key_blocks[1:]:

	# loop over  all curves in this action
	for fcu in action.fcurves:
		# Decipher morph name  from datapath
		morph_name = MorphFromDataPath(fcu.data_path)
		if morph_name:
			# Add a track with this morphname
			cal3d_morph_track = MorphTrack(morph_name)
			if cal3d_morph_track:
				# Add track to morph animation
				cal3d_morph_animation.morph_tracks.append(cal3d_morph_track)
				#print("Track for morph name:"+morph_name)
				if len(fcu.keyframe_points) > 0:
					# Keyframes present
					for key in fcu.keyframe_points:
						# value = weight in this context
						frame, value = key.co
						# Compute KeyFrame time from frame and framerate
						frame_time = frame / fps
						# Add KeyFrame for morph
						cal3d_morph_key_frame = MorphKeyFrame(frame_time,value)
						if cal3d_morph_key_frame:
							#print("frame, weight: "+ str(frame)+", "+str(value))
							cal3d_morph_track.keyframes.append(cal3d_morph_key_frame)
				else:
					print("WARNING: no keyframe points for morph "+morph_name)

# TODO: change Frame to seconds!!!!!!!!!!!!!!!!!

	return cal3d_morph_animation

	for action_group in action.groups:

		# TODO: test if Action name same as ShapeKey name ???? is this useful and necessary?
		#if not cal3d_bone:
		#	print("WARNING: no bone found corresponding to action group "+action_group.name)
		#	continue
		
		print("action group: "+action_group.name)

		weight_fcu = get_action_group_fcurve(action_group, "value", 0)
		print("weight: "+str(weight_fcu))

		# loc_x_fcu = get_action_group_fcurve(action_group, "location", 0)
		# loc_y_fcu = get_action_group_fcurve(action_group, "location", 1)
		# loc_z_fcu = get_action_group_fcurve(action_group, "location", 2)

		# # jgb NB: w first instead of last, thus has index 0, not 3!
		# quat_w_fcu = get_action_group_fcurve(action_group,
				                             # "rotation_quaternion", 0)
		# quat_x_fcu = get_action_group_fcurve(action_group, 
				                             # "rotation_quaternion", 1)
		# quat_y_fcu = get_action_group_fcurve(action_group,
				                             # "rotation_quaternion", 2)
		# quat_z_fcu = get_action_group_fcurve(action_group,
				                             # "rotation_quaternion", 3)

		# keyframes_list = []

		# keyframes_list.extend(get_keyframes_list(loc_x_fcu))
		# keyframes_list.extend(get_keyframes_list(loc_y_fcu))
		# keyframes_list.extend(get_keyframes_list(loc_z_fcu))

		# keyframes_list.extend(get_keyframes_list(quat_x_fcu))
		# keyframes_list.extend(get_keyframes_list(quat_y_fcu))
		# keyframes_list.extend(get_keyframes_list(quat_z_fcu))
		# keyframes_list.extend(get_keyframes_list(quat_w_fcu))

		# # remove duplicates
		# keyframes_set = set(keyframes_list)
		# keyframes_list = list(keyframes_set)
		# keyframes_list.sort()
		
		# if len(keyframes_list) == 0:
			# print("WARNING: no keyframes in action group "+action_group.name)
			# continue

		# if initialized_borders:
			# first_keyframe = min(keyframes_list[0], first_keyframe)
			# last_keyframe = max(keyframes_list[len(keyframes_list) - 1], 
			                    # last_keyframe)
		# else:
			# first_keyframe = keyframes_list[0]
			# last_keyframe = keyframes_list[len(keyframes_list) - 1]
			# initialized_borders = True

		# cal3d_track.keyframes = []

		# for keyframe in keyframes_list:
			# dloc = evaluate_loc(loc_x_fcu, loc_y_fcu, loc_z_fcu, keyframe)
			# dquat = evaluate_quat(quat_x_fcu, quat_y_fcu, 
			                      # quat_z_fcu, quat_w_fcu, keyframe)

			# quat = dquat.copy()
			# quat.rotate(cal3d_bone.quat)
			# quat.normalize()

			# dloc.x *= cal3d_skeleton.anim_scale.x
			# dloc.y *= cal3d_skeleton.anim_scale.y
			# dloc.z *= cal3d_skeleton.anim_scale.z

			# dloc.rotate(cal3d_bone.quat)
			# loc = cal3d_bone.loc + dloc

			# cal3d_keyframe = KeyFrame(keyframe, loc, quat)
			# cal3d_track.keyframes.append(cal3d_keyframe)

		# if len(cal3d_track.keyframes) > 0:
			# cal3d_animation.tracks.append(cal3d_track)

	# cal3d_animation.duration = ((last_keyframe - first_keyframe) / fps)
	# cal3d_animation.tracks.sort(key=track_sort_key)

	# for track in cal3d_animation.tracks:
		# for keyframe in track.keyframes:
			# keyframe.time = (keyframe.time - first_keyframe) / fps


	# if len(cal3d_animation.tracks) > 0:
		# return cal3d_animation

	return None


