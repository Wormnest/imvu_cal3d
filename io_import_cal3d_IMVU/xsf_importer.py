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

# This file is intended to be the XSF importer.
# Copyright 2012 Jacob Boerema

# Import some general stuff
import bpy
import mathutils
import math
from math import *
from mathutils import Vector, Matrix, Quaternion
from . import support_functions
from .support_functions import ReadNodeAsFloats, ReadNodeAsInt, ReadFloats, \
    quaternion_to_cal3d_matrix, cal3d_matrix3_multiply

# Read count string float values and return them as a list of floats
# Returns None if there is a different amount of floats than specified in count
# def ReadFloats(input,count):
    # if input:
        # # Cal3d XML divides float strings by a single space
        # floats = input.split(' ')
        # if len(floats) == count:
            # result = [float(f) for f in floats]
            # return result

    # # All other cases: there was an error
    # print("WARNING: incorrect number of input values")
    # return None


# # ReadNodeAsFloats read the xml node text which has count float values
# def ReadNodeAsFloats(tag, count):
    # data = tag.text
    # if data:
        # return ReadFloats(data,count)
    # else:
        # print("ERROR: tag {0} has no values".format(str(tag.tag)))
        # return None


# # ReadNodeAsInt read the xml node text as an int, in case of error return default_value
# def ReadNodeAsInt(tag, default_value):
    # data = tag.text
    # if data:
        # return int(data)
    # else:
        # print("ERROR: tag {0} has no value".format(str(tag.tag)))
        # return default_value

# Class Bone will hold the Bone data as read from XSF
class Bone():

    def __init__(self, name, id, numchilds):
        self.DEBUG = 1

        self.name = name
        self.id = id
        self.numchilds = numchilds
        self.lighttype = 0
        self.lightcolor = [0.0, 0.0, 0.0]
        self.translation = [0.0, 0.0, 0.0]
        self.rotation = [0.0, 0.0, 0.0, 0.0]
        self.localtranslation = [0.0, 0.0, 0.0]
        self.localrotation = [0.0, 0.0, 0.0, 0.0]
        self.parent = None
        self.children = []

    def SetLocation(self, translation, rotation, localtranslation, localrotation):
        if translation:
            self.translation = translation
        if rotation:
            self.rotation = rotation
        if localtranslation:
            self.localtranslation = localtranslation
        if localrotation:
            self.localrotation = localrotation

    def SetLight(self, lighttype, lightcolor):
        self.lighttype = lighttype
        self.lightcolor = lightcolor

    def SetParent(self, parent):
        self.parent = parent
        if parent:
            parent.children.append(self)

    # For debugging: print the values of Bone
    def PrintBone(self):
        print("Bone {0}, name: {1}, has {2} children".format(self.id,
            self.name, self.numchilds))
        if self.lighttype != 0:
            print("light type: {0}, light color: {1}, {2}, {3}".format(self.lighttype,
                str(self.lightcolor[0]), str(self.lightcolor[1]), str(self.lightcolor[2])))
        print("Translation: {0}, {1}, {2}".format(self.translation[0],
            self.translation[1], self.translation[2]))
        print("Rotation: {0}, {1}, {2}, {3}".format(self.rotation[0],
            self.rotation[1], self.rotation[2], self.rotation[3]))
        print("Local Translation: {0}, {1}, {2}".format(self.localtranslation[0],
            self.localtranslation[1], self.localtranslation[2]))
        print("Local Rotation: {0}, {1}, {2}, {3}".format(self.localrotation[0],
            self.localrotation[1], self.localrotation[2], self.localrotation[3]))
        if self.parent == None:
            print("Parent id: -1")
        else:
            print("Parent id: {0}, name: {1}".format(str(self.parent.id),self.parent.name))

