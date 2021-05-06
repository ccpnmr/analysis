"""
Generate PulldownListCompoundWidget for project objects; 
set callback's on creation, deletion and rename

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-05-06 14:04:51 +0100 (Thu, May 06, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys

from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier


SELECT = '> Select <'
UNDEFINED = '<Undefined>'

DEBUG = True


class _PulldownABC(PulldownListCompoundWidget):
    """
    Abstract base class for v3 object PulldownListCompound widgets
    """

    # need to subclass these
    _klass = None
    _className = None
    _shortClassName = None
    _attributeName = None
    _currentAttributeName = None

    def __init__(self, parent,
                 mainWindow=None,
                 showBorder=False, orientation='left',
                 minimumWidths=(100, 150), maximumWidths=None, fixedWidths=None,
                 labelText=None,
                 showSelectName=False, selectNoneText=None,
                 callback=None, default=None,
                 sizeAdjustPolicy=None, editable=False,
                 filterFunction=None, useIds=False,
                 setCurrent=False, followCurrent=False,
                 **kwds):
        """
        Create a PulldownListCompoundWidget with callbacks responding to changes in the objects
        in project; not to be used directly, used as a base class for the specific classes for 
        the different V3 objects, as defined below.

        :param parent: parent widget
        :param project: containing project
        :param showBorder: flag to display the border of Frame (True, False)
        :param orientation: flag to determine the orientation of the labelText relative to the pulldown widget.
                            Allowed values: 'left', 'right', 'top', 'bottom'
        :param minimumWidths: tuple of two values specifying the minimum width of the Label and Pulldown widget, respectively
        :param labelText: (optional) text for the Label
        :param texts: (optional) iterable generating text values for the Pulldown
        :param showSelectName: (optional) insert <Select> at the top of the Pulldown
        :param selectNameText: (optional) alternative text for <Select> at the top of the Pulldown
        :param callback: (optional) callback for the Pulldown
        :param default: (optional) initially selected element of the Pulldown (text or index)
        :param editable: If True: allows for editing the value
        :param filterFunction: a function(pids:list)->list for editing the pids shown in the pulldown;
                               returns list of new pids
        :param useIds: If true: use id's in stead of pids
        :param setCurrent: Also set appropriate current attribute when selecting
        :param followCurrent: Follow current attribute; updating when it changes
        :param kwds: (optional) keyword, value pairs for the gridding of Frame
      
        """
        # class needs some attributes to be checked and defined before super()

        if self._attributeName is None:
            raise RuntimeError('%s: _attributeName needs to be defined for proper functioning' % self.__class__.__name__)

        self.mainWindow = mainWindow
        if self.mainWindow:
            self.application = mainWindow.application
            project = self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            project = self.project = None
            self.current = None

        self._showSelectName = showSelectName
        self._selectNoneText = selectNoneText
        self._filterFunction = filterFunction
        self._useIds = useIds
        self._userCallback = callback

        if labelText is None:
            labelText = self._className + ':'

        if setCurrent and self._currentAttributeName is None:
            raise ValueError('setCurrent option only valid if _currentAttributeName is defined for class')
        self._setCurrent = setCurrent
        if followCurrent and self._currentAttributeName is None:
            raise ValueError('followCurrent option only valid if _currentAttributeName is defined for class')
        self._followCurrent = followCurrent

        super().__init__(parent=parent, showBorder=showBorder,
                         orientation=orientation,
                         minimumWidths=minimumWidths, maximumWidths=maximumWidths, fixedWidths=fixedWidths,
                         labelText=labelText,
                         texts=self._getPids(),
                         sizeAdjustPolicy=sizeAdjustPolicy,
                         callback=self._callback,
                         editable=editable,
                         **kwds)

        if default is not None:
            if isinstance(default, int):
                pass

            elif isinstance(default, self._klass):
                # objs = self.getObjects()
                # default = objs.index(default) if default in objs else None
                default = self.object2value(default)

            else:
                raise ValueError('default parameter: expected int or "%s" object, got "%s"'
                                 % (self._klass.className, type(default)))

            if default is not None:
                self.select(default, blockSignals=True)

        # add a notifier to update the pulldown list
        if project:
            self._notifier1 = Notifier(project,
                                       [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                       self._className,
                                       self._updatePulldownList)
            self._notifier1.setDebug(DEBUG)

            self._notifier2 = None
            if self._followCurrent:
                self._notifier2 = Notifier(self.current,
                                           [Notifier.CURRENT],
                                           targetName=self._currentAttributeName,
                                           callback=self._updateFromCurrent
                                           )
                self._notifier2.setDebug(DEBUG)

    @property
    def textList(self):
        """Compatibility with previous implementation
        """
        return self.pulldownList.texts

    def getSelectedObject(self):
        """Return the selected object, or None if not selected or empty
        """
        obj = None
        value = self.getText()
        if value != SELECT and len(value) > 0:
            obj = self.value2object(value)
        return obj

    def getObjects(self):
        """Return a list of objects from the pulldown list
        """
        return [self.value2object(val) for val in self.textList if val != SELECT]

    def getCurrentObject(self):
        """Return relevant attribute from current if _currentAttributeName is defined
        """
        if self._currentAttributeName is None:
            raise RuntimeError('%s: _currentAttributeName needs to be defined for proper functioning' % self.__class__.__name__)
        obj = None
        _tmp = getattr(self.current, self._currentAttributeName)
        if _tmp is not None and len(_tmp) > 0:
            obj = _tmp[0]
        #sys.stderr.write('>>> currentObject:\n', obj)
        return obj

    def getFirstItemText(self):
        result = None
        texts = [txt for txt in self.pulldownList.texts if txt != SELECT]
        if texts:
            result = texts[0]
        return result

    def selectFirstItem(self):
        """Set the table to the first item.
        """
        firstItemName = self.getFirstItemText()
        if firstItemName:
            self.select(firstItemName)

    def object2value(self, obj):
        """Convert object to a value (pid or id), to be displayed
        """
        if obj is None:
            return str(None)
        value = obj.id if self._useIds else obj.pid
        return value

    def value2object(self, value):
        """Convert value to object, using pid or construct a pid from id
        Return None if value does not represent a valid V3 object
        """
        if value is None or len(value) == 0 or value == SELECT:
            return None
        if self._useIds:
            value = self._shortClassName + ':' + value
        obj = self.project.getByPid(value)
        return obj

    def update(self):
        """Public function to update
        """
        if self._followCurrent:
            self._updateFromCurrent()
        else:
            self._updatePulldownList()

    def unRegister(self):
        """Unregister the notifiers; needs to be called when disgarding a instance
        """
        try:
            if self._notifier1 is not None:
                self._notifier1.unRegister()
                del (self._notifier1)
            if self._notifier2 is not None:
                self._notifier2.unRegister()
                del (self._notifier2)
        except:
            pass

    #==============================================================================================
    # Implementation
    #==============================================================================================

    def _getPids(self) -> list:
        """Return a list of pids defined by 'self._attributeName' from project.
        """
        if self.project:
            pids = [self.object2value(obj) for obj in getattr(self.project, self._attributeName)]
            if self._filterFunction:
                pids = self._filterFunction(pids)
            if self._followCurrent:
                # add current if it is not part of the pids
                current = self.getCurrentObject()
                if current is not None:
                    currentPid = self.object2value(current)
                    if currentPid not in pids:
                        pids = [currentPid] + pids
                if current is None and not self._showSelectName:
                    pids = [UNDEFINED] + pids

            if self._showSelectName:
                if self._selectNoneText:
                    select = [self._selectNoneText]
                else:
                    select = [SELECT]
                pids = select + pids
            return pids
        return []

    def _updatePulldownList(self, callbackDict=None):
        """Callback to update the pulldown list; triggered by object creation, deletion or renaming
        """
        if DEBUG: sys.stderr.write('>>> %s._updatePulldownList()\n' % self)
        pids = self._getPids()

        # update the pid list with renamed, created or deleted pids
        lastPulldownItem = self.getText()
        newName = None
        if callbackDict:
            obj = callbackDict[Notifier.OBJECT]
            trigger = callbackDict[Notifier.TRIGGER]
            if trigger == Notifier.DELETE:
                # the object has been notified for delete but still exists so needs to be removed from the list
                if obj.pid in pids:
                    pids.remove(obj.pid)
            elif trigger == Notifier.RENAME:
                if callbackDict[Notifier.OLDPID] == lastPulldownItem:
                    newName = obj.pid

        self.modifyTexts(pids)

        # if the pulldownlist has updated then emit a changed notifier; assumes that the texts are unique
        newPulldownItem = self.getText()
        if lastPulldownItem != newPulldownItem:
            if newName:
                self.select(newName, blockSignals=True)

            else:
                newItem = self.pulldownList.currentIndex()
                self.pulldownList.currentIndexChanged.emit(newItem)

        if DEBUG: sys.stderr.write('  < %s._updatePulldownList()\n' % self)

    def _updateFromCurrent(self, callbackDict=None):
        """Callback to update the selection from current change
        """
        obj = self.getCurrentObject()
        if DEBUG: sys.stderr.write('>>> %s._updateFromCurrent() "%s": %s\n' %
                                   (self, self._currentAttributeName, obj))
        self._updatePulldownList(callbackDict=callbackDict)
        if obj is not None:
            value = self.object2value(obj)
            self.select(value, blockSignals=True)
        else:
            self.setIndex(0, blockSignals=True)
        if DEBUG: sys.stderr.write('  < %s._updateFromCurrent()\n' % self)

    def _callback(self, value):
        """Callback when selecting the pulldown
        """
        if DEBUG: sys.stderr.write('>>> %s._callback() selecting pulldown: %s\n' % (self, value))
        if self._userCallback:
            value = self._userCallback(value)
        if self._setCurrent and value != SELECT and len(value) > 0:
            obj = self.value2object(value)
            if DEBUG: sys.stderr.write('>>> %s._callback() selecting pulldown: setting current.%s to %s\n' %
                                       (self, self._currentAttributeName, obj))
            setattr(self.current, self._currentAttributeName, [obj])
        if DEBUG: sys.stderr.write('  < %s._callback() selecting pulldown\n' % self)

    def __str__(self):
        return '<%s>' % self.__class__.__name__

    @staticmethod
    def onDestroyed(widget):
        if DEBUG: sys.stderr.write('>>> being destroyed:\n', widget)


#==========================================================================================================
# Implementations for the various V3 objects
#==========================================================================================================

def _definedBy(klass):
    """Return relevant attributes from klass
    """
    return (klass, klass.className, klass.shortClassName, klass._pluralLinkName)


class AtomPulldown(_PulldownABC):
    """"A PulldownListCompoundWidget class for Atoms
    """
    from ccpn.core.Atom import Atom

    _klass, _className, _shortClassName, _attributeName = _definedBy(Atom)
    _currentAttributeName = None


class CalculationStepPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for CalculationSteps
    """
    from ccpn.core.CalculationStep import CalculationStep

    _klass, _className, _shortClassName, _attributeName = _definedBy(CalculationStep)
    _currentAttributeName = None


class ChainPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Chains
    """
    from ccpn.core.Chain import Chain

    _klass, _className, _shortClassName, _attributeName = _definedBy(Chain)
    _currentAttributeName = 'chains'


class ChemicalShiftPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for ChemicalShifts
    """
    from ccpn.core.ChemicalShift import ChemicalShift

    _klass, _className, _shortClassName, _attributeName = _definedBy(ChemicalShift)
    _currentAttributeName = 'chemicalShifts'


class ChemicalShiftListPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for ChemicalShiftLists
    """
    from ccpn.core.ChemicalShiftList import ChemicalShiftList

    _klass, _className, _shortClassName, _attributeName = _definedBy(ChemicalShiftList)
    _currentAttributeName = 'chemicalShiftLists'


class ComplexPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Complexs
    """
    from ccpn.core.Complex import Complex

    _klass, _className, _shortClassName, _attributeName = _definedBy(Complex)
    _currentAttributeName = None


class DataPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Datas
    """
    from ccpn.core.Data import Data

    _klass, _className, _shortClassName, _attributeName = _definedBy(Data)
    _currentAttributeName = None


class DataSetPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for DataSets
    """
    from ccpn.core.DataSet import DataSet

    _klass, _className, _shortClassName, _attributeName = _definedBy(DataSet)
    _currentAttributeName = None


class IntegralPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Integrals
    """
    from ccpn.core.Integral import Integral

    _klass, _className, _shortClassName, _attributeName = _definedBy(Integral)
    _currentAttributeName = 'integrals'


class IntegralListPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for IntegralLists
    """
    from ccpn.core.IntegralList import IntegralList

    _klass, _className, _shortClassName, _attributeName = _definedBy(IntegralList)
    _currentAttributeName = None


class ModelPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Models
    """
    from ccpn.core.Model import Model

    _klass, _className, _shortClassName, _attributeName = _definedBy(Model)
    _currentAttributeName = None


class MultipletPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Multiplets
    """
    from ccpn.core.Multiplet import Multiplet

    _klass, _className, _shortClassName, _attributeName = _definedBy(Multiplet)
    _currentAttributeName = 'multiplets'


class MultipletListPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for MultipletLists
    """
    from ccpn.core.MultipletList import MultipletList

    _klass, _className, _shortClassName, _attributeName = _definedBy(MultipletList)
    _currentAttributeName = None


class NmrAtomPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for NmrAtoms
    """
    from ccpn.core.NmrAtom import NmrAtom

    _klass, _className, _shortClassName, _attributeName = _definedBy(NmrAtom)
    _currentAttributeName = 'nmrAtoms'


class NmrChainPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for NmrChains
    """
    from ccpn.core.NmrChain import NmrChain

    _klass, _className, _shortClassName, _attributeName = _definedBy(NmrChain)
    _currentAttributeName = 'nmrChains'


class NmrResiduePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for NmrResidues
    """
    from ccpn.core.NmrResidue import NmrResidue

    _klass, _className, _shortClassName, _attributeName = _definedBy(NmrResidue)
    _currentAttributeName = 'nmrResidues'


class NotePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Notes
    """
    from ccpn.core.Note import Note

    _klass, _className, _shortClassName, _attributeName = _definedBy(Note)
    _currentAttributeName = None


class PeakPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Peaks
    """
    from ccpn.core.Peak import Peak

    _klass, _className, _shortClassName, _attributeName = _definedBy(Peak)
    _currentAttributeName = 'peaks'


class PeakClusterPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for PeakClusters
    """
    from ccpn.core.PeakCluster import PeakCluster

    _klass, _className, _shortClassName, _attributeName = _definedBy(PeakCluster)
    _currentAttributeName = None


class PeakListPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for PeakLists
    """
    from ccpn.core.PeakList import PeakList

    _klass, _className, _shortClassName, _attributeName = _definedBy(PeakList)
    _currentAttributeName = None


class PseudoDimensionPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for PseudoDimensions
    """
    from ccpn.core.PseudoDimension import PseudoDimension

    _klass, _className, _shortClassName, _attributeName = _definedBy(PseudoDimension)
    _currentAttributeName = None


class ResiduePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Residues
    """
    from ccpn.core.Residue import Residue

    _klass, _className, _shortClassName, _attributeName = _definedBy(Residue)
    _currentAttributeName = 'residues'


class RestraintPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Restraints
    """
    from ccpn.core.Restraint import Restraint

    _klass, _className, _shortClassName, _attributeName = _definedBy(Restraint)
    _currentAttributeName = None


class RestraintContributionPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for RestraintContributions
    """
    from ccpn.core.RestraintContribution import RestraintContribution

    _klass, _className, _shortClassName, _attributeName = _definedBy(RestraintContribution)
    _currentAttributeName = None


class RestraintListPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for RestraintLists
    """
    from ccpn.core.RestraintList import RestraintList

    _klass, _className, _shortClassName, _attributeName = _definedBy(RestraintList)
    _currentAttributeName = None


class SamplePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Samples
    """
    from ccpn.core.Sample import Sample

    _klass, _className, _shortClassName, _attributeName = _definedBy(Sample)
    _currentAttributeName = 'samples'


class SampleComponentPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for SampleComponents
    """
    from ccpn.core.SampleComponent import SampleComponent

    _klass, _className, _shortClassName, _attributeName = _definedBy(SampleComponent)
    _currentAttributeName = None


class SpectrumPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Spectrums
    """
    from ccpn.core.Spectrum import Spectrum

    _klass, _className, _shortClassName, _attributeName = _definedBy(Spectrum)
    _currentAttributeName = None


class SpectrumGroupPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for SpectrumGroups
    """
    from ccpn.core.SpectrumGroup import SpectrumGroup

    _klass, _className, _shortClassName, _attributeName = _definedBy(SpectrumGroup)
    _currentAttributeName = 'spectrumGroups'


class SpectrumHitPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for SpectrumHits
    """
    from ccpn.core.SpectrumHit import SpectrumHit

    _klass, _className, _shortClassName, _attributeName = _definedBy(SpectrumHit)
    _currentAttributeName = 'spectrumHits'


class SpectrumReferencePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for SpectrumReferences
    """
    from ccpn.core.SpectrumReference import SpectrumReference

    _klass, _className, _shortClassName, _attributeName = _definedBy(SpectrumReference)
    _currentAttributeName = None


class StructureEnsemblePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for StructureEnsembles
    """
    from ccpn.core.StructureEnsemble import StructureEnsemble

    _klass, _className, _shortClassName, _attributeName = _definedBy(StructureEnsemble)
    _currentAttributeName = None


class SubstancePulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for Substances
    """
    from ccpn.core.Substance import Substance

    _klass, _className, _shortClassName, _attributeName = _definedBy(Substance)
    _currentAttributeName = 'substances'


class SpectrumDisplayPulldown(_PulldownABC):
    """A PulldownListCompoundWidget class for SpectrumDisplays
    """
    from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay

    _klass, _className, _shortClassName, _attributeName = _definedBy(SpectrumDisplay)
    _currentAttributeName = None
