from functools import partial

import pyqtgraph as pg
from PyQt4 import QtCore, QtGui

from ccpn.core.PeakList import PeakList
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.BarGraph import BarGraph, CustomViewBox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.GroupBox import GroupBox
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Widget import Widget


class InputWidget(Widget):
  def __init__(self, **kw):
    super(InputWidget, self).__init__()
    self.params = {}
    l = QtGui.QHBoxLayout()
    self.setLayout(l)

    self.peakListInput = PulldownList(None, ['Select'])
    self.sb = DoubleSpinbox(None)
    self.sb.setSingleStep(0.01)
    self.closeIcon = Icon('icons/window-close')
    self.deleteButton = Button(None, '',icon=self.closeIcon)
    self.deleteButton.setStyleSheet("background-color: transparent; border: 0px;")
    self.deleteButton.setMaximumWidth(20)
    l.addWidget(self.peakListInput)
    l.addWidget(self.sb)
    l.addWidget(self.deleteButton)

  def getParams(self):
    return {self.peakListInput.getObject(): self.sb.value()}

  def setParams(self, names, peakListObjs, select=None, value=None):
    self.peakListInput.setData(names, peakListObjs)
    if select is not None:
      self.peakListInput.select(select)
    if value is not None:
      self.sb.setValue(float(value))



class SettingWidget(Widget):
  def __init__(self, parent=None, **kw):
    super(SettingWidget, self).__init__()
    self.application = QtCore.QCoreApplication.instance()._ccpnApplication
    self.project = self.application.project
    if parent is not None:
      self.parent = parent
    self.inputWidgetList = []

    self.inputDataBoundary = InputDataBoundary(self.application)
    self.mainLayout = QtGui.QVBoxLayout(self)
    self.initUIinputWidget()
    self.applyButtons = ButtonList(None, texts=['Save', 'Update', 'Apply'],
                                   callbacks=[None, None, self._sendDataToPlot],
                                   tipTexts=['', '', ''], direction='h',
                                   hAlign='r')

    self.mainLayout.addStretch(1)
    self.mainLayout.addWidget(self.applyButtons)

    self._setInputWidgetData()
    self.__registerNotifiers()

  def initUIinputWidget(self):
    mygroupbox = GroupBox(None)
    self.myform = QtGui.QFormLayout()

    for i in range(3):
      self.addInputWidget()

    self.myform.addWidget(Button(None, 'Add Input', callback=self.addInputWidget))
    mygroupbox.setLayout(self.myform)
    scroll = ScrollArea(None)
    scroll.setWidget(mygroupbox)
    scroll.setWidgetResizable(True)
    self.mainLayout.addWidget(scroll)

  def getInputPeakLists(self):
    if self.project:
      if self.project.peakLists:
        return [pl for pl in self.project.peakLists]
      else:
        print('No peakList Found')
        return False



  def addInputWidget(self):
    rc = self.myform.rowCount()
    iw = InputWidget()

    self.inputWidgetList.append(iw)
    self.myform.insertRow(rc-1, iw)
    iw.deleteButton.clicked.connect(partial(self.deleteInputWidget, iw))
    self._setInputWidgetData()

  def _setInputWidgetData(self, *args):
    if self.inputWidgetList:
      for iw in self.inputWidgetList:

        if self.getInputPeakLists():
          pids =[pl.pid for pl in self.getInputPeakLists()]
          pls = self.getInputPeakLists()
          oldSelection = list(iw.getParams().keys())[0]
          if oldSelection is not None:
            iw.setParams(names=pids, peakListObjs=pls, select=oldSelection, value=None)
          else:
            iw.setParams(names=pids, peakListObjs=pls, value=None)



  def deleteInputWidget(self, iw):
    if iw in self.inputWidgetList:
      self.inputWidgetList.remove(iw)
    iw.deleteLater()

  def _getDataToPlot(self):
    sources = {}
    pName = None
    for iw in self.inputWidgetList:
      iwParams = iw.getParams()
      sources.update(iwParams)
    for key in sources.keys():
      if isinstance(key, PeakList):

        self.inputDataBoundary.sources = sources
        dataFrame = self.inputDataBoundary._setDataFrame()

        shifts = self.inputDataBoundary.calculateChemicalShift(dataFrame, pName)
        cs = self.inputDataBoundary.getChemicalShifts(shifts)
        pids = cs['pid'].values.tolist()
        objs = [self.project.getByPid(pid) for pid in pids]
        xValues = [int(x) for x in cs['numb'].values.tolist()]
        yValues = [float(y) for y in cs['value'].values.tolist()]
        return xValues, yValues, objs
      else:
        return False
    return False


  def _sendDataToPlot(self):
    data = self._getDataToPlot()
    if data:
      xValues, yValues, objs = data

      self.parent.barGraphWidget._updateGraph()
      self.parent.barGraphWidget.setValue(xValues=xValues, yValues=yValues, objects=objs)
      self.parent.barGraphWidget.addBarItems()


  def __registerNotifiers(self):
    self.project.registerNotifier('PeakList', 'create', self._setInputWidgetData)
    self.project.registerNotifier('PeakList', 'modify', self._setInputWidgetData)
    self.project.registerNotifier('PeakList', 'rename', self._setInputWidgetData)
    self.project.registerNotifier('PeakList', 'delete', self._setInputWidgetData)


  def __deregisterNotifiers(self):
    self.project.unRegisterNotifier('PeakList', 'create', self._setInputWidgetData)
    self.project.unRegisterNotifier('PeakList', 'modify', self._setInputWidgetData)
    self.project.unRegisterNotifier('PeakList', 'rename', self._setInputWidgetData)
    self.project.unRegisterNotifier('PeakList', 'delete', self._setInputWidgetData)


