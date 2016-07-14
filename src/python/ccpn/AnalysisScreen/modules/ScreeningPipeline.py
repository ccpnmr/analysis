__author__ = 'luca'


from ccpn.AnalysisScreen.lib.Screening import writeBruker, createStdDifferenceSpectrum, matchedPosition

from ccpn.AnalysisScreen.modules.ShowScreeningHits import ShowScreeningHits

import decimal
from functools import partial
import pyqtgraph as pg
from PyQt4 import QtCore, QtGui
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

class StdSpectrumCreator(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.project = project
    self.path = self.project._appBase.preferences.general.auxiliaryFilesPath+'/'


    self.createButton = Button(self, text = 'create new spectrum', callback=self._createSpectrumDifference,
                               grid=(0, 0), hAlign='c')
    self.pullDownOffRes = PulldownList(self, texts=['SG:STD_OFF_Res'], grid=(0,1))
    self.pullDownOffRes = PulldownList(self, texts=['SG:STD_ON_Res'], grid=(0, 2))
    self.lineEditPath = LineEdit(self, text=str(self.path),  hAlign='l', grid=(0, 3), gridSpan=(0,3))
    # self.lineEditPath.setFixedWidth = 300

    # self.sgSTDdiff = self.project.newSpectrumGroup('STD_DIFF')

  def _createSpectrumDifference(self):
    for sample in self.project.samples:
      if not sample.isVirtual:

        spectrumDiff = createStdDifferenceSpectrum(sample.spectra[0], sample.spectra[1])
        if self.lineEditPath.text().endswith("/"):
          self.newFilePath = self.lineEditPath.text()+sample.name + '_Std_diff'
        else:
          self.newFilePath = self.lineEditPath.text()+'/'+ sample.name + '_Std_diff'
        writeBruker(self.newFilePath, spectrumDiff)
        self._loadSpectrumDifference(self.newFilePath + '/pdata/1/1r')

  def _loadSpectrumDifference(self, path):
    self.newSpectrumStd = self.project.loadData(path)
    self.newSpectrumStd[0].scale = float(0.1)
    spectrumName = str(self.newSpectrumStd[0].name)

    for sample in self.project.samples:
      if not sample.isVirtual:
        if sample.name == spectrumName.replace('_Std_diff-1',''):
          sample.spectra += (self.newSpectrumStd[0],)
          spectrumGroupSTD = self.project.getByPid('SG:STD_DIFF')
          spectrumGroupSTD.spectra += (self.newSpectrumStd[0],)
          print(self.newSpectrumStd[0].id, 'created and loaded in the project')



class ExcludeRegions(QtGui.QWidget):

  '''This create a widget group to exclude Regions from the Spectrum when automatically peak picking '''

  def __init__(self, parent=None,**kw):
    super(ExcludeRegions, self).__init__(parent)


    self.solvents = {'Acetic Acid-d4': [0,0, 2.14,2.0, 11.75,11.65],
            'Acetone-d6 & Water': [0,0, 2.15,2.0, 2.90, 2.80],
            'Acetonitrile-d3 & water': [0,0, 2.20,1.94],
            'Benzene-d6 & water': [0,0, 0.60,0.50, 7.25,7.15],
            'Chloroform-d': [0,0, 1.60,1.50, 7.35,7.25],
            'Deuterium Oxide': [0,0, 4.75,4.65],
            'Dichloromethane-d2 & water': [0,0, 1.60,1.50, 5.42,5.32],
            'Dimethyl Sulfoxide-d6': [0,0, 2.60,2.50, 3.40,3.30],
            'Dimethylformamide-d7 & water': [0,0, 8.11,8.01, 2.99,2.91, 2.83,2.73, 3.60,3.50],
            'p-Dioxane-d8 & water':[0,0, 2.60,2.50, 3.63,3.50 ],
            'Tetrachloromethane-d2 & water': [0,0, 1.70,1.60, 6.10,6.00],
            'Ethanol-d6 & water': [0,0, 1.21,1.11, 3.66,3.56, 5.40,5.29],
            'Methanol-d4': [0,0, 3.40,3.30, 4.90,4.80],
            'Pyridine-d5 & water': [0,0, 8.74,8.84, 7.68,7.58, 7.32,7.22, 5.10,5.00],
            'Trifluoroacetic acid-d': [0,0, 11.60,11.50],
            'Tetrahydrofuran-d8 & water': [0,0, 3.68,3.58, 2.60,2.50, 1.83,1.73],
            'New regions': [0,0, 0.2, 0.1],
            'Toulene-d8 & water': [0,0, 7.18,6.98, 2.19,2.09, 2.50,2.40, 5.10,5.00],
            'Trifluoroethanol-d3 & water':[0,0, 5.12,5.02, 3.98,3.88],
            'Carbon Tetrachloride & water ': [0,0, 1.20, 1.10],
            'water': [0,0, 5, 4.5]}

    self.pulldownSolvents = PulldownList(self, grid=(0, 1),)
    # self.pulldownSolvents.setFixedWidth(105)
    self.pulldownSolvents.activated[str].connect(self._addRegions)
    for solvent in sorted(self.solvents):
      self.pulldownSolvents.addItem(solvent)
    self.SolventsLabel = Label(self, "Select Regions or \nsolvents to exclude", grid=(0, 0), hAlign='l')
    self.scrollArea = ScrollArea(self, grid=(2, 0), gridSpan=(2,2))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = QtGui.QFrame()

    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.regioncount = 0
    self.excludedRegions = []
    self.comboBoxes = []


  def _addRegions(self, pressed):
    '''   '''
    widgetList = []
    for solvent in sorted(self.solvents):
      if pressed == ('%s' %solvent):
        self.solventType = Label(self.scrollAreaWidgetContents, text=solvent, grid=(self.regioncount,0))
        self.closebutton = Button(self.scrollAreaWidgetContents,'Remove from selection', grid=(self.regioncount,1))
        values = (self.solvents[solvent])
        self.selectedSolventValue = sorted(values)
        self.new_list = [values[i:i+2] for i in range(0, len(values), 2)]
        del self.new_list[0:1]  #delete [0,0] used only to set the layout

        self.excludedRegions.append(self.new_list)

        valueCount = len(values)//2
        self.positions = [(i+self.regioncount, j) for i in range(valueCount)
                     for j in range(2)]
        for self.position, values in zip(self.positions, sorted(values)):
          if values == 0:
             continue
          self.regioncount += valueCount
          self.spin = DoubleSpinbox(self.scrollAreaWidgetContents, grid=(self.position))
          self.spin.setSingleStep(0.01)
          self.spin.setMinimum(-20)
          self.spin.setPrefix('ppm')
          self.spin.setValue(values)
          widgetList.append(self.spin)
    self.comboBoxes.append(widgetList)
    self.closebutton.clicked.connect(partial(self._deleteRegions, self.positions))


  def _deleteRegions(self, positions):
    '''   '''
    for position in positions:
      widget1 = self.scrollAreaWidgetContents.layout().itemAtPosition(*position).widget()
      if widget1 is self.solventType:
        widget1.hide()
      else:
        widget1.deleteLater()

  def _getExcludedRegions(self): # How to do better!?
    '''   '''
    excludedRegions = []

    for comboboxPair in self.comboBoxes:
      try:
        if comboboxPair[0].value() is not None:
          firstPair = (sorted([comboboxPair[0].value(), comboboxPair[1].value()],reverse=True))
          excludedRegions.append(firstPair)
        if comboboxPair[2].value() is not None:
          secondPair = (sorted([comboboxPair[2].value(), comboboxPair[3].value()],reverse=True))
          excludedRegions.append(secondPair)
        if comboboxPair[4].value() is not None:
          thirdPair = (sorted([comboboxPair[4].value(), comboboxPair[5].value()],reverse=True))
          excludedRegions.append(thirdPair)
        if comboboxPair[6].value() is not None:
          fourthPair = (sorted([comboboxPair[6].value(), comboboxPair[7].value()],reverse=True))
          excludedRegions.append(fourthPair)
      except:
        pass
      for i in excludedRegions:
          if len(i) == 0:
            excludedRegions.remove(i)
    return excludedRegions


class PickPeaksWidget(QtGui.QWidget):
  ''''''

  def __init__(self, parent=None, project=None, **kw):
    QtGui.QWidget.__init__(self, parent)

    self.project = project

    self.pickPeaksButton = Button(self, text = 'pick Peaks', callback=self._pickPeaks,
                                  grid=(0, 3), hAlign='c')
    self.pickAll = CheckBox(self, text='Pick All', checked=True, grid=(0, 0), hAlign='c')
    # self.pickStD = CheckBox(self, text='Pick References Only', checked=True, grid=(0, 1),)
    self.samplePullDown = PulldownList(self, grid=(0, 1), hAlign='l')
    self.referenceComponentPullDown = PulldownList(self, grid=(0, 2), hAlign='l')
    self._populatePullDowns()

  def _pickPeaks(self):
    for sample in self.project.samples:
      if hasattr(sample, 'minScore'):
        pass
      else:
        for spectrum in sample.spectra:
         spectrum.peakLists[0].pickPeaks1dFiltered(size=9, ignoredRegions=None, noiseThreshold=0)
        for sampleComponent in sample.sampleComponents:
          sampleComponent.substance.referenceSpectra[0].peakLists[0].pickPeaks1dFiltered(ignoredRegions=None, noiseThreshold=0)

  def _populatePullDowns(self):
    if len(self.project.samples)>0:
      samplesData = []
      for sample in self.project.samples:
        if hasattr(sample, 'minScore'):
          pass
        else:
          samplesData.append([str(spectrum.id) for spectrum in sample.spectra])
      self.samplePullDown.setData(samplesData[0])

    if len(self.project.substances)>0:
      substanceData =[]
      for substance in self.project.substances:
        substanceData.append(str(substance.referenceSpectra[0].id))
      self.referenceComponentPullDown.setData(substanceData)

class MatchPeaks(QtGui.QWidget):
  ''''''

  def __init__(self, parent=None, project=None, **kw):
    QtGui.QWidget.__init__(self, parent)

    self.project = project
    if len(self.project.windows)>0:
     self.mainWindow = self.project.windows[0]
    self.screeningSettingModule = parent.parent()

    self.minimumDistanceValue = str(0.005)


    self.matchPositionsButton = Button(self, text = 'Match', callback=self._matchPosition,
                                       grid=(0, 4), hAlign='c')

    # self.minimumPeaksLabel = Label(self, text='Minimum Peaks', hAlign='l', grid=(0, 2))
    self.minimumDistanceLabel = Label(self, text='Minimum Distance (ppm)', hAlign='c', grid=(0, 0))
    self.minimumDistanceLine = LineEdit(self, text=self.minimumDistanceValue,  hAlign='c', grid=(0, 1))
    self.minimumDistanceLine.setMaximumWidth(100)


    # self.minimumPeaksLabel = Label(self, text='Minimum Peaks', hAlign='l', grid=(0, 2))
    # self.minimumPeaksBox = Spinbox(self, value=1, min=1,  hAlign='l', grid=(0, 3))



  def _matchPosition(self):
    # print(self.sender().parent().parent().parent().parent().parent().parent().parent())
    for sample in self.project.samples:
      if hasattr(sample, 'minScore'):
        pass
      else:
        componentList = []

        spectrumOffResonancePeaks = [peak for peak in sample.spectra[0].peakLists[0].peaks]
        spectrumOffPeaksPosition =[peak.position[0] for peak in spectrumOffResonancePeaks]

        spectrumOnResonancePeaks = [peak for peak in sample.spectra[1].peakLists[0].peaks]
        spectrumOffPeaksPosition =[peak.position[0] for peak in spectrumOnResonancePeaks]

        stdPeakList =  [peak for peak in sample.spectra[2].peakLists[0].peaks]
        stdPosition =[peak.position[0] for peak in stdPeakList]

        for sampleComponent in sample.sampleComponents:
          componentPeakList = [peak for peak in sampleComponent.substance.referenceSpectra[0].peakLists[0].peaks]
          componentPosition = [peak.position[0] for peak in componentPeakList]
          componentDict = {sampleComponent:componentPosition}
          componentList.append(componentDict)
          newPeakList = sampleComponent.substance.referenceSpectra[0].newPeakList()

        for components in componentList:
          for sampleComponent, peakPositions in components.items():
            match = matchedPosition(stdPosition, peakPositions, tolerance=float(self.minimumDistanceLine.text()), minimumMatches=1)#self.minimumPeaksBox.value())
            if match is not None:
              newHit = sample.spectra[0].newSpectrumHit(substanceName=str(sampleComponent.name))
              for position in match:

                newPeakListPosition = sampleComponent.substance.referenceSpectra[0].peakLists[1].newPeak(position=[position], height=0.00)

              merit = self._stdEfficency(spectrumOffResonancePeaks, spectrumOnResonancePeaks, stdPosition)
              if len(merit)>0:
                newHit.meritCode =  str(merit[0])+'%'
    self._showHitsModule()



  def _showHitsModule(self):
    # self.screeningSettingModule.close()
    showScreeningHits = ShowScreeningHits(parent=self.mainWindow, project=self.project)
    # if self._appBase.ui.mainWindow is not None:
    #   self.mainWindow = self._appBase.ui.mainWindow
    # else:
    #   self.mainWindow = self._appBase._mainWindow
    showScreeningHitsModule = self.mainWindow.moduleArea.addModule(showScreeningHits, position='bottom')
    spectrumDisplay = self.mainWindow.createSpectrumDisplay(self.project.spectra[0])

    self.mainWindow.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=showScreeningHitsModule)
    self.mainWindow.moduleArea.guiWindow.deleteBlankDisplay()

    self.project.strips[0].viewBox.autoRange()

    currentDisplayed = self.project.strips[0]
    for spectrumView in currentDisplayed.spectrumViews:
      spectrumView.delete()


  def _stdEfficency(self, spectrumOffResonancePeaks, spectrumOnResonancePeaks, matchedPositions):

    efficiency = []
    for position in matchedPositions:
      for onResPeak in spectrumOnResonancePeaks:
        for offResPeak in spectrumOffResonancePeaks:
          if abs(offResPeak.position[0] - onResPeak.position[0]) <= 0.001 and offResPeak.position[0] == position:
            differenceHeight = abs(offResPeak.height - onResPeak.height)
            fullValue = ((abs(offResPeak.height - onResPeak.height))/offResPeak.height)*100
            value = decimal.Decimal(fullValue).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            efficiency.append(value)
    # print(efficiency)
    return efficiency



