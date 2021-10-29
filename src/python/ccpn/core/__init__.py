"""CCPN core package. High level interface for normal data access

Projects are saved by myProject.save(path, ...)

Within the CcpNmr suite there is always a project open, assigned to the variable 'project'.

Module Organisation
-------------------

Class Hierarchy
^^^^^^^^^^^^^^^

Classes are organised in a hierarchy, with all data objects ultimately contained within the Project:
The diagram shows the hierarchy, with child objects displaced to the right of the containing parent
object. E.g. Spectrum, SpectrumGroup, and DataSet are all children of Project; PeakList and
IntegralList are both children of Spectrum; and Peak is a child of PeakList.

::

  Project
  \-------Spectrum
          \-------SpectrumReference
          \-------PeakList
                  \-------Peak
          \-------IntegralList
                  \-------Integral
          \-------PseudoDimension
          \-------SpectrumHit
  \-------SpectrumGroup
  \-------Sample
          \-------SampleComponent
  \-------Substance
  \-------Chain
          \-------Residue
                  \-------Atom
  \-------Complex
  \-------NmrChain
          \-------NmrResidue
                  \-------NmrAtom
  \-------ChemicalShiftList
          \-------ChemicalShift
  \-------DataSet
          \-------RestraintList
                  \-------Restraint
                          \-------RestraintContribution
          \-------CalculationStep
          \-------Data
  \-------StructureEnsemble
          \-------Model
  \-------Note
  \-------Collection
  \-------DataTable

The **Project** object serves as container for all other data objects and the starting
point for navigation.

A **Spectrum** object contains all the stored properties of a spectrum, as well as the path to the
stored NMR data file.

A **SpectrumReference** holds detailed information about axes and referencing needed for
e.g. multple-quantum, projection, and reduced-dimensionality experiments.

A **PeakList** serves as a container for **Peak** objects,
which contain Peak position, intensity and assignment information.

An **IntegralList** serves as a container for **Integral**
objects, which contain Integral intervals and values.

A **PseudoDimension** object is used to describe
sampled-value axes, such as the time delay axis for T1 experiments.

A **SpectrumHis** object is used in screening and metabolomics implementations to describe
that a Substance has been found to be present (metabolomics) or active (screening) in a given
spectrum.

A **SpectrumGroup** combines multiple Spectrum objects, so they can be treated as a single object.

A **Sample** corresponds to an NMR sample. It is made up of **SampleComponents**, which indicate
which individual chemical entities make up that Sample, (e.g. protein, buffer, salt), and
their concentrations.

A **Substance** object represents a defined chemical entity, e.g. Lysozyme, ATP, NaCl, or (less
commonly) a composite material like fetal calf serum or standard lysis buffer.

A **Chain** object corresponds to a molecular chain. It is made up of **Residue** objects,
which in turn are made up of **Atom** objects.

A **Complex** is a group of chain objects, combined so that they can be treated as a single
object.

Assignment is done through a hierarchy of **NmrChain**, **NmrResidue**, and **NmrAtom**
objects. that parallels the hierarchy of molecular chains. An NmrChain (NmrResidue, Atom) is
considered assigned to the Chain (Residue, Atom) with the same ID.
NmrAtom objects serve as a way of connecting a named nucleus to an observed chemical shift, and
peaks are assigned to NmrAtoms.

A **ChemicalShiftList** object is a container for **ChemicalShift** objects, which represent
observed chemical shifts.

**DataSet** objects serve to group RestraintLists and other input and output from a
calculation.

A **RestraintList** contains **Restraint** Objects of a specific type (distance, dihedral, etc.).
**RestraintContribution** objects hold the detailed information; they are needed for
complex restraints, like coupled phi and psi dihedral restraints.

The **CalculatioinStep** object is used to track the calculation history of DataSets, storing
input and output DataSet IDs, and the names of the programs used.

**Data** object storing links to the data structures (PeakLists, Spectra, StructureEnsembles
etc.) connected to a given DataSet, and their associated calculation parameters.

A **StructureEnsemble** object is a container for ensembles of coordinate structures, with each
coordinate structure defined by a **Model** object.

**Note** objects contain free-text information to be stored in a project.

A **Collection** is a container, a list of core objects. It can also contain nested collections.

A **DataTable** is a container for a pandas dataFrame object.


Common Class elements
^^^^^^^^^^^^^^^^^^^^^

All classes in this module are subclasses of the core._implementation.AbstractWrapperObject,
and inherit the following elements:

**project** - *ccpn.core.Project*

The Project (root) containing the object.

**pid** - *ccpn.util.Pid.Pid*

Identifier for the object, unique within the project.
Set automatically from the short class name and object.id
E.g. 'NA:A.102.ALA.CA'

**longPid** - *ccpn.util.Pid.Pid*

Identifier for the object, unique within the project.
Set automatically from the full class name and object.id
E.g. 'NmrAtom:A.102.ALA.CA'

**id** - *str*

Identifier for the object, used to generate the pid and longPid.
Generated by combining the id of the containing object, with the
value of one or more key attributes that uniquely identify the
object in context.
E.g. the id for an Atom, 'A.55.VAL.HA' is generated from:

    - 'A' *Chain.shortName*

    - '55' *Residue.sequenceCode*

    - 'VAL' *Residue.residueType*

    - 'HA' *Atom.name*

**delete()**

Delete object, with all contained objects and underlying data.

**getByPid(pidString)**

Get an arbitrary data object from either its pid (e.g. 'SP:HSQC2') or its longPid
(e.g. 'Spectrum:HSQC2'

Returns None for invalid or unrecognised input strings.

**rename(newName)**

Change the object name or other key attribute(s), changing the object id, pid,
and all internal references to maintain consistency.
A number of Objects (Chain, Residue, Atom, Peak, cannot be renamed

Data access
^^^^^^^^^^^

The data of objects are accessed with the normal Python syntax (x = object.value; object.value = x.
There are no public getter and setter functions. For collections you will get an unmodifiable copy
of the internal collection, to prevent accidental modification of the data
(e.g. myPeakList.peaks will return a tuple, not a list)

Each object has a link to the containing (parent) object (e.g. myPeakList.spectrum)

Each class has a link to contained objects,
and a function to get a contained object by relative id.
E.g. myProject.peaks, mySpectrum.peaks, and myPeakList.peaks will each get
all peaks contained within the relevant object. The lists will be in creation order
(where applicable) otherwise sorted by name or underlying key.
Similarly, a given peak can be found by either myProject.getPeak('HSQC2.1.593'),
mySpectrum.getPeak('1.593'), or myPeakList.getPeak('593')

Most objects can be created using a *newXyzObject* method on the parent.
E.g. you can create a new Restraint object with the myRestraintList.newRestraint(...) function.
'new' functions create a single objects, using the passed-in parameters.
There is no 'newSpectrum' function; spectra are created with 'loadSpectrum' as a complete spectrum
object requires an external file with the data.

More complex object creation is done with 'create...()' functions, that may create multiple
objects, and use heuristics to fill in missing parameters.
E.g. the myRestraintList.createRestraint(....) function creates a Restraint with the
contained RestraintContributions and restraintItems.

Functions whose names start with 'get' (e.g. getNmrAtom(...)) mostly take some kind of identifier
as an argument and returns the identified object if it exists, None otherwise.

Functions whose names start with 'fetch' (e.g. fetchNmrAtom(...)) also take some kind of identifier
as an argument.
These will return the identified object if it exists, but will create a new object otherwise.

Other common prefixes for function names include 'add' and 'remove' (which add and remove
pre-existing objects to collections), 'copy', 'clear', 'load', 'process' and 'toggle',
all of which should be self-explanatory.

Objects sort by type (in import order) then by parent, then by local key.
Sorting the objects will give a sensible and reproducible ordering for all classes.
A number of classes are returned sorted by creation order (e.g. NmrAtoms), but are
sorted by a more significant key (for NmrAtoms alphabetically by name).
ChemicalShift objects sort as the NmrAtom they belong to.
NmrResidue objects behave in there different ways:

  - If they are assigned to a Residue they sort like the Residue, in sequential order
  - If they belong to a connected NmrChain, they sort by the order they appear in the NmrChain.
  - In other 4cases they sort by creation order.
  - Offset NmrResidues in all cases sort alongside their main NmrResidue, by offset.

"""

