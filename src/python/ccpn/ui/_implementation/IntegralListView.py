"""IntegralList View in a specific SpectrumView

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
from ccpn.core.IntegralList import IntegralList
from ccpn.core.Project import Project
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripIntegralListView as ApiStripIntegralListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.ui._implementation.PMIListViewABC import PMIListViewABC


class IntegralListView(PMIListViewABC):
    """Integral List View for 1D or nD IntegralList
    """

    #: Short class name, for PID.
    shortClassName = 'GI'
    # Attribute it necessary as subclasses must use superclass className
    className = 'IntegralListView'

    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'integralListViews'

    #: List of child classes.
    _childClasses = []

    _isGuiClass = True

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripIntegralListView._metaclass.qualifiedName()

    def _setListClasses(self):
        """Set the primary classType for the child list attached to this container
        """
        self._apiListView = self._wrappedData.integralListView
        self._apiListSerial = self._wrappedData.integralListView.integralListSerial
        self._apiList = self._wrappedData.integralListView.integralList

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiIntegralListView(self) -> ApiStripIntegralListView:
        """ CCPN IntegralListView matching IntegralListView"""
        return self._wrappedData

    @property
    def _childClass(self):
        """Ccpn core obj that integralListView refers to"""
        return self.integralList

    @property
    def integralList(self) -> IntegralList:
        """IntegralList that IntegralListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.integralListView.integralList)

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.integralListView.integralListSerial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.integralListView.integralListSerial,)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: SpectrumView) -> typing.Optional[list]:
        """get wrappedData (ccpnmr.gui.Task.IntegralListView) in serial number order"""
        if hasattr(parent._wrappedData, 'stripIntegralListViews'):
            return sorted(parent._wrappedData.stripIntegralListViews,
                          key=operator.attrgetter('integralListView.integralListSerial'))
        else:
            return None


#=========================================================================================
# CCPN functions
#=========================================================================================


# newIntegralListView functions: None

# IntegralList.integralListViews property
def getter(integralList: IntegralList) -> typing.Tuple[IntegralListView, ...]:
    data2ObjDict = integralList._project._data2Obj
    return tuple(data2ObjDict[y]
                 for x in integralList._wrappedData.sortedIntegralListViews()
                 for y in x.sortedStripIntegralListViews() if not x.isDeleted)


IntegralList.integralListViews = property(getter, None, None,
                                          "IntegralListViews showing Spectrum")
del getter

# Notifiers:
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
        ('_notifyRelatedApiObject', {'pathToObject': 'stripIntegralListViews', 'action': 'change'},
         ApiStripIntegralListView._metaclass.qualifiedName(), '')
        )


#EJB 20181122: moved to IntegralList
# Notify IntegralListView change when IntegralList changes
# IntegralList._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                                 {'pathToObject': 'integralListViews', 'action': 'change'})


def _integralListAddIntegralListViews(project: Project, apiIntegralList: Nmr.IntegralList):
    """Add ApiIntegralListView when ApiIntegralList is created"""
    for apiSpectrumView in apiIntegralList.dataSource.spectrumViews:
        apiListView = apiSpectrumView.newIntegralListView(integralListSerial=apiIntegralList.serial, integralList=apiIntegralList)


#
Project._setupApiNotifier(_integralListAddIntegralListViews, Nmr.IntegralList, 'postInit')


def _spectrumViewAddIntegralListViews(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiIntegralListView when ApiSpectrumView is created"""
    for apiIntegralList in apiSpectrumView.dataSource.integralLists:
        apiListView = apiSpectrumView.newIntegralListView(integralListSerial=apiIntegralList.serial, integralList=apiIntegralList)


#
Project._setupApiNotifier(_spectrumViewAddIntegralListViews, ApiSpectrumView, 'postInit')
