"""This file contains path definitions and Url definitions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-09 13:55:53 +0100 (Wed, June 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

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
ccpnCodePath                    = Path.aPath(Path.getTopDirectory())
ccpnConfigPath                  = ccpnCodePath / 'config'
ccpnRunTerminal                 = ccpnCodePath / 'bin' / 'runTerminal.sh'
defaultPreferencesPath          = ccpnConfigPath / 'defaultv3settings.json'
tipOfTheDayConfig               = ccpnConfigPath / 'tipConfig.json'
_ccpnPythonPath                 = Path.aPath(Path.getPythonDirectory())
ccpnmodelPythonPath             = _ccpnPythonPath / 'ccpnmodel'
ccpnmodelDataPythonPath         = _ccpnPythonPath / 'ccpnmodel' / 'data'
ccpnmodelRefDataPythonPath      = _ccpnPythonPath / 'ccpnmodel' / 'data' / 'ccpnv3'
ccpnPythonPath                  = _ccpnPythonPath / 'ccpn'
analysisAssignPath              = ccpnPythonPath / 'AnalysisAssign'
analysisScreenPath              = ccpnPythonPath / 'AnalysisScreen'
analysisStructurePath           = ccpnPythonPath / 'AnalysisStructure'
analysisMetabolomicsPath        = ccpnPythonPath / 'AnalysisMetabolomics'
macroPath                       = ccpnPythonPath / 'macros'
pluginPath                      = ccpnPythonPath / 'plugins'
pipePath                        = ccpnPythonPath / 'pipes'
pipeTemplates                   = ccpnPythonPath / 'framework' / 'lib' / 'pipeline' / 'templates'
fontsPath                       = ccpnPythonPath / 'ui' / 'gui' / 'widgets' / 'fonts'
iconsPath                       = ccpnPythonPath / 'ui' / 'gui' / 'widgets' / 'icons'
openGLFontsPath                 = fontsPath / 'Fonts'
nefValidationPath               = ccpnPythonPath / 'util' / 'nef' / 'NEF' / 'specification' / 'mmcif_nef_v1_1.dic'
peakPickerPath                  = ccpnPythonPath / 'core' / 'lib' / 'PeakPickers'

# Program tutorials and documentation
shortcutsPath                   = ccpnCodePath / 'doc' / 'static' / 'AnalysisShortcuts.pdf'
tutorialsPath                   = ccpnCodePath / 'tutorials'
beginnersTutorialPath           = ccpnCodePath / 'tutorials' / 'BeginnersTutorial.pdf'
backboneAssignmentTutorialPath  = ccpnCodePath / 'tutorials' / 'BackboneAssignmentTutorial.pdf'
screenTutorialPath              = ccpnCodePath / 'tutorials' / 'CcpNmr_AnalysisScreen_Tutorial_Beta2Release.pdf'
cspTutorialPath                 = ccpnCodePath / 'tutorials' / 'CSPTutorial.pdf'
solidStatePeptideTutorialPath   = ccpnCodePath / 'tutorials' / 'SolidStatePeptideAssignmentTutorial.pdf'
solidStateSH3TutorialPath       = ccpnCodePath / 'tutorials' / 'SolidStateAssignmentTutorial.pdf'
analysisScreenTutorialPath      = ccpnCodePath / 'tutorials' / 'ScreenTutorial.pdf'
howTosPath                      = tutorialsPath / 'How-Tos'

documentationPath               = ccpnCodePath / 'doc' / 'build' / 'html' / 'index.html'
licensePath                     = ccpnCodePath / 'LICENSE.txt'

# User settings
userPreferencesDirectory        = Path.aPath('~/.ccpn')
userCcpnPath                    = userPreferencesDirectory
userPreferencesPath             = userPreferencesDirectory / 'v3settings.json'
userCcpnDataPath                = userCcpnPath / 'data'
userDefaultProjectPath          = userCcpnDataPath / 'default.ccpn'
userCcpnPathSubDirectories      = ['data', 'macros', 'pipes']  # These get created by framework

# Predefined layouts
predefinedLayouts               = ccpnCodePath / 'layouts'

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
