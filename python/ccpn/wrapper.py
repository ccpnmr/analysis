"""Wrapper around CCPN NMR project - only file appliations need to import"""

from ccp.api.nmr.Nmr import NmrProject as Ccpn_NmrProject

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is simported
from ccpcode._AbstractWrapperClass import AbstractWrapperClass
from ccpcode._Project import Project
from ccpcode._Molecule import Molecule
from ccpcode._Chain import Chain
from ccpcode._Residue import Residue


def makeWrapperProject(ccpn_NmrProject: Ccpn_NmrProject) -> Project:
  """make wrapper project around CCPN NmrProject"""
  return Project(ccpn_NmrProject)
