"""IntegralList View in a specific SpectrumView

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:41 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumView import SpectrumView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import StripIntegralListView as ApiStripIntegralListView

# from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import IntegralListView as ApiIntegralListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr


class IntegralListView(AbstractWrapperObject):
    """Integral List View for 1D or nD IntegralList"""

    #: Short class name, for PID.
    shortClassName = 'GI'
    # Attribute it necessary as subclasses must use superclass className
    className = 'IntegralListView'

    _parentClass = SpectrumView

    #: Name of plural link to instances of class
    _pluralLinkName = 'integralListViews'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiStripIntegralListView._metaclass.qualifiedName()

    # CCPN properties  
    @property
    def _apiIntegralListView(self) -> ApiStripIntegralListView:
        """ CCPN IntegralListView matching IntegralListView"""
        return self._wrappedData

    @property
    def _parent(self) -> SpectrumView:
        """SpectrumView containing IntegralListView."""
        return self._project._data2Obj.get(self._wrappedData.stripSpectrumView)

    spectrumView = _parent

    def delete(self):
        """IntegralListViews cannot be deleted, except as a byproduct of deleting other things"""
        raise Exception("IntegralListViews cannot be deleted directly")

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.integralListView.integralListSerial)

    @property
    def _childClass(self):
        """Ccpn core obj that integralListView refers to"""
        return self.integralList

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.integralListView.integralListSerial,)

    @property
    def symbolStyle(self) -> str:
        """Symbol style for displayed integral markers.
    
        If not set for IntegralListView gives you the value for IntegralList.
        If set for IntegralListView overrides IntegralList value.
        Set IntegralListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.integralListView
        result = wrappedData.symbolStyle
        if result is None:
            obj = wrappedData.integralList
            result = obj and obj.symbolStyle
        return result

    @symbolStyle.setter
    def symbolStyle(self, value: str):
        if self.symbolStyle != value:
            self._wrappedData.integralListView.symbolStyle = value

    @property
    def symbolColour(self) -> str:
        """Symbol style for displayed integral markers.
    
        If not set for IntegralListView gives you the value for IntegralList.
        If set for IntegralListView overrides IntegralList value.
        Set IntegralListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.integralListView
        result = wrappedData.symbolColour
        if result is None:
            obj = wrappedData.integralList
            result = obj and obj.symbolColour
        return result

    @symbolColour.setter
    def symbolColour(self, value: str):
        if self.symbolColour != value:
            self._wrappedData.integralListView.symbolColour = value

    @property
    def textColour(self) -> str:
        """Symbol style for displayed integral markers.
    
        If not set for IntegralListView gives you the value for IntegralList.
        If set for IntegralListView overrides IntegralList value.
        Set IntegralListView value to None to return to non-local value"""
        wrappedData = self._wrappedData.integralListView
        result = wrappedData.textColour
        if result is None:
            obj = wrappedData.integralList
            result = obj and obj.textColour
        return result

    @textColour.setter
    def textColour(self, value: str):
        if self.textColour != value:
            self._wrappedData.integralListView.textColour = value

    @property
    def isSymbolDisplayed(self) -> bool:
        """True if the integral marker symbol is displayed."""
        return self._wrappedData.integralListView.isSymbolDisplayed

    @isSymbolDisplayed.setter
    def isSymbolDisplayed(self, value: bool):
        self._wrappedData.integralListView.isSymbolDisplayed = value

    @property
    def isTextDisplayed(self) -> bool:
        """True if the integral annotation is displayed?"""
        return self._wrappedData.integralListView.isTextDisplayed

    @isTextDisplayed.setter
    def isTextDisplayed(self, value: bool):
        self._wrappedData.integralListView.isTextDisplayed = value

    @property
    def integralList(self) -> IntegralList:
        """IntegralList that IntegralListView refers to"""
        return self._project._data2Obj.get(self._wrappedData.integralListView.integralList)

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
        apiSpectrumView.newIntegralListView(integralListSerial=apiIntegralList.serial, integralList=apiIntegralList)


#
Project._setupApiNotifier(_integralListAddIntegralListViews, Nmr.IntegralList, 'postInit')


def _spectrumViewAddIntegralListViews(project: Project, apiSpectrumView: ApiSpectrumView):
    """Add ApiIntegralListView when ApiSpectrumView is created"""
    for apiIntegralList in apiSpectrumView.dataSource.integralLists:
        apiSpectrumView.newIntegralListView(integralListSerial=apiIntegralList.serial, integralList=apiIntegralList)


#
Project._setupApiNotifier(_spectrumViewAddIntegralListViews, ApiSpectrumView, 'postInit')