# jgb 2012-12-04 utility functions now moved outside the Class
# Taken from: http://gamedev.stackexchange.com/questions/32529/calculating-the-correct-roll-from-a-bone-transform-matrix
# Which is a conversion of Blender's own c code:
# https://svn.blender.org/svnroot/bf-blender/trunk/blender/source/blender/blenkernel/intern/armature.c
# jgb 2012-12-02 value of 0.000000001 taken from the curren blender sourcecode, old value was 0.0000000001 (one 0 more)
X_ON = 0    # default 0
Y_ON = 1    # default 1
Z_ON = 0    # default 0
AXIS_ON_1 = 1   # default 1 (y)
AXIS_ON_2 = 1   # default 1
def vec_roll_to_mat3(vec, roll):
    global X_ON, Y_ON, Z_ON
    target = mathutils.Vector((X_ON,Y_ON,Z_ON)) # original/default = 0,1,0
    nor = vec.normalized()
    axis = target.cross(nor)
    if axis.dot(axis) > 0.000000001: # this seems to be the problem for some bones, no idea how to fix
        axis.normalize()
        theta = target.angle(nor)
        bMatrix = mathutils.Matrix.Rotation(theta, 3, axis)
    else:
        updown = 1 if target.dot(nor) > 0 else -1
        print("small axis.dot! Updown = {0}".format(updown))
        bMatrix = mathutils.Matrix.Scale(updown, 3)
        # jgb NOTE: original c code/old cal3d only seems to only change updown for first 2 rows not z row
        # INVESTIGATE!!!!!!! test below:
        #bMatrix[2][2] = 1
        # ##############
    rMatrix = mathutils.Matrix.Rotation(roll, 3, nor)
    mat = rMatrix * bMatrix
    #print("vec roll matrix: {0}".format(mat))
    return mat

# Taken from: http://gamedev.stackexchange.com/questions/32529/calculating-the-correct-roll-from-a-bone-transform-matrix
def mat3_to_vec_roll(mat):
    global AXIS_ON_1, AXIS_ON_2
    vec = mat.col[AXIS_ON_1]    # original was 1
    #print("mat col 1: {0}".format(vec))
    vecmat = vec_roll_to_mat3(mat.col[AXIS_ON_2], 0)    # original for AXIS_ON was 1
    vecmatinv = vecmat.inverted()
    rollmat = vecmatinv * mat
    roll = math.atan2(rollmat[0][2], rollmat[2][2])
    return vec, roll

# How to use them: [i.e. above function]

# pos = mymatrix.to_translation()
# axis, roll = mat3_to_vec_roll(mymatrix.to_3x3())

# bone = armature.edit_bones.new('name')
# bone.head = pos
# bone.tail = pos + axis
# bone.roll = roll

# Sadly, it seems even the Blender C code is buggy and doesn't take into account 
# cases when the bone is parallel to (0,1,0).
# So such bones can get assigned wrong (by 180 degrees) rolls and mess up animations.

# jgb 2012-12-03 found this link, http://forum.alternativaplatform.com/posts/list/10265.page
# link not working atm, what google lists: (try again later!)
#Here are the actual matrix data for the bones in blender . 
#RootBone. World Matrix 1, 0, 0, 0 0, 0, -1, 0 0, 1, 0, 0 0, 0, 0, 1 FirstBone. 
#World Matrix ...


