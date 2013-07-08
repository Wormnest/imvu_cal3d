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

bl_info = \
{
  "name": "IMVU Cal3D XSF import TEST",
  "author": "Jean-Baptiste Lamy (Jiba), " \
            "Chris Montijin, "            \
            "Damien McGinnes, "           \
            "David Young, "               \
            "Alexey Dorokhov, "           \
            "Matthias Ferch, "            \
            "Peter Amstutz, "             \
            "Etory, "                     \
            "Jacob Boerema",
  "version": (0, 1, 1),
  "blender": (2, 6, 3),
  "location": "File > Import > IMVU Cal3D (.xsf)",
  "description": "Import armature from Cal3D for IMVU.",
  "warning": "You must have Blender 2.6.3 or higher to run this script.",
  "wiki_url": "https://bitbucket.org/jacobb/imvu_cal3d",
  "tracker_url": "https://bitbucket.org/jacobb/imvu_cal3d/issues?status=new&status=open",
  "category": "Import-Export"
}


# Get string: Copyright 2012-<current year> 
def get_copyright():
    import datetime
    from datetime import date
    return "Portions Copyright 2012-{0} by DutchTroy aka Jacob Boerema\n".format(date.today().year)

# Print Copyright 2012-<current year> line
def print_copyright():
    print(get_copyright())

def get_version_string():
    return "version {0}.{1}.{2}".format(
        str(bl_info['version'][0]),
        str(bl_info['version'][1]),
        str(bl_info['version'][2]))

print("\nInitializing IMVU Cal3D import " + get_version_string())
print_copyright()

# To support reload properly, try to access a package var, 
# if it's there, reload everything
if "bpy" in locals():
    import imp
    print("reloading script classes")
    # reload the logging class
    if "logger_class" in locals():
        imp.reload(logger_class)

    if "import_cal3d_xml" in locals():
        imp.reload(import_cal3d_xml)

    if "xsf_importer" in locals():
        imp.reload(xsf_importer)

    if "support_functions" in locals():
        imp.reload(support_functions)


import bpy
from bpy import ops
from bpy import context
from bpy.props import BoolProperty,       \
                      EnumProperty,        \
                      CollectionProperty,  \
                      FloatProperty,       \
                      StringProperty,      \
                      FloatVectorProperty, \
                      IntProperty

import bpy_extras
from bpy_extras.io_utils import ImportHelper

import mathutils
import os.path
import sys
import traceback


class TestImportCal3D(bpy.types.Operator, ImportHelper):
    """Load Cal3D files in XML format, targeted at IMVU compatibility"""
    # bl_idname should be unique and not the same for import and export!
    bl_idname = "test_cal3d_import_xsf.xsf"
    bl_label = 'Import Cal3D XSF (TESTING)'
    bl_options = {'UNDO'}

    filename_ext = ".xsf"
    filter_glob = StringProperty(default="*.xsf;*.csf",
        options={'HIDDEN'})


    def execute(self, context):
        parentsubdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) +  '\\io_export_cal3d_IMVU'
        sys.path.insert(0,parentsubdir)
        print(parentsubdir)
        # import our importer
        from . import import_cal3d_xml
        from .import_cal3d_xml import importer_main
        # import logging functionality
        #from .io_export_cal3d_IMVU import logger_class
        import logger_class
        from logger_class import Logger, LogMessage

        # local function in case of an exception/crash to log the error and close log file
        def fatal_error(LogMessage, fatal_error_msg, fatal_error_e, traceback=''):
            if LogMessage:
                LogMessage.log_error(fatal_error_msg)
                LogMessage.log_message("Runtime error message: " + str(fatal_error_e))
                if traceback != '':
                    LogMessage.log_message(traceback)
                LogMessage.log_message("\nExport aborted.\n")
                # Log amount of errors
                LogMessage.log_counters()
                # Close the logger
                LogMessage.close_log()

        name_only = os.path.splitext(os.path.basename(self.filepath))[0]
        self.log_file = os.path.dirname(self.filepath)+'\\'+name_only+"_IMPORT.log"

        # Initialize our logger
        LogMessage = Logger("Cal3dImportLogger", type ="file", file= self.log_file)
        logger_class.LogMessage = LogMessage

        # Always add empty line to make it easier to find start of our info (don't log it to file though)
        print("\n\n")
        LogMessage.file_and_print = True
        LogMessage.log_message("IMVU Cal3D import " + get_version_string())
        LogMessage.log_message(get_copyright())
        # Console only message to show where we are writing the log file:
        print("Logging info to file: " + LogMessage.file + "\n")
        
        LogMessage.log_message("Importing Cal3D to Blender started.")

        # start the main importer function
        importer_main(self.filepath, name_only)

        LogMessage.log_message("\nImport finished.\n")

        # Log amount of errors
        LogMessage.log_counters()

        # Close the logger
        LogMessage.close_log()
        
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(TestImportCal3D.bl_idname, text="TEST Cal3d XSF import")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()
