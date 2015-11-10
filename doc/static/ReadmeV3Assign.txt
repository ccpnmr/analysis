Welcome to the CCPNMR V3 Assign alpha release.

1. Setup and installation

Inside the analysis distribution, there is a folder called bin, which contains
a script called assign. This is a csh script for starting the program we
recommend that you set an alias to this script in your cshrc/bashrc:

in csh:

alias assign /path/to/distribution/bin/assign

in bash:

alias assign="/path/to/distribution/bin/assign"

After sourcing your rc file or opening a new terminal you can open assign by
typing assign into the terminal.

2. Code Structure

In the top ccpnv3 directory, there are six directories:

c - contains the c code used by contouring and peak picking routines and the
files required to compile it.

data - contains data required for CCPNMR in the ccp directory and in the
testProjects directory there are projects and spectra for testing the program,
and two tutorials complete with spectra.

doc - contains the html documentation for the software.

python - contains the python code for the application.

The python directory has three subdirectories:

ccpn - contains the wrapper code the the ccpn data model and some lib functions
for working with the API and data wrapper.

ccpncore - contains the API in python code, lib and utility functions for
working with the API and the base GUI elements used to construct the interface.

application - contains all the application level code, including popups,
modules and some sample macros.

3. Bug Reporting and Updating.

Inside the Assign interface, under the Help menu, there is an option called
Submit Feedback. This should be used to report any bugs and request new
features. By default the option to send the log file is checked and there is
also an option to send the project along with the bug report.

Under the Help menu, there is also an option to update the code, namely Check
for Updates. This should be used to obtain any fixes and developments to the
software. After updating, you will be required to restart the program for the
changes to take effect.

4. Interacting with data inside Assign.

Almost all objects in Assign have a project Id or Pid. This is a multipart
identifier specifying the type and identity of the object. You can get the pid
of an object, by typing object.pid and objects can be obtained using the
project.getByPid(Pid) function. This function can be used in macros, application
code and in the python console inside the assign main window (shortcut py).

A list of all shortcuts and mouse interactions/events is available under the
help menu using the show shortcuts function and the two tutorials provided with
this release are accessible from the tutorials submenu of the help menu.

