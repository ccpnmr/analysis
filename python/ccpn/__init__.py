"""Top level module for CCPN data wrapper """

from ccpncore.util import Io as ioUtil

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpn._Molecule import Molecule
from ccpn._Chain import Chain
from ccpn._Residue import Residue
from ccpn._Atom import Atom
from ccpn._Spectrum import Spectrum

# Set up interclass links and related functions
Project._linkWrapperClasses()


def openProject(path:str, nmrProjectName=None) -> Project:
  """Open project at path, and create a wrapper project.
  Will use named nmrProject, first NmrProject if no name given,
  and will create a new NmrProject if none exists"""
  apiProject = ioUtil.loadProject(path)
  if apiProject is None:
    raise ValueError("No valid project loaded from %s" % path )
  else:
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

def newProject(projectName:str, path:str=None) -> Project:
  """Open project at path, and create a wrapper project"""
  apiProject = ioUtil.newProject(projectName, path, removeExisting=True)
  if apiProject is None:
    raise ValueError("New project could not be created (overlaps exiting project?) name:%s, path:%s"
                     % (projectName, path) )
  else:
    return Project(apiProject.newNmrProject(name=projectName))
