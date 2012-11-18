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

from operator import attrgetter
from array import array

class MaterialColor:
	def __init__(self, r, g, b, a):
		self.r = r
		self.g = g
		self.b = b
		self.a = a



class Material:
	def __init__(self, name, index, xml_version):
		self.ambient = MaterialColor(255, 255, 255, 255)
		self.diffuse = MaterialColor(255, 255, 255, 255)
		self.specular = MaterialColor(0, 0, 0, 255)
		self.shininess = 0.0
		self.maps_filenames = []
    
		self.name = name
		self.index = index
		# jgb 2012-11-15 Add flag in_use to track which materials are actually used in meshes
		self.in_use = False
		# used_index = Index into used materials (default -1 for not in use)
		self.used_index = -1
		self.xml_version = xml_version


	def to_cal3d_xml(self):
		s = "<HEADER MAGIC=\"XRF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
		s += "  <MATERIAL NUMMAPS=\"{0}\">\n".format(len(self.maps_filenames))

		s += "  <AMBIENT>{0} {1} {2} {3}</AMBIENT>\n".format(self.ambient.r, 
		                                                     self.ambient.g, 
		                                                     self.ambient.b, 
		                                                     self.ambient.a)

		s += "  <DIFFUSE>{0} {1} {2} {3}</DIFFUSE>\n".format(self.diffuse.r,
		                                                     self.diffuse.g,
		                                                     self.diffuse.b,
		                                                     self.diffuse.a)

		s += "  <SPECULAR>{0} {1} {2} {3}</SPECULAR>\n".format(self.specular.r,
		                                                       self.specular.g, 
		                                                       self.specular.b,
		                                                       self.specular.a)

		s += "  <SHININESS>{0:0.6f}</SHININESS>\n".format(self.shininess)

		for map_filename in self.maps_filenames:
			s += "  <MAP>{0}</MAP>\n".format(map_filename)
		s += "</MATERIAL>\n"
		return s

		
	def to_cal3d_binary(self, file):
		s = b'CRF\0'
		ar = array('b', list(s))
		ar.tofile(file)

		# Etory : downgrade version to 700 for Cal3D 0.11 compatibility
		ar = array('I', [700])
		ar.tofile(file)
		
		ar = array('B', [self.ambient.r, 
		                 self.ambient.g, 
		                 self.ambient.b, 
		                 self.ambient.a,
						 self.diffuse.r, 
		                 self.diffuse.g, 
		                 self.diffuse.b, 
		                 self.diffuse.a,
						 self.specular.r, 
		                 self.specular.g, 
		                 self.specular.b, 
		                 self.specular.a])
		ar.tofile(file)
		
		ar = array('f', [self.shininess])
		ar.tofile(file)
		
		ar = array('I', [len(self.maps_filenames)])
		ar.tofile(file)
		
		for map_filename in self.maps_filenames:
			map_filename += '\0' # all strings end in null
			ar = array('I', [len(map_filename)])
			ar.tofile(file)
			
			ar = array('b', list(map_filename.encode("utf8")))
			ar.tofile(file)

			

class Map:
	def __init__(self, u, v):
		self.u = u
		self.v = v
    
    
	def to_cal3d_xml(self):
		return "      <TEXCOORD>{0:0.6f} {1:0.6f}</TEXCOORD>\n".format(self.u, self.v)

		
	def to_cal3d_binary(self, file):
		ar = array('f', [self.u, self.v])
		ar.tofile(file)



class Influence:
	def __init__(self, bone_index, weight):
		self.bone_index = bone_index
		self.weight = weight
    
	
	def to_cal3d_xml(self):
		return "      <INFLUENCE ID=\"{0}\">{1:0.6f}</INFLUENCE>\n".format(self.bone_index, 
		                                                              self.weight)

		
	def to_cal3d_binary(self, file):
		ar = array('L', [self.bone_index])
		ar.tofile(file)
		ar = array('f', [self.weight])
		ar.tofile(file)



