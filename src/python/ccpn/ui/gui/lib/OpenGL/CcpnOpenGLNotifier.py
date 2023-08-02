"""
A Small class to control the communication of information across strips.
E.g.  Mouse co-ordinates
      Signals to other connected strips to rescale on axis changes
      Signal other strips to update
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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-08-02 16:18:35 +0100 (Wed, August 02, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from contextlib import contextmanager
from ccpn.util.decorators import singleton
from ccpn.util.Logging import getLogger


@singleton
class GLNotifier(QtWidgets.QWidget):
    """
    Class to control the communication between different strips
    """
    GLSOURCE = 'source'
    GLAXISVALUES = 'axisValues'
    GLMOUSECOORDS = 'mouseCoords'
    GLMOUSEMOVEDDICT = 'mouseMovedict'
    GLSPECTRUMDISPLAY = 'spectrumDisplay'
    GLSTRIP = 'strip'
    GLMAINWINDOW = 'mainWindow'
    GLKEY = 'key'
    GLMODIFIER = 'modifier'
    GLBOTTOMAXISVALUE = 'bottomAxis'
    GLTOPAXISVALUE = 'topAxis'
    GLLEFTAXISVALUE = 'leftAxis'
    GLRIGHTAXISVALUE = 'rightAxis'
    GLASPECTRATIOS = 'aspectRatios'
    GLSTRIPROW = 'stripRow'
    GLSTRIPCOLUMN = 'stripColumn'
    GLSTRIPZOOMALL = 'stripZoomAll'
    GLSTRIPAXES = 'stripAxes'
    GLADD1DPHASING = 'add1DPhasing'
    GLCLEARPHASING = 'clearPhasing'
    GLALLCONTOURS = 'updateAllContours'
    GLHIGHLIGHTPEAKS = 'glHighlightPeaks'
    GLHIGHLIGHTINTEGRALS = 'glHighlightIntegrals'
    GLHIGHLIGHTMULTIPLETS = 'glHighlightMultiplets'
    GLRESCALE = 'glRescale'
    GLALLPEAKS = 'glAllPeaks'
    GLALLINTEGRALS = 'glAllIntegrals'
    GLALLMULTIPLETS = 'glAllMultiplets'
    GLPEAKNOTIFY = 'glPeakNotify'
    GLPEAKLISTS = 'glUpdatePeakLists'
    GLPEAKLISTLABELS = 'glUpdatePeakListLabels'
    GLINTEGRALLISTS = 'glUpdateIntegralLists'
    GLINTEGRALLISTLABELS = 'glUpdateIntegralListLabels'
    GLMULTIPLETLISTS = 'glUpdateMultipletLists'
    GLMULTIPLETLISTLABELS = 'glUpdateMultipletListLabels'

    GLUPDATEPIVOT = 'updatePivot'
    GLPREFERENCES = 'glPreferences'
    GLGRID = 'glUpdateGrid'
    GLAXES = 'glUpdateAxes'
    GLCURSOR = 'glUpdateCursor'
    GLANY = 'glUpdateAny'
    GLMARKS = 'glUpdateMarks'
    GLTARGETS = 'glTargets'
    GLTRIGGERS = 'glTriggers'
    GLVALUES = 'glValues'
    GLDATA = 'glData'

    # not used yet
    _triggerKeywords = (GLHIGHLIGHTPEAKS, GLALLPEAKS,
                        GLPEAKNOTIFY, GLPEAKLISTS, GLPEAKLISTLABELS, GLGRID, GLAXES,
                        GLCURSOR, GLANY, GLMARKS, GLTARGETS, GLTRIGGERS, GLVALUES, GLDATA)

    glXAxisChanged = pyqtSignal(dict)
    glYAxisChanged = pyqtSignal(dict)
    glAllAxesChanged = pyqtSignal(dict)
    glMouseMoved = pyqtSignal(dict)
    _syncChanged = pyqtSignal(dict)
    glEvent = pyqtSignal(dict)
    glAxisLockChanged = pyqtSignal(dict)
    glAxisUnitsChanged = pyqtSignal(dict)
    glSymbolsChanged = pyqtSignal(dict)
    glKeyEvent = pyqtSignal(dict)
    _blocked = False

    def __init__(self, parent=None, strip=None):
        super().__init__()
        self._parent = parent
        self._strip = strip

        # set a global flag for the mouse in any strip
        self._mouseInGLWidget = False

    #=========================================================================================
    # Properties
    #=========================================================================================

    @property
    def blocked(self):
        return self._blocked

    @blocked.setter
    def blocked(self, value):
        self._blocked = value

    @contextmanager
    def blocking(self):
        """block all emitters.
        """
        _currentBlocking = self.blocked
        self.blocked = True
        try:
            # transfer control to the calling function
            yield

        except Exception as es:
            getLogger().warning(f'Error while blocking in GLNotifier {es}')

        finally:
            # reset blocking
            self.blocked = _currentBlocking

    #=========================================================================================
    # Signal control
    #=========================================================================================

    def emitPaintEvent(self, source=None):
        if self._blocked:
            return

        if source:
            self.glEvent.emit({GLNotifier.GLSOURCE  : source,
                               GLNotifier.GLTARGETS : [],
                               GLNotifier.GLTRIGGERS: []})
        else:
            self.glEvent.emit({})

    def emitEvent(self, source=None, strip=None, display=None, targets=[], triggers=[], values={}):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: display,
                 GLNotifier.GLTARGETS        : tuple(targets),
                 GLNotifier.GLTRIGGERS       : tuple(triggers),
                 GLNotifier.GLVALUES         : values,
                 }
        self.glEvent.emit(aDict)

    def emitEventToSpectrumDisplay(self, source=None, strip=None, display=None, targets=[], triggers=[], values={}):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: display,
                 GLNotifier.GLTARGETS        : tuple(targets),
                 GLNotifier.GLTRIGGERS       : tuple(triggers),
                 GLNotifier.GLVALUES         : values,
                 }
        self.glEvent.emit(aDict)

    def _emitAllAxesChanged(self, source=None, strip=None, spectrumDisplay=None,
                            axisB=None, axisT=None, axisL=None, axisR=None,
                            row=None, column=None, stripAxes=None, zoomAll=False):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: spectrumDisplay or (strip.spectrumDisplay if strip else None),
                 GLNotifier.GLAXISVALUES     : {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                                GLNotifier.GLTOPAXISVALUE   : axisT,
                                                GLNotifier.GLLEFTAXISVALUE  : axisL,
                                                GLNotifier.GLRIGHTAXISVALUE : axisR,
                                                GLNotifier.GLSTRIPAXES      : stripAxes,
                                                GLNotifier.GLSTRIPROW       : row,
                                                GLNotifier.GLSTRIPCOLUMN    : column,
                                                GLNotifier.GLSTRIPZOOMALL   : zoomAll}
                 }
        self.glAllAxesChanged.emit(aDict)
        self._syncChanged.emit(aDict)

    def _emitXAxisChanged(self, source=None, strip=None, spectrumDisplay=None,
                          axisB=None, axisT=None, axisL=None, axisR=None,
                          row=None, column=None, stripAxes=None, zoomAll=False,
                          aspectRatios=None):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: spectrumDisplay or (strip.spectrumDisplay if strip else None),
                 GLNotifier.GLAXISVALUES     : {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                                GLNotifier.GLTOPAXISVALUE   : axisT,
                                                GLNotifier.GLLEFTAXISVALUE  : axisL,
                                                GLNotifier.GLRIGHTAXISVALUE : axisR,
                                                GLNotifier.GLSTRIPAXES      : stripAxes,
                                                GLNotifier.GLASPECTRATIOS   : aspectRatios,
                                                GLNotifier.GLSTRIPROW       : row,
                                                GLNotifier.GLSTRIPCOLUMN    : column,
                                                GLNotifier.GLSTRIPZOOMALL   : zoomAll}
                 }
        self.glXAxisChanged.emit(aDict)
        self._syncChanged.emit(aDict)


    def _emitYAxisChanged(self, source=None, strip=None, spectrumDisplay=None,
                          axisB=None, axisT=None, axisL=None, axisR=None,
                          row=None, column=None, stripAxes=None, zoomAll=False,
                          aspectRatios=None):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: spectrumDisplay or (strip.spectrumDisplay if strip else None),
                 GLNotifier.GLAXISVALUES     : {GLNotifier.GLBOTTOMAXISVALUE: axisB,
                                                GLNotifier.GLTOPAXISVALUE   : axisT,
                                                GLNotifier.GLLEFTAXISVALUE  : axisL,
                                                GLNotifier.GLRIGHTAXISVALUE : axisR,
                                                GLNotifier.GLSTRIPAXES      : stripAxes,
                                                GLNotifier.GLASPECTRATIOS   : aspectRatios,
                                                GLNotifier.GLSTRIPROW       : row,
                                                GLNotifier.GLSTRIPCOLUMN    : column,
                                                GLNotifier.GLSTRIPZOOMALL   : zoomAll}
                 }
        self.glYAxisChanged.emit(aDict)
        self._syncChanged.emit(aDict)


    def _emitMouseMoved(self, source=None, coords=None, mouseMovedDict=None, mainWindow=None):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE        : source,
                 GLNotifier.GLMOUSECOORDS   : coords,
                 GLNotifier.GLMOUSEMOVEDDICT: mouseMovedDict,
                 GLNotifier.GLMAINWINDOW    : mainWindow}
        self.glMouseMoved.emit(aDict)

        # for specDisplay in mainWindow.spectrumDisplays:
        #     for strip in specDisplay.strips:
        #         if strip._CcpnGLWidget != source:
        #             strip._CcpnGLWidget._glMouseMoved(aDict)
        #     # specDisplay.stripFrame.update()

    def _emitAxisLockChanged(self, source=None, strip=None, lockValues=None):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay if strip else None,
                 GLNotifier.GLVALUES         : lockValues,
                 }
        self.glAxisLockChanged.emit(aDict)

    def _emitAxisUnitsChanged(self, source=None, strip=None, dataDict={}):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay if strip else None,
                 GLNotifier.GLVALUES         : dataDict
                 }
        self.glAxisUnitsChanged.emit(aDict)

    def _emitSymbolsChanged(self, source=None, strip=None, symbolDict={}):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay if strip else None,
                 GLNotifier.GLVALUES         : symbolDict
                 }
        self.glSymbolsChanged.emit(aDict)

    def _emitSymbolsChanged(self, source=None, strip=None, symbolDict={}):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSOURCE         : source,
                 GLNotifier.GLSTRIP          : strip,
                 GLNotifier.GLSPECTRUMDISPLAY: strip.spectrumDisplay if strip else None,
                 GLNotifier.GLVALUES         : symbolDict
                 }
        self.glSymbolsChanged.emit(aDict)

    def _emitKeyEvent(self, strip=None, key=None, modifier=None):
        if self._blocked:
            return

        aDict = {GLNotifier.GLSTRIP   : strip,
                 GLNotifier.GLKEY     : key,
                 GLNotifier.GLMODIFIER: modifier
                 }
        self.glKeyEvent.emit(aDict)
        self._syncChanged.emit(aDict)

