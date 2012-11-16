Cal3d blender exporter for IMVU version 1.2
===========================================

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
After you have downloaded the zip file with this script start Blender.
Go to menu File, User Preferences, Addons tab.
Click the Install Addons button located at the bottom.
Browse to the location of the zip file and click the Install Addon button.
Note: you don't have to unzip it first yourself.
Next click the checkbox for the IMVU Cal3d Export addon to enable it.
Finally click Save As Default.

If you want to manually install the files then read the Blender manual
on where and how to do that:
http://wiki.blender.org/index.php/Doc:2.6/Manual/Extensions/Python/Add-Ons


2. Export
---------
To export select your bones and mesh, then go to menu File, Export, IMVU Cal3d export.
Note that currently it is required to have material(s) assigned to the mesh
for the export to work.
You can choose which files you want to export. IMVU only needs XMF, XSF and XAF files.
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