class Vertex:
	# jgb 2012-11-07 Add vertex color to mesh
	def __init__(self, submesh, index, loc, normal, vertex_color):
		self.submesh = submesh
		self.index = index
		# jgb 2012-11-06 vertex indexes should be exported  starting from 0 for every submesh apparently to work in imvu
		self.exportindex = len(submesh.vertices)
		# jgb 2012-11-07 Store vertex color of this vertex
		self.vertex_color = vertex_color

		self.loc = loc.copy()
		self.normal = normal.copy()
		self.maps = []
		self.influences = []
		self.weight = 0.0
		self.hasweight = False


	def to_cal3d_xml(self):
		# sort influences by weights, in descending order
		self.influences = sorted(self.influences, key=attrgetter('weight'), reverse=True)

		# normalize weights
		total_weight = 0.0
		for influence in self.influences:
			total_weight += influence.weight

		if total_weight != 1.0:
			for influence in self.influences:
				influence.weight /= total_weight
		
		s = "    <VERTEX ID=\"{0}\" NUMINFLUENCES=\"{1}\">\n".format(self.exportindex,
		                                                             len(self.influences))
		s += "      <POS>{0:0.6f} {1:0.6f} {2:0.6f}</POS>\n".format(self.loc[0],
		                                             self.loc[1], 
		                                             self.loc[2])

		s += "      <NORM>{0:0.6f} {1:0.6f} {2:0.6f}</NORM>\n".format(self.normal[0],
		                                               self.normal[1],
		                                               self.normal[2])

		s += "      <COLOR>{0:0.3f} {1:0.3f} {2:0.3f}</COLOR>\n".format(self.vertex_color[0],
		                                               self.vertex_color[1],
		                                               self.vertex_color[2])

		s += "".join(map(Map.to_cal3d_xml, self.maps))
		s += "".join(map(Influence.to_cal3d_xml, self.influences))
		if self.hasweight:
			s += "      <PHYSIQUE>{0:0.6f}</PHYSIQUE>\n".format(self.weight)
		s += "    </VERTEX>\n"
			
		return s

		
	def to_cal3d_binary(self, file):
		# sort influences by weights, in descending order
		self.influences = sorted(self.influences, key=attrgetter('weight'), reverse=True)

		# normalize weights
		total_weight = 0.0
		for influence in self.influences:
			total_weight += influence.weight

		if total_weight != 1.0:
			for influence in self.influences:
				influence.weight /= total_weight
		
		ar = array('f', [self.loc[0],
						 self.loc[1], 
						 self.loc[2],
						 self.normal[0],
						 self.normal[1],
						 self.normal[2]])
		ar.tofile(file)
		
		ar = array('I', [0, #collapse id
						 0]) #face collapse count
		ar.tofile(file)
		
		for mp in self.maps:
			mp.to_cal3d_binary(file)
			
		ar = array('I', [len(self.influences)])
		ar.tofile(file)
		
		for ic in self.influences:
			ic.to_cal3d_binary(file)
			
		if self.hasweight:
			ar = array('f', [self.weight])
			ar.tofile(file) # writes the weight as a float for cloth hair animation (0.0 == rigid)



class Spring:
	def __init__(self, vertex1, vertex2, spring_coef, idle_length):
		self.vertex1 = vertex1
		self.vertex2 = vertex2
		self.spring_coef = spring_coef
		self.idle_length = idle_length


	def to_cal3d_xml(self):
		s = "    <SPRING VERTEXID=\"{0} {1}\" COEF=\"{2:0.6f}\" LENGTH=\"{3:0.6f}\"/>\n".format(self.vertex1.index,
																					  self.vertex2.index,
																					  self.spring_coef,
																					  self.idle_length)

		
	def to_cal3d_binary(self, file):
		ar = array('I', [self.vertex1.index,
						 self.vertex2.index])
		ar.tofile(file)
		ar = array('f', [self.spring_coef,
						 self.idle_length])
		ar.tofile(file)



