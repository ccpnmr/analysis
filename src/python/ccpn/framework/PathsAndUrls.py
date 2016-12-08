"""This file contains path definitions and Url definitions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
__version__ = "$Revision: 9605 $"

#=========================================================================================
# Start of code
#=========================================================================================

import os
from ccpn.util import Path


# CCPN Urls
ccpnUrl                         = 'http://www.ccpn.ac.uk'
ccpn2Url                        = 'http://www2.ccpn.ac.uk'
ccpnLicenceUrl                  = 'http://www.ccpn.ac.uk/v3-software/downloads/license'
ccpnIssuesUrl                   = 'https://sourceforge.net/p/ccpn/bugs/'

# CCPN code
ccpnCodePath                    = Path.getTopDirectory()
ccpnConfigPath                  = os.path.join(ccpnCodePath, 'config')
defaultPreferencesPath          = os.path.join(ccpnConfigPath, 'defaultv3settings.json')
ccpnPythonPath                  = os.path.join(Path.getPythonDirectory(), 'ccpn')
macroPath                       = os.path.join(ccpnPythonPath, 'macros')
pluginPath                      = os.path.join(ccpnPythonPath, 'plugins')
pipePath                        = os.path.join(ccpnPythonPath, 'pipes')
fontsPath                       = os.path.join(ccpnPythonPath, 'ui', 'gui', 'widgets', 'fonts')

# Program tutorials and documentation
shortcutsPath                   = os.path.join(ccpnCodePath, 'doc', 'static', 'AnalysisShortcuts.pdf')
beginnersTutorialPath           = os.path.join(ccpnCodePath, 'tutorials', 'BeginnersTutorial.pdf')
backboneAssignmentTutorialPath  = os.path.join(ccpnCodePath, 'tutorials', 'BackboneAssignmentTutorial.pdf')
documentationPath               = os.path.join(ccpnCodePath, 'doc', 'build', 'html', 'index.html')
licensePath                     = os.path.join(ccpnCodePath, 'LICENSE.txt')

# User settings
userPreferencesDirectory        = os.path.expanduser('~/.ccpn')
userPreferencesPath             = os.path.join(userPreferencesDirectory,'v3settings.json')
