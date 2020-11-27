"""
Module Documentation Here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import shutil
import numpy as np
import pandas as pd
import pyqtgraph as pg
import ccpn.ui.gui.widgets as Widgets
from functools import partial
from collections import OrderedDict as od
import ccpn.ui.gui.guiSettings as gs
import ccpn.ui.gui.lib.mouseEvents as me
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.util.Colour import hexToRgb, rgbaRatioToHex
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.lib.MenuActions import _openItemObject
from ccpn.ui.gui.widgets.CustomExportDialog import CustomExportDialog
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.Frame import Frame
# from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier


# colours
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]
OriginAxes = pg.functions.mkPen(hexToRgb(gs.getColours()[gs.GUISTRIP_PIVOT]), width=1, style=QtCore.Qt.DashLine)
SelectedPoint = pg.functions.mkPen(rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_HIGHLIGHT]), width=4)
ROIline = rgbaRatioToHex(*gs.getColours()[gs.CCPNGLWIDGET_SELECTAREA])
DefaultRoi = [[0, 0], [10, 10]]  #


class ScatterPlot(Widget):
    def __init__(self,
                 application,
                 dataFrame,
                 axesDefinitions = None,
                 roiVisible = True,
                 mouseSelectionRegion = True,
                 spotSelectionCallback = None,
                 spotActionCallback = None,
                 **kwds):
        super().__init__(setLayout=True, **kwds)

        self.application = application
        self._dataFrame = dataFrame
        self._roiData = DefaultRoi
        self._axesDefs = axesDefinitions
        self._scatterView = pg.GraphicsLayoutWidget()
        self._scatterView.setBackground(BackgroundColour)
        self._plotItem = self._scatterView.addPlot()
        self._scatterViewbox = self._plotItem.vb
        self._addScatterSelectionBox()
        self._scatterViewbox.mouseClickEvent = self._scatterViewboxMouseClickEvent
        self._scatterViewbox.mouseDragEvent = self._scatterMouseDragEvent
        self._scatterViewbox.scene().sigMouseMoved.connect(self.mouseMoved) #use this if you need the mouse Posit
        self._plotItem.setMenuEnabled(False)
        self._exportDialog = None
        self.scatterPlot = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0))
        # self.scatterPlot.sigClicked.connect(self._plotClicked)
        self.scatterPlot.mouseClickEvent = self._scatterMouseClickEvent
        self.scatterPlot.mouseDoubleClickEvent = self._scatterMouseDoubleClickEvent

        ## adjustable ROI box
        self.roiItem = pg.ROI(*DefaultRoi, pen=ROIline)
        self._setROIhandles()
        self.roiItem.sigRegionChangeFinished.connect(self.getROIdata)
        self._plotItem.addItem(self.roiItem)
        self.xLine = pg.InfiniteLine(angle=90, pos=0, pen=OriginAxes)
        self.yLine = pg.InfiniteLine(angle=0, pos=0, pen=OriginAxes)

        self._plotItem.addItem(self.scatterPlot)
        self._plotItem.addItem(self.xLine)
        self._plotItem.addItem(self.yLine)
        self.getLayout().addWidget(self._scatterView)

        self.axisSelectionFrame = Frame(self, setLayout=True, grid=(1, 0))
        self._xSelCW = PulldownListCompoundWidget(self.axisSelectionFrame, labelText='Select X-axis',
                                        callback=self._axisSelectionCallback, grid=(0, 0))#,  hAlign='l',)
        self._ySelCW = PulldownListCompoundWidget(self.axisSelectionFrame, labelText='Select Y-axis',
                                                  callback=self._axisSelectionCallback, grid=(0, 1))#,  hAlign='l',)
        self.xAxisSelector = self._xSelCW.pulldownList
        self.yAxisSelector = self._ySelCW.pulldownList
        self.setAxesWidgets()
        # coordinates
        self.coordinatesLabel = Label(self.axisSelectionFrame, text='', grid=(0,2))

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self.dataFrame = dataFrame

    @property
    def roiData(self) -> list:
        """
        :return: a list of 4 elements: [xMin, xMax, yMin, yMax]
        """
        self._roiData = self.getROIdata()
        return self._roiData

    @roiData.setter
    def roiData(self, data):
        '''
        :param data: list of 4 elements: [xMin, xMax, yMin, yMax]
        :return: None, sets the ROI on the plot.
        '''
        if len(data) != 4:
            getLogger().warn('ROI Data must be a list of 4 elements: [xMin, xMax, yMin, yMax]')
            return
        self._roiData = data
        self._setROI(*data)

    def setAxesDefinitions(self, defs:od):
        '''
        :param defs: orderedDict key: visible label to appear in the pulldown, value: the dataframe column header name.
        if None, they will be used the  header names as they appear in the original dataframe.
        '''
        if isinstance(defs, dict):
            # filter-out definitions that are not present in the df headers
            defs = od([k,v] for k,v in defs.items() if v in self.dataFrame.columns)
            self._axesDefs = defs
        if defs is None:
            self._axesDefs = None
        self.setAxesWidgets()

    def setAxesWidgets(self):
        '''
        Set from the _axesDefs. If None, uses the dataFrame column names.
        '''
        if isinstance(self._axesDefs, dict):
            pulldownTexts = self._axesDefs.keys()
            pulldownObjs = self._axesDefs.values()
        else:
            pulldownTexts = self.dataFrame.columns
            pulldownObjs = self.dataFrame.columns
        self.xAxisSelector.setData(list(pulldownTexts), objects=list(pulldownObjs))
        self.yAxisSelector.setData(list(pulldownTexts), objects=list(pulldownObjs))

    def selectAxes(self, xHeader=None, yHeader=None):
        '''
        :param x: str, header as appears in the selection Pulldown
        :param y: str, header as appears in the selection Pulldown
        if None is given, it keeps the current value.
        '''
        if xHeader:
            self.xAxisSelector.select(xHeader)
        if yHeader:
            self.yAxisSelector.select(yHeader)

    def _axisSelectionCallback(self, *args):
        self.scatterPlot.clear()
        self._setPlotItemLabels()
        xDf = self.dataFrame.get(self.xAxisSelector.currentObject())
        yDf = self.dataFrame.get(self.yAxisSelector.currentObject())
        xValues = []
        yValues = []
        if xDf is not None:
            xValues = xDf.values
        if yDf is not None:
            yValues = yDf.values
        # todo check/replace np.nan or wrong input (str)
        if len(xValues) == len(yValues):
            self.scatterPlot.addPoints(x=xValues, y=yValues)
        else:
            Widgets.MessageDialog.showWarning('Error displaying data',
                                    'Values lenght mismatch')

    def _setPlotItemLabels(self):
        self._plotItem.setLabel('bottom', self.xAxisSelector.getText())
        self._plotItem.setLabel('left', self.yAxisSelector.getText())

    def _addScatterSelectionBox(self):
        self._scatterSelectionBox = QtWidgets.QGraphicsRectItem(0, 0, 1, 1)
        self._scatterSelectionBox.setPen(pg.functions.mkPen((255, 0, 255), width=1))
        self._scatterSelectionBox.setBrush(pg.functions.mkBrush(255, 100, 255, 100))
        self._scatterSelectionBox.setZValue(1e9)
        self._scatterViewbox.addItem(self._scatterSelectionBox, ignoreBounds=True)
        self._scatterSelectionBox.hide()

    def _scatterViewboxMouseClickEvent(self, event):
        """ click on scatter viewBox. The parent of scatterPlot. Opens the context menu at any point. """
        if event.button() == QtCore.Qt.RightButton:
            event.accept()
            self._raiseScatterContextMenu(event)



    def _raiseScatterContextMenu(self, ev):
        """ Creates all the menu items for the scatter context menu. """

        self._scatterContextMenu = Menu('', None, isFloatWidget=True)
        # self._scatterContextMenu.addAction('Reset View', self._plotItem.autoRange)
        # self._scatterContextMenu.addSeparator()
        #
        # # Selection
        # self.resetSelectionAction = QtGui.QAction("Clear selection", self,
        #                                           triggered=self._clearScatterSelection)
        # self._scatterContextMenu.addAction(self.resetSelectionAction)
        #
        # self.invertSelectionAction = QtGui.QAction("Invert selection", self,
        #                                            triggered=self._invertScatterSelection)
        # self._scatterContextMenu.addAction(self.invertSelectionAction)
        #
        # self.groupSelectionAction = QtGui.QAction("Create Group from selection", self,
        #                                           triggered=self._createGroupSelection)
        #
        # self._scatterContextMenu.addAction(self.groupSelectionAction)
        # self._openSelectedAction = QtGui.QAction("Open selected", self,
        #                                          triggered=self._openSelectedPoint)
        #
        # self._scatterContextMenu.addAction(self._openSelectedAction)
        # self._scatterContextMenu.addSeparator()

        self._scatterContextMenu.addSeparator()
        self.exportAction = QtGui.QAction("Export image...", self, triggered=partial(self._showExportDialog, self._scatterViewbox))
        self._scatterContextMenu.addAction(self.exportAction)
        # self._toggleSelectionOptions()

        self._scatterContextMenu.exec_(ev.screenPos().toPoint())

    def _showExportDialog(self, viewBox):
        """
        :param viewBox: the viewBox obj for the selected plot
        :return:
        """
        if self._exportDialog is None:
            self._exportDialog = CustomExportDialog(viewBox.scene(), titleName='Exporting')
        self._exportDialog.show(viewBox)

    ###########  scatter Mouse Events ############

    def _scatterMouseDoubleClickEvent(self, event):
        """
        e-implementation of scatter double click event
        """
        self._openSelectedPoint()

    def _scatterMouseClickEvent(self, ev):
        """
          Re-implementation of scatter mouse event to allow selections of a single point
        """
        plot = self.scatterPlot
        pts = plot.pointsAt(ev.pos())
        obj = None
        if len(pts) > 0:
            point = pts[0]
            obj = point.data()

        if me.leftMouse(ev):
            if obj:
                self._selectedObjs = [obj]
                if self.current:
                    self.current.pcaComponents = self._selectedObjs
                ev.accept()
            else:
                # "no spots, clear selection"
                self._selectedObjs = []
                if self.current:
                    self.current.pcaComponents = self._selectedObjs
                ev.accept()

        elif me.controlLeftMouse(ev):
            # Control-left-click;  add to selection
            self._selectedObjs.extend([obj])
            if self.current:
                self.current.pcaComponents = self._selectedObjs
            ev.accept()

        else:
            ev.ignore()

    def mouseMoved(self, event):
        """
        use this if you need for example display the mouse coords on display
        :param event:
        :return:
        """

        position = event
        if self._scatterViewbox.sceneBoundingRect().contains(position):
            mousePoint = self._scatterViewbox.mapSceneToView(position)
            x = mousePoint.x()
            y =  mousePoint.y()
            self.coordinatesLabel.setText("x=%0.2f, y=%0.2f" % (x, y))

    def _scatterMouseDragEvent(self, event, *args):
        """
        Re-implementation of PyQtGraph mouse drag event to allow custom actions off of different mouse
        drag events. Same as spectrum Display. Check Spectrum Display View Box for more documentation.
        Known bug: left drag on the axis, raises a pyqtgraph exception
        """
        if me.leftMouse(event):
            pg.ViewBox.mouseDragEvent(self._scatterViewbox, event)
        elif me.controlLeftMouse(event):
            self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
            event.accept()
            if not event.isFinish():
                self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())

            else:  ## the event is finished.
                pts = self._updateScatterSelectionBox(event.buttonDownPos(), event.pos())
                df = self.dataFrame
                print(pts)
                #todo add the data
                # if self.decomposition:
                #     i, o = self.decomposition.splitDataWithinRange(self.getPcaResults(),
                #                                                    *self._getSelectedAxesLabels(), *pts)
                #     self._selectedObjs.extend(i.index)
                #     self._selectScatterPoints()
                self._resetSelectionBox()
        else:
            self._resetSelectionBox()
            event.ignore()

    ########### ROI box for scatter Plot ############

    def _roiPresetCallBack(self, *args):
        v = self.roiMethodPulldown.getObject()
        perc = self.roiPercValue.get()
        self.presetROI(v, perc)

    def _roiMouseActionCallBack(self, *args):
        """ called by the context menu. Sets the settings checkbox, The settings CB will do the actual work"""
        self.roiCheckbox.set(not self.roiCheckbox.get())
        self._toggleROI()

    def _toggleROI(self, *args):
        """ Toggle the ROI from the scatter plot"""
        v = self.roiCheckbox.get()
        if v:
            self.roiItem.show()
        else:
            self.roiItem.hide()

    def _setROIhandles(self):
        """ sets the handle in each corners, no matter the roiItem sizes """
        self.roiItem.addScaleHandle([1, 1], [0.5, 0.5], name='topRight')
        self.roiItem.addScaleHandle([0, 1], [1, 0], name='topLeft')
        self.roiItem.addScaleHandle([0, 0], [0.5, 0.5], name='bottomLeft')
        self.roiItem.addScaleHandle([1, 0], [0, 1], name='bottomRight'),

    def getROIdata(self):
        """
        the values for the ROI
        (getState returns a dict ['pos']  left bottom corner, ['size'] the size of RO1 and ['angle'] for this RectROI is 0)
        :return: a list of rectangle coordinates in the format minX, maxX, minY, maxY
        """
        state = self.roiItem.getState()
        pos = state['pos']
        size = state['size']
        xMin = pos[0]
        xMax = pos[0] + size[0]
        yMin = pos[1]
        yMax = pos[1] + size[1]
        return [xMin, xMax, yMin, yMax]

    def presetROI(self, func=np.median, percent=20):
        """
        Apply the function (default np.mean) to the currently displayed plot data
        to get the x,y values for setting the ROI box.
        :param func: a function applicable to the x,y data
        :return: set the ROI on the scatter plot
        """

        x, y = self.scatterPlot.getData()
        if not len(x) > 0 and not len(y) > 0:
            return

        xR = func(x)
        yR = func(y)
        xRange = np.max(x) - np.min(x)
        yRange = np.max(y) - np.min(y)

        xperc = percentage(percent, xRange)
        yperc = percentage(percent, yRange)

        xMin = xR - xperc
        yMin = yR - yperc
        xMax = xR + xperc
        yMax = yR + yperc

        self.setROI(xMin, xMax, yMin, yMax)

    def _setROI(self, xMin, xMax, yMin, yMax):
        """
        a conversion mechanism to the internal roiItem setState
        :return:  set the ROI box
        """
        state = {'pos': [], 'size': [], 'angle': 0}
        xSize = abs(xMin) + xMax
        ySize = abs(yMin) + yMax
        state['pos'] = [xMin, yMin]
        state['size'] = [xSize, ySize]
        self.roiItem.setState(state)

    def _selectFromROI(self):

        scores = self.getPcaResults()
        if scores is not None:
            roi = self.getROIdata()
            i, o = self.decomposition.splitDataWithinRange(scores, *self._getSelectedAxesLabels(), *roi)
            if i is not None:
                self._selectedObjs = i.index
                self._selectScatterPoints()

    def _createGroupFromROI(self, inside=True):
        pass
        # TODO

        # xsel = self.xAxisSelector.get()
        # ysel = self.yAxisSelector.get()
        # xl = PC + str(xsel)
        # yl = PC + str(ysel)
        # scores = self.getPcaResults()
        # if scores is not None:
        #     roiItem = self.getROIdata()
        #     i, o = self.decomposition.splitDataWithinRange(scores, xl, yl, *roiItem)
        #     if inside:
        #         self.decomposition.createSpectrumGroupFromScores(list(i.index))
        #     else:
        #         self.decomposition.createSpectrumGroupFromScores(list(i.index))

    def _axisChanged(self, *args):
        """callback from axis pulldowns which will replot the scatter"""
        pass
        #TODO
        # self.plotPCAscatterResults(self.getPcaResults(), *self._getSelectedAxesLabels(), selectedObjs=self._selectedObjs)

    def _updateScatterSelectionBox(self, p1: float, p2: float):
        """
        Updates drawing of selection box as mouse is moved.
        """
        vb = self._scatterViewbox
        r = QtCore.QRectF(p1, p2)
        r = vb.childGroup.mapRectFromParent(r)
        self._scatterSelectionBox.setPos(r.topLeft())
        self._scatterSelectionBox.resetTransform()
        self._scatterSelectionBox.scale(r.width(), r.height())
        self._scatterSelectionBox.show()
        minX = r.topLeft().x()
        minY = r.topLeft().y()
        maxX = minX + r.width()
        maxY = minY + r.height()
        return [minX, maxX, minY, maxY]

    def _resetSelectionBox(self):
        "Reset/Hide the boxes "
        self._successiveClicks = None
        self._scatterSelectionBox.hide()
        self._scatterViewbox.rbScaleBox.hide()

    def _clearScatterSelection(self):
        self._selectedObjs = []
        self._selectScatterPoints()

    def _selectScatterPoints(self):
        self.scatterPlot.clear()
        if self.current:
            self.current.pcaComponents = self._selectedObjs  # does selection through notifier
        else:  # does still selection. E.g. if used as stand alone module
            self.plotPCAscatterResults(self.getPcaResults(), *self._getSelectedAxesLabels(), selectedObjs=self._selectedObjs)

    def _invertScatterSelection(self):
        invs = [point.data() for point in self.scatterPlot.points() if point.data() not in self._selectedObjs]
        self._selectedObjs = invs
        self._selectScatterPoints()

    def _getObjFromPoints(self, points=None):
        if points is None:
            points = self.scatterPlot.points()
        df = pd.DataFrame(points, index=[point.data() for point in points], columns=['item'])
        return df

if __name__ == '__main__':
    from PyQt5 import QtGui, QtWidgets
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    from ccpn.ui.gui.modules.CcpnModule import CcpnModule
    n = 300

    data = pd.DataFrame({
        'Values1': np.random.rand(n),
        'Values2': np.random.rand(n),
        'Values3': np.random.rand(n),
        'Values4': np.random.rand(n),
                        })
    data = pd.DataFrame({
        'Values0': np.arange(1, 21),
        'Values1': np.arange(100, 120),
        'Values2': np.arange(200, 220),
        'Values3': np.arange(300, 320),
        'Values4': np.arange(400, 420),
                        })
    data = pd.DataFrame({
        'Values0': np.arange(1, 6),
        'Values1': np.array([0.5, np.nan, 1.3, 2.4, 1.22]),
        'Values2': np.array(['Dog', 'Bee', 'Ant', 'Bird', 'Cat']),
                        })

    defs = od([
               ['#', 'Values0'],
               ['noos', 'Values1'],
               ['boos', 'Values2'],
    ])
    app = TestApplication()
    win = QtWidgets.QMainWindow()

    moduleArea = CcpnModuleArea(mainWindow=None)
    module = CcpnModule(mainWindow=None, name='Testing Module')
    moduleArea.addModule(module)
    scatterPlot = ScatterPlot(parent=module.mainWidget, application=None, dataFrame=data, grid=(0,0))
    scatterPlot.setAxesDefinitions(defs)
    scatterPlot.selectAxes(xHeader='#', yHeader='noos')
    scatterPlot.roiData = [0,1,0,10]


    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.setWindowTitle('Testing %s' % module.moduleName)
    win.show()

    app.start()
    win.close()