class ChemicalShiftsMapping(CcpnModule):

  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True
  className = 'ChemicalShiftsMapping'

  def __init__(self, mainWindow, name='Chemical Shifts Mapping', **kw):
    # super(ChemicalShiftsMapping, self)
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name,  settingButton=True)
    self.mainWindow = mainWindow
    self.project = self.mainWindow.project
    self.application = self.mainWindow.application

    self.barGraphWidget = BarGraphWidget()
    self.settingWidget = SettingWidget(parent=self)
    self.addWidget(self.settingWidget, 0,0)
    self.addWidget(self.barGraphWidget, 0,1)

  def _closeModule(self):
    """
    Re-implementation of closeModule function from CcpnModule to unregister notification on current
    """
    # FIXME __deregisterNotifiers
    # self.settingWidget.__deregisterNotifiers()
    super(ChemicalShiftsMapping, self)._closeModule()



class BarGraphWidget(Widget):

  def __init__(self,xValues=None, yValues=None, objects=None, **kw):
    super(BarGraphWidget, self).__init__()

    self._setViewBox()
    self._setLayout()

    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects
    self.addBarItems()

    self._addExtraItems()

  def _setViewBox(self):
    self.customViewBox = CustomViewBox()
    self.customViewBox.setMenuEnabled(enableMenu=False)  # override pg default context menu
    self.plotWidget = pg.PlotWidget(viewBox=self.customViewBox, background='w')
    self.customViewBox.setParent(self.plotWidget)

  def _setLayout(self):
    hbox = QtGui.QHBoxLayout()
    self.setLayout(hbox)
    hbox.addWidget(self.plotWidget)

  def _addExtraItems(self):
    self.addLegend()
    self.addThresholdLine()


  def setValue(self, xValues, yValues, objects):
    self.xValues = xValues
    self.yValues = yValues
    self.objects = objects

  def setViewBoxLimits(self, xMin, xMax, yMin, yMax):
    self.customViewBox.setLimits(xMin=xMin, xMax=xMax, yMin=yMin, yMax=yMax)

  def updateViewBoxLimits(self):
    '''Updates with default paarameters. Minimum values to show the data only'''
    if self.xValues and self.yValues:
      self.customViewBox.setLimits(xMin=min(self.xValues), xMax=max(self.xValues) + (max(self.xValues) * 0.5),
                                   yMin=min(self.yValues),yMax=max(self.yValues) + (max(self.yValues) * 0.5))

  def addBarItems(self):
    bg = BarGraph(viewBox=self.customViewBox, xValues=self.xValues, yValues=self.yValues, objects=self.objects, brush = 'r')
    self.customViewBox.addItem(bg)
    self.updateViewBoxLimits()

  def addThresholdLine(self):
    self.xLine = pg.InfiniteLine(pos=1, angle=0, movable=True, pen='b')
    self.customViewBox.addItem(self.xLine)

  def showThresholdLine(self, value:True):
    if value:
      self.xLine.show()
    else:
      self.xLine.hide()

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





