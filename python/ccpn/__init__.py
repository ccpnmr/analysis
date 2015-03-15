"""CCPN data. High level interface for normal data access

The standard ways of starting a project are:

- ccpn.openProject(*path*, ...)
- ccpn.newProject(*projectName*, ...)
- ccpn.Project(*ccpncore.api.ccp.nmr.Nmr.NmrProject*)


.. currentmodule:: ccpn

.. autosummary::

  openProject
  newProject
   _Project.Project
   _Chain.Chain
   _Residue.Residue
   _Atom.Atom
   _NmrChain.NmrChain
   _NmrResidue.NmrResidue
   _NmrAtom.NmrAtom
   _ChemicalShiftList.ChemicalShiftList
   _ChemicalShift.ChemicalShift
   _Spectrum.Spectrum
   _SpectrumReference.SpectrumReference
   _PeakList.PeakList
   _Peak.Peak
   _RestraintSet.RestraintSet
   _RestraintList.RestraintList
   _Restraint.Restraint
   _RestraintContribution.RestraintContribution
   _AbstractWrapperClass.AbstractWrapperClass

ccpn.Project class
------------------

.. autoclass:: ccpn._wrapper._Project.Project

ccpn.Chain class
----------------

.. autoclass:: ccpn._wrapper._Chain.Chain

ccpn.Residue class
------------------

.. autoclass:: ccpn._wrapper._Residue.Residue

ccpn.Atom class
---------------

.. autoclass:: ccpn._wrapper._Atom.Atom

ccpn.NmrChain class
-------------------

.. autoclass:: ccpn._wrapper._NmrChain.NmrChain

ccpn.NmrResidue class
---------------------

.. autoclass:: ccpn._wrapper._NmrResidue.NmrResidue

ccpn.NmrAtom class
------------------

.. autoclass:: ccpn._wrapper._NmrAtom.NmrAtom

ccpn.ChemicalShiftList class
----------------------------

.. autoclass:: ccpn._wrapper._ChemicalShiftList.ChemicalShiftList

ccpn.ChemicalShift class
------------------------

.. autoclass:: ccpn._wrapper._ChemicalShift.ChemicalShift

ccpn.Spectrum class
-------------------

.. autoclass:: ccpn._wrapper._Spectrum.Spectrum

ccpn.SpectrumReference class
----------------------------

.. autoclass:: ccpn._wrapper._SpectrumReference.SpectrumReference

ccpn.PeakList class
-------------------

.. autoclass:: ccpn._wrapper._PeakList.PeakList

ccpn.Peak class
---------------

.. autoclass:: ccpn._wrapper._Peak.Peak

ccpn.RestraintSet class
-----------------------

.. autoclass:: ccpn._wrapper._RestraintSet.RestraintSet

ccpn.RestraintList class
------------------------

.. autoclass:: ccpn._wrapper._RestraintList.RestraintList

ccpn.Restraint class
--------------------

.. autoclass:: ccpn._wrapper._Restraint.Restraint

ccpn.RestraintContribution class
--------------------------------

.. autoclass:: ccpn._wrapper._RestraintContribution.RestraintContribution


ccpn.AbstractWrapperObject class
--------------------------------

.. autoclass:: ccpn._wrapper._AbstractWrapperObject.AbstractWrapperObject

"""

# import sys
# print ('sys.path=', sys.path)
# for key in sorted(sys.modules):
#   print(' - ', key)

from ccpncore.util import ApiFunc
from ccpn.util import Io as ccpnIo
openProject = ccpnIo.openProject
newProject = ccpnIo.newProject

libModule = 'ccpn.lib.wrapper'

# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Chain import Chain
from ccpn._wrapper._Residue import Residue
from ccpn._wrapper._Atom import Atom
from ccpn._wrapper._NmrChain import NmrChain
from ccpn._wrapper._NmrResidue import NmrResidue
from ccpn._wrapper._NmrAtom import NmrAtom
from ccpn._wrapper._ChemicalShiftList import ChemicalShiftList
from ccpn._wrapper._ChemicalShift import ChemicalShift
from ccpn._wrapper._Spectrum import Spectrum
from ccpn._wrapper._SpectrumReference import SpectrumReference
from ccpn._wrapper._PeakList import PeakList
from ccpn._wrapper._Peak import Peak
from ccpn._wrapper._RestraintSet import RestraintSet
from ccpn._wrapper._RestraintList import RestraintList
from ccpn._wrapper._Restraint import Restraint
from ccpn._wrapper._RestraintContribution import RestraintContribution

# Set up interclass links and related functions
Project._linkWrapperClasses()

# Load in additional utility functions int wrapper classes
# NB this does NOT pick up utility functions in non-child classes
# (e.g. AbstractWrapperObject or MainWindow) so these must be avoided
allActiveClasses = [Project]
for cls in allActiveClasses:
  # moduleName = '%s.%s' % (libModule, cls.__name__)
  ApiFunc._addModuleFunctionsToApiClass( cls.__name__, cls, rootModuleName=libModule)
  allActiveClasses.extend(cls._childClasses)

