import os
from application.core import AppBase

from ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2015-09-14 18:11:59 +0100 (Mon, 14 Sep 2015) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2015-09-14 18:11:59 +0100 (Mon, 14 Sep 2015) $"
__version__ = "$Revision: 8631 $"

#=========================================================================================
# Start of code
#=========================================================================================

def test_get_preferences():

  preferences = AppBase.getPreferences()

  print(preferences)

def test_get_preferences_default():

  defaultPreferencesPath = os.path.join(TEST_PROJECTS_PATH, 'defaultv3settingsTest.json')
  preferences = AppBase.getPreferences(defaultPreferencesPath=defaultPreferencesPath)

  print(preferences)

def test_get_preferences_user():

  userPreferencesPath = os.path.join(TEST_PROJECTS_PATH, 'userv3settingsTest.json')
  preferences = AppBase.getPreferences(userPreferencesPath=userPreferencesPath)
  print(preferences)

def test_get_preferences_default_user():

  defaultPreferencesPath = os.path.join(TEST_PROJECTS_PATH, 'defaultv3settingsTest.json')
  userPreferencesPath = os.path.join(TEST_PROJECTS_PATH, 'userv3settingsTest.json')
  preferences = AppBase.getPreferences(defaultPreferencesPath=defaultPreferencesPath,
                               userPreferencesPath=userPreferencesPath)
  print(preferences)

