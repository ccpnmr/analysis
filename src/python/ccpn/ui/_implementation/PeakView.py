"""Peak view in a specific PeakList View.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-05-18 18:49:16 +0100 (Thu, May 18, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.Project import Project
from ccpn.core.Peak import Peak
from ccpn.core.lib.ContextManagers import ccpNmrV3CoreSetter  #, undoStackBlocking
from ccpn.util.decorators import logCommand
from ccpn.ui._implementation.PeakListView import PeakListView
from ccpn.ui._implementation.PMIViewABC import PMIViewABC
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import PeakView as ApiPeakView
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr

# TODO:ED - should be in a Gui-class
from ccpn.ui.gui.lib.PeakListLib import line_rectangle_intersection


class PeakView(PMIViewABC):
    """PeakView for 1D or nD PeakList.
    """

    #: Short class name, for PID.
    shortClassName = 'GP'
    # Attribute it necessary as subclasses must use superclass className
    className = 'PeakView'

    _parentClass = PeakListView
    _parentClassName = PeakListView.__class__.__name__

    #: Name of plural link to instances of class
    _pluralLinkName = 'peakViews'

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiPeakView._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiPeakView(self) -> ApiPeakView:
        """CCPN PeakView matching PeakView"""
        return self._wrappedData

    @property
    def _parent(self) -> PeakListView:
        """PeakListView containing PeakView."""
        return self._project._data2Obj.get(self._wrappedData.peakListView.sortedStripPeakListViews()[0])

    peakListView = _parent

    @property
    def _key(self) -> str:
        """id string - """
        return str(self._wrappedData.peak.serial)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        return (self._wrappedData.peak.serial,)

    @property
    def peak(self) -> Peak:
        """Peak that PeakView refers to.
        """
        return self._project._data2Obj.get(self._wrappedData.peak)

    @property
    def pixelOffset(self) -> tuple:
        """X,Y text annotation offset in pixels.
        """
        if not (pixelSize := self.peakListView.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - peakListView pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - peakListView pixelSize contains 0.0')

        return tuple(to / abs(ps) for to, ps in zip(self._wrappedData.textOffset, pixelSize))

    @pixelOffset.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def pixelOffset(self, value: tuple):
        """Set the visible offset for the text annotation in pixels.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize contains 0.0')

        try:
            # with undoStackBlocking():
            # this is a gui operation and shouldn't need an undo? if no undo, remove core decorator above
            self._wrappedData.textOffset = tuple(to * abs(ps) for to, ps in zip(value, pixelSize))

        except Exception as es:
            raise TypeError(f'{self.__class__.__name__}:pixelOffset must be a tuple of int/floats') from es

    @property
    def textCentre(self) -> tuple:
        """X,Y text annotation centre in ppm.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:pixelOffset - {self._parent.classname} pixelSize contains 0.0')

        offset = self._wrappedData.textOffset
        return (offset[0] + abs(pixelSize[0] * self._width / 2.0), offset[1] + abs(pixelSize[1] * self._height / 2.0))

    ppmCentre = textCentre

    @property
    def pixelCentre(self) -> tuple:
        """X,Y text annotation centre in pixels.
        """
        offset = self.pixelOffset
        return (offset[0] + self._width / 2, offset[1] + self._height / 2)

    def getIntersect(self, ppmPoint):
        """X,Y text annotation co-ordinates to nearest point of bounding box from start-point in ppm.
        """
        if not (pixelSize := self._parent.pixelSize):
            raise TypeError(f'{self.__class__.__name__}:getIntersect - {self._parent.classname} pixelSize is undefined')
        if 0.0 in pixelSize:
            raise ValueError(f'{self.__class__.__name__}:getIntersect - {self._parent.classname} pixelSize contains 0.0')

        bLeft = self._wrappedData.textOffset
        tRight = (bLeft[0] + abs(self._width * pixelSize[0]), bLeft[1] + abs(self._height * pixelSize[1]))

        return line_rectangle_intersection(ppmPoint, self.textCentre, bLeft, tRight)

    getPpmIntersect = getIntersect

    def getPixelIntersect(self, pixelPoint):
        """X,Y text annotation co-ordinates to nearest point of bounding box from start-point in pixels.
        """
        bLeft = self.pixelOffset
        tRight = (bLeft[0] + self._width, bLeft[1] + self._height)

        return line_rectangle_intersection(pixelPoint, self.textCentre, bLeft, tRight)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: PeakListView) -> list:
        """get wrappedData (ccpnmr.gui.Task.PeakView) in serial number order.
        """
        return parent._wrappedData.peakListView.sortedPeakViews()

    def _finaliseAction(self, action: str, **actionKwds):
        if super()._finaliseAction(action, **actionKwds):

            if action == 'change':
                self.peak._finaliseAction(action)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    # None


# Peak.peakViews property
def getter(peak: Peak) -> typing.Tuple[PeakView, ...]:
    """PeakViews associated with Peak.
    """
    return tuple(peak._project._data2Obj[x] for x in peak._wrappedData.sortedPeakViews())


Peak.peakViews = property(getter, None, None, 'PeakViews associated with Peak.')

del getter


def getTextOffset(self: Peak, peakListView: PeakListView) -> tuple:
    """Get textOffset for the peak for the specified peakListView
    """
    if view := self._wrappedData.findFirstPeakView(peakListView=peakListView._wrappedData.peakListView):
        # bypass the v3-operator in superclass
        tOffset = view.textOffset
        if any(tOffset):
            return view.textOffset


Peak.getTextOffset = getTextOffset

del getTextOffset


def getPeakView(self: Peak, peakListView: PeakListView) -> tuple:
    """Get peakView for the peak for the specified peakListView.
    """
    if view := self._wrappedData.findFirstPeakView(peakListView=peakListView._wrappedData.peakListView):
        return self.project._data2Obj.get(view)


Peak.getPeakView = getPeakView

del getPeakView


def _peakAddPeakViews(project: Project, apiPeak: Nmr.Peak):
    """Add ApiPeakViews when ApiPeak is created.
    """
    if project._apiNotificationBlanking == 0:
        # create new apiObjects if not blocked
        for apiPeakListView in apiPeak.parent.peakListViews:
            apiPeakListView.newPeakView(peak=apiPeak, peakSerial=0)


Project._setupApiNotifier(_peakAddPeakViews, Nmr.Peak, 'postInit')
