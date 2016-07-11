"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os
from ccpn.framework import Framework

def test_get_preferences():

  preferences = Framework.getPreferences()

  print(preferences)

def test_get_preferences_default():

  defaultPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
  preferences = Framework.getPreferences(defaultPath=defaultPath)
  print(preferences)

def test_get_preferences_user():

  userPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
  preferences = Framework.getPreferences(userPath=userPath)
  print(preferences)

def test_get_preferences_default_user():

  defaultPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
  userPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
  preferences = Framework.getPreferences(defaultPath=defaultPath, userPath=userPath)
  print(preferences)

