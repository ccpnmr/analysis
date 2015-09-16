"""Wrapper level utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn import Project
from ccpncore.api.memops.Implementation import MemopsRoot as ApiProject
from ccpncore.util import Io as ioUtil

def loadProject(path:str, nmrProjectName:str=None, useFileLogger:bool=True) -> Project:
  """Open project (API project) stored at path.

  If the API project contains several NmrProjects (rare),
  nmrProjectName lets you select which one to open"""
  apiProject = ioUtil.loadProject(path, useFileLogger=useFileLogger)
  if apiProject is None:
    raise ValueError("No valid project loaded from %s" % path )
  else:
    return _wrapApiProject(apiProject, nmrProjectName=nmrProjectName)


def newProject(projectName:str, path:str=None, useFileLogger:bool=True) -> Project:
  """Make new project, putting underlying data storage (API project) at path"""
  apiProject = ioUtil.newProject(projectName, path, removeExisting=True, useFileLogger=useFileLogger)
  if apiProject is None:
    raise ValueError("New project could not be created (overlaps exiting project?) name:%s, path:%s"
                     % (projectName, path) )
  else:
    return Project(apiProject.newNmrProject(name=projectName))


def _wrapApiProject(apiProject:ApiProject, nmrProjectName:str=None) -> Project:
  """convert existing MemopsRoot to wrapped Project, using nmrProjectName to select NmrProject"""

  nmrProjects = apiProject.sortedNmrProjects()
  if nmrProjects:
    if nmrProjectName:
      nmrProject = apiProject.findFirstNmrProject(name=nmrProjectName)
      if nmrProject is None:
        raise ValueError("No NmrProject found with name: %s" % nmrProjectName)
    else:
      nmrProject = nmrProjects[0]
  else:
    nmrProject = apiProject.newNmrProject(name=nmrProjectName or 'default')

  return Project(nmrProject)