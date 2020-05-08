from ccpn.framework.Framework import AnalysisScreen, AnalysisAssign, AnalysisMetabolomics, AnalysisStructure
from ccpn.util import Path
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
import os


def loadPipeSysModules(paths):
    '''
    dynamic pipe importer. Called upon initialisation of the program for loading the registered ccpn Pipes.
    Path = path of the top dir containing the pipes files.
    Users pipes are loaded only when opening a Gui Pipeline.
    '''
    import pkgutil as _pkgutil
    import traceback
    from ccpn.util.Logging import getLogger
    import sys

    modules = []
    name = None

    for loader, name, isPpkg in _pkgutil.walk_packages(paths):
        if name:
            try:
                found = loader.find_module(name)
                if found:
                    if sys.modules.get(name): # already loaded.
                        continue
                    else:
                        module = found.load_module(name)
                        modules.append(module)
            except Exception as err:
                traceback.print_tb(err.__traceback__)
                getLogger().warning('Error Loading Pipe %s. %s' % (name, str(err)))
    return modules


def _fetchUserPipesPath(application=None):
    '''
    get the userPipesPath from preferences if defined, otherwise it creates a dir in the .ccpn dir
    '''

    defaultDirName = 'pipes'
    preferencesPipesTag = 'userPipesPath'
    if application:
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


def _fetchDemoPipe(path):
    '''
    create the __init__.py required in the pipe directory

    '''
    from ccpn.framework.PathsAndUrls import pipeTemplates
    from shutil import copyfile

    dest = _fetchUserPipesPath()
    pass
