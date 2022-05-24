"""
Module documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-24 16:33:28 +0100 (Tue, May 24, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
import numpy as np
from functools import partial
import pyqtgraph as pg
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_HEXBACKGROUND, MEDIUM_BLUE, GUISTRIP_PIVOT, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_GRID, CCPNGLWIDGET_LABELLING
from ccpn.ui.gui.widgets.Font import Font, getFont
from PyQt5 import QtWidgets, QtCore, QtGui
from ccpn.core.lib.AssignmentLib import CCP_CODES
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.util.Colour import spectrumHexDarkColours, spectrumHexLightColours
from ccpn.ui.gui.guiSettings import getColours, CCPNGLWIDGET_HEXBACKGROUND
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.core.lib.Notifiers import Notifier
from collections import defaultdict
from ccpn.util.Colour import spectrumColours, hexToRgb, rgbaRatioToHex, _getRandomColours
from ccpn.util.isotopes import isotopeCode2Nucleus, getIsotopeRecords


# GridFont = Font('Helvetica', 16, bold=True)
GridFont = getFont()
BackgroundColour = getColours()[CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(getColours()[GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
SelectedPoint = pg.functions.mkPen(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
SelectedLabel = pg.functions.mkBrush(rgbaRatioToHex(*getColours()[CCPNGLWIDGET_HIGHLIGHT]), width=4)
c = rgbaRatioToHex(*getColours()[CCPNGLWIDGET_LABELLING])
GridPen = pg.functions.mkPen(c, width=1, style=QtCore.Qt.SolidLine)
bc = getColours()[CCPNGLWIDGET_HEXBACKGROUND]

Hydrogen = 'Hydrogen'
Heavy = 'Heavy'
Other = 'Other'
H = 'H'

class ReferenceChemicalShifts(CcpnModule):  # DropBase needs to be first, else the drop events are not processed

    includeSettingsWidget = False
    maxSettingsState = 2
    settingsPosition = 'top'
    className = 'ReferenceChemicalShifts'

    def __init__(self, mainWindow, name='Reference Chemical Shifts', ):
        super().__init__(mainWindow=mainWindow, name=name)

        self.preferences = self.mainWindow.application.preferences

        self.mainWindow = mainWindow
        self.current = self.mainWindow.current
        self.project = self.mainWindow.project
        self.displayedAxisCodes = defaultdict(list)
        self._RCwidgetFrame = Frame(self.mainWidget, setLayout=True,
                                    grid=(0, 0), gridSpan=(1, 1),
                                    hPolicy='ignored'
                                    )

        self._RCwidget = Frame(self._RCwidgetFrame, setLayout=True,
                               grid=(0, 0), gridSpan=(1, 1),
                               hAlign='l', margins=(5, 5, 5, 5))
        self._TBFrame = Frame(self._RCwidgetFrame, setLayout=True,
                               grid=(1, 0), gridSpan=(1, 1),
                               hAlign='l', margins=(5, 5, 5, 5))

        self._RCwidget.getLayout().setSizeConstraint(QtWidgets.QLayout.SetMinAndMaxSize)

        self.residueTypeLabel = Label(self._RCwidget, "Residue Type:", grid=(0, 0))
        self.residueTypePulldown = PulldownList(self._RCwidget, callback=self._updateModule, hAlign='l', grid=(0, 1))
        self.residueTypePulldown.setData(CCP_CODES)
        self.atomTypeLabel = Label(self._RCwidget, 'Atom Type:', grid=(0, 2))
        self.atomTypePulldown = PulldownList(self._RCwidget, callback=self._updateModule, hAlign='l', grid=(0, 3))
        self.zoomAllButton = Button(self._RCwidget, icon=Icon('icons/zoom-full'), callback=self._zoomAllCallback, hAlign='l',grid=(0, 4))
        self.zoomAllButton.setFixedSize(25,25)
        self.atomTypePulldown.setData([Hydrogen, Heavy])
        self.toolBar = ToolBar(self._TBFrame,  grid=(0, 0))

        self.plotWidget = pg.PlotWidget(background=bc)
        self.plotWidget.invertX()
        self.mainWidget.getLayout().addWidget(self.plotWidget, 2, 0, 1, 1)

        self.plots = {}
        self._setupPlot()

        # cross hair
        self.vLine = pg.InfiniteLine(angle=90, label='', movable=False, pen=GridPen, labelOpts={'color':c})
        self.hLine = pg.InfiniteLine(pos=0, angle=0, movable=False, pen=GridPen)
        self.plotWidget.addItem(self.vLine,  ignoreBounds=True,)
        self.plotWidget.addItem(self.hLine, ignoreBounds=True,)
        self.viewBox = self.plotWidget.plotItem.vb
        self.plotWidget.scene().sigMouseMoved.connect(self.mouseMoved)
        self.plotWidget.plotItem.autoBtn.setOpacity(0.0)
        self.plotWidget.plotItem.autoBtn.enabled = False
        self.viewBox.setMenuEnabled(enableMenu=False)

        # GL crossHair notifier
        self.mousePosNotifier = Notifier(self.current,
                                         [Notifier.CURRENT],
                                         targetName='cursorPositions',
                                         callback=self.mousePosNotifierCallback,
                                         onceOnly=True)
        self.GLSignals = GLNotifier(parent=self, strip=None)
        self._updateModule()

    def _zoomAllCallback(self):
        self.plotWidget.plotItem.autoRange()

    def mousePosNotifierCallback(self, *args):
        """Set the vertical line based on current cursor position """
        pos = None
        axisCodeDict =  self.current.mouseMovedDict.get(1, {})
        for currentAxisCode, currentAxisCodePos in axisCodeDict.items():
            # try an exact match first
            for displayedAxisCode in self.displayedAxisCodes:
                exactCodes = self.displayedAxisCodes[displayedAxisCode]
                for exactCode in exactCodes:
                    if exactCode == currentAxisCode:
                        pos = currentAxisCodePos[0]
                        break
                if pos is None:
                    # try a first letter match
                    if len(currentAxisCode)>0:
                        if displayedAxisCode == currentAxisCode[0]:
                            pos = currentAxisCodePos[0]
                            break

        if pos:
            self.vLine.setPos(pos)
            self.vLine.label.setText(str(round(pos, 3)))


    def mouseMoved(self, event):
        # self.plotWidget.plotItem.autoBtn.hide() #make sure is never shown
        position = event
        mousePoint = self.viewBox.mapSceneToView(position)
        x = mousePoint.x()
        y = mousePoint.y()
        self.vLine.setPos(x)
        self.vLine.label.setText(str(round(x,3)))
        # mouseMovedDict = {'H':{'1H':5}}
        # self.GLSignals._emitMouseMoved(source=self, coords=None, mouseMovedDict=mouseMovedDict,
        #                                mainWindow=self.mainWindow)


    def clearPlot(self):
        """ Clear plot but keep infinite lines"""
        for item in self.viewBox.addedItems:
            if not isinstance(item, pg.InfiniteLine):
                self.viewBox.removeItem(item)
        for ch in self.viewBox.childGroup.childItems():
            if not isinstance(ch, pg.InfiniteLine):
                self.viewBox.removeItem(ch)

    def _setupPlot(self):
        self.plotWidget.plotItem.getAxis('bottom').setPen(GridPen)
        self.plotWidget.plotItem.getAxis('left').setPen(GridPen)
        self.plotWidget.plotItem.getAxis('bottom').tickFont = GridFont
        self.plotWidget.plotItem.getAxis('left').tickFont = GridFont
        self.plotWidget.showGrid(x=False, y=False)

    def _getDistributionForResidue(self, ccpCode: str, atomType: str):
        """
        Takes a ccpCode and an atom type (Hydrogen or Heavy) and returns a dictionary of lists
        containing the chemical shift distribution for each atom of the specified type in the residue
        """
        dataSets = {}
        ccpData = self.project.getCcpCodeData(ccpCode, molType='protein', atomType=atomType)

        atomNames = list(ccpData.keys())

        for atomName in atomNames:
            distribution = ccpData[atomName].distribution
            refPoint = ccpData[atomName].refPoint
            refValue = ccpData[atomName].refValue
            valuePerPoint = ccpData[atomName].valuePerPoint
            x = []
            y = []
            if self.preferences.general.colourScheme == 'dark':
                col = (11 + 7 * atomNames.index(atomName)) % len(spectrumHexLightColours) - 1
                colour = spectrumHexLightColours[col]
            else:
                col = (11 + 7 * atomNames.index(atomName)) % len(spectrumHexDarkColours) - 1
                colour = spectrumHexDarkColours[col]
            for i in range(len(distribution)):
                x.append(refValue + valuePerPoint * (i - refPoint))
                y.append(distribution[i])

            dataSets[atomName] = [np.array(x), np.array(y), colour, ]
            self.displayedAxisCodes[atomName[0]].append(atomName)

        return dataSets



    def _updateModule(self, item=None):
        """
        Updates the information displayed in the module when either the residue type or the atom type
        selectors are changed.
        """
        self.clearPlot()
        self.plots = {}
        self.toolBar.clear()
        self.displayedAxisCodes.clear()
        self.plotWidget.showGrid(x=False, y=False)
        atomType = self.atomTypePulldown.currentText()
        ccpCode = self.residueTypePulldown.currentText()
        dataSets = self._getDistributionForResidue(ccpCode, atomType)
        self.toolBar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        for atomName, dataSet in dataSets.items():
            xs = dataSet[0]
            ys = dataSet[1]
            color = dataSet[2]
            plotPen = pg.functions.mkPen(color, width=2, style=QtCore.Qt.SolidLine)
            plot = self.plotWidget.plot(xs, ys, pen=plotPen, name=atomName)
            anchor=(-0.3,0.5) # try to don't overlap labels
            textItem = pg.TextItem(atomName, color=color, anchor=anchor, angle=0, border='w', )
            labelY = max(ys)
            labelposXs = xs[ys==labelY]
            labelX = labelposXs[0]
            textItem.setPos(labelX, labelY+(np.random.random()*0.01))

            self.plots.update({atomName:plot})
            action = Action(self, text=atomName, callback=partial(self.toolbarActionCallback, plot, textItem),
                            checked=True, shortcut=None, checkable=True)
            action.setObjectName(atomName)
            action.setIconText(atomName)
            pixmap = QtGui.QPixmap(20, 5)
            pixmap.fill(QtGui.QColor(color))
            action.setIcon(QtGui.QIcon(pixmap))
            self.toolBar.addAction(action)
            self.plotWidget.addItem(textItem)
            widgetAction = self.toolBar.widgetForAction(action)
            widgetAction.setFixedSize(55, 30)
        self._zoomAllCallback()


    def toolbarActionCallback(self, plot, textItem):
        checked = self.sender().isChecked()
        if plot:
            plot.setVisible(checked)
            textItem.setVisible(checked)
