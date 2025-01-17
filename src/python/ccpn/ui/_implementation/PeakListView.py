"""PeakList View in a specific SpectrumView

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-07-03 17:29:33 +0100 (Wed, July 03, 2024) $"
__version__ = "$Revision: 3.2.5 $"
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

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import PeakListView as ApiPeakListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.ui._implementation.PMIListViewABC import PMIListViewABC


class PeakListView(PMIListViewABC):
    """Peak List View for 1D or nD PeakList
    """

    #: Short class name, for PID.
    shortClassName = 'GL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakListView'

    _parentClassName = 'SpectrumView'
    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakListViews'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripPeakListView._metaclass.qualifiedName()

    def _setListClasses(self):
        """Set the primary classType for the child list attached to this container
        """
        self._apiListView = self._wrappedData.peakListView
        self._apiListSerial = self._wrappedData.peakListView.peakListSerial
        self._apiList = self._wrappedData.peakListView.peakList

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiPeakListView(self) -> ApiStripPeakListView:
        """ CCPN PeakListView matching PeakListView"""
        return self._wrappedData

    @property
    def _childClass(self):
        """Ccpn core obj that PeakListView refers to"""
        return self.peakList

    @property
    def peakList(self) -> PeakList:
        """PeakList that PeakListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.peakListView.peakList)

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.peakListView.peakListSerial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.peakListView.peakListSerial,)

    #=========================================================================================
    # property STUBS: hot-fixed later
    #=========================================================================================

    @property
    def peakViews(self) -> list['PeakView']:
        """STUB: hot-fixed later
        :return: a list of peakViews in the PeakListView
        """
        return []

    #=========================================================================================
    # getter STUBS: hot-fixed later
    #=========================================================================================

    def getPeakView(self, relativeId: str) -> 'PeakView | None':
        """STUB: hot-fixed later
        :return: an instance of PeakView, or None
        """
        return None

    #=========================================================================================
    # Core methods
    #=========================================================================================

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumView) -> list:
        """get wrappedData (ccpnmr.gui.Task.PeakListView) in serial number order.
        """
        if hasattr(parent._wrappedData, 'stripPeakListViews'):
            return sorted(parent._wrappedData.stripPeakListViews,
                          key=operator.attrgetter('peakListView.peakListSerial'))
        return []


#=========================================================================================
# CCPN functions
#========================================================================================


# newPeakListView functions: None

# PeakList.peakListViews property
def getter(peakList: PeakList) -> typing.Tuple[PeakListView, ...]:
    data2ObjDict = peakList._project._data2Obj
    return tuple(data2ObjDict[y]
                 for x in peakList._wrappedData.sortedPeakListViews()
                 for y in x.sortedStripPeakListViews() if not x.isDeleted)


PeakList.peakListViews = property(getter, None, None,
                                  "PeakListViews showing Spectrum")
del getter

# Notifiers:
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripPeakListViews', 'action': 'change'},
         ApiPeakListView._metaclass.qualifiedName(), '')
        )


#EJB 20181122: moved to PeakList _finaliseAction
# Notify PeakListView change when PeakList changes
# PeakList._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                             {'pathToObject': 'peakListViews', 'action': 'change'})


def _peakListAddPeakListViews(project: Project, apiPeakList: Nmr.PeakList):
    """Add ApiPeakListView when ApiPeakList is created"""
    if project._apiNotificationBlanking == 0:
        # create new apiObjects if not blocked
        for apiSpectrumView in apiPeakList.dataSource.spectrumViews:
            apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)


Project._setupApiNotifier(_peakListAddPeakListViews, Nmr.PeakList, 'postInit')


def _spectrumViewAddPeakListViews(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiPeakListView when ApiSpectrumView is created"""
    for apiPeakList in apiSpectrumView.dataSource.peakLists:
        apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)


Project._setupApiNotifier(_spectrumViewAddPeakListViews, ApiSpectrumView, 'postInit')
