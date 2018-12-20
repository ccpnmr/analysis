"""Peak View in a specific PeakList View. NB currently NOT used

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:40 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
# from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import PeakView as ApiPeakView


class PeakView(AbstractWrapperObject):
    """Peak View for 1D or nD PeakList. Currently NOT used."""

    #: Short class name, for PID.
    shortClassName = 'GP'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakView'

    _parentClass = PeakListView

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakViews'

    #: List of child classes.
    _childClasses = []

    # CCPN properties
    @property
    def _apiPeakView(self) -> ApiPeakView:
        """ CCPN PeakView matching PeakView"""
        return self._wrappedData

    @property
    def _parent(self) -> PeakListView:
        """PeakListView containing PeakView."""
        return self._project._data2Obj.get(self._wrappedData.peakListView)

    spectrumView = _parent

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.peak.serial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.peak.serial,)

    @property
    def textOffset(self) -> tuple:
        """Peak X,Y text annotation offset"""
        return self._wrappedData.textOffset

    @textOffset.setter
    def textOffset(self, value: tuple):
        self._wrappedData.textOffset = value

    @property
    def peak(self) -> Peak:
        """Peak that PeakView refers to"""
        return self._project._data2Obj.get(self._wrappedData.peak)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: PeakListView) -> list:
        """get wrappedData (ccpnmr.gui.Task.PeakView) in serial number order"""
        return parent._wrappedData.sortedPeakViews()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

# newPeakView functions: None

# NB This will be needed when (if) we start using PeakViews
# # Peak.peakViews property
# def getter(peak:Peak) -> Tuple[PeakView]:
#   return tuple(peak._project._data2Obj[x]
#                for x in peak._wrappedData.sortedPeakViews())
# Peak.peakViews = property(getter, None, None,
#                                          "PeakListViews showing Spectrum")
