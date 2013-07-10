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

# This file is intended to be the main part of the XML importer.
# Copyright 2012-2013 Jacob Boerema


import sys
import bpy

# importer_main: Main function for importing Cal3D XML files
def importer_main(filename, name_only, file_ext, LogMessage):
    # XSF/CSF parser
    from . import xsf_importer
    from .xsf_importer import ImportXsf

    if file_ext.lower() == ".csf":
        # We need struct module for converting binary data
        import struct
        
        # Binary XSF file
        file = open(filename, "rb")
        close_file = True
        try:
            header = file.read(4)
            LogMessage.log_message("Read Header {0}".format(header))
            if header == b'CSF\0':
                #file.seek(4)
                #version_data = file.read(4)
                version = struct.unpack("<I", file.read(4))[0]
                if version > 0:
                    LogMessage.log_message("Cal3D CSF file version: {0}".format(version))
                    save_obj = bpy.context.object
                    if save_obj:
                        save_mode = save_obj.mode
                        bpy.ops.object.mode_set(mode='OBJECT')
                    #xsf_importer = ImportXsf(skeleton, LogMessage)
                    #xsf_importer.parse_xml()
                    #xsf_importer.create_armature(name_only)
                    obj = bpy.context.object
                    if obj and obj == save_obj:
                        bpy.ops.object.mode_set(mode=save_mode)
                
        finally:
            # Close input file
            if close_file:
                file.close()
    else:
        # We need an xml parser
        import xml.etree.ElementTree as ET

        file = open(filename, "rb")
        close_file = True
        try:
            LogMessage.log_message('Parsing XML...')
            # Set the xml parser
            parser = ET.XMLParser()

            # The XML parser won't recognize the first line of our XML correctly.
            # We are going to remove the / and pretend that the header line is the start tag of the root
            # Then at the end of the file we are going to add a closing /HEADER tag.
            data = file.read(65536)
            if data:
                # It seems that both  '/' and ' /' are possible
                str_data = str(data)
                findpos = str_data.find('/>')
                if findpos > -1:
                    # Everywhere 2 extra because of b' at start of data
                    # 2012-12-11: In case of extra linefeeds (\r\n) we get even more extra difference because of the slashes
                    # TODO FIX THIS
                    if str_data[findpos-1] == ' ':
                        endpos = findpos-3
                        startpos = findpos-1
                    else:
                        endpos = findpos-2
                        startpos = findpos-1
                    # feed part before ' /'
                    parser.feed(data[:endpos])
                    # feed part after ' /'
                    #print(data[:endpos])
                    #print("endpos {0}, startpos {1}".format(endpos,startpos))
                    #print(data[startpos:200])
                    parser.feed(data[startpos:])

                    # loop over the rest of the data
                    while 1:
                        data = file.read(65536)
                        if not data:
                            # The end: Add a closing /header tag
                            parser.feed('</HEADER>')
                            break
                        parser.feed(data)
                else:
                    LogMessage.log_error("File format not recognized")
                    return False

        finally:
            # Close input file
            if close_file:
                file.close()

        save_obj = bpy.context.object
        if save_obj:
            save_mode = save_obj.mode
            bpy.ops.object.mode_set(mode='OBJECT')

        # Close parsing and get the root
        root = parser.close()
        magic = root.get("MAGIC")
        version = root.get("VERSION")
        if magic == "XSF":
            #print("XML: magic is XSF")
            # start the XSF class
            skeleton = root.find('SKELETON')
            if skeleton is not None:    # This way because of a python warning about future changes
                LogMessage.log_message("Cal3D version {0} XSF file".format(version))
                LogMessage.log_message("Importing armature from {0}\n".format(filename))
                xsf_importer = ImportXsf(skeleton, LogMessage)
                xsf_importer.parse_xml()
                xsf_importer.DEBUG = 1  # debug armature creation only atm
                xsf_importer.create_armature(name_only)
            else:
                LogMessage.log_error("Couldn't find SKELETON tag!")
        elif magic == "XMF":
            LogMessage.log_message("XMF not supported yet")
        elif magic == "XAF":
            LogMessage.log_message("XAF not supported yet")
        elif magic == "XPF":
            LogMessage.log_message("XPF not supported yet")
        elif magic == "XRF":
            LogMessage.log_message("XRF not supported yet")
        else:
            LogMessage.log_error("Unrecognized Cal3D file type.")

        obj = bpy.context.object
        if obj and obj == save_obj:
            bpy.ops.object.mode_set(mode=save_mode)

    return True
