"""This file contains path definitions and Url definitions
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Daniel Thompson $"
__dateModified__ = "$dateModified: 2024-09-26 15:12:49 +0100 (Thu, September 26, 2024) $"
__version__ = "$Revision: 3.2.5 $"
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
ccpnUrl                         = 'https://www.ccpn.ac.uk'
ccpn2Url                        = 'https://www.ccpn.ac.uk'
ccpnLicenceUrl                  = 'https://www.ccpn.ac.uk/software/licensing'
ccpnTutorials                   = 'https://www.ccpn.ac.uk/support/tutorials'
ccpnForum                       = 'https://forum.ccpn.ac.uk'
ccpnVideos                      = 'https://www.ccpn.ac.uk/manual/v3/'
oldCcpnIssuesUrl                = 'https://sourceforge.net/p/ccpn/bugs/'
ccpnIssuesUrl                   = 'https://bitbucket.org/ccpnmr/issue-tracker/issues?status=new&status=open'
ccpnDocumentationUrl            = 'https://www.ccpn.ac.uk/api-documentation/v3/html'

# subdirectories of Projects
CCPN_API_DIRECTORY          = 'ccpnv3'
CCPN_ARCHIVES_DIRECTORY     = 'archives'
CCPN_BACKUPS_DIRECTORY      = 'backups'
CCPN_SUMMARIES_DIRECTORY    = 'summaries'
CCPN_LOGS_DIRECTORY         = 'logs'
CCPN_DATA_DIRECTORY         = 'data'
CCPN_PLUGINS_DIRECTORY      = 'data/plugins'
CCPN_SPECTRA_DIRECTORY      = 'data/spectra'
CCPN_PLOTS_DIRECTORY      =    'data/plots'
CCPN_SCRIPTS_DIRECTORY      = 'scripts'
CCPN_STATE_DIRECTORY        = 'state'
CCPN_STATESPECTRA_DIRECTORY = 'state/spectra'
CCPN_RESOURCES_DIRECTORY   = 'resources'

# CCPN code
ccpnCodePath                    = Path.aPath(Path.getTopDirectory())
ccpnConfigPath                  = ccpnCodePath / 'config'
ccpnResourcesPath               = ccpnCodePath / CCPN_RESOURCES_DIRECTORY
ccpnBinPath                     = ccpnCodePath / 'bin'
ccpnBatchPath                   = ccpnCodePath / 'bat'
ccpnRunTerminal                 = ccpnBinPath / 'runTerminal.sh'
defaultPreferencesPath          = ccpnConfigPath / 'defaultv3settings.json'
tipOfTheDayConfig               = ccpnConfigPath / 'tipConfig.hjson'

_ccpnPythonPath                 = Path.aPath(Path.getPythonDirectory())
ccpnmodelPythonPath             = _ccpnPythonPath / 'ccpnmodel'
ccpnmodelDataPythonPath         = _ccpnPythonPath / 'ccpnmodel' / 'data'
ccpnmodelRefDataPythonPath      = _ccpnPythonPath / 'ccpnmodel' / 'data' / 'ccpnv3'

ccpnPythonPath                  = _ccpnPythonPath / 'ccpn'
ccpnGUIPath                     =  ccpnPythonPath / 'ui' / 'gui'
analysisAssignPath              = ccpnPythonPath / 'AnalysisAssign'
analysisScreenPath              = ccpnPythonPath / 'AnalysisScreen'
analysisStructurePath           = ccpnPythonPath / 'AnalysisStructure'
analysisMetabolomicsPath        = ccpnPythonPath / 'AnalysisMetabolomics'
ccpnApplicationPaths            = (analysisAssignPath, analysisScreenPath, analysisStructurePath, analysisMetabolomicsPath)

macroPath                       = ccpnPythonPath / 'macros'
pluginPath                      = ccpnPythonPath / 'plugins'
pipePath                        = ccpnPythonPath / 'pipes'
pipeTemplates                   = ccpnPythonPath / 'framework' / 'lib' / 'pipeline' / 'templates'
widgetsPath                     = ccpnGUIPath / 'widgets'
fontsPath                       = widgetsPath    / 'fonts'
iconsPath                       = widgetsPath    / 'icons'
openGLFontsPath                 = fontsPath      / 'Fonts'
nefValidationPath               = ccpnPythonPath / 'util' / 'nef' / 'NEF' / 'specification' / 'mmcif_nef_v1_1.dic'
peakPickerPath                  = ccpnPythonPath / 'core' / 'lib' / 'PeakPickers'
ccpnModuleHelpPath              = ccpnGUIPath / 'modules' / 'moduleHelp'

# Program tutorials and documentation
shortcutsPath                   = ccpnCodePath / 'doc' / 'static' / 'AnalysisShortcuts.htm'
tutorialsPath                   = ccpnCodePath / 'tutorials'
beginnersTutorialPath           = ccpnCodePath / 'tutorials' / 'BeginnersTutorial.pdf'
backboneAssignmentTutorialPath  = ccpnCodePath / 'tutorials' / 'BackboneAssignmentTutorial.pdf'
screenTutorialPath              = ccpnCodePath / 'tutorials' / 'CcpNmr_AnalysisScreen_Tutorial_Beta2Release.pdf'
cspTutorialPath                 = ccpnCodePath / 'tutorials' / 'CSPTutorial.pdf'
solidStatePeptideTutorialPath   = ccpnCodePath / 'tutorials' / 'SolidStatePeptideAssignmentTutorial.pdf'
solidStateHETsTutorialPath      = ccpnCodePath / 'tutorials' / 'SolidStateHETsAssignmentTutorial.pdf'
solidStateSH3TutorialPath       = ccpnCodePath / 'tutorials' / 'SolidStateSH3AssignmentTutorial.pdf'
macroWritingTutorialPath        = ccpnCodePath / 'tutorials' / 'MacroWritingTutorial.pdf'
screeningTutorialPath           = ccpnCodePath / 'tutorials' / 'ScreeningTutorial.pdf'
howTosPath                      = tutorialsPath / 'How-Tos'

documentationPath               = ccpnCodePath / 'doc' / 'build' / 'html' / 'index.html'
licensePath                     = ccpnCodePath / 'LICENSE.txt'

# Resources Path
ccpnResourcesChemicalShifts     = ccpnResourcesPath / 'referenceChemicalShifts'

# User settings
userPreferencesDirectory        = Path.aPath('~/.ccpn')
userPreferencesPath             = userPreferencesDirectory / 'v3settings.json'
userPreferencesPathInvalid      = userPreferencesDirectory / 'invalidPreferences'

userCcpnPath                    = Path.aPath('~/.ccpn')
userCcpnDataPath                = userCcpnPath / 'data'
userCcpnMacroPath               = userCcpnPath / 'macro'
userCcpnPipesPath               = userCcpnPath / 'pipes'
userCcpnResourcesPath               = userCcpnPath / CCPN_RESOURCES_DIRECTORY
userCcpnPathSubDirectories      = ['data', 'macros', 'pipes']  # These get created by framework

userDefaultProjectPath          = userCcpnDataPath / 'default.ccpn'

# Predefined layouts
predefinedLayouts               = ccpnCodePath / 'layouts'
# layout file name in the Project/State directory
projectStateLayoutFileName      = 'layout_3_1.json'

# others; also defined in util.Path and from there imported in Api and Implementation
# DO NOT REMOVE and keep in sync (for circular import reasons) (for now!)
CCPN_DIRECTORY_SUFFIX    = '.ccpn'
CCPN_BACKUP_SUFFIX       = '_backup'  # used by Project, ApiLoader; deprecated

CCPN_SUB_DIRECTORIES = [
    CCPN_API_DIRECTORY, CCPN_ARCHIVES_DIRECTORY, CCPN_BACKUPS_DIRECTORY,
    CCPN_SUMMARIES_DIRECTORY, CCPN_LOGS_DIRECTORY, CCPN_DATA_DIRECTORY,
    CCPN_PLUGINS_DIRECTORY, CCPN_SPECTRA_DIRECTORY, CCPN_SCRIPTS_DIRECTORY,
    CCPN_STATE_DIRECTORY, CCPN_STATESPECTRA_DIRECTORY, CCPN_RESOURCES_DIRECTORY,
    CCPN_PLOTS_DIRECTORY
]

ccpnVersionHistory = 'versionHistory.json'

# historical
CCPN_EXTENSION = CCPN_DIRECTORY_SUFFIX
