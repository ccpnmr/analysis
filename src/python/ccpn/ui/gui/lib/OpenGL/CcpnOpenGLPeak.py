"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-06-10 17:38:59 +0100 (Thu, June 10, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-12-11 17:51:14 +0000 (Fri, December 11, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.Peak import Peak
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakId, _getPeakAnnotation
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLLabelling import GLLabelling, GL1dLabelling


class GLpeakListMethods():
    """Class of methods common to 1d and Nd peaks
    This is added to the Peak Classes below and doesn't require an __init__
    """

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List handlers
    #   The routines that have to be changed when accessing different named
    #   lists.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _isSelected(self, peak):
        """return True if the obj in the defined object list
        """
        if self.current.peaks:
            return peak in self.current.peaks
        return False

    def objects(self, obj):
        """return the peaks attached to the object
        """
        return obj.peaks if obj else []

    def objectList(self, obj):
        """return the peakList attached to the peak
        """
        return obj.peakList if obj else None

    def listViews(self, peakList):
        """Return the peakListViews attached to the peakList
        """
        return peakList.peakListViews

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List specific routines
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getLabelling(self, obj, labelType):
        """Get the object label based on the current labelling method
        For peaks, this is constructed from the pids of the attached nmrAtoms
        """
        if labelType == 0:
            # return the short code form
            text = _getScreenPeakAnnotation(obj, useShortCode=True)
        elif labelType == 1:
            # return the long form
            text = _getScreenPeakAnnotation(obj, useShortCode=False)
        elif labelType == 2:
            # return the original pid
            # text = _getPeakAnnotation(obj)
            text = _getScreenPeakAnnotation(obj, useShortCode=False, usePid=True)
        elif labelType == 3:
            # return the minimal form
            text = _getScreenPeakAnnotation(obj, useShortCode=True, useMinimalCode=True)
        elif labelType == 4:
            # return the minimal form
            text = _getPeakId(obj)
        else:
            # return the peak annotation
            text = _getPeakAnnotation(obj)

        return text

    def extraIndicesCount(self, obj):
        """Calculate how many indices to add
        """
        return 0

    def appendExtraIndices(self, drawList, index, obj):
        """Add extra indices to the index list
        """
        return 0, 0

    def extraVerticesCount(self, obj):
        """Calculate how many vertices to add
        """
        return 0

    def appendExtraVertices(self, *args):
        """Add extra vertices to the vertex list
        """
        return 0

    def insertExtraIndices(self, *args):
        """Insert extra indices into the vertex list
        """
        return 0, 0

    def insertExtraVertices(self, *args):
        """Insert extra vertices into the vertex list
        """
        return 0

    def _processNotifier(self, data):
        """Process notifiers
        """
        triggers = data[Notifier.TRIGGER]
        obj = data[Notifier.OBJECT]

        if isinstance(obj, Peak):

            # update the peak labelling
            if Notifier.DELETE in triggers:
                self._deleteSymbol(obj)
                self._deleteLabel(obj)

            if Notifier.CREATE in triggers:
                self._createSymbol(obj)
                self._createLabel(obj)

            if Notifier.CHANGE in triggers:
                self._changeSymbol(obj)
                self._changeLabel(obj)

        elif isinstance(obj, NmrAtom):

            # update the labels on the peaks
            for peak in obj.assignedPeaks:
                self._changeSymbol(peak)
                self._changeLabel(peak)


class GLpeakNdLabelling(GLpeakListMethods, GLLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    # def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #     """Initialise the class
    #     """
    #     super().__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List specific routines
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def objIsInVisiblePlanes(self, spectrumView, peak, viewOutOfPlanePeaks=True):
        """Return whether in plane or flanking plane

        :param spectrumView: current spectrumView containing peaks
        :param peak: peak to test
        :param viewOutOfPlanePeaks: whether to show outofplane peaks, defaults to true
        :return: inPlane - true/false
                inFlankingPlane - true/false
                type of outofplane - currently 0/1/2 indicating whether normal, infront or behind
                fade for colouring
        """
        try:
            # try to read from the cache
            return self._objIsInVisiblePlanesCache[spectrumView][peak]
        except:
            # calculate and store the new value
            value = self._objIsInVisiblePlanes(spectrumView, peak, viewOutOfPlanePeaks=viewOutOfPlanePeaks)
            if spectrumView not in self._objIsInVisiblePlanesCache:
                self._objIsInVisiblePlanesCache[spectrumView] = {peak: value}
            else:
                self._objIsInVisiblePlanesCache[spectrumView][peak] = value

            return value

    def _objIsInVisiblePlanes(self, spectrumView, peak, viewOutOfPlanePeaks=True):

        pntPos = peak.pointPosition
        if not pntPos:
            return False, False, 0, 1.0

        displayIndices = self._GLParent.visiblePlaneDimIndices[spectrumView]
        if displayIndices is None:
            return False, False, 0, 1.0

        inPlane = True
        endPlane = 0

        # settings = self._spectrumSettings[spectrumView]
        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:

                # If no axis matches the index may be None
                zPosition = pntPos[displayIndex]
                if not zPosition:
                    return False, False, 0, 1.0
                actualPlane = int(zPosition + 0.5) - (1 if zPosition >= 0 else 2)

                # zPointFloat0 = settings[GLDefs.SPECTRUM_VALUETOPOINT][ii](zPosition)
                # actualPlane = int(zPointFloat0 + 0.5) - (1 if zPointFloat0 >= 0 else 2)

                thisVPL = self._GLParent.visiblePlaneList[spectrumView]
                if not thisVPL:
                    return False, False, 0, 1.0

                planes = thisVPL[ii]
                if not (planes and planes[0]):
                    return False, False, 0, 1.0

                visiblePlaneList = planes[0]
                vplLen = len(visiblePlaneList)

                if actualPlane in visiblePlaneList[1:vplLen - 1]:
                    return True, False, 0, 1.0

                # exit if don't want to view outOfPlane peaks
                elif not viewOutOfPlanePeaks:
                    return False, False, 0, 1.0

                elif actualPlane == visiblePlaneList[0]:
                    inPlane = False
                    endPlane = 1

                elif actualPlane == visiblePlaneList[vplLen - 1]:
                    inPlane = False
                    endPlane = 2

                else:
                    # catch any stray conditions
                    return False, False, 0, 1.0

        # return True, False, 0, 1.0
        return inPlane, (not inPlane), endPlane, GLDefs.INPLANEFADE if inPlane else GLDefs.OUTOFPLANEFADE


class GLpeak1dLabelling(GL1dLabelling, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for 1d peak displays
    """

    def objIsInVisiblePlanes(self, spectrumView, obj):
        """Get the current object is in visible planes settings
        """
        return True, False, 0, 1.0