class Face:
	def __init__(self, submesh, vertex1, vertex2, vertex3, vertex4):
		self.vertex1 = vertex1
		self.vertex2 = vertex2
		self.vertex3 = vertex3
		self.vertex4 = vertex4
    
		self.can_collapse = 0
    
		self.submesh = submesh


	def to_cal3d_xml(self):
		if self.vertex4:
			s = "    <FACE VERTEXID=\"{0} {1} {2}\"/>\n".format(self.vertex1.exportindex,
			                                                    self.vertex2.exportindex,
			                                                    self.vertex3.exportindex)

			s += "    <FACE VERTEXID=\"{0} {1} {2}\"/>\n".format(self.vertex1.exportindex,
			                                                     self.vertex3.exportindex,
			                                                     self.vertex4.exportindex)
			return s
		else:
			return "    <FACE VERTEXID=\"{0} {1} {2}\"/>\n".format(self.vertex1.exportindex,
			                                                       self.vertex2.exportindex,
			                                                       self.vertex3.exportindex)

		
	def to_cal3d_binary(self, file):
		if self.vertex4:
			ar = array('I', [self.vertex1.exportindex,
							 self.vertex2.exportindex,
							 self.vertex3.exportindex,
							 self.vertex1.exportindex,
							 self.vertex3.exportindex,
							 self.vertex4.exportindex])
		else:
			ar = array('I', [self.vertex1.exportindex,
							 self.vertex2.exportindex,
							 self.vertex3.exportindex])
		
		ar.tofile(file)


class BlendVertex:
	# jgb 2012-11-07 Add vertex color to mesh
	def __init__(self, morph, index, loc, normal):
		self.morph = morph
		self.index = index
		self.exportindex = len(morph.blend_vertices)
		self.loc = loc.copy()
		self.normal = normal.copy()
		self.maps = []


	def to_cal3d_xml(self):
		s = "    <BLENDVERTEX ID=\"{0}\">\n".format(self.exportindex)
		s += "      <POSITION>{0:0.6f} {1:0.6f} {2:0.6f}</POSITION>\n".format(self.loc[0],
		                                             self.loc[1], 
		                                             self.loc[2])

		s += "      <NORMAL>{0:0.6f} {1:0.6f} {2:0.6f}</NORMAL>\n".format(self.normal[0],
		                                               self.normal[1],
		                                               self.normal[2])

		s += "".join(map(Map.to_cal3d_xml, self.maps))	# = TEXCOORD
		s += "    </BLENDVERTEX>\n"
			
		return s


class Morph:
	def __init__(self, name, morph_id, xml_version):
		self.name = name
		self.xml_version = xml_version
		self.blend_vertices = []
		self.morph_id = morph_id
		# TODO: find out if morph_id index is 0 base local to submesh or if it is a global id number for all morphs in this mesh
		# probably per submesh because we need vertex id to identify and vertex ids start at 0 for every submesh

	def to_cal3d_xml(self):
		# IMVU requires morph names (not counting Head morphs which are TODO here) to end in 1 of 4 names:
		# .Clamped, . Averaged, .Exclusive, or .Additive (see IMVU documentation on what they do)
		# We will give a warning here if the morph name doesn't conform to that
		if ! (self.name.endswith(".Exclusive") or self.name.endswith(".Additive") or
				self.name.endswith(".Averaged") or self.name.endswith(".Clamped")):
			print("WARNING: morph name doesn't end in one of the IMVU specified suffixes!")
		#  Morph has 2  xml formats: 1 without blendvertex data ends with />, the other 2 has a separate end morph tag
		s = "<MORPH NAME=\"{0}\" NUMBLENDVERTS=\"{1}\" MORPHID=\"{2}\"".format(len(self.name), len(self.blend_vertices), self.morph_id)
		if len(self.blend_vertices) > 0:
			s += ">\n"
			s += "".join(map(BlendVertex.to_cal3d_xml, self.blend_vertices))
			s += "</MORPH>\n"
		else:
			s += " />\n"
		return s


