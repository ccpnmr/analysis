"""PeakList View in a specific SpectrumView

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import operator
import typing

from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView

# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import PeakListView as ApiPeakListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr


class PeakListView(AbstractWrapperObject):
    """Peak List View for 1D or nD PeakList"""

    #: Short class name, for PID.
    shortClassName = 'GL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakListView'

    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakListViews'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripPeakListView._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiPeakListView(self) -> ApiStripPeakListView:
        """ CCPN PeakListView matching PeakListView"""
        return self._wrappedData

    @property
    def _parent(self) -> SpectrumView:
        """SpectrumView containing PeakListView."""
        return self._project._data2Obj.get(self._wrappedData.stripSpectrumView)

    spectrumView = _parent

    def delete(self):
        """PeakListViews cannot be deleted, except as a byproduct of deleting other things"""
        raise Exception("PeakListViews cannot be deleted directly")

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.peakListView.peakListSerial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.peakListView.peakListSerial,)

    @property
    def symbolStyle(self) -> str:
        """Symbol style for displayed peak markers.

        If not set for PeakListView gives you the value for PeakList.
        If set for PeakListView overrides PeakList value.
        Set PeakListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.peakListView
        result = wrappedData.symbolStyle
        if result is None:
            obj = wrappedData.peakList
            result = obj and obj.symbolStyle
        return result

    @symbolStyle.setter
    def symbolStyle(self, value: str):
        if self.symbolStyle != value:
            self._wrappedData.peakListView.symbolStyle = value

    @property
    def symbolColour(self) -> str:
        """Symbol style for displayed peak markers.

        If not set for PeakListView gives you the value for PeakList.
        If set for PeakListView overrides PeakList value.
        Set PeakListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.peakListView
        result = wrappedData.symbolColour
        if result is None:
            obj = wrappedData.peakList
            result = obj and obj.symbolColour
        return result

    @symbolColour.setter
    def symbolColour(self, value: str):
        if self.symbolColour != value:
            self._wrappedData.peakListView.symbolColour = value

    @property
    def textColour(self) -> str:
        """Symbol style for displayed peak markers.

        If not set for PeakListView gives you the value for PeakList.
        If set for PeakListView overrides PeakList value.
        Set PeakListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.peakListView
        result = wrappedData.textColour
        if result is None:
            obj = wrappedData.peakList
            result = obj and obj.textColour
        return result

    @textColour.setter
    def textColour(self, value: str):
        if self.textColour != value:
            self._wrappedData.peakListView.textColour = value

    @property
    def isSymbolDisplayed(self) -> bool:
        """True if the peak marker symbol is displayed."""
        return self._wrappedData.peakListView.isSymbolDisplayed

    @isSymbolDisplayed.setter
    def isSymbolDisplayed(self, value: bool):
        self._wrappedData.peakListView.isSymbolDisplayed = value

    @property
    def isTextDisplayed(self) -> bool:
        """True if the peak annotation is displayed?"""
        return self._wrappedData.peakListView.isTextDisplayed

    @isTextDisplayed.setter
    def isTextDisplayed(self, value: bool):
        self._wrappedData.peakListView.isTextDisplayed = value

    @property
    def peakList(self) -> PeakList:
        """PeakList that PeakListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.peakListView.peakList)

    @property
    def _childClass(self):
        """Ccpn core obj that PeakListView refers to"""
        return self.peakList

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumView) -> typing.Optional[list]:
        """get wrappedData (ccpnmr.gui.Task.PeakListView) in serial number order"""
        if hasattr(parent._wrappedData, 'stripPeakListViews'):
            return sorted(parent._wrappedData.stripPeakListViews,
                          key=operator.attrgetter('peakListView.peakListSerial'))
        else:
            return None

#=========================================================================================
# CCPN functions
#========================================================================================

# newPeakListView functions: None

from ccpn.util.Common import makeIterableList

# PeakList.peakListViews property
def getter(peakList: PeakList) -> typing.Tuple[PeakListView, ...]:
    data2ObjDict = peakList._project._data2Obj

    # splvs = [x for x in peakList._wrappedData.sortedPeakListViews()]
    # ssplvs = [y.sortedStripPeakListViews() for y in splvs if not y.isDeleted]
    # plvs = tuple(data2ObjDict[y] for y in makeIterableList(ssplvs))

    return tuple(data2ObjDict[y]
                 for x in peakList._wrappedData.sortedPeakListViews()
                 for y in x.sortedStripPeakListViews() if not x.isDeleted)

    # could add the test .. and y in data2ObjDict)
    # but just moves the error somewhere else


PeakList.peakListViews = property(getter, None, None,
                                  "PeakListViews showing Spectrum")
del getter

# # MultipletList.peakListViews property
# from ccpn.core.MultipletList import MultipletList
# def getter(multipletList:MultipletList) -> typing.Tuple[PeakListView, ...]:
#   data2ObjDict = multipletList._project._data2Obj
#   return tuple(data2ObjDict[y]
#                for x in multipletList._wrappedData.sortedPeakListViews()
#                for y in x.sortedStripPeakListViews() if not x.isDeleted)
# MultipletList.peakListViews = property(getter, None, None,
#                                   "peakListViews showing Spectrum")
# del getter


# Notifiers:
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripPeakListViews', 'action': 'change'},
         ApiStripPeakListView._metaclass.qualifiedName(), '')
        )

#EJB 20181122: moved to PeakList _finaliseAction
# Notify PeakListView change when PeakList changes
# PeakList._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                             {'pathToObject': 'peakListViews', 'action': 'change'})


def _peakListAddPeakListViews(project: Project, apiPeakList: Nmr.PeakList):
    """Add ApiPeakListView when ApiPeakList is created"""
    for apiSpectrumView in apiPeakList.dataSource.spectrumViews:
        apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)


#
Project._setupApiNotifier(_peakListAddPeakListViews, Nmr.PeakList, 'postInit')


def _spectrumViewAddPeakListViews(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiPeakListView when ApiSpectrumView is created"""
    for apiPeakList in apiSpectrumView.dataSource.peakLists:
        apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)


#
Project._setupApiNotifier(_spectrumViewAddPeakListViews, ApiSpectrumView, 'postInit')
