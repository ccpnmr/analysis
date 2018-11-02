"""
Generate PulldownListCompoundWidget for project objects; 
set callback's on creation, deletion and rename

"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:55 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.core.lib.Notifiers import Notifier

SELECT = '<Select>'


class _Pulldown(PulldownListCompoundWidget):
    # need to subclass this
    _klass = None
    className = None
    attributeName = None
    currentAttributeName = None


    def __init__(self, parent, project,
                 showBorder=False, orientation='left',
                 minimumWidths=(100, 150), maximumWidths=None, fixedWidths=None,
                 labelText=None,
                 showSelectName=False, callback=None, default=None,
                 sizeAdjustPolicy=None, editable=False,
                 filterFunction=None, useIds=False,
                 setCurrent=False, followCurrent=False,
                 **kwds):
        """
        Create  a PulldownListCompoundWidget with callbacks responding to changes in the objects
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
        if self._klass is not None:
            self.className = self._klass.className
            self.shortClassName = self._klass.shortClassName

        self.project = project
        self.current = self.project.application.current

        self._showSelectName = showSelectName
        self._filterFunction = filterFunction
        self._useIds = useIds
        self._userCallback = callback

        if labelText is None:
            labelText = self.className + ':'

        if setCurrent and self.currentAttributeName is None:
            raise ValueError('setCurrent option only valied if currentAttributeName is defined for class')
        self._setCurrent = setCurrent
        if followCurrent and self.currentAttributeName is None:
            raise ValueError('followCurrent option only valied if currentAttributeName is defined for class')
        self._followCurrent = followCurrent

        super(_Pulldown, self).__init__(parent=parent, showBorder=showBorder,
                                        orientation=orientation,
                                        minimumWidths=minimumWidths, maximumWidths=maximumWidths, fixedWidths=fixedWidths,
                                        labelText=labelText,
                                        texts=self._getPids(),
                                        sizeAdjustPolicy=sizeAdjustPolicy,
                                        callback=self._callback, default=default,
                                        editable=editable,
                                        **kwds)
        # add a notifier to update the pulldown list
        self._notifier1 = Notifier(project,
                                   [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                   self.className,
                                   self._updatePulldownList)
        self._notifier2 = None
        if self._followCurrent:
            self._notifier2 = Notifier(self.current,
                                       [Notifier.CURRENT],
                                       targetName=self.currentAttributeName,
                                       callback=self._updateFromCurrent
                                      )

    @property
    def textList(self):
        "Compatibility with previous implementation"
        return self.pulldownList.texts

    def _getPids(self)->list:
        """Return a list of pids defined by 'self.attributeName' from project.
        """
        if not hasattr(self, 'attributeName'):
            raise RuntimeError('%s: attributeName needs to be defined for proper functioning' % self.__class__.__name__)
        pids = [self._obj2value(obj) for obj in getattr(self.project, self.attributeName)]
        if self._filterFunction:
            pids = self._filterFunction(pids)
        if self._showSelectName:
            pids = [SELECT] + pids
        return pids

    def _obj2value(self, obj):
        "Convert object to a value (pid or id), to be displayed"
        if obj is None:
            return str(None)
        value = obj.id if self._useIds else obj.pid
        return value

    def _value2obj(self, value):
        "Convert value to object, using pid or construct a pid from id"
        if self._useIds:
            value = self.shortClassName + ':' + value
        #print('>>> _value2obj:', value)
        obj = self.project.getByPid(value)
        return obj

    def _updatePulldownList(self, callbackDict=None):
        "Callback to update the pulldown list; triggered by object creation, deletion or renaming"
        print('>>> updatePulldownList')
        pids = self._getPids()
        self.modifyTexts(pids)

    def _updateFromCurrent(self, callbackDict=None):
        "Callback to update the selection from current change"
        newValue = callbackDict[Notifier.VALUE]
        print('>>> updateFromCurrent:', newValue)
        if newValue:
            self.select(self._obj2value(newValue[0]))

    def update(self):
        "Public function to update"
        self._updatePulldownList()

    def _callback(self, value):
        "Callback when selecting the pulldown"
        print('>>> callback selecting pulldown:', value)
        if self._userCallback:
            value = self._userCallback(value)
        if self._setCurrent and value != SELECT and len(value) > 0:
            obj = self._value2obj(value)
            print('>>> callback setting current.%s: %s' % (self.currentAttributeName, obj))
            setattr(self.current, self.currentAttributeName, [obj])

    def __str__(self):
        return '<PulldownListCompoundWidget for "%s">' % self.className

    def __del__(self):
        "cleanup"
        try:
            if self._notifier1 is not None:
                self._notifier1.unRegister()
                del (self._notifier1)
            if self._notifier2 is not None:
                self._notifier2.unRegister()
                del(self._notifier2)
        except:
            pass

#==========================================================================================================
# Implementations for the various V3 objects
#==========================================================================================================

class MultipletListPulldown(_Pulldown):
    className = 'MultipletList'
    attributeName = 'multipletLists'


from ccpn.core.NmrChain import NmrChain
class NmrChainPulldown(_Pulldown):
    _klass = NmrChain
    attributeName = 'nmrChains'
    currentAttributeName = 'nmrChains'

from ccpn.core.NmrResidue import NmrResidue
class NmrResiduePulldown(_Pulldown):
    _klass = NmrResidue
    attributeName = 'nmrResidues'
    currentAttributeName = 'nmrResidues'

from ccpn.core.NmrAtom import NmrAtom
class NmrAtomPulldown(_Pulldown):
    _klass = NmrAtom
    attributeName = 'nmrAtoms'
    currentAttributeName = 'nmrAtoms'


class ComplexesPulldown(_Pulldown):
    className = 'Complex'
    attributeName = 'complexes'


class ChainPulldown(_Pulldown):
    className = 'Chain'
    attributeName = 'chains'


class StructurePulldown(_Pulldown):
    className = 'StructureEnsemble'
    attributeName = 'structureEnsembles'


class NotesPulldown(_Pulldown):
    className = 'Note'
    attributeName = 'notes'


class RestraintsPulldown(_Pulldown):
    className = 'RestraintList'
    attributeName = 'restraintLists'


class ChemicalShiftListPulldown(_Pulldown):
    className = 'ChemicalShiftList'
    attributeName = 'chemicalShiftLists'


class PeakListPulldown(_Pulldown):
    className = 'PeakList'
    attributeName = 'peakLists'


class SubstancePulldown(_Pulldown):
    className = 'Substance'
    attributeName = 'substances'


class SpectrumPulldown(_Pulldown):
    className = 'Spectrum'
    attributeName = 'spectra'


class IntegralListPulldown(_Pulldown):
    className = 'IntegralList'
    attributeName = 'integralLists'