import pandas as pd


class InputDataBoundary:
  ''' Converts CCPN objects into dataFrame'''
  # from ccpn.core.peakList import PeakList

  def __init__(self, application ):

    self.sources = {None: (None, None)}  #{'peakList':('param','value')}

    self.application = application
    self.project = application.project


  def getSources(self):
    return self.sources

  def setSources(self, peakList, param:str, value:float or int ):
    self.sources.update({peakList:(param,value)})

  def _setDataFrame(self) -> pd.DataFrame:
    'create a dataframe from sources'

    dfs = []
    for pl, t in self.sources.items():
      if pl is not None:
        d = self.createPeakListDF(pl, 'temp', t)
        dfs.append(d)
    if dfs:
      dataFrame = pd.concat(dfs)
      return  dataFrame

  def createPeakListDF(self,peakList, paramName, value):
    '''
    :param peakList: ccpnPeakList obj
    :param paramName: str.  EG. Temperature, Concentration
    :param value: parameter value
    :return: dataframe of 'residueNumber', 'Nh', 'Hn', 'Hpos', 'Npos', 'height', 'paramValue'
    '''

    items = []
    columns = ['residueNumber', 'Hn', 'Nh', 'Hpos', 'Npos', 'height', str(paramName)]
    if peakList.peaks is not None:
      for peak in peakList.peaks:
        if peak.assignedNmrAtoms is not None:
          if len(peak.assignedNmrAtoms) > 0:
            residueNumber = peak.assignedNmrAtoms[0][0].nmrResidue.sequenceCode
            Hn = peak.assignedNmrAtoms[0][0].pid
            Nh = peak.assignedNmrAtoms[0][1].pid
            HnPos = str(peak.position[0])
            NhPos = str(peak.position[1])
            height = str(peak.height)
            param = value

            items.append([residueNumber, Hn, Nh, HnPos, NhPos, height, param])

    dataFrame = pd.DataFrame(items, columns=columns)
    dataFrame['residue number'] = dataFrame.index.astype('int')

    dataFrame.index = dataFrame['residueNumber']

    return dataFrame

  def calculateChemicalShift(self, data, paramName):

    sel = data['Hn'].str.endswith('H')
    sel = sel & data['Nh'].str.endswith('N')
    data = data[sel]

    data['Hpos'] = data['Hpos'].astype('float64')
    data['Npos'] = data['Npos'].astype('float64')

    shifts = {}
    for r, pid in zip(data['residueNumber'].unique(), data['Hn']):
      d = data[data['residueNumber'] == r]
      d.index = d.temp
      minParm = d['temp'].min()
      print(minParm, 'min')

      start_H = float(d.loc[minParm, 'Hpos'])
      start_N = float(d.loc[minParm, 'Npos'])

      delta = (((d['Hpos'] - start_H) * 7) ** 2 + (d['Npos'] - start_N) ** 2) ** 0.5
      delta.name = pid
      shifts[int(r)] = delta.sort_index()

    max_shift = 0
    for shift in shifts.values():
      if shift.max() > max_shift:
        max_shift = shift.max()
    return shifts

  def getChemicalShifts(self, shifts):
    d = []
    for n, i in sorted(shifts.items()):
      max_index = shifts[n].index.max()
      d.append([i.name, str(n), str(shifts[n].loc[max_index])])
    g = pd.DataFrame(d, columns = ['pid', 'numb','value'])
    return g





class InputDataInteractor:
  from typing import Tuple
  def __init__(self):
    self.sources = ()

  @property
  def sources(self)-> Tuple[pd.DataFrame, ...]:
    return self.__sources

  @sources.setter
  def sources(self, value):
    self.__sources = value