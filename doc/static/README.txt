Welcome to the CcpNmr V3 alpha release (version 3.0.0.m0)

0. Names and versions
---------------------

From this version on, the CcpNmr suite is divided into several components.
Currently we only have CcpNmr-Assign, but later we will also release
CcpNmr-Structure, CcpNmr-Screen, and others.
The name 'Analysis' will not be used for V3 versions.

CcpNmr versions like '3.2.11.m4' mean 'major version 3, minor version 2, release 11,
data model version 4. The data model version is used to control the backwards compatibility 
code. The revision number is given in the title bar of the main window.


1. Setup and installation
-------------------------

Inside the CcpNmr distribution, there is a folder called bin, which contains
a script called assign. This is a csh script for starting CcpNmr-Assign we
recommend that you set an alias to this script in your cshrc/bashrc:

in csh:

alias assign /path/to/distribution/bin/assign

in bash:

alias assign="/path/to/distribution/bin/assign"

After sourcing your .cshrc (in csh) or .bashrc (in bash) file or opening a
new terminal you can open assign by typing assign into the terminal.


2. Code Structure
-----------------

The release directory contains

- bin - with the scripts to run CcpNMr-Assign and other components of CcpNmr.

- ccpnmodel - contains code and data for code generation and the automatic 
reading of files from previous versions. 
Anyone not working for CCPN is unlikely to ever need to look inside.

- ccpnv3 - with the application code

- scripts - with scripts used in (re)installation.


In the ccpnv3 directory, there are five directories:

- c - contains the c code used by contouring and peak picking routines and the
files required to compile it.


- data - data/ccp contains data required for CCPNMR, and data/testProjects contains
projects and spectra for testing the program, and two tutorials complete with 
spectra.

- doc - contains the html documentation for the application.
  There are two main documentation trees, one for the top data access layer ('wrapper')
  and one for the underlying data storage layer (mainly for specialists). Both are linked
  from the release directory and accessible from the aplication 'Help'. If you are 
  interested, they can be found in 'doc'build/.html' and 'doc/apidoc', respectively
  

- python - contains the python code for the application. There are three subdirectories:

    - python/application
    contains all the application specific code, including popups, modules and sample macros.

    - python/ccpn - contains the data access code ('wrapper') that lets you interact
    with the data (including the display modules etc. on screen), and a number of 
    library functions to interact with it. This is the code you need in order to understand
    the data structure, write macros, or type on the command line.

    - python/ccpncore - contains underlying data storage and access layer, corresponding
    to the V2 data model (V3 uses a simplified data access layer, the 'wrapper' layer, 
    built on top of the more complex V2 model, the 'API' layer). Also the base GUI 
    elements used to construct the interface, and various utility functions.
    In general only application programmers (and not all of those) should need to look
    into this layer.


3. Bug Reporting and Updating.
------------------------------

Inside the Assign interface, under the Help menu, there is an option called
Submit Feedback. This should be used to report any bugs and request new
features. By default the option to send the log file is checked and there is
also an option to send the project along with the bug report.

Under the Help menu, there is also an option to update the code, namely Check
for Updates. This should be used to obtain any fixes and developments to the
software. After updating, you will be required to restart the program for the
changes to take effect.


4. Interacting with data inside Assign.
---------------------------------------

Almost all objects in Assign have a project Id or Pid. This is a multipart string
identifier specifying the type and identity of the object. You can get the pid
of an object, by typing object.pid and objects can be obtained using the
project.getByPid(Pid) function. This function can be used in macros, application
code and in the python console inside the assign main window (shortcut py).

A list of all shortcuts and mouse interactions/events is available under the
help menu using the 'show shortcuts' function and the two tutorials provided with
this release are accessible from the tutorials submenu of the help menu.

The project keeps track of all spectrum data in three standard locations: inside the project 
('INSIDE'), alongside the project ('ALONGSIDE') and a remote data directory specified in the 
preferences ('DATA'). Inside the SpectrumPropertiesPopup, spectrum paths that match either of
these are displayed as $INSIDE/path, $ALONGSIDE/path or $DATA/path. This notation can also
be used if you hand-edit the files. If you move a projest to a different location, the
INSIDE and ALONGSIDE directory paths are automatically updated if obsolete, and the DATA
directory can be updated by setting the preferences. It is recommended (but not mandatory)
to put your spectrum files under one of these three locations, for easier management

