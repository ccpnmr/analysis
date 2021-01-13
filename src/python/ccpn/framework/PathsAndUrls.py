"""This file contains path definitions and Url definitions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-02 17:47:52 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
ccpnRunTerminal                 = os.path.join(ccpnCodePath, 'bin', 'runTerminal.sh')
defaultPreferencesPath          = os.path.join(ccpnConfigPath, 'defaultv3settings.json')
ccpnmodelPythonPath             = os.path.join(Path.getPythonDirectory(), 'ccpnmodel')
ccpnmodelDataPythonPath         = os.path.join(Path.getPythonDirectory(), 'ccpnmodel', 'data')
ccpnmodelRefDataPythonPath      = os.path.join(Path.getPythonDirectory(), 'ccpnmodel', 'data', 'ccpnv3')
ccpnPythonPath                  = os.path.join(Path.getPythonDirectory(), 'ccpn')
analysisAssignPath              = os.path.join(ccpnPythonPath, 'AnalysisAssign')
analysisScreenPath              = os.path.join(ccpnPythonPath, 'AnalysisScreen')
analysisStructurePath           = os.path.join(ccpnPythonPath, 'AnalysisStructure')
analysisMetabolomicsPath        = os.path.join(ccpnPythonPath, 'AnalysisMetabolomics')
macroPath                       = os.path.join(ccpnPythonPath, 'macros')
pluginPath                      = os.path.join(ccpnPythonPath, 'plugins')
pipePath                        = os.path.join(ccpnPythonPath, 'pipes')
pipeTemplates                   = os.path.join(ccpnPythonPath, 'framework', 'lib', 'pipeline', 'templates')
fontsPath                       = os.path.join(ccpnPythonPath, 'ui', 'gui', 'widgets', 'fonts')
nefValidationPath               = os.path.join(ccpnPythonPath, 'util', 'nef', 'NEF', 'specification', 'mmcif_nef_v1_1.dic')

# Program tutorials and documentation
shortcutsPath                   = os.path.join(ccpnCodePath, 'doc', 'static', 'AnalysisShortcuts.pdf')
tutorialsPath                   = os.path.join(ccpnCodePath, 'tutorials')
beginnersTutorialPath           = os.path.join(ccpnCodePath, 'tutorials', 'BeginnersTutorial.pdf')
backboneAssignmentTutorialPath  = os.path.join(ccpnCodePath, 'tutorials', 'BackboneAssignmentTutorial.pdf')
screenTutorialPath              = os.path.join(ccpnCodePath, 'tutorials', 'CcpNmr_AnalysisScreen_Tutorial_Beta2Release.pdf')
cspTutorialPath                 = os.path.join(ccpnCodePath, 'tutorials', 'CSPTutorial.pdf')
solidStateTutorialPath          = os.path.join(ccpnCodePath, 'tutorials', 'SolidStateAssignmentTutorial.pdf')
analysisScreenTutorialPath      = os.path.join(ccpnCodePath, 'tutorials', 'ScreenTutorial.pdf')

documentationPath               = os.path.join(ccpnCodePath, 'doc', 'build', 'html', 'index.html')
licensePath                     = os.path.join(ccpnCodePath, 'LICENSE.txt')

# User settings
userPreferencesDirectory        = os.path.expanduser('~/.ccpn')
userPreferencesPath             = os.path.join(userPreferencesDirectory, 'v3settings.json')
userCcpnPath                    = userPreferencesDirectory
userCcpnPathSubDirectories      = ['data', 'macros', 'pipes']  # These get created by framework
userCcpnDataPath                = os.path.join(userCcpnPath, 'data')
userDefaultProjectPath          = os.path.join(userCcpnDataPath, 'default.ccpn')

# Predefined layouts
predefinedLayouts               = os.path.join(ccpnCodePath, 'layouts')

# others; also defined in util.Path and from there imported in Api and Implementation
# DO NOT REMOVE and keep in sinc (for circular import reasons) (for now!)
CCPN_DIRECTORY_SUFFIX    = '.ccpn'
CCPN_BACKUP_SUFFIX       = '_backup'  # used by ApiLoader; deprecated

# subdirectories of Projects
CCPN_API_DIRECTORY       = 'ccpnv3'
CCPN_ARCHIVES_DIRECTORY  = 'archives'
CCPN_BACKUPS_DIRECTORY   = 'backups'
CCPN_SUMMARIES_DIRECTORY = 'summaries'
CCPN_LOGS_DIRECTORY      = 'logs'
CCPN_DATA_DIRECTORY      = 'data'
CCPN_PLUGINS_DIRECTORY   = 'data/plugins'
CCPN_SPECTRA_DIRECTORY   = 'data/spectra'
CCPN_SCRIPTS_DIRECTORY   = 'scripts'
CCPN_STATE_DIRECTORY     = 'state'

# historical
CCPN_EXTENSION = CCPN_DIRECTORY_SUFFIX
