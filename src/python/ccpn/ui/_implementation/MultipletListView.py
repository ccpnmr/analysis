"""MultipletList View in a specific SpectrumView

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import operator
import typing
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
# from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripMultipletListView as ApiStripMultipletListView
# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import MultipletListView as ApiMultipletListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.ui._implementation.PeakListViewABC import PeakListViewABC


class MultipletListView(PeakListViewABC):
    """Multiplet List View for 1D or nD MultipletList"""

    #: Short class name, for PID.
    shortClassName = 'GU'
    # Attribute it necessary as subclasses must use superclass className
    className = 'MultipletListView'

    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'multipletListViews'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripMultipletListView._metaclass.qualifiedName()

    def _setListClasses(self):
        """Set the primary classType for the child list attached to this container
        """
        self._apiListView = self._wrappedData.multipletListView
        self._apiListSerial = self._wrappedData.multipletListView.multipletListSerial
        self._apiList = self._wrappedData.multipletListView.multipletList

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiMultipletListView(self) -> ApiStripMultipletListView:
        """ CCPN MultipletListView matching MultipletListView"""
        return self._wrappedData

    # @property
    # def _parent(self) -> SpectrumView:
    #     """SpectrumView containing MultipletListView."""
    #     return self._project._data2Obj.get(self._wrappedData.stripSpectrumView)
    #
    # spectrumView = _parent
    #
    # def delete(self):
    #     """MultipletListViews cannot be deleted, except as a byproduct of deleting other things"""
    #     raise Exception("MultipletListViews cannot be deleted directly")
    #
    # @property
    # def _key(self) -> str:
    #     """id string - """
    #     return str(self._wrappedData.multipletListView.multipletListSerial)

    @property
    def _childClass(self):
        """Ccpn core obj that multipletListView refers to"""
        return self.multipletList

    # @property
    # def _localCcpnSortKey(self) -> typing.Tuple:
    #     """Local sorting key, in context of parent."""
    #     return (self._wrappedData.multipletListView.multipletListSerial,)
    #
    # @property
    # def symbolStyle(self) -> str:
    #     """Symbol style for displayed multiplet markers.
    #
    #     If not set for MultipletListView gives you the value for MultipletList.
    #     If set for MultipletListView overrides MultipletList value.
    #     Set MultipletListView value to None to return to non-local value"""
    #     wrappedData = self._wrappedData.multipletListView
    #     result = wrappedData.symbolStyle
    #     if result is None:
    #         obj = wrappedData.multipletList
    #         result = obj and obj.symbolStyle
    #     return result
    #
    # @symbolStyle.setter
    # def symbolStyle(self, value: str):
    #     if self.symbolStyle != value:
    #         self._wrappedData.multipletListView.symbolStyle = value
    #
    # @property
    # def symbolColour(self) -> str:
    #     """Symbol style for displayed multiplet markers.
    #
    #     If not set for MultipletListView gives you the value for MultipletList.
    #     If set for MultipletListView overrides MultipletList value.
    #     Set MultipletListView value to None to return to non-local value"""
    #     wrappedData = self._wrappedData.multipletListView
    #     result = wrappedData.symbolColour
    #     if result is None:
    #         obj = wrappedData.multipletList
    #         result = obj and obj.symbolColour
    #     return result
    #
    # @symbolColour.setter
    # def symbolColour(self, value: str):
    #     if self.symbolColour != value:
    #         self._wrappedData.multipletListView.symbolColour = value
    #
    # @property
    # def textColour(self) -> str:
    #     """Symbol style for displayed multiplet markers.
    #
    #     If not set for MultipletListView gives you the value for MultipletList.
    #     If set for MultipletListView overrides MultipletList value.
    #     Set MultipletListView value to None to return to non-local value"""
    #     wrappedData = self._wrappedData.multipletListView
    #     result = wrappedData.textColour
    #     if result is None:
    #         obj = wrappedData.multipletList
    #         result = obj and obj.textColour
    #     return result
    #
    # @textColour.setter
    # def textColour(self, value: str):
    #     if self.textColour != value:
    #         self._wrappedData.multipletListView.textColour = value
    #
    # @property
    # def isSymbolDisplayed(self) -> bool:
    #     """True if the multiplet marker symbol is displayed."""
    #     return self._wrappedData.multipletListView.isSymbolDisplayed
    #
    # @isSymbolDisplayed.setter
    # def isSymbolDisplayed(self, value: bool):
    #     self._wrappedData.multipletListView.isSymbolDisplayed = value
    #
    # @property
    # def isTextDisplayed(self) -> bool:
    #     """True if the multiplet annotation is displayed?"""
    #     return self._wrappedData.multipletListView.isTextDisplayed
    #
    # @isTextDisplayed.setter
    # def isTextDisplayed(self, value: bool):
    #     self._wrappedData.multipletListView.isTextDisplayed = value

    @property
    def multipletList(self) -> MultipletList:
        """MultipletList that MultipletListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.multipletListView.multipletList)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumView) -> typing.Optional[list]:
        """get wrappedData (ccpnmr.gui.Task.MultipletListView) in serial number order"""
        if hasattr(parent._wrappedData, 'stripMultipletListViews'):
            return sorted(parent._wrappedData.stripMultipletListViews,
                          key=operator.attrgetter('multipletListView.multipletListSerial'))
        else:
            return None

    def _propagateAction(self, data):
        from ccpn.core.lib.Notifiers import Notifier

        trigger = data[Notifier.TRIGGER]

        trigger = 'change' if trigger == 'observe' else trigger
        if trigger in ['change']:
            self._finaliseAction(trigger)


#=========================================================================================
# CCPN functions
#=========================================================================================


# newMultipletListView functions: None

# MultipletList.multipletListViews property
def getter(multipletList: MultipletList) -> typing.Tuple[MultipletListView, ...]:
    data2ObjDict = multipletList._project._data2Obj
    return tuple(data2ObjDict[y]
                 for x in multipletList._wrappedData.sortedMultipletListViews()
                 for y in x.sortedStripMultipletListViews() if not x.isDeleted)


MultipletList.multipletListViews = property(getter, None, None,
                                            "MultipletListViews showing Spectrum")
del getter

# Notifiers:
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripMultipletListViews', 'action': 'change'},
         ApiStripMultipletListView._metaclass.qualifiedName(), '')
        )

#EJB 20181122: moved to MultipletList
# Notify MultipletListView change when MultipletList changes
# MultipletList._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                                  {'pathToObject': 'multipletListViews', 'action': 'change'})


def _multipletListAddMultipletListViews(project: Project, apiMultipletList: Nmr.MultipletList):
    """Add ApiMultipletListView when ApiMultipletList is created"""
    for apiSpectrumView in apiMultipletList.dataSource.spectrumViews:
        apiListView = apiSpectrumView.newMultipletListView(multipletListSerial=apiMultipletList.serial, multipletList=apiMultipletList)
        apiListView.__dict__['symbolColour'] = None
        apiListView.__dict__['textColour'] = None


#
Project._setupApiNotifier(_multipletListAddMultipletListViews, Nmr.MultipletList, 'postInit')


def _spectrumViewAddMultipletListViews(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiMultipletListView when ApiSpectrumView is created"""
    for apiMultipletList in apiSpectrumView.dataSource.multipletLists:
        apiListView = apiSpectrumView.newMultipletListView(multipletListSerial=apiMultipletList.serial, multipletList=apiMultipletList)
        apiListView.__dict__['symbolColour'] = None
        apiListView.__dict__['textColour'] = None


#
Project._setupApiNotifier(_spectrumViewAddMultipletListViews, ApiSpectrumView, 'postInit')
