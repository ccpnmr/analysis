from functools import partial

import pyqtgraph as pg
from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox , CustomLabel
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.SpectraSelectionWidget import SpectraSelectionWidget
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Base import Base
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Colour import spectrumColours
from ccpn.ui.gui.widgets.Table import ObjectTable, Column
from ccpn.core.lib.peakUtils import getDeltaShiftsNmrResidue
from ccpn.core.lib import CcpnSorting
from ccpn.util.Logging import getLogger


DefaultAtoms = ['H', 'N']
DefaultThreshould = 0.1
LightColourSchemeCurrentLabel = '#3333ff'
DarkColourSchemeCurrentLabel = '#00ff00'


class CustomNmrResidueTable(NmrResidueTable):
  ''' Custon nmrResidue Table with extra Delta Shifts column'''
  deltaShiftsColumn = ('Delta Shifts', lambda nmrResidue: nmrResidue._deltaShift, '', None)

  columnDefs = [
    ('#', lambda nmrResidue: nmrResidue.serial, 'NmrResidue serial number', None),
    ('Index', lambda nmrResidue: NmrResidueTable._nmrIndex(nmrResidue), 'Index of NmrResidue in the NmrChain', None),
    ('Sequence', lambda nmrResidue: nmrResidue.sequenceCode, 'Sequence code of NmrResidue', None),
    ('Type', lambda nmrResidue: nmrResidue.residueType, 'NmrResidue type', None),
    ('Selected NmrAtoms', lambda nmrResidue: CustomNmrResidueTable._getSelectedNmrAtomNames(nmrResidue), 'NmrAtoms selected in NmrResidue', None),
    ('Selected Spectra count', lambda nmrResidue: CustomNmrResidueTable._getNmrResidueSpectraCount(nmrResidue)
     , 'Number of spectra selected for calculating the delta shift', None),
    ('Delta Shifts', lambda nmrResidue: nmrResidue._deltaShift, '', None),
    ('Comment', lambda nmr: NmrResidueTable._getCommentText(nmr), 'Notes', lambda nmr, value: NmrResidueTable._setComment(nmr, value))
  ]

  # columnDefs = NmrResidueTable.columnDefs+[deltaShiftsColumn,]
  # columnDefs[-1], columnDefs[-2] = columnDefs[-2], columnDefs[-1]

  def __init__(self, parent, application, actionCallback=None, selectionCallback=None, nmrChain=None, **kwds):

    NmrResidueTable.__init__(self, parent=parent, application=application,actionCallback=actionCallback,
                             selectionCallback=selectionCallback, nmrChain=nmrChain, multiSelect = True, **kwds)
    self.NMRcolumns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for
                       colName, func, tipText, editValue in self.columnDefs]
    self.multiSelect = True




  @staticmethod
  def _getNmrResidueSpectraCount(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return nmrResidue.spectraCount
    except:
      return None

  @staticmethod
  def _getSelectedNmrAtomNames(nmrResidue):

    """
    CCPN-INTERNAL: Insert an index into ObjectTable
    """
    try:
      return ', '.join(nmrResidue.selectedNmrAtomNames)
    except:
      return None

class ChemicalShiftsMapping(CcpnModule):

  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsPosition = 'left'
  className = 'ChemicalShiftsMapping'

  def __init__(self, mainWindow, name='Chemical Shift Mapping', nmrChain= None, **kw):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name, settingButton=True)

    BarGraph.mouseClickEvent = self._mouseClickEvent
    BarGraph.mouseDoubleClickEvent = self._mouseDoubleClickEvent


    self.mainWindow = mainWindow
    self.application = None
    self.atoms = set()
    self.atomCheckBoxes = []
    if self.mainWindow is not None:
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application
      self.current = self.application.current

      if len(self.project.nmrResidues):

        for i in self.project.nmrResidues:
          for j in i.nmrAtoms:
            self.atoms.add(j.name)

    self.thresholdLinePos = DefaultThreshould

    self._setWidgets()
    self._setSettingsWidgets()

    self._selectCurrentNmrResiduesNotifier = Notifier(self.current , [Notifier.CURRENT] , targetName='nmrResidues'
                                                     , callback=self._selectCurrentNmrResiduesNotifierCallback)



  def _setWidgets(self):

    if self.application:
      self.barGraphWidget = BarGraphWidget(self.mainWidget, application=self.application, grid=(0, 0))
      self.barGraphWidget.xLine.setPos(DefaultThreshould)
      self.barGraphWidget.customViewBox.mouseClickEvent = self._viewboxMouseClickEvent
      self.nmrResidueTable = CustomNmrResidueTable(parent=self.mainWidget, application=self.application,
                                                   actionCallback= self._customActionCallBack,
                                                   setLayout=True, grid=(1, 0))
      self.nmrResidueTable.displayTableForNmrChain = self._displayTableForNmrChain





  def _setSettingsWidgets(self):

    self.scrollArea = ScrollArea(self, setLayout=False, )
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(self, setLayout=True)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.scrollAreaWidgetContents.getLayout().setAlignment(QtCore.Qt.AlignTop)
    self.settingsWidget.getLayout().addWidget(self.scrollArea)

    # self.settingFrame = Frame(self, setLayout=False)
    # self.settingWidgetsLayout = QtGui.QGridLayout()
    # self.settingFrame.setLayout(self.settingWidgetsLayout)
    # self.settingsWidget.getLayout().addWidget(self.settingFrame)
    # self.settingsWidget.getLayout().setAlignment(self.settingFrame, QtCore.Qt.AlignLeft)
    # self.settingsWidget.getLayout().setContentsMargins(1, 1, 1, 1)
    # self.settingWidgetsLayout.setContentsMargins(10, 10, 1, 15) #l,t,r,b
    # self.settingFrame.setMaximumWidth(340)
    # self._settingsScrollArea.setMaximumWidth(340)

    # self.settingsWidget.getLayout().setAlignment(QtCore.Qt.AlignTop)
    i = 0
    self.inputLabel = Label(self.scrollAreaWidgetContents, text='Select Data Input', grid=(i, 0), vAlign='t')
    self.spectraSelectionWidget = SpectraSelectionWidget(self.scrollAreaWidgetContents, mainWindow=self.mainWindow, grid=(i,1))
    i += 2
    self.atomLabel = Label(self.scrollAreaWidgetContents,text='Select Atoms', grid=(i,0))
    for atom in sorted(self.atoms, key=CcpnSorting.stringSortKey):
      self.atomCheckBox = CheckBox(self.scrollAreaWidgetContents, text=atom, checked=True, grid=(i,1))
      if atom in DefaultAtoms:
        self.atomCheckBox.setChecked(True)
      else:
        self.atomCheckBox.setChecked(False)
      self.atomCheckBoxes.append(self.atomCheckBox)
      i += 1

    self.thresholdLAbel = Label(self.scrollAreaWidgetContents, text='Threshold value', grid=(i, 0))
    self.thresholdSpinBox = DoubleSpinbox(self.scrollAreaWidgetContents, value=DefaultThreshould, decimals=3, grid=(i, 1))
    i += 1
    self.aboveThresholdColourLabel =  Label(self.scrollAreaWidgetContents,text='Above Threshold Colour', grid=(i,0))
    self.aboveThresholdColourBox = PulldownList(self.scrollAreaWidgetContents,  grid=(i, 1))
    for item in spectrumColours.items():
      pix = QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      self.aboveThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    self.aboveThresholdColourBox.select(list(spectrumColours.values())[-1])

    i += 1
    self.belowThresholdColourLabel = Label(self.scrollAreaWidgetContents, text='Below Threshold Colour', grid=(i, 0))
    self.belowThresholdColourBox = PulldownList(self.scrollAreaWidgetContents, grid=(i, 1))
    for item in spectrumColours.items():
      pix = QtGui.QPixmap(QtCore.QSize(20, 20))
      pix.fill(QtGui.QColor(item[0]))
      self.belowThresholdColourBox.addItem(icon=QtGui.QIcon(pix), text=item[1])
    self.belowThresholdColourBox.setCurrentIndex(0)
    i += 1
    self.updateButton = Button(self.scrollAreaWidgetContents, text='Update All', callback=self.updateModule, grid=(i, 1))

  def updateTable(self, nmrChain):
    self.nmrResidueTable.ncWidget.select(nmrChain.pid)
    self.nmrResidueTable.setColumns(self.nmrResidueTable.NMRcolumns)

    self.nmrResidueTable.setObjects([nr for nr in nmrChain.nmrResidues if nr._deltaShift])
    self.nmrResidueTable._selectOnTableCurrentNmrResidues(self.current.nmrResidues)

  def _displayTableForNmrChain(self, nmrChain):

    self.updateModule()
    # self.updateTable(nmrChain)
    # self.updateBarGraph()

  def updateBarGraph(self):
    xs = []
    ys = []
    obs = []
    aboveX = []
    aboveY = []
    aboveObjects = []
    belowX = []
    belowY = []
    belowObjects = []
    aboveBrush = 'g'
    belowBrush = 'r'
    thresholdPos = self.thresholdSpinBox.value()

    if self.barGraphWidget.xLine:
      self.thresholdLinePos = self.barGraphWidget.xLine.pos().y()

      for nmrResidue in self.nmrResidueTable.objects:
        x = int(nmrResidue.sequenceCode)
        y = float(nmrResidue._deltaShift)
        xs.append(x)
        ys.append(y)
        obs.append(nmrResidue)
        if y > self.thresholdLinePos:
          aboveY.append(y)
          aboveX.append(x)
          aboveObjects.append(nmrResidue)
        else:
          belowX.append(x)
          belowY.append(y)
          belowObjects.append(nmrResidue)

    selectedNameColourA = self.aboveThresholdColourBox.getText()
    for code, name in spectrumColours.items():
      if name == selectedNameColourA:
        aboveBrush = code

    selectedNameColourB = self.belowThresholdColourBox.getText()
    for code, name in spectrumColours.items():
      if name == selectedNameColourB:
        belowBrush = code


    self.barGraphWidget.deleteLater()
    self.barGraphWidget = None
    self.barGraphWidget = BarGraphWidget(self.mainWidget, application=self.application,
                                         xValues=xs, yValues=ys, objects=obs,threshouldLine = thresholdPos,
                                         grid=(0, 0))
    self.barGraphWidget.customViewBox.mouseClickEvent = self._viewboxMouseClickEvent
    self.barGraphWidget.xLine.sigPositionChangeFinished.connect(self._updateThreshold)
    self.barGraphWidget.customViewBox.addSelectionBox()


    self.barGraphWidget._lineMoved(aboveX=aboveX,
                                   aboveY=aboveY,
                                   aboveObjects=aboveObjects,
                                   belowX=belowX,
                                   belowY=belowY,
                                   belowObjects=belowObjects,
                                   belowBrush=belowBrush,
                                   aboveBrush=aboveBrush
                                   )


  def _updateThreshold(self):
    self.thresholdSpinBox.setValue(self.barGraphWidget.xLine.pos().y())
    self.barGraphWidget._lineMoved()

  def _viewboxMouseClickEvent(self, event):

    if event.button() == QtCore.Qt.RightButton:
      event.accept()
      self.barGraphWidget.customViewBox._raiseContextMenu(event)
      self.barGraphWidget.customViewBox._resetBoxes()

    elif event.button() == QtCore.Qt.LeftButton:
      self.barGraphWidget.customViewBox._resetBoxes()
      self.application.current.clearNmrResidues()
      event.accept()

  def _customActionCallBack(self, nmrResidue, *args):
    from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, _getCurrentZoomRatio


    if nmrResidue:
      xPos = int(nmrResidue.sequenceCode)
      yPos = nmrResidue._deltaShift
      self.barGraphWidget.customViewBox.setRange(xRange=[xPos-10, xPos+10], yRange=[0, yPos],)
      self.application.ui.mainWindow.clearMarks()
      if self.current.strip is not None:
        strip = self.current.strip
        if len(nmrResidue.selectedNmrAtomNames) == 2:
          nmrAtom1 = nmrResidue.getNmrAtom(str(nmrResidue.selectedNmrAtomNames[0]))
          nmrAtom2 = nmrResidue.getNmrAtom(str(nmrResidue.selectedNmrAtomNames[1]))
          if nmrAtom1 and nmrAtom2:
            navigateToNmrAtomsInStrip(strip,
                                      nmrAtoms=[nmrAtom1, nmrAtom2],
                                      widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                      markPositions=True
                                      )
      else:
        getLogger().warning('Impossible to navigate to peak position. Set a current strip first')

  def updateModule(self):
    selectedAtomNames = [cb.text() for cb in self.atomCheckBoxes if cb.isChecked()]
    if self.nmrResidueTable.nmrChain:
      for nmrResidue in self.nmrResidueTable.nmrChain.nmrResidues:
        spectra = self.spectraSelectionWidget.getSelections()
        nmrResidue.spectraCount = len(spectra)
        nmrResidueAtoms = [atom.name for atom in nmrResidue.nmrAtoms]
        nmrResidue.selectedNmrAtomNames =  [atom for atom in nmrResidueAtoms if atom in selectedAtomNames]
        nmrResidue._deltaShift = getDeltaShiftsNmrResidue(nmrResidue, selectedAtomNames, spectra=spectra)
      self.updateTable(self.nmrResidueTable.nmrChain)
      self.updateBarGraph()


  def _selectCurrentNmrResiduesNotifierCallback(self, data):
    for bar in self.barGraphWidget.barGraphs:
      for label in bar.labels:
        if label.data(int(label.text())) is not None:
          if self.application is not None:

            if label.data(int(label.text())) in self.current.nmrResidues:

              if self.application.colourScheme == 'light':
                highlightColour = '#3333ff'
              else:
                highlightColour = '#00ff00'
              label.setBrush(QtGui.QColor(highlightColour))
              label.setVisible(True)
              label.setSelected(True)

            else:
              label.setSelected(False)
              label.setBrush(QtGui.QColor(bar.brush))
              if label.isBelowThreshold and not self.barGraphWidget.customViewBox.allLabelsShown:
                label.setVisible(False)


  def _mouseClickEvent(self, event):

    position = event.pos().x()
    self.clicked = int(position)
    if event.button() == QtCore.Qt.LeftButton:
      for bar in self.barGraphWidget.barGraphs:
        for label in bar.labels:
          if label.text() == str(self.clicked):
            self.current.nmrResidue = label.data(self.clicked)
            label.setSelected(True)
      event.accept()

  def _mouseDoubleClickEvent(self, event):
    from ccpn.ui.gui.lib.Strip import navigateToNmrAtomsInStrip, _getCurrentZoomRatio

    self.nmrResidueTable.scrollToSelectedIndex()

    self.application.ui.mainWindow.clearMarks()
    position = event.pos().x()
    self.doubleclicked = int(position)
    if event.button() == QtCore.Qt.LeftButton:
      for bar in self.barGraphWidget.barGraphs:
        for label in bar.labels:
          if label.text() == str(self.doubleclicked):
           nmrResidue =  label.data(self.doubleclicked)
           if nmrResidue:
             if self.current.strip is not None:
               strip = self.current.strip
               if len(nmrResidue.selectedNmrAtomNames) == 2:
                 nmrAtom1 = nmrResidue.getNmrAtom(str(nmrResidue.selectedNmrAtomNames[0]))
                 nmrAtom2 = nmrResidue.getNmrAtom(str(nmrResidue.selectedNmrAtomNames[1]))
                 if nmrAtom1 and nmrAtom2:

                   navigateToNmrAtomsInStrip(strip,
                                             nmrAtoms=[nmrAtom1, nmrAtom2],
                                             widths=_getCurrentZoomRatio(strip.viewBox.viewRange()),
                                             markPositions=True
                                             )
             else:
               getLogger().warning('Impossible to navigate to peak position. Set a current strip first')

  def close(self):
    """
    Close the table from the commandline
    """
    self._closeModule()

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification on current
    """
    if self._selectCurrentNmrResiduesNotifier is not None:
      self._selectCurrentNmrResiduesNotifier.unRegister()

    super(ChemicalShiftsMapping, self)._closeModule()



class BarGraphWidget(Widget, Base):


  def __init__(self, parent, application=None, xValues=None, yValues=None, colour='r', objects=None, threshouldLine=0.01, **kw):
    Widget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.application = application
    # set background from application
    if self.application:
      if self.application.colourScheme == 'light':
        self.backgroundColour = '#f7ffff'
      else:
        self.backgroundColour = '#080000'
    else:
      self.backgroundColour = 'w'
    self.thresholdLineColour = 'b'

    self._setViewBox()
    self._setLayout()
    self.setContentsMargins(1, 1, 1, 1)
    self.xLine = None
    self.barGraphs = []

    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects
    self.colour = colour
    self.aboveBrush = 'g'
    self.belowBrush = 'r'
    self.threshouldLine = threshouldLine



    self.setData(viewBox=self.customViewBox, xValues=xValues,yValues=yValues, objects=objects,colour=colour,replace=True)
    self._addExtraItems()
    # self.updateViewBoxLimits()

  def _setViewBox(self):
    self.customViewBox = CustomViewBox(application = self.application)
    self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
    self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background=self.backgroundColour)
    self.customViewBox.setParent(self.plotWidget)

  def _setLayout(self):
    hbox = QtGui.QHBoxLayout()
    self.setLayout(hbox)
    hbox.addWidget(self.plotWidget)
    hbox.setContentsMargins(1, 1, 1, 1)

  def _addExtraItems(self):
    # self.addLegend()
    self.addThresholdLine()


  def setData(self,viewBox, xValues, yValues, objects, colour, replace=True):
    if replace:
      self.barGraphs = []
      self.customViewBox.clear()

    self.barGraph = BarGraph(viewBox=viewBox, application = self.application,
                             xValues=xValues, yValues=yValues, objects=objects, brush=colour)
    self.barGraphs.append(self.barGraph)
    self.customViewBox.addItem(self.barGraph)
    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects
    self.updateViewBoxLimits()


  def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
    self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

  def updateViewBoxLimits(self):
    '''Updates with default paarameters. Minimum values to show the data only'''
    if self.xValues and self.yValues:
      self.customViewBox.setLimits(xMin=min(self.xValues)/2, xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                   yMin=min(self.yValues)/2 ,yMax=max(self.yValues) + (max(self.yValues) * 0.5),
                                   )



  def clearBars(self):
    self.barGraphs = []
    for item in self.customViewBox.addedItems:
      if not isinstance(item, pg.InfiniteLine):
        self.customViewBox.removeItem(item)

  def addThresholdLine(self):

    self.xLine = pg.InfiniteLine(angle=0, movable=True, pen=self.thresholdLineColour)
    self.customViewBox.addItem(self.xLine)

    # self.thresholdValueTextItem = pg.TextItem(str(self.xLine.pos().y()), anchor=(self.customViewBox.viewRange()[0][0], 1.0),)
    # self.thresholdValueTextItem.setParentItem(self.xLine)
    # self.thresholdValueTextItem.setBrush(QtGui.QColor(self.thresholdLineColour))
    if self.yValues is not None:
      if len(self.yValues)>0:
        self.xLine.setPos(self.threshouldLine)
    self.showThresholdLine(True)
    self.xLine.sigPositionChangeFinished.connect(self._lineMoved)
    # self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))
    print(str(round(self.xLine.pos().y(), 4)))
    self.xLine.sigPositionChanged.connect(self._updateTextLabel)

  def _updateTextLabel(self):
    # self.thresholdValueTextItem.setText(str(round(self.xLine.pos().y(),3)))#, color=self.thresholdLineColour)

    self.xLine.setToolTip(str(round(self.xLine.pos().y(), 4)))

  def showThresholdLine(self, value=True):
    if value:
      self.xLine.show()
    else:
      self.xLine.hide()

  def _lineMoved(self, **args):

    self.clearBars()
    if len(args)>0:
        aboveX = args['aboveX']
        aboveY =  args['aboveY']
        aboveObjects = args['aboveObjects']
        belowX =  args['belowX']
        belowY =  args['belowY']
        belowObjects =  args['belowObjects']
        self.aboveBrush = args['aboveBrush']
        self.belowBrush = args['belowBrush']

    else:
      aboveX = []
      aboveY = []
      aboveObjects = []
      belowX = []
      belowY = []
      belowObjects = []


      pos = self.xLine.pos().y()
      if self.xValues:
        for x,y,obj in zip(self.xValues, self.yValues, self.objects):
          if y > pos:
            aboveY.append(y)
            aboveX.append(x)
            aboveObjects.append(obj)
          else:
            belowX.append(x)
            belowY.append(y)
            belowObjects.append(obj)



    self.aboveThreshold = BarGraph(viewBox=self.customViewBox, application = self.application,
                                   xValues=aboveX, yValues=aboveY, objects=aboveObjects, brush=self.aboveBrush)
    self.belowTrheshold = BarGraph(viewBox=self.customViewBox, application = self.application,
                                   xValues=belowX, yValues=belowY, objects=belowObjects,brush=self.belowBrush)

    self.customViewBox.addItem(self.aboveThreshold)
    self.customViewBox.addItem(self.belowTrheshold)
    self.barGraphs.append(self.aboveThreshold)
    self.barGraphs.append(self.belowTrheshold)
    self.updateViewBoxLimits()
    if self.customViewBox.allLabelsShown:
      self.customViewBox.showAllLabels()
    if self.customViewBox.showAboveThresholdOnly:
      self.customViewBox.showAboveThreshold()


  def addLegend(self):
    self.legendItem = pg.LegendItem((100, 60), offset=(70, 30))  # args are (size, offset)
    self.legendItem.setParentItem(self.customViewBox.graphicsItem())

  def addLegendItem(self, pen='r', name=''):
    c = self.plotWidget.plot(pen=pen, name=name)
    self.legendItem.addItem(c, name)

  def showLegend(self, value:False):
    if value:
      self.legendItem.show()
    else:
     self.legendItem.hide()

  def _updateGraph(self):
    self.customViewBox.clear()





#######################################################################################################
####################################      Mock DATA TESTING    ########################################
#######################################################################################################

from collections import namedtuple
import random

nmrResidues = []
for i in range(30):
  nmrResidue = namedtuple('nmrResidue', ['sequenceCode','peaksShifts'])
  nmrResidue.__new__.__defaults__ = (0,)
  nmrResidue.sequenceCode = i
  nmrResidue.peaksShifts = random.uniform(1.5, 3.9)
  nmrResidues.append(nmrResidue)

nmrChain = namedtuple('nmrChain', ['nmrResidues'])
nmrChain.nmrResidues = nmrResidues




if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea

  app = TestApplication()
  win = QtGui.QMainWindow()

  moduleArea = CcpnModuleArea(mainWindow=None, )
  chemicalShiftsMapping = ChemicalShiftsMapping(mainWindow=None, nmrChain=nmrChain)
  moduleArea.addModule(chemicalShiftsMapping)




  win.setCentralWidget(moduleArea)
  win.resize(1000, 500)
  win.setWindowTitle('Testing %s' % chemicalShiftsMapping.moduleName)
  win.show()

  app.start()
