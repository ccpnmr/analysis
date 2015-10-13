from ccpnmrcore.app import AppBase

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

  preferences = AppBase.getPreferences(defaultPreferencesPath='defaultv3settingsTest.json')

  print(preferences)

def test_get_preferences_user():

  preferences = AppBase.getPreferences(userPreferencesPath='userv3settingsTest.json')
  print(preferences)

def test_get_preferences_default_user():

  preferences = AppBase.getPreferences(defaultPreferencesPath='defaultv3settingsTest.json',
                               userPreferencesPath='userv3settingsTest.json')
  print(preferences)

