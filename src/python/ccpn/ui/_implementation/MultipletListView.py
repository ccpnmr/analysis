"""MultipletList View in a specific SpectrumView

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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-10-25 11:08:17 +0100 (Fri, October 25, 2024) $"
__version__ = "$Revision: 3.2.7.GWV $"
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

from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripMultipletListView as ApiStripMultipletListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import MultipletListView as ApiMultipletListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpn.ui._implementation.PMIListViewABC import PMIListViewABC


class MultipletListView(PMIListViewABC):
    """Multiplet List View for 1D or nD MultipletList
    """
    #-----------------------------------------------------------------------------------------

    #: Short class name, for PID.
    shortClassName = 'GU'
    # Attribute it necessary as subclasses must use superclass className
    className = 'MultipletListView'

    _parentClassName = 'SpectrumView'
    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'multipletListViews'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripMultipletListView._metaclass.qualifiedName()

    #-----------------------------------------------------------------------------------------

    def _setListClasses(self):
        """Set the primary classType for the child list attached to this container
        """
        self._apiListView = self._wrappedData.multipletListView
        self._apiListSerial = self._wrappedData.multipletListView.multipletListSerial
        self._apiList = self._wrappedData.multipletListView.multipletList

    @property
    def _listObject(self):
        """:return: the Peak|Multiplet|Integral List object associated with this view
        """
        return self.multipletList

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiMultipletListView(self) -> ApiStripMultipletListView:
        """ CCPN MultipletListView matching MultipletListView"""
        return self._wrappedData

    @property
    def multipletList(self) -> MultipletList:
        """MultipletList that MultipletListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.multipletListView.multipletList)

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.multipletListView.multipletListSerial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.multipletListView.multipletListSerial,)

    #=========================================================================================
    # property STUBS: hot-fixed later
    #=========================================================================================

    @property
    def multipletViews(self) -> list['MultipletView']:
        """STUB: hot-fixed later
        :return: a list of multipletViews in the MultipletListView
        """
        return []

    #=========================================================================================
    # getter STUBS: hot-fixed later
    #=========================================================================================

    def getMultipletView(self, relativeId: str) -> 'MultipletView | None':
        """STUB: hot-fixed later
        :return: an instance of MultipletView, or None
        """
        return None

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumView) -> list:
        """get wrappedData (ccpnmr.gui.Task.MultipletListView) in serial number order.
        """
        if hasattr(parent._wrappedData, 'stripMultipletListViews'):
            return sorted(parent._wrappedData.stripMultipletListViews,
                          key=operator.attrgetter('multipletListView.multipletListSerial'))
        return []

    def _propagateAction(self, data):
        from ccpn.core.lib.Notifiers import Notifier

        trigger = data[Notifier.TRIGGER]

        trigger = 'change' if trigger == 'observe' else trigger
        if trigger in ['change']:
            self._finaliseAction(trigger)


#=========================================================================================
# CCPN functions
#=========================================================================================


def _newMultipletListView(spectrumView, multipletList: MultipletList) -> MultipletListView:
    """Create a new MultipletListView object
    :param spectrumView: the (parent) SpectrumView object
    :param multipletList: the corresponding MultipletList object
    :return MultipletListView instance
    """
    apiSpectrumView = spectrumView._wrappedData
    project = multipletList.project

    apiMultipletListView = apiSpectrumView.newStripMultipletListView(multipletListSerial=multipletList.serial,
                                                                     multipletList=multipletList._wrappedData)
    if (result := MultipletListView._newInstanceFromApiData(apiObj=apiMultipletListView, project=project)) is None:
        raise RuntimeError('Failed to generate new MultipletListView instance')

    return result


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
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripMultipletListViews', 'action': 'change'},
         ApiMultipletListView._metaclass.qualifiedName(), '')
        )


def _newApiMultipletListCallback(project: Project, apiMultipletList: Nmr.MultipletList):
    """Add ApiMultipletListView when ApiMultipletList is created"""
    from ccpn.core.lib.Notifiers import NotifierBase
    # need to use the gui version
    from ccpn.ui.gui.lib.MultipletListView import MultipletListView as _MultipletListView

    if NotifierBase._apiNotificationBlanking == 0:
        # create new apiObjects if not blocked
        for apiSpectrumView in apiMultipletList.dataSource.spectrumViews:
            apiMultipletListView = apiSpectrumView.newMultipletListView(multipletListSerial=apiMultipletList.serial,
                                                                        multipletList=apiMultipletList)
            if _MultipletListView._newInstanceFromApiData(apiObj=apiMultipletListView.findFirstStripMultipletListView(),
                                                          project=project) is None:
                raise RuntimeError('Unable to generate new MultipletListView')


Project._setupApiNotifier(_newApiMultipletListCallback, Nmr.MultipletList, 'postInit')


def _newApiSpectrumViewAddMultipletListViewCallback(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiMultipletListView when ApiSpectrumView is created
    """
    # need to use the gui version
    from ccpn.ui.gui.lib.MultipletListView import MultipletListView as _MultipletListView

    for apiMultipletList in apiSpectrumView.dataSource.multipletLists:
        apiMultipletListView = apiSpectrumView.newMultipletListView(multipletListSerial=apiMultipletList.serial,
                                                                    multipletList=apiMultipletList)
        if _MultipletListView._newInstanceFromApiData(apiObj=apiMultipletListView.findFirstStripMultipletListView(),
                                                      project=project) is None:
            raise RuntimeError('Unable to generate new MultipletListView')


Project._setupApiNotifier(_newApiSpectrumViewAddMultipletListViewCallback, ApiSpectrumView, 'postInit')
