"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import os
import sys

from ccpn import openProject, newProject

from ccpncore.gui.Application import Application

# from ccpnmrcore.gui.MainWindow import MainWindow

from ccpnmrcore.app.AppBase import AppBase

applicationName = 'Assign'
applicationVersion = '1.0'

def usage():

  print('Correct syntax: %s [projectPath]' % sys.argv[0])

class Assign(AppBase):
  pass

if __name__ == '__main__':
  if len(sys.argv) == 2:
    projectPath = sys.argv[1]
    project = openProject(projectPath)
  elif len(sys.argv) != 1:
    usage()
    sys.exit(1)
  else:
    project = newProject('defaultProject')

  app = Application(applicationName, applicationVersion)
  assign = Assign(project=project)
  app.start()