class ExcludeBaselinePoints(QtGui.QWidget, Base):
  def __init__(self, parent, project, spectra=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.pointLabel = Label(self, 'Exclusion Points ', grid=(0, 0))
    self.pointBox1 = Spinbox(self, grid=(0, 1), max=100000000000, min=-100000000000)
    self.pointBox2 = Spinbox(self, grid=(0, 2), max=100000000000, min=-100000000000)
    self.current = project._appBase.current
    self.pickOnSpectrumButton = Button(self, grid=(0, 3), toggle=True, icon='icons/target3+',hPolicy='fixed')
    self.pickOnSpectrumButton.setChecked(False)
    self.multiplierLabel = Label(self, 'Baseline Multipler', grid=(0, 4))
    self.multiplierBox = DoubleSpinbox(self, grid=(0, 5))
    self.pickOnSpectrumButton.toggled.connect(self._togglePicking)
    self.linePoint1 = pg.InfiniteLine(angle=0, pos=self.pointBox1.value(), movable=True, pen=(255, 0, 100))
    self.linePoint2 = pg.InfiniteLine(angle=0, pos=self.pointBox2.value(), movable=True, pen=(255, 0, 100))
    if self.current.strip is not None:
      self.current.strip.plotWidget.addItem(self.linePoint1)
      self.current.strip.plotWidget.addItem(self.linePoint2)
      self.pointBox1.setValue(self.linePoint1.pos().y())
      self.pointBox2.setValue(self.linePoint2.pos().y())
      self.linePoint1.hide()
      self.linePoint1.sigPositionChanged.connect(partial(self._lineMoved, self.pointBox1, self.linePoint1))
      self.linePoint2.hide()
      self.linePoint2.sigPositionChanged.connect(partial(self._lineMoved, self.pointBox2, self.linePoint2))
      self.pointBox1.valueChanged.connect(partial(self._setLinePosition, self.linePoint1, self.pointBox1))
      self.pointBox2.valueChanged.connect(partial(self._setLinePosition, self.linePoint2, self.pointBox2))

  def _togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self._turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self._turnOffPositionPicking()

  def _turnOnPositionPicking(self):
    # print('picking on')
    self.linePoint1.show()
    self.linePoint2.show()

  def _turnOffPositionPicking(self):
    # print('picking off')
    # print(self.pointBox1.value(), self.pointBox2.value())
    self.linePoint1.hide()
    self.linePoint2.hide()

  def _lineMoved(self, box, linePoint):
    box.setValue(linePoint.pos().y())

  def _setLinePosition(self, linePoint, pointBox):
    linePoint.setPos(pointBox.value())

  def _getParams(self):

    return {'function': 'excludeBaselinePoints',
            'baselineRegion': [self.pointBox1.value(), self.pointBox2.value()],
            'baselineMultiplier': self.multiplierBox.value()}