# Previous documentation with links to top level functions. Kept here to serve as example


# All data are organised in Projects. The standard ways of starting a project are:
#
# - myProject = :ref:`ccpn-loadProject-ref` (*path*, ...)
# - myProject = :ref:`ccpn-newProject-ref` (*projectName*, ...)


# .. currentmodule:: ccpn
#
# Module level functions :
# ------------------------
#
# .. _ccpn-loadProject-ref:
#
# ccpn.loadProject
# ^^^^^^^^^^^^^^^^
#
# .. autofunction:: ccpn.loadProject
#
# .. _ccpn-newProject-ref:
#
# ccpn.newProject
# ^^^^^^^^^^^^^^^
#
# .. autofunction:: ccpn.newProject


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:44 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import importlib
import collections


# Import classes and set to this module
# All classes must be imported in correct order for subsequent code
# to work, as connections between classes are set when child class is imported
# _wrappedClassNames gives import order
#
# NB this list will be added to from other modules that also add to _coreClassMap
# in practice ccpn.ui.gui.Gui
_coreImportOrder = (
    'Project', 'Spectrum', 'SpectrumReference', 'SpectrumGroup', 'PeakList', 'Peak',
    'IntegralList', 'Integral', 'PseudoDimension', 'SpectrumHit', 'Sample', 'SampleComponent',
    'Substance', 'Chain', 'Residue', 'Atom', 'Complex', 'NmrChain', 'NmrResidue', 'NmrAtom',
    'ChemicalShiftList', '_OldChemicalShift',
    'DataSet', 'RestraintList', 'Restraint',
    'RestraintContribution', 'CalculationStep', 'Data', 'StructureEnsemble', 'Model', 'Note',
    'PeakCluster', 'MultipletList', 'Multiplet', 'DataTable', 'Collection'
    )

