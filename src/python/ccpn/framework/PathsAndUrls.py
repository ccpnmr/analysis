"""This file contains path definitions and Url definitions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from ccpn.util import Path


# CCPN Urls
ccpnUrl                         = 'http://www.ccpn.ac.uk'
ccpn2Url                        = 'http://www.ccpn.ac.uk'
ccpnLicenceUrl                  = 'http://www.ccpn.ac.uk/v3-software/licences'
ccpnTutorials                   = 'https://www.ccpn.ac.uk/v3-software/tutorials'
ccpnForum                       = 'https://www.ccpn.ac.uk/v3-software/v3-forum'
ccpnVideos                      = 'https://www.ccpn.ac.uk/v3-software/v3-video-tutorials'
oldCcpnIssuesUrl                = 'https://sourceforge.net/p/ccpn/bugs/'
ccpnIssuesUrl                   = 'https://bitbucket.org/ccpnmr/issue-tracker/issues?status=new&status=open'

# CCPN code
ccpnCodePath                    = Path.getTopDirectory()
ccpnConfigPath                  = os.path.join(ccpnCodePath, 'config')
defaultPreferencesPath          = os.path.join(ccpnConfigPath, 'defaultv3settings.json')
ccpnmodelPythonPath             = os.path.join(Path.getPythonDirectory(), 'ccpnmodel')
ccpnPythonPath                  = os.path.join(Path.getPythonDirectory(), 'ccpn')
analysisAssignPath              = os.path.join(ccpnPythonPath, 'AnalysisAssign')
analysisScreenPath              = os.path.join(ccpnPythonPath, 'AnalysisScreen')
analysisStructurePath           = os.path.join(ccpnPythonPath, 'AnalysisStructure')
analysisMetabolomicsPath        = os.path.join(ccpnPythonPath, 'AnalysisMetabolomics')
macroPath                       = os.path.join(ccpnPythonPath, 'macros')
pluginPath                      = os.path.join(ccpnPythonPath, 'plugins')
pipePath                        = os.path.join(ccpnPythonPath, 'pipes')
fontsPath                       = os.path.join(ccpnPythonPath, 'ui', 'gui', 'widgets', 'fonts')

# Program tutorials and documentation
shortcutsPath                   = os.path.join(ccpnCodePath, 'doc', 'static', 'AnalysisShortcuts.pdf')
tutorialsPath                   = os.path.join(ccpnCodePath, 'tutorials')
beginnersTutorialPath           = os.path.join(ccpnCodePath, 'tutorials', 'BeginnersTutorial.pdf')
backboneAssignmentTutorialPath  = os.path.join(ccpnCodePath, 'tutorials', 'BackboneAssignmentTutorial.pdf')
screenTutorialPath              = os.path.join(ccpnCodePath, 'tutorials', 'CcpNmr_AnalysisScreen_Tutorial_Beta2Release.pdf')
cspTutorialPath                 = os.path.join(ccpnCodePath, 'tutorials', 'CSPtutorial.pdf')
solidStateTutorialPath          = os.path.join(ccpnCodePath, 'tutorials', 'SolidStateAssignmentTutorial.pdf')

documentationPath               = os.path.join(ccpnCodePath, 'doc', 'build', 'html', 'index.html')
licensePath                     = os.path.join(ccpnCodePath, 'LICENSE.txt')

# User settings
userPreferencesDirectory        = os.path.expanduser('~/.ccpn')
userPreferencesPath             = os.path.join(userPreferencesDirectory, 'v3settings.json')

# Predefined layouts
predefinedLayouts               = os.path.join(ccpnCodePath, 'layouts')

# others
CCPN_EXTENSION = '.ccpn'
