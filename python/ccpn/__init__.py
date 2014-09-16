"""CCPN data. High level interface for normal data access

The standard ways of starting a project are:

- ccpn.openProject(*path*, ...)
- ccpn.newProject(*projectName*, ...)
- ccpn.Project(*ccpncore.api.ccp.nmr.Nmr.NmrProject*)


.. currentmodule:: ccpn

.. autosummary::

  openProject
  newProject
   _AbstractWrapperClass.AbstractWrapperClass
   _Project.Project
   _Molecule.Molecule
   _Chain.Chain
   _Residue.Residue
   _Atom.Atom
   _Spectrum.Spectrum


ccpn.AbstractWrapperClass class
-------------------------------

.. autoclass:: ccpn._wrapper._AbstractWrapperClass.AbstractWrapperClass

ccpn.Project class
------------------

.. autoclass:: ccpn._wrapper._Project.Project

ccpn.Molecule class
-------------------

.. autoclass:: ccpn._wrapper._Molecule.Molecule

ccpn.Chain class
----------------

.. autoclass:: ccpn._wrapper._Chain.Chain

ccpn.Residue class
------------------

.. autoclass:: ccpn._wrapper._Residue.Residue

ccpn.Atom class
---------------

.. autoclass:: ccpn._wrapper._Atom.Atom

ccpn.Spectrum class
-------------------

.. autoclass:: ccpn._wrapper._Spectrum.Spectrum

"""

# import sys
# print ('sys.path=', sys.path)
# for key in sorted(sys.modules):
#   print(' - ', key)

from ccpncore.util import Io as ioUtil

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Molecule import Molecule
from ccpn._wrapper._Chain import Chain
from ccpn._wrapper._Residue import Residue
from ccpn._wrapper._Atom import Atom
from ccpn._wrapper._ChemicalShiftList import ChemicalShiftList
from ccpn._wrapper._ChemicalShift import ChemicalShift
from ccpn._wrapper._Spectrum import Spectrum
from ccpn._wrapper._SpectrumReference import SpectrumReference
from ccpn._wrapper._PeakList import PeakList
from ccpn._wrapper._Peak import Peak

# Set up interclass links and related functions
Project._linkWrapperClasses()


def openProject(path:str, nmrProjectName:str=None) -> Project:
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
  """Make new project at path, and create a wrapper project"""
  apiProject = ioUtil.newProject(projectName, path, removeExisting=True)
  if apiProject is None:
    raise ValueError("New project could not be created (overlaps exiting project?) name:%s, path:%s"
                     % (projectName, path) )
  else:
    return Project(apiProject.newNmrProject(name=projectName))
