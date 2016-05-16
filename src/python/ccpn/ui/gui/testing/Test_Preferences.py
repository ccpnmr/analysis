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
from ccpn.ui.gui import AppBase

def test_get_preferences():

  preferences = AppBase.getPreferences()

  print(preferences)

def test_get_preferences_default():

  defaultPreferencesPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
  preferences = AppBase.getPreferences(defaultPreferencesPath=defaultPreferencesPath)

  print(preferences)

def test_get_preferences_user():

  userPreferencesPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
  preferences = AppBase.getPreferences(userPreferencesPath=userPreferencesPath)
  print(preferences)

def test_get_preferences_default_user():

  defaultPreferencesPath = os.path.join(os.path.dirname(__file__), 'defaultv3settingsTest.json')
  userPreferencesPath = os.path.join(os.path.dirname(__file__), 'userv3settingsTest.json')
  preferences = AppBase.getPreferences(defaultPreferencesPath=defaultPreferencesPath,
                               userPreferencesPath=userPreferencesPath)
  print(preferences)

