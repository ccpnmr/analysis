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

# Set up interclass links and related functions
Project._linkWrapperClasses()


def openProject(path:str) -> Project:
  """Open project at path, and create a wrapper project"""
  return Project(ioUtil.loadProject(path))

def newProject(projectName:str, path:str=None) -> Project:
  """Open project at path, and create a wrapper project"""
  return Project(ioUtil.newProject(projectName, path))
