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

# A class to log messages
# Input:
#   name = name of logger
#   type = console (default), or file
#   file = filename

class Logger:

    def __init__(self, name, type='console', file=''):
        self.name = name
        if self.name == '':
            self.name = 'Logger'
        self.type = type
        if self.type == 'file':
            self.file = file
            if self.file == '':
                self.file = self.name + '.log'
            self.logfile = open(self.file, "wt")
        else:
            self.logfile = None
        self.errors = 0
        self.warnings = 0
        self.debug = 0
        self.info = 0


    def close_log(self):
        if self.logfile:
            self.logfile.close()

    def log_message(self, message):
        if self.type == 'console':
            print(message)
        else:
            self.logfile.write(message + "\n")

    def log_warning(self, warning):
        self.warnings += 1
        self.log_message("WARNING: " + warning)

    def log_error(self, error):
        self.warnings += 1
        self.log_message("ERROR: " + error)

# ---------------------------------------------------------------------------------------------------------------------------------

# Current logger class:
LogMessage = None
