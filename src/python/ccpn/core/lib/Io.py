"""Wrapper level I/O utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

# NB this import cna cause circular imports, but ccpn.__init__ makes sure it does not happen
from ccpn.core.Project import Project
# from ccpnmodel.ccpncore.api.memops.Implementation import MemopsRoot as ApiProject
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
# from ccpnmodel.ccpncore.lib import V2Upgrade

# def _fixLoadedProject(apiProject:ApiProject):
#   """Ad hoc fixes, for reading temporary in-house data model versions etc.
#
#   No-op for regular projects"""
#   for nmrConstraintStore in apiProject.sortedNmrConstraintStores():
#     for constraintList in nmrConstraintStore.sortedConstraintLists():
#       if constraintList.className != 'GenericConstraintList':
#         newConstraintList = V2Upgrade.upgradeConstraintList(constraintList)

def loadProject(path:str, nmrProjectName:str=None, useFileLogger:bool=True) -> Project:
  """Open project matching the API Project stored at path.

  If the API project contains several NmrProjects (rare),
  nmrProjectName lets you select which one to open"""
  apiProject = apiIo.loadProject(path, useFileLogger=useFileLogger)

  # # Ad hoc fixes for temporary internal versions (etc.).
  # _fixLoadedProject(apiProject)

  if apiProject is None:
    raise ValueError("No valid project loaded from %s" % path )
  else:
    apiNmrProject = apiProject.fetchNmrProject(name=nmrProjectName)
    apiNmrProject.initialiseData()
    return Project(apiNmrProject)


def newProject(name:str='default', path:str=None, useFileLogger:bool=True) -> Project:
  """Make new project, putting underlying data storage (API project) at path"""
  apiProject = apiIo.newProject(name, path, overwriteExisting=True,
                                 useFileLogger=useFileLogger)
  if apiProject is None:
    raise ValueError("New project could not be created (overlaps exiting project?) name:%s, path:%s"
                     % (name, path) )
  else:
    apiNmrProject = apiProject.fetchNmrProject()
    apiNmrProject.initialiseData()
    return Project(apiNmrProject)

