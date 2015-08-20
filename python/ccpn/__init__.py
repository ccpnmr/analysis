"""CCPN data. High level interface for normal data access

The standard ways of starting a project are:

- :ref:`ccpn-openProject-ref` (*path*, ...)
- :ref:`ccpn-newProject-ref` (*projectName*, ...)
- :ref:`ccpn-Project-ref` (*ccpncore.api.ccp.nmr.Nmr.NmrProject*)

Classes are listed with parent (containing) classes before their child (contained) classes.
The Project class is the top of the tree, and  a single directly or indirectly contains
all other objects.

All classes in this module are subclasses of the :ref:`ccpn-AbstractWrapperObject-ref`


.. currentmodule:: ccpn

Module level functions :
------------------------

.. _ccpn-openProject-ref:

ccpn.openProject
^^^^^^^^^^^^^^^^

.. autofunction:: ccpn.openProject

.. _ccpn-newProject-ref:

ccpn.newProject
^^^^^^^^^^^^^^^

.. autofunction:: ccpn.newProject

"""

import importlib
from ccpncore.util import ApiFunc

# Import classes and set to this module
# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
# _wrappedClassNames gives import order
_wrappedClasses = []
AbstractWrapperObject = cls = importlib.import_module(
  'ccpn._wrapper._AbstractWrapperObject').AbstractWrapperObject
_wrappedClasses.append(cls)
Project = cls = importlib.import_module('ccpn._wrapper._Project').Project
_wrappedClasses.append(cls)
#Note = cls = importlib.import_module('ccpn._wrapper._Note').Note
#_wrappedClasses.append(cls)
Chain = cls = importlib.import_module('ccpn._wrapper._Chain').Chain
_wrappedClasses.append(cls)
Residue = cls = importlib.import_module('ccpn._wrapper._Residue').Residue
_wrappedClasses.append(cls)
Atom = cls = importlib.import_module('ccpn._wrapper._Atom').Atom
_wrappedClasses.append(cls)
NmrChain = cls = importlib.import_module('ccpn._wrapper._NmrChain').NmrChain
_wrappedClasses.append(cls)
NmrResidue = cls = importlib.import_module('ccpn._wrapper._NmrResidue').NmrResidue
_wrappedClasses.append(cls)
NmrAtom = cls = importlib.import_module('ccpn._wrapper._NmrAtom').NmrAtom
_wrappedClasses.append(cls)
ChemicalShiftList = cls = importlib.import_module(
  'ccpn._wrapper._ChemicalShiftList').ChemicalShiftList
_wrappedClasses.append(cls)
ChemicalShift = cls = importlib.import_module('ccpn._wrapper._ChemicalShift').ChemicalShift
_wrappedClasses.append(cls)
Sample = cls = importlib.import_module('ccpn._wrapper._Sample').Sample
_wrappedClasses.append(cls)
SampleComponent = cls = importlib.import_module('ccpn._wrapper._SampleComponent').SampleComponent
_wrappedClasses.append(cls)
Spectrum = cls = importlib.import_module('ccpn._wrapper._Spectrum').Spectrum
_wrappedClasses.append(cls)
SpectrumReference = cls = importlib.import_module(
  'ccpn._wrapper._SpectrumReference').SpectrumReference
_wrappedClasses.append(cls)
PseudoDimension = cls = importlib.import_module('ccpn._wrapper._PseudoDimension').PseudoDimension
_wrappedClasses.append(cls)
SpectrumHit = cls = importlib.import_module('ccpn._wrapper._SpectrumHit').SpectrumHit
_wrappedClasses.append(cls)
PeakList = cls = importlib.import_module('ccpn._wrapper._PeakList').PeakList
_wrappedClasses.append(cls)
Peak = cls = importlib.import_module('ccpn._wrapper._Peak').Peak
_wrappedClasses.append(cls)
RestraintSet = cls = importlib.import_module('ccpn._wrapper._RestraintSet').RestraintSet
_wrappedClasses.append(cls)
RestraintList = cls = importlib.import_module('ccpn._wrapper._RestraintList').RestraintList
_wrappedClasses.append(cls)
Restraint = cls = importlib.import_module('ccpn._wrapper._Restraint').Restraint
_wrappedClasses.append(cls)
RestraintContribution = cls = importlib.import_module(
  'ccpn._wrapper._RestraintContribution').RestraintContribution
_wrappedClasses.append(cls)

# Add class list for extended sphinx documentation to module
# putting AnstractWrapperObj3ct last
_sphinxWrappedClasses = _wrappedClasses[1:] + _wrappedClasses[:1]

# set main starting functions in namespace. Must be done after setting Project
# to avoid circular import problems
from ccpn.util import Io as ccpnIo
openProject = ccpnIo.openProject
newProject = ccpnIo.newProject


# NBNB set function parameter annotations for AbstractBaseClass functions
# MUST be done here to get correct class type
AbstractWrapperObject.__init__.__annotations__['project'] = Project
AbstractWrapperObject.project.fget.__annotations__['return'] = Project


# Set up interclass links and related functions
Project._linkWrapperClasses()

# Load in additional utility functions int wrapper classes
# NB this does NOT pick up utility functions in non-child classes
# (e.g. AbstractWrapperObject or MainWindow) so these must be avoided
libModule = 'ccpn.lib.wrapper'
allActiveClasses = [Project]
for cls in allActiveClasses:
  # moduleName = '%s.%s' % (libModule, cls.__name__)
  ApiFunc._addModuleFunctionsToApiClass( cls.__name__, cls, rootModuleName=libModule)
  allActiveClasses.extend(cls._childClasses)

