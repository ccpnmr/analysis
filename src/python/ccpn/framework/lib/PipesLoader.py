from ccpn.framework.Framework import AnalysisScreen, AnalysisAssign, AnalysisMetabolomics, AnalysisStructure
from ccpn.util import Path
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
import os


PIPE_ANALYSIS = 'Analysis'
PIPE_ASSIGN = AnalysisAssign
PIPE_SCREEN = AnalysisScreen
PIPE_METABOLOMICS = AnalysisMetabolomics
PIPE_STRUCTURE = AnalysisStructure

PIPE_PROCESSING = 'Processing'
PIPE_POSTPROCESSING = 'Post-Processing'
PIPE_GENERIC = 'Generic'
PIPE_OUTPUTS = 'Outputs'
PIPE_USER = 'User'

PIPE_CATEGORIES = [PIPE_ANALYSIS,
                   PIPE_ASSIGN,
                   PIPE_SCREEN,
                   PIPE_METABOLOMICS,
                   PIPE_STRUCTURE,
                   PIPE_PROCESSING,
                   PIPE_POSTPROCESSING,
                   PIPE_GENERIC,
                   PIPE_OUTPUTS,
                   PIPE_USER]

def loadPipes(path):
    '''
    dynamic pipe importer. When called on the __init__ file inside a directory containing registered pipes,
    they will appear inside the pipeline
    '''
    import pkgutil as _pkgutil
    for loader, name, isPpkg in _pkgutil.walk_packages(path):
        found = loader.find_module(name)
        if found:
            module = found.load_module(name)


def _fetchUserPipesPath(application):
    '''
    get the userPipesPath from preferences if defined, otherwise it creates a dir in the .ccpn dir
    '''
    defaultDirName = 'pipes'
    preferencesPipesTag = 'userPipesPath'
    preferences = application.preferences
    if preferencesPipesTag in preferences.general:
        savedPath = preferences.general.userPipesPath
        if os.path.exists(savedPath):
            return savedPath
        else:
            path = Path.fetchDir(userPreferencesDirectory, defaultDirName)
            return path
    else:
        path = Path.fetchDir(userPreferencesDirectory, defaultDirName)
        return path