# Class to do the actual importing of XSF
class ImportXsf():

    # Init variables of our class
    def __init__(self, skeleton):
        self.DEBUG = 0

        # Copy parameters
        self.skeleton = skeleton

        # Set some default initial values
        self.numbones = 0
        self.scene_ambient_color = [0.0, 0.0, 0.0]
        # bones will hold the info of all found bones, bone id is index into this list
        self.bones = []
        
        if self.DEBUG:
            print("init ImportXSF")


    # parse_xml: parses the xml and collects all needed data
    def parse_xml(self):

        if self.DEBUG:
            print("ImportXSF: parse xml")
            print("Reading Skeleton")

        # 1. Read the global skeleton values
        # 1.1 Get the number of bones in this skeleton
        numbones = self.skeleton.get('NUMBONES')
        if numbones:
            self.numbones = int(numbones)
        else:
            numbones = -1
        # 1.2 Get the scene ambient color
        sa_color = self.skeleton.get('SCENEAMBIENTCOLOR')
        # This tag is not required so just ignore without warning if its not there
        if sa_color:
            sac = ReadFloats(sa_color,3)
            if sac:
                self.scene_ambient_color = sac

        if self.DEBUG:
            print("Bonecount: "+self.numbones)
            print("Scene ambient color: "+str(self.scene_ambient_color))

        # 2. Loop over all the bones
        for i, bone in enumerate(self.skeleton):
            # Get the Bone info: name, id and number of children
            if bone.tag == "BONE":
                bone_name = bone.get("NAME")
                if bone_name == None:
                    bone_name = "UNKNOWN_"+str(i)
                    print("ERROR: can't find name of bone!")

                bone_id = bone.get("ID")
                if bone_id == None:
                    bone_id = -1
                    print("ERROR: can't find id of bone!")
                elif int(bone_id) != i:
                    print("ERROR: invalid bone id {0}, expected: {1}".format(str(bone_id),str(i)))
                    break

                bone_childs = bone.get("NUMCHILDS")
                if bone_childs == None:
                    bone_childs = 0
                    print("ERROR: can't find number of children of bone!")

                # optional lighttype and lightcolor values
                light_type = bone.get("LIGHTTYPE")
                if light_type == None:
                    light_type = 0
                str_light_color = bone.get("LIGHTCOLOR")
                light_color = [0.0, 0.0, 0.0]
                if str_light_color != None:
                    color = ReadFloats(str_light_color,3)
                    if color:
                        light_color = color

                # Add the bone to our list
                obj_bone = Bone(bone_name, bone_id, bone_childs)
                if obj_bone:
                    # Get the bone info: translations, rotations, parentid
                    trans = rot = loctrans = locrot = None
                    parent_id = -1
                    for child in bone:
                        if str(child.tag) == "TRANSLATION":
                            trans = ReadNodeAsFloats(child, 3)
                        elif str(child.tag) == "ROTATION":
                            rot = ReadNodeAsFloats(child, 4)
                        elif str(child.tag) == "LOCALTRANSLATION":
                            loctrans = ReadNodeAsFloats(child, 3)
                        elif  str(child.tag) == "LOCALROTATION":
                            locrot = ReadNodeAsFloats(child, 4)
                        elif  str(child.tag) == "PARENTID":
                            parent_id = ReadNodeAsInt(child, parent_id)
                        
                        # For now at least we are going to ignore CHILDID.
                        # We will encounter the child bones later on and will be able to
                        # connect them to this paren then

                    # Add bone object and set its parameters
                    self.bones.append(obj_bone)
                    obj_bone.SetLight(light_type, light_color)
                    obj_bone.SetLocation(trans,rot,loctrans,locrot)
                    if parent_id == -1:
                        parent = None
                    else:
                        parent = self.bones[parent_id]
                    obj_bone.SetParent(parent)
                    
                    if self.DEBUG:
                        obj_bone.PrintBone()

        if self.numbones != len(self.bones):
            print("WARNING: number of bones read ({0}) is not the same as the expected number of bones ({1})!".
                format(len(self.bones),self.numbones))

        if self.DEBUG:
            print("ImportXSF: parsing finished")

    # Add bone btree and all its children to armature arm
    def add_bone_tree(self, arm, btree, parent_bone):
        def isLeftHand(matrix):
            #Is the matrix a left-hand-system, or not?
            ma = matrix.to_euler().to_matrix()
            crossXY = ma[0].cross(ma[1])
            check = crossXY.dot(ma[2])
            print("LeftHand check: {0}".format(check))
            if check < 0.00001: return 1
            return 0

        # FOR DEBUGGING ONLY
        MAX_DEBUG_BONE = 5
        if int(btree.id) > MAX_DEBUG_BONE:
            return
        # ###############
        # info

        Config_RotateX = 0
        Config_CoordinateSystem = 0 # 1 left hand, 2 right hand
        SystemMatrix = Matrix()
        NegRotX4 = Matrix.Rotation(radians(-90), 4, "X")
        NegRotZ4 = Matrix.Rotation(radians(-90), 4, "Z")
        PosRotZ4 = Matrix.Rotation(radians(90), 4, "Z")

        NegRotX3 = Matrix.Rotation(radians(-90), 3, "X")
        PosRotX3 = Matrix.Rotation(radians(90), 3, "X")
        NegRotY3 = Matrix.Rotation(radians(-90), 3, "Y")
        PosRotY3 = Matrix.Rotation(radians(90), 3, "Y")
        NegRotZ3 = Matrix.Rotation(radians(-90), 3, "Z")
        PosRotZ3 = Matrix.Rotation(radians(90), 3, "Z")
        NegScaleY4 = Matrix.Scale(-1, 4, Vector((0, 1, 0)))
        if Config_RotateX:
            SystemMatrix *= NegRotX4
        if Config_CoordinateSystem == 1:
            SystemMatrix *= NegScaleY4
            print("{0} = System Matrix".format(SystemMatrix))
        elif Config_RotateX:
            print("")
        else:
            print("<SystemMatrix is Identity>")

        # Console output handling
        if btree.parent is not None:
            bparent = btree.parent.name
            LINE_LEN = 80
            BASE_DASH_LEN = 60
            SPACE_LEN = 5
            #print(dir(btree.name))
            line_length = BASE_DASH_LEN+SPACE_LEN+len(btree.name)
            dash_len = BASE_DASH_LEN
            if line_length > LINE_LEN:
                if line_length < (2*LINE_LEN):
                    dash_len -= (line_length-LINE_LEN)
                else:
                    dash_len = 10
            
            print("-"*dash_len + " "*SPACE_LEN + btree.name)

            #print("Adding bone: {0} as child of: {1}".format(btree.name,bparent))
            TRY_CROSS_DOT = 0
            if TRY_CROSS_DOT == 1:
                # Testing code from MaxInterface
                pm = parent_bone.matrix.to_3x3()
                # Looks like Max uses columns instead of rows? (since row3 = translation part)
                TRY_COL = 0
                TRY_ROW = 1
                if TRY_COL:
                    vec1 = pm.col[0].normalized()
                    vec2 = pm.col[1].normalized()
                    vec3 = pm.col[2].normalized()
                # try also rows:
                if TRY_ROW:
                    vec1 = pm.col[0].normalized()
                    vec2 = pm.col[1].normalized()
                    vec3 = pm.col[2].normalized()
                cross_vec = vec1.cross(vec2).normalized()
                dot_vec = cross_vec.dot(vec3)
                if TRY_COL == 1:
                    rc = "COLUMN"
                else:
                    rc = "ROW"
                print("dot(cross) {0} vector: {1}".format(rc,dot_vec))

        # TESTING
        # if btree.name == "lfHip":
            # # test negating the values
            # btree.translation[0] = -btree.translation[0]
            # btree.translation[1] = -btree.translation[1]
            # btree.translation[2] = -btree.translation[2]

        # 1. add bone
        bone = arm.edit_bones.new(btree.name)

        # Convert Cal3d xyzw roation to quaternion wxyz
        # Since the export script does -self.quat.inverted on export we do try the reverse here
        #bquat = mathutils.Quaternion([-btree.rotation[3], -btree.rotation[0], 
        #   -btree.rotation[1], -btree.rotation[2]]).inverted()
        # jgb 2012-12-03 Since cal3d rotation is counterclock and Blender clockwise we need to
        # negate the w sign here just as we do on export
        # NOT ENTIRELY SURE IF THIS IS CORRECT, TEST WITH/WITHOUT IT!
        NEGATE_QUAT_W = 0
        NEGATE_NON_ZERO = 0
        if NEGATE_QUAT_W == 1:
            NEGATE_NON_ZERO = 0     # MUTUALLY EXCLUSIVE
            btree.rotation[3] = -btree.rotation[3]
        if NEGATE_NON_ZERO == 1:
            if btree.rotation[0] != 0.0:
                btree.rotation[0] = -btree.rotation[0]
            if btree.rotation[1] != 0.0:
                btree.rotation[1] = -btree.rotation[1]
            if btree.rotation[2] != 0.0:
                btree.rotation[2] = -btree.rotation[2]

        bquat = mathutils.Quaternion((btree.rotation[3], btree.rotation[0], 
            btree.rotation[1], btree.rotation[2]))
        bmatrix = bquat.to_matrix()
        #print("{0} = bquat as Matrix".format(bmatrix))
        bloc = mathutils.Vector(btree.translation)
        btransmat = Matrix.Translation(bloc)
        loctrans = bloc
        
        # LEFT HANDED FUNCTION TESTING...
        # LH_matrix = support_functions.quaternion_to_cal3d_matrix(bquat)
        # bquat.w = -bquat.w
        # LH_matrix2 = support_functions.quaternion_to_cal3d_matrix(bquat)
        # print("{0} = bquat".format(bquat))
        # print("{0} = quat as Matrix (RH)\n{1} = quat as LH Matrix".format(bmatrix,LH_matrix))
        # print("{0} = quat as LH Matrix (uncorrected w)".format(LH_matrix))
        # TESTING_MATRIX = PosRotX3
        # test_RH_mat = bmatrix * TESTING_MATRIX
        # test_LH_mat = support_functions.cal3d_matrix3_multiply(LH_matrix, TESTING_MATRIX)
        # test_LH_mat2 = support_functions.cal3d_matrix3_multiply(TESTING_MATRIX,LH_matrix)
        # print("{0} = matrix mul RH\n{1} = matrix mul LH\n{1} = matrix mul LH2".format(test_RH_mat,test_LH_mat,test_LH_mat2))
        
        # #####################
        
        #bmat4 = Matrix.Translation(bloc) * bmatrix.to_4x4() * SystemMatrix
        #print("{0} = Matrix * System".format(bmat4))
        #testquat = bmat4.to_quaternion()
        #print("quat axis (%.2f, %.2f, %.2f), angle %.2f" % (testquat.axis[:] +
        #   (math.degrees(testquat.angle), )))

        # testing left hand:
        #if isLeftHand(bmatrix):
        #   print("LEFTHAND MATRIX!")
        # #########
        print("quat axis (%.2f, %.2f, %.2f), angle %.2f" % (bquat.axis[:] +
            (math.degrees(bquat.angle), )))
        print("quat as euler: %.2f, %.2f, %.2f" % tuple(math.degrees(a) for a in bquat.to_euler()))
        if parent_bone:
            pquat = parent_bone.matrix.to_quaternion()
            print("parent axis (%.2f, %.2f, %.2f), angle %.2f" % (pquat.axis[:] +
                (math.degrees(pquat.angle), )))
        
        # Test if we need to rotate the matrix
        # mat_rotx = mathutils.Matrix.Rotation(math.radians(90.0), 3, 'Y')
        # bmatrix = bmatrix * mat_rotx

        TEST1 = 0
        if TEST1 == 1:
            if parent_bone is not None:
                if int(btree.id) < 0:
                    print("rotation: {0}".format(str(btree.rotation)))
                    print("bquat: {0}".format(str(bquat)))
                    print("quat axis (%.2f, %.2f, %.2f), angle %.2f" % (bquat.axis[:] +
                        (math.degrees(bquat.angle), )))
                    print("bmatrix: {0}".format(str(bmatrix)))
                bone.parent = parent_bone
                bone.head = mathutils.Vector(btree.translation)
                bone.align_roll((parent_bone.matrix.to_3x3()*bmatrix)[2])
                #bone.head = parent_bone.tail
                #bone.align_roll((parent_bone.matrix.to_3x3()*bmatrix)[2])
                #bone.use_connect = True
            else:
                bone.head = mathutils.Vector(btree.translation)
                rot = Matrix.Translation((0,0,0))   # identity matrix
                bone.align_roll(bmatrix[2])
                #bone.head = (0,0,0)
                #rot = Matrix.Translation((0,0,0))  # identity matrix
                #bone.align_roll(bmatrix[2])
                #bone.use_connect = False
            if btree.children and len(btree.children) > 0:
                btail = mathutils.Vector(btree.children[0].translation)
                #bm = bmatrix.to_4x4()
                #btran = mathutils.Matrix.Translation(btree.translation)
                #bm = bm * btran
                #btail = mathutils.Matrix.to_translation(bm)
            else:
                btail = bone.head.copy()
                btail.z += 100.0    # TESTING!!
            bone.tail = btail
            #bone.tail = bone.head + mathutils.Vector(btree.translation)

        # TESTING
        #print("translation: {0}".format(str(mathutils.Vector(btree.translation))))
        #print("head: {0}\ntail: {1}".format(bone.head,bone.tail))
        lquat = mathutils.Quaternion([btree.localrotation[3], btree.localrotation[0], 
            btree.localrotation[1], btree.localrotation[2]])
        #print("lquat: "+str(lquat))
        #print("quat axis (%.2f, %.2f, %.2f), angle %.2f" % (lquat.axis[:] +
        #   (math.degrees(lquat.angle), )))
        lmat = lquat.to_matrix().to_4x4()
        ltran = mathutils.Matrix.Translation(btree.localtranslation)
        #print("ltran: "+str(ltran))
        lmat = lmat * ltran
        #lmat = lmat.inverted()
        #print("lmat: "+str(lmat))
        # #####

        # test 2 #
        TEST2 = 0
        if TEST2 == 1:
            mat2 = bmatrix.to_4x4() * mathutils.Matrix.Translation(btree.translation)
            if bone.parent is not None:
                par_mat = bone.parent.matrix.copy().inverted()
                # In exporter we do local matrix * inverted parent matrix
                # We need to do the inverse: matrix divided by the inverted parent:
                # Which I think the inverse of an inverted matrix is the matrix itself so just multiply?
                if int(btree.id) < 0:
                    print("matrix:\n{0}".format(str(mat2)))
                mat2 = mat2 * par_mat
                if int(btree.id) < 0:
                    print("matrix * parent matrix:\n{0}".format(str(mat2)))

        # 2012-12-02 new try: take into account the way its exported and revert that:
        TEST3 = 0
        if TEST3 == 1:
            transmat = mathutils.Matrix.Translation(btree.translation)
            if bone.parent is not None:
                print("translation: {0}\nhead of parent: {1}".format(
                    transmat.to_translation(),bone.parent.head))
                # # first take out the parent matrix
                # pmat = bone.parent.matrix.inverted().to_4x4()
                # #pmat = bone.parent.matrix.inverted().to_4x4()
                # locmat = transmat * pmat
                # #pquat = pmat.to_quaternion()
                # # Remove parent location from local location
                # loctrans = locmat.to_translation() + bone.parent.head.copy()
                # print("loc translation: {0}".format(loctrans))
                # if btree.name == "Bone.006" or btree.name == "lfHip":
                    # print("parent matrix inverted: {0}\nnormal: {1}\ntwice inverted: {2}".format(pmat,
                        # bone.parent.matrix.to_4x4(),pmat.inverted()))
                    # print("transmat: {0}\nlocmat: {0}".format(transmat,locmat))
                    # pquat = pmat.to_quaternion()  # pmat = inverted parent mat
                    # btrans = pquat * mathutils.Vector(btree.translation)
                    # print("pquat: {0}\nbtrans: {0}, \noriginal trans: {2}".format(pquat,btrans,mathutils.Vector(btree.translation)))
                    # m = pquat.to_matrix().to_4x4().inverted() * transmat
                    # print("m: {0}".format(m))
                    # # create a rotation matrix
                    # mat_rotx = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')
                    # print("mat_rot 90x: {0}".format(mat_rotx))
                    # mat_roty = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Y')
                    # print("mat_rot 90y: {0}".format(mat_roty))
                    # mat_rotz = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
                    # print("mat_rot 90z: {0}".format(mat_rotz))
                    # matx = mat_rotx * transmat
                    # maty = mat_roty * transmat
                    # matz = mat_rotz * transmat
                    # print("mat * 90x: {0}".format(matx))
                    # print("mat * 90y: {0}".format(maty))
                    # print("mat * 90z: {0}".format(matz))
                mat_local = bone.parent.matrix.to_4x4() * transmat
                print("parent mat * transmat: {0}".format(mat_local))
                locmat = mat_local.copy()
                loctrans = locmat.to_translation()
                # bp = bone.parent
                # while bp:
                    # bmatrix = bmatrix * bp.matrix.to_3x3()
                    # if int(btree.id) < 6:
                        # print("bmatrix: {0}".format(bmatrix))
                    # bp = bp.parent
                bmatrix = bmatrix * bone.parent.matrix.to_3x3()
                if btree.name.endswith("Hip-TURNED OFF"):
                    print("Rotating Hip bone -90 degrees over Z")
                    mat_rot_test = mathutils.Matrix.Rotation(math.radians(-90.0), 3, 'Z')
                    bmatrix = bmatrix * mat_rot_test
                #testmat = mathutils.matrix.
            else:
                locmat = transmat
                loctrans = locmat.to_translation()

        # new test 2012-12-21
        TEST4 = 1
        if TEST4 == 1:
            if parent_bone is None:
                # We are the root:
                #rootmat = Matrix.Translation(bloc) * bmatrix.to_4x4() * PosRotZ4
                rootmat = Matrix.Translation(bloc) * bmatrix.to_4x4()
                loctrans = rootmat.to_translation()
                bmatrix = rootmat.to_3x3()
            else:
                par_mat = parent_bone.matrix
                inv_par_mat = parent_bone.matrix.inverted()
                adjusted_mat1 = btransmat * par_mat
                adjusted_mat2 = btransmat * inv_par_mat
                local_trans1 = adjusted_mat1.to_translation() + parent_bone.head
                local_trans2 = adjusted_mat2.to_translation() #+ parent_bone.head
                print("{0} = local trans\n{1} = local trans inverted".format(local_trans1,local_trans2))
                loctrans = local_trans2
                #bone_mat = Matrix.Translation(bloc) * bmatrix.to_4x4() * parent_bone.matrix.inverted()
                #loctrans = bone_mat.to_translation()
                #bmatrix = bone_mat.to_3x3()
            

        
        POSITION_CODE_TO_USE = 0
        print("Matrix before Blender conversion:\n{0}".format(bmatrix))
        print("Same as quat: {0}".format(bmatrix.to_quaternion()))
        if POSITION_CODE_TO_USE == 0:
            pos = loctrans
            print("Vector columns 0,1,2:\n{0}\n{1}\n{2}".format(bmatrix.col[0],bmatrix.col[1],bmatrix.col[2]))
            axis, roll = mat3_to_vec_roll(bmatrix)
            if int(btree.id) < 10:
                print("pos: {0}\naxis: {1}, roll: {2}".format(str(pos),str(axis),str(roll)))

            bone.head = pos
            bone.tail = pos + (axis*100.0)
            
            # Question: doesn cal3d have the notion of roll? maybe we shouldnt define a roll????
            bone.roll = roll
            #bone.roll = 0.0
            
            # testing axis change:
            axis_mat = mathutils.Matrix.Translation(axis) * mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z')
            axis_quat = axis_mat.to_quaternion()
            axis_tail = axis_mat.to_translation()
            #print("TAIL quat axis (%.2f, %.2f, %.2f), angle %.2f" % (axis_quat.axis[:] +
            #   (math.degrees(axis_quat.angle), )))
            #print("TAIL axis: {0}".format(axis_tail))
        if POSITION_CODE_TO_USE == 1:
            # Test another solution for setting head and tail
            # This does not produce as good results as the one above because
            # as soon as you change a head or tail the bone matrix gets changed
            bone.head = Vector([0,0,0])
            bone.tail = Vector([0,100,0])   # try 100 at different axis?
            bone.transform(bmatrix) # try with roll = True/False ?????????????
            bone.translate(loctrans)

        print("Matrix after conversion:\n{0}".format(bone.matrix))
        print("Same as quat: {0}".format(bmatrix.to_quaternion()))

        if int(btree.id) < 10:
            print("head: {0}\ntail: {1}".format(bone.head,bone.tail))

        # 2. loop over all children
        for b in btree.children:
            self.add_bone_tree(arm, b, bone)

    # create_armature: convert the collected bone data into an armature
    def create_armature(self, armature_name):

        if self.DEBUG:
            print("ImportXSF: create armature")

        print("Create armature: {0}".format(armature_name))
        # Create armature and object
        arm_origin = arm_rotation = Vector((0,0,0))
        bpy.ops.object.add(type = 'ARMATURE', 
            enter_editmode = True,
            location = arm_origin,
            rotation = arm_rotation)
        ob = bpy.context.object
        ob.name = armature_name
        # test: Set rotation mode to Quaternion, dont wanna have problems with Euler Gimball lock
        ob.rotation_mode = "QUATERNION"
        arm = ob.data
        # We wanna see the axes and bone names
        arm.show_names = True
        arm.show_axes = True
        #print("World matrix: {0}".format(ob.matrix_world))

        # now go over all toplevel bones and add them and their children recursively
        for b in self.bones:
            # Handle only toplevel bones here
            if b.parent is None:
                print("Creating root level bone: {0}".format(b.name))
                self.add_bone_tree(arm, b, None)

        if self.DEBUG:
            print("ImportXSF: armature created")
