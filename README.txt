Cal3d blender exporter for IMVU v 1.0
=====================================

This python script is intended for Blender version 2.63 or higher.
It's purpose is to export blender objects to Cal3d, and specifically
targeted at IMVU compatibility.
This version has not been extensively tested yet. Please report all
bugs, inconsistensies etc so that I can hopefully fix it.

In addition to what older exporters for blender 2.49 could do, this
version also supports vertex colors.

The latest version of this script can always be found here:
https://bitbucket.org/jacobb/imvu_cal3d


1. Install
----------
To install this script you have to copy the entire folder called
io_export_cal3d_IMVU to your blender version's addons folder.
This folder can be found in the following location:
 AppData\Roaming\Blender Foundation\Blender\<your Blender version>\scripts\addons
Note that the scripts and/or addons folder may not exist. If that is the case
then create the folder(s) first.
Where AppData is located depends on your Windows version. If you don't
know where to find it search on the internet, there are loads of tutorials
available.
Drop the entire io_export_cal3d_IMVU folder inside the addons folder.

Then you need to install the script in Blender.
Start Blender, go to menu File, User Preferences.
Choose Import-Export, then browse to IMVU Cal3d export and check it.
Next click Save As Default.


2. Export
---------
To export select your bones and mesh, then go to menu File, Export, IMVU Cal3d export.
Note that currently it is required to have material(s) assigned to the mesh
for the export to work.
The default settings should generally be fine for IMVU.
Choose a location where the files should be saved and press the button
called Export Cal3d for IMVU.
If anything went wrong look in the system console window. To see the system
console go to menu Window, Toggle system console.


3. Credits
----------
This version was based on the version found in the terra tenebrae repository:
http://sourceforge.net/p/terratenebrae/code/157/tree/trunk/tools/blender/2.6/

That version was based on alexeyd's version for blender 2.58:
https://github.com/alexeyd/blender2cal3d

Which was apparently based on a cal3d version in the offical cal3d repository.
http://svn.gna.org/viewcvs/cal3d/trunk/cal3d/plugins/cal3d_blender_exporter/

Besides these the following cal3d scripts were also inspected:
* http://code.google.com/p/blender2cal3d-exporter/
* Erykgecko XMF/XSF exporters for blender 2.62 http://www.imvufreelancer.com/
* The Blender to IMVU 1.4 Sapphire Edition version for blender 2.49
* drtron version for blender 2.49 using vertex colors


Jacob Boerema (DutchTroy on IMVU), november 2012
