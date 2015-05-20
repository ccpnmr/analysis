"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

import sys

from ccpnmrcore.app.AppBase import AppBase, startProgram
from ccpnmrcore.app.Version import applicationVersion

applicationName = 'Assign'

class Assign(AppBase):
  pass

if __name__ == '__main__':
  import argparse  

  parser = argparse.ArgumentParser(description='Process startup arguments')
  parser.add_argument('--language', help='Language for menus, etc.')
  parser.add_argument('projectPath', help='Project path')
  args = parser.parse_args()
  
  startProgram(Assign, applicationName, applicationVersion, args.projectPath, args.language)

