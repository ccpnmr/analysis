"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-07-25 11:28:58 +0100 (Tue, July 25, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.core.lib.SpectrumLib import _calibrateY1D
# import pyqtgraph as pg
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.popups.Dialog import handleDialogApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from functools import partial


OP = 'Calibrate Y - Original Position: '
NP = 'New Position: '

ToolTip = 'Click the line to select. Hold left click and drag. Release the mouse to set the original ' \
          'position to the new position '


class CalibrateY1DWidgets(Frame):
    def __init__(self, parent=None, mainWindow=None, strip=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        if mainWindow is None:  # This allows opening the popup for graphical tests
            self.mainWindow = None
            self.project = None
        else:
            self.mainWindow = mainWindow
            self.project = self.mainWindow.project
            self.application = self.mainWindow.application
            self.current = self.application.current

        self.originalPosition = None
        self.newPosition = None
        self.strip = strip
        self.targetLineVisible = True

        try:
            self.GLWidget = self.current.strip._CcpnGLWidget
        except Exception as es:
            getLogger().debugGL('OpenGL widget not instantiated')

        i = 0
        self.labelOriginalPosition = Label(self, OP, grid=(0, i), hAlign='r')
        i += 1
        self.boxOriginalPosition = ScientificDoubleSpinBox(self, step=0.001, decimals=3, grid=(0, i))
        i += 1
        self.labelNewPosition = Label(self, NP, grid=(0, i), hAlign='r')
        i += 1
        self.boxNewPosition = ScientificDoubleSpinBox(self, step=0.001, decimals=3, grid=(0, i))
        i += 1
        # self.okButtons = ButtonList(self, ['Apply', 'Close'], callbacks=[self._apply, self._close],
        #                             grid=(0, i))
        self.okButtons = ButtonList(self, ['Apply'], callbacks=[self._apply],
                                    grid=(0, i))

        # self.infiniteLine = pg.InfiniteLine(movable=True, angle=0)
        # self.originalPosInfiniteLine = pg.InfiniteLine(movable=False, angle=0, pen='g')
        #
        # # self.infiniteLine.sigPositionChangeFinished.connect(self._calibrateSpectra)
        # self.infiniteLine.sigPositionChanged.connect(self._newPositionLineCallback)

        self.labelOriginalPosition.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.boxOriginalPosition.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.labelNewPosition.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.boxNewPosition.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        self.okButtons.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)

        if self.GLWidget:
            self.infiniteLine = self.GLWidget.addInfiniteLine(colour='highlight', movable=True, lineStyle='dashed', orientation='h', lineWidth=2.0)
            self.originalPosInfiniteLine = self.GLWidget.addInfiniteLine(colour='highlight', movable=True, lineStyle='solid', orientation='h', lineWidth=2.0)

            # openGL callbacks
            self.infiniteLine.valuesChanged.connect(self._newPositionLineCallback)
            self.originalPosInfiniteLine.valuesChanged.connect(self._originalPositionLineCallback)

        self.boxOriginalPosition.valueChanged.connect(self._originalPositionBoxCallback)
        self.boxNewPosition.valueChanged.connect(self._newPositionBoxCallback)

        self._initLines()
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Minimum)

        self.GLSignals = GLNotifier(parent=None)

    def _initLines(self):
        if self.mainWindow is not None:
            # if self.strip is not None:
            #   self.strip.plotWidget.addItem(self.infiniteLine)
            #   self.strip.plotWidget.addItem(self.originalPosInfiniteLine)
            # if self.strip.plotWidget.viewBox.contextMenuPosition is not None:

            # self.originalPosition = self.strip.plotWidget.viewBox.contextMenuPosition[1]

            self.originalPosition = float(self.strip._CcpnGLWidget.cursorCoordinate[1])

            self.infiniteLine.setValue(self.originalPosition)
            self.originalPosInfiniteLine.setValue(self.originalPosition)
            self.boxOriginalPosition.setValue(round(self.originalPosition, 3))

            self.infiniteLine.visible = True and self.targetLineVisible
            self.originalPosInfiniteLine.visible = True

    def _newBoxCallback(self):
        spinboxValue = self.sender().value()
        self.infiniteLine.setValue(spinboxValue)

    def _newPositionLineCallback(self):
        # self.newPosition = self.infiniteLine.pos().y()

        self.newPosition = self.infiniteLine.values  # [0]
        self.boxNewPosition.setValue(round(self.newPosition, 3))

    def _newPositionBoxCallback(self):
        box = self.sender()
        if box.hasFocus():
            self.newPosition = round(box.value(), 3)
            self.infiniteLine.setValue(self.newPosition)

    def _originalPositionLineCallback(self):
        self.originalPosition = self.originalPosInfiniteLine.values  # [0]
        self.boxOriginalPosition.setValue(round(self.originalPosition, 3))

    def _originalPositionBoxCallback(self):
        box = self.sender()
        if box.hasFocus():
            self.originalPosition = round(box.value(), 3)
            self.originalPosInfiniteLine.setValue(self.originalPosition)

    def setOriginalPos(self, value):
        self.originalPosition = round(value, 3)
        self.originalPosInfiniteLine.setValue(self.originalPosition)

    def _removeLines(self):
        if self.mainWindow is not None:
            # if self.strip is not None:
            #   self.strip.plotWidget.removeItem(self.infiniteLine)
            #   self.strip.plotWidget.removeItem(self.originalPosInfiniteLine)

            if self.GLWidget:
                self.infiniteLine.visible = False
                self.originalPosInfiniteLine.visible = False

    def _toggleLines(self):
        if self.isVisible():
            self._initLines()
        else:
            self._removeLines()

    def _apply(self):
        with handleDialogApply(self) as error:

            fromPos = self.originalPosition
            toPos = self.newPosition

            # add an undo item to the stack
            with undoStackBlocking() as addUndoItem:

                # get the list of visible spectra in this strip
                spectra = [(specView, specView.spectrum) for specView in self.strip.spectrumViews if specView.isVisible()]
                self._calibrateSpectra(spectra, fromPos, toPos)

                addUndoItem(undo=partial(self._calibrateSpectra, spectra, toPos, fromPos),
                            redo=partial(self._calibrateSpectra, spectra, fromPos, toPos))

    def _calibrateSpectra(self, spectra, fromPos, toPos):

        for specView, spectrum in spectra:
            _calibrateY1D(spectrum, fromPos, toPos)

            if specView and not specView.isDeleted:
                specView.buildContours = True

        self.setOriginalPos(toPos)
        if self.mainWindow and self.strip and self.GLWidget:
            # spawn a redraw of the GL windows
            self.GLWidget._moveAxes((0.0, toPos - fromPos))
            self.GLSignals.emitPaintEvent()

    def _cancel(self):
        """Cancel has been pressed, undo all items since the widget was opened
        Dangerous as other stuff may have happened
        """
        pass

    def _close(self):
        self.setVisible(False)
        self.strip.calibrateYAction.setChecked(False)
        self._toggleLines()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog()
    f = CalibrateY1DWidgets(popup)

    popup.show()
    popup.raise_()

    app.start()