# This list includes ui classes (added below)
_importOrder = list(_coreImportOrder)

# {className:class, shortClassName:class} dictionary in import order for all wrapper classes
_coreClassMap = collections.OrderedDict()

# Main data classes
for className in _coreImportOrder:
    cls = getattr(importlib.import_module('ccpn.core.%s' % className), className)
    parentClass = cls._parentClass
    if parentClass is not None:
        if cls not in parentClass._childClasses:
            # Should not be necessary to check, but apparently this code can be executed twice
            parentClass._childClasses.append(cls)
    _coreClassMap[cls.className] = cls
    _coreClassMap[cls.shortClassName] = cls

# Wrapped graphics data classes
from ccpn.ui._implementation import _uiImportOrder


_importOrder.extend(_uiImportOrder)
for className in _uiImportOrder:
    cls = getattr(importlib.import_module('ccpn.ui._implementation.%s' % className), className)
    parentClass = cls._parentClass
    if parentClass is not None:
        if cls not in parentClass._childClasses:
            # Should not be necessary to check, but apparently this code can be executed twice
            parentClass._childClasses.append(cls)
    _coreClassMap[cls.className] = cls
    _coreClassMap[cls.shortClassName] = cls

# connect classes to project
# NB - customisation for different UIs is done by inserting _factoryFunctions
# from the UI class setUp
_coreClassMap['Project']._linkWrapperClasses()
