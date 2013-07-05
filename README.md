Cal3d blender exporter for IMVU version 1.4
===========================================

Contents
--------
1. Introduction
2. How to install in Blender
3. How to export from Blender
4. Questions and bug reporting
5. Credits


1. Introduction
---------------
This python script is intended for Blender version 2.63 or higher.
Older versions of Blender are not supported.
It's purpose is to export Blender objects to Cal3d, and specifically
targeted at IMVU compatibility.

Although this script has been used with success for a while there
could still be some problems, especially with animations and morph
animations. Please report all bugs, inconsistensies, etc. so that 
I can have a look and hopefully fix it.

In addition to what older exporters for Blender 2.49 could do, this
version also supports:

* Vertex colors.
* Setting the room SCENEAMBIENTCOLOR when you check the exporter option.
  The color is taken from Blender's world ambient color which is gamma 
  corrected and may look different than the color in IMVU.
* Setting LIGHTTYPE and LIGHTCOLOR for lights. Define your light bones
  as usual. Depending on the name starting with omni or spot it assigns
  type 1 or 3 to it. To set a custom light color add a light (lamp) to
  your scene with the scene name as your light bone.
  e.g. if you have a light bone Omni01 then add a light with name Omni01
  and then set that lights color as you wish.

New in version 1.3:

* Morph animations. Use shape keys to define a morph. Then in dopesheet
  change editor mode to ShapeKey editor and define animation frames.
  Note: currently only Relative shapekeys are supported and only with
  weight ranges from 0.0 to 1.0.

Changes in version 1.4:
* You can now set explicit material numbers by adding a number in
  square brackets to the end of the material name. By default this
  script assigns increasing material numbers starting from 0 to each
  submesh. However in certain cases like updating an existing mesh or
  making a custom head the submeshes might need a fixed material
  number. e.g. with a head the third material is for the eyelashes which
  would get material id 2 (because numbering starts at 0) but it needs 
  material id 5, therefore add [5] to the material name
  e.g. eyelashes_material[5]
* Bugfix: incorrect shapekey id assignment.
* Reduce size of exported mesh: certain vertices where exported twice.
* IMVU's Morph Target tutorial wrongly states one of the morph suffixes
  as .Averaged, it should be .Average as seen on IMVU's Avatar Morph 
  Animations page.

The latest version of this script can always be found here:
https://bitbucket.org/jacobb/imvu_cal3d


2. How to install in Blender
----------------------------
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


3. How to export from Blender
-----------------------------
To export you need to select **both your bones (skeleton) and your mesh**,
then go to menu File, Export, IMVU Cal3d export. It is also **required to 
have material(s) assigned to the mesh** for the export to work.

You can choose which files you want to export. IMVU only needs
XMF, XSF, XAF and XPF files. The default settings should generally be fine for IMVU.
Choose a location where the files should be saved and press the button
called Export Cal3d for IMVU.

If anything went wrong look in the **system console window**. To see the system
console go to Blender's main menu: Window, Toggle system console. A separate
Blender window should open which will show information about what happened.


4. Questions and bug reporting
------------------------------
If you have any questions about this exporter or think you have found a
possible bug then the preferred place of contact is the Blender Creators 
group on IMVU (you need to become a member first):
http://www.imvu.com/groups/group/Blender+Creators/

Note that questions regarding problems exporting need to always include
the complete error text as shown in the system console. See Export on
how to show the system console. In the system console you can use
Alt+space, then Edit to access the copy, select and paste menu items.

For reporting bugs or feature requests you can also add them to my Bitbucket
issue tracker:
https://bitbucket.org/jacobb/imvu_cal3d/issues


5. Credits
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


Jacob Boerema (DutchTroy on IMVU), November 2012-July 2013