class SubMesh:
	# jgb 2012-11-05 add mesh_material_id
	# material_id is global blender/cal3d material id
	# mesh_material_id is id relative to current mesh which we need to determine which material belongs to which face
	def __init__(self, mesh, index, material_id, mesh_material_id):
		self.mesh = mesh
		self.index = index
		self.material_id = material_id
		self.mesh_material_id = mesh_material_id

		self.vertices = []
		self.faces = []
		self.nb_lodsteps = 0
		self.springs = []
		#jgb  morphs present in this submesh
		self.morphs = []


	def to_cal3d_xml(self):
		self.vertices = sorted(self.vertices, key=attrgetter('exportindex'))
		texcoords_num = 0
		if self.vertices and len(self.vertices) > 0:
			texcoords_num = len(self.vertices[0].maps)

		faces_num = 0
		for face in self.faces:
			if face.vertex4:
				faces_num += 2
			else:
				faces_num += 1

		s = "  <SUBMESH NUMVERTICES=\"{0}\" NUMFACES=\"{1}\" MATERIAL=\"{2}\" ".format(len(self.vertices),
		                                                                        faces_num,
		                                                                        self.material_id)

		s += "NUMLODSTEPS=\"{0}\" NUMSPRINGS=\"{1}\" NUMTEXCOORDS=\"{2}\" NUMMORPHS=\"{3}\">\n".format(self.nb_lodsteps,
			len(self.springs),
			texcoords_num,
			len(self.morphs))

		s += "".join(map(Vertex.to_cal3d_xml, self.vertices))
		if self.springs and len(self.springs) > 0:
			s += "".join(map(Spring.to_cal3d_xml, self.springs))
		if self.morphs and len(self.morphs) > 0:
			s += "".join(map(Morph.to_cal3d_xml, self.morphs))
		s += "".join(map(Face.to_cal3d_xml, self.faces))
		s += "  </SUBMESH>\n"
		return s

		
	def to_cal3d_binary(self, file):
		self.vertices = sorted(self.vertices, key=attrgetter('exportindex'))
		texcoords_num = 0
		if self.vertices and len(self.vertices) > 0:
			texcoords_num = len(self.vertices[0].maps)

		faces_num = 0
		for face in self.faces:
			if face.vertex4:
				faces_num += 2
			else:
				faces_num += 1

		ar = array('i', [self.material_id,
						 len(self.vertices),
						 faces_num,
						 self.nb_lodsteps,
						 len(self.springs),
						 texcoords_num])
		ar.tofile(file)
		
		for vt in self.vertices:
			vt.to_cal3d_binary(file)
		
		if self.springs and len(self.springs) > 0:
			for sp in self.springs:
				sp.to_cal3d_binary(file)
		
		for fc in self.faces:
			fc.to_cal3d_binary(file)


class Mesh:
	def __init__(self, name, xml_version):
		self.name = name
		self.xml_version = xml_version
		self.submeshes = [] 


	def to_cal3d_xml(self):
		s = "<HEADER MAGIC=\"XMF\" VERSION=\"{0}\"/>\n".format(self.xml_version)
		s += "<MESH NUMSUBMESH=\"{0}\">\n".format(len(self.submeshes))
		s += "".join(map(SubMesh.to_cal3d_xml, self.submeshes))
		s += "</MESH>\n"
		return s

		
	def to_cal3d_binary(self, file):
		s = b'CMF\0'
		ar = array('b', list(s))
		ar.tofile(file)

		# Etory : downgrade version to 700 for Cal3D 0.11 compatibility
		#ar = array('L', [1200])
		ar = array('I', [700])
		ar.tofile(file)
		
		ar = array('I', [len(self.submeshes)])
		ar.tofile(file)
		
		for sm in self.submeshes:
			sm.to_cal3d_binary(file)

	# jgb 2012-11-04 Get the submesh that has the requested material index assigned to it
	# jgb 2012-11-05 Need mesh_material_id to compare to mat which is id relative to mesh
	def get_submesh(self, mat):
		sm = None
		for sm in self.submeshes:
			if sm.mesh_material_id == mat:
				break
		return sm
