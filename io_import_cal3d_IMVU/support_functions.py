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

# Purpose of this file: support functions
# Copyright 2012-2013 Jacob Boerema


# Read count string float values and return them as a list of floats
# Returns None if there is a different amount of floats than specified in count
def ReadFloats(input,count):
    if input:
        # Cal3d XML divides float strings by a single space
        floats = input.split(' ')
        if len(floats) == count:
            result = [float(f) for f in floats]
            return result

    # All other cases: there was an error
    print("WARNING: incorrect number of input values")
    return None


# Read count string int values and return them as a list of ints
# Returns None if there is a different amount of ints than specified in count
def ReadInts(input,count):
    if input:
        # Cal3d XML divides int strings by a single space
        ints = input.split(' ')
        if len(ints) == count:
            result = [int(f) for f in ints]
            return result

    # All other cases: there was an error
    print("WARNING: incorrect number of input values")
    return None


# ReadNodeAsFloats read the xml node text which has count float values
def ReadNodeAsFloats(tag, count):
    data = tag.text
    if data:
        return ReadFloats(data,count)
    else:
        print("ERROR: tag {0} has no values".format(str(tag.tag)))
        return None


# ReadNodeAsInt read the xml node text as an int, in case of error return default_value
def ReadNodeAsInt(tag, default_value):
    data = tag.text
    if data:
        return int(data)
    else:
        print("ERROR: tag {0} has no value".format(str(tag.tag)))
        return default_value


# ========== Support for Cal3d style left-handed math ==========
import mathutils
from mathutils import Vector, Matrix, Quaternion


# Converts a quaternion to a Cal3D style left-handed matrix (3x3)
# After testing seems that for this function there is no difference with making a normal Matrix
def quaternion_to_cal3d_matrix(q):
    print("quat: {0}".format(q))
    xx2=q.x*q.x*2
    yy2=q.y*q.y*2
    zz2=q.z*q.z*2
    xy2=q.x*q.y*2
    zw2=q.z*q.w*2
    xz2=q.x*q.z*2
    yw2=q.y*q.w*2
    yz2=q.y*q.z*2
    xw2=q.x*q.w*2
    # X column
    dxdx=1-yy2-zz2
    dxdy=  xy2+zw2
    dxdz=  xz2-yw2
    # Y column
    dydx=  xy2-zw2
    dydy=1-xx2-zz2
    dydz=  yz2+xw2
    # Z columns
    dzdx=  xz2+yw2
    dzdy=  yz2-xw2
    dzdz=1-xx2-yy2
    Mat = Matrix.Identity(3)
    # I guess the Cal3d code uses columns instead of rows for x,y,z
    #Mat[0].xyz = dxdx, dxdy, dxdz
    #Mat[1].xyz = dydx, dydy, dydz
    #Mat[2].xyz = dzdx, dzdy, dzdz
    Mat[0].xyz = dxdx, dydx, dzdx
    Mat[1].xyz = dxdy, dydy, dzdy
    Mat[2].xyz = dxdz, dydz, dzdz
    return Mat

# do matrix m1 * m2
def cal3d_matrix3_multiply(m1, m2):
    dxdx1, dydx1, dzdx1 = m1[0].xyz
    dxdy1, dydy1, dzdy1 = m1[1].xyz
    dxdz1, dydz1, dzdz1 = m1[2].xyz
    dxdx2, dydx2, dzdx2 = m2[0].xyz
    dxdy2, dydy2, dzdy2 = m2[1].xyz
    dxdz2, dydz2, dzdz2 = m2[2].xyz

    dxdx=dxdx2*dxdx1+dxdy2*dydx1+dxdz2*dzdx1;
    dydx=dydx2*dxdx1+dydy2*dydx1+dydz2*dzdx1;
    dzdx=dzdx2*dxdx1+dzdy2*dydx1+dzdz2*dzdx1;

    dxdy=dxdx2*dxdy1+dxdy2*dydy1+dxdz2*dzdy1;
    dydy=dydx2*dxdy1+dydy2*dydy1+dydz2*dzdy1;
    dzdy=dzdx2*dxdy1+dzdy2*dydy1+dzdz2*dzdy1;

    dxdz=dxdx2*dxdz1+dxdy2*dydz1+dxdz2*dzdz1;
    dydz=dydx2*dxdz1+dydy2*dydz1+dydz2*dzdz1;
    dzdz=dzdx2*dxdz1+dzdy2*dydz1+dzdz2*dzdz1;

    Mat = Matrix.Identity(3)
    Mat[0].xyz = dxdx, dydx, dzdx
    Mat[1].xyz = dxdy, dydy, dzdy
    Mat[2].xyz = dxdz, dydz, dzdz
    return Mat
