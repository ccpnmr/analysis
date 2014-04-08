"""Wrapper around CCPN NMR project - only file appliations need to import"""

from ccpncore.api.ccp.nmr.Nmr import NmrProject as Ccpn_NmrProject

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpn._Molecule import Molecule
from ccpn._Chain import Chain
from ccpn._Residue import Residue


def makeWrapperProject(ccpn_NmrProject: Ccpn_NmrProject) -> Project:
  """make wrapper project around CCPN NmrProject"""
  return Project(ccpn_NmrProject)
