"""Wrapper level utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn._wrapper._Project import Project
from ccpncore.api.memops.Implementation import MemopsRoot as ApiProject
from ccpncore.util import Io as ioUtil, Io

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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


def openProject(path:str, nmrProjectName:str=None) -> Project:
  """Open project at path, and create a wrapper project.

  Will use named nmrProject, first NmrProject if no name given,
  and will create a new NmrProject if none exists"""
  apiProject = ioUtil.loadProject(path)
  if apiProject is None:
    raise ValueError("No valid project loaded from %s" % path )
  else:
    return _wrapApiProject(apiProject, nmrProjectName=nmrProjectName)


def newProject(projectName:str, path:str=None) -> Project:
  """Make new project at path, and create a wrapper project"""
  apiProject = ioUtil.newProject(projectName, path, removeExisting=True)
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