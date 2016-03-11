__author__ = 'luca'


from functools import partial
import numpy as np
from PyQt4 import QtCore, QtGui
from pandas import DataFrame

from ccpncore.gui.Base import Base
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Button import Button
from ccpncore.gui.Spinbox import Spinbox
from ccpncore.gui.FileDialog import FileDialog

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles
from application.core.popups.SampleSetupPopup import solvents, SamplePopup, ExcludeRegions
from application.core.lib.Window import navigateToNmrResidue, navigateToPeakPosition

Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

experimentType = ["STD.H", "T2-filtered.H", "Water-LOGSY.H",  "H", "Other"]
# what about: SLAPSTIC, TINS, Tr-NOEs, NOE Pumping


multiselection = ["Select an option to display", "Minimum change with protein",
                  "Maximum change with protein", "Average change with protein",]
                  # "Minimum change with protein and inhibitor",
                  # "Maximum change with protein and inhibitor",
                  # "Average change with protein and inhibitor"]

class ScreeningSetup(CcpnDock, Base):

  def __init__(self, project, **kw):
    super(ScreeningSetup, self)
    CcpnDock.__init__(self, name='Screening')
    self.project = project
    self.smiles = ''
    self.compound = None
    self.variant = None
    self.samples = self.project.samples
    self.colourScheme = self.project._appBase.preferences.general.colourScheme

    # Three different areas:
    # 1st Area: General screening Setting Widgets,
    # 2nd Area: Table1: samples/hit count; Table2: hits analysis.
    # 3th Area: peaks analysis and molecule view.

    # 1st Area:
    self.settingArea = ScrollArea(self)
    self.setOrientation('vertical', force=True)
    self.settingArea.setWidgetResizable(True)
    self.settingArea.setMaximumSize(300,920)
    self.settingAreaWidget = QtGui.QWidget()
    self.settingArea.setWidget(self.settingAreaWidget)
    self.layout.addWidget(self.settingArea, 0, 0, 9, 1)
    self.settingArea.setStyleSheet("border-style: outset; border-width: 0px; border-color: beige;""border-radius: 1px;")
    # 2nd Area:
    self.tablesArea = ScrollArea(self)
    self.tablesArea.setStyleSheet("border-style: outset; border-width: 1px; border-color: beige;""border-radius: 1px;")
    self.tablesArea.setWidgetResizable(True)
    self.table1AreaWidget = QtGui.QWidget()
    self.tablesArea.setWidget(self.table1AreaWidget)
    self.layout.addWidget(self.tablesArea, 0, 1, 1, 4)

    # 3th Area
    self.peaksMoleculeArea = ScrollArea(self)
    self.peaksMoleculeArea.setStyleSheet("border-style:outset;border-width: 1px; border-color: beige;""border-radius: 1px;")
    self.peaksMoleculeArea.setWidgetResizable(True)
    self.peaksMoleculeAreaWidget = QtGui.QWidget()
    self.peaksMoleculeArea.setWidget(self.peaksMoleculeAreaWidget)
    self.layout.addWidget(self.peaksMoleculeArea, 6, 1, 1, 4)

  ## 1st Area: General screening Settings
    pulldownExpTypeLabel = Label(self.settingAreaWidget, text="ExpType:", grid=(0, 0), hAlign='l')
    self.pulldownExpType = PulldownList(self.settingAreaWidget, grid=(0, 1))
    self.pulldownExpType.setFixedWidth(108)
    self.pulldownExpType.setData(experimentType)

    # efficency
    efficencyLabel = Label(self.settingAreaWidget, text="Height", grid=(2, 0), hAlign='l')
    self.efficiency = DoubleSpinbox(self.settingAreaWidget, grid=(2, 1), hAlign='l')
    self.efficiency.setFixedWidth(105)
    self.efficiency.setMaximum(100000000000000000)

    # matchPeak
    matchPeakLabel = Label(self.settingAreaWidget, text="Matching peaks:", grid=(3, 0), hAlign='l')
    self.matchPeak = DoubleSpinbox(self.settingAreaWidget, grid=(3, 1))
    self.matchPeak.setFixedWidth(105)
    self.matchPeak.setRange(0.00, 1)
    self.matchPeak.setValue(0.01)
    self.matchPeak.setSingleStep(0.01)
    self.matchPeak.setSuffix(" ppm")

    # numOfPeaks
    numOfPeaksLabel = Label(self.settingAreaWidget, text="Num of peaks", grid=(4, 0), hAlign='l')
    self.numOfPeaks = Spinbox(self.settingAreaWidget, grid=(4, 1))
    self.numOfPeaks.setFixedWidth(105)
    self.numOfPeaks.setValue(4)

    # noise
    noiseLabel = Label(self.settingAreaWidget, text="Noise threshold", grid=(5, 0), hAlign='l')
    self.noise = DoubleSpinbox(self.settingAreaWidget, grid=(5, 1), hAlign='l')
    self.noise.setFixedWidth(105)
    self.noise.setMaximum(100000000000000000)

    # compare Peaks by Height
    self.comparePeaksLabel = Label(self.settingAreaWidget, text="Compare Peaks by", grid=(6, 0), hAlign='l')
    self.comparePeaksHeightLabel = Label(self.settingAreaWidget, text="Height", grid=(6, 1), hAlign='l')
    self.comparePeaksHeightCheckBox = CheckBox(self.settingAreaWidget, grid=(6, 1), hAlign='c', checked=True)
    self.comparePeaksHeightCheckBox.toggled.connect(self.compareByHeightIsChecked)

    # compare Peaks by Volume
    self.comparePeaksVolumeLabel = Label(self.settingAreaWidget, text="Volume", grid=(7, 1), hAlign='l')
    self.comparePeaksVolumeCheckBox = CheckBox(self.settingAreaWidget, grid=(7, 1), hAlign='c', checked=False)
    self.comparePeaksVolumeCheckBox.toggled.connect(self.compareByVolumeIsChecked)

    # exclude Regions
    self.excludeRegions =  ExcludeRegions(self.settingAreaWidget, grid=(8, 0), gridSpan=(8,0))

    # perform button
    self.performButton = Button(self.settingAreaWidget, grid=(20, 0), gridSpan=(1,0), hAlign='c', text='Perform', callback=self.perform)
    self.performButton.setMinimumSize(90, 30)


  ## 2nd Area widgets:

    # Show Only Hits
    self.displayHitOnlyLabel = Label(self.table1AreaWidget, text="Show Only Hits", grid=(0, 0), hAlign='l')
    self.displayHitOnlyCheckBox = CheckBox(self.table1AreaWidget, grid=(0, 0), hAlign='r', checked=False)
    self.displayHitOnlyCheckBox.toggled.connect(self.displayHitOnly)


    # Table1: samples/hit count
    self.listOfSample = []
    for sample in self.project.samples:

        self.listOfSample.append(sample)

    columns = [Column('STD On', lambda sample:str(sample.spectra[0].pid)),
               Column('STD Off', lambda sample:str(sample.spectra[1].pid)),
               Column('Sample', lambda sample:str(sample.name)),
               Column('Hits', lambda sample:str(len(sample.spectrumHits)))]

    self.screenTable = ObjectTable(self.table1AreaWidget, columns, callback=partial(self.hitsTable), objects=[], grid=(1, 0))


    # Multiselection
    self.pulldownMultiselection = PulldownList(self.table1AreaWidget, grid=(0, 1))
    self.pulldownMultiselection.setData(multiselection)
    self.pulldownMultiselection.activated[str].connect(self.pulldownMultiselectionChanged)

    # Table2: Analysis hits
    self.hitAnalysisList = []
    columnsHit= [Column('Substance',lambda hit:str(hit.substanceName)),
               Column('Status', lambda hit:str(hit.meritCode)),
               Column('Scoring', lambda hit:str(hit.figureOfMerit))]

    self.hitAnalysisTable2 = ObjectTable(self.table1AreaWidget, columnsHit,
                               callback=self.showMolecule, objects=[],
                               grid=(1, 1))


  ## 3th Area: peaks analysis and molecule view.

    # Labels
    self.referenceTableLabel = Label(self.peaksMoleculeAreaWidget, text="Matched Peaks", grid=(1, 0), hAlign='c')

    self.moleculeLabel = Label(self.peaksMoleculeAreaWidget, text="Molecule View", grid=(1, 3), hAlign='c')

    # table: peaks analysis
    self.referenceList = []

    columnsReference= [Column('Number','serial'),
              Column('Matched Positions',  lambda peak: '%.3f' % peak.position[0]),
              Column('Diff Height Off-On', lambda peak: peak.height),
             ]

    self.referenceTable = ObjectTable(self.peaksMoleculeAreaWidget, columnsReference,
                                 callback=self.showPeaks, objects=[], grid=(2, 0), gridSpan=(3,1))

    self.referenceTable.setMinimumSize(350,100)
    self.referenceTable.setMaximumSize(400,200)

    # Molecule view
    self.compoundView = CompoundView(self.peaksMoleculeAreaWidget,  grid=(2,2), gridSpan=(3,3), hAlign='c',
                                      preferences=self.project._appBase.preferences.general)
    self.compoundView.setMinimumSize(350,100)
    self.compoundView.setMaximumSize(400,200)
    if self.colourScheme == 'dark':
      self.compoundView.setStyleSheet(""" background-color:  #001044;""")
    else:
      self.compoundView.setStyleSheet(""" background-color:  #A9BCF5;""")


    # Export Button
    self.exportButton = Button(self.peaksMoleculeAreaWidget, grid=(7, 2), hAlign='r',
                                     text='Export results', callback= self.exportToXls)

    # menuExportButton = QtGui.QMenu(self)
    # menuExportButton.addAction('PDF')
    # menuExportButton.addAction('Lookup')
    # menuExportButton.addAction('Print')
    # self.exportButton.setMenu(menuExportButton)


  def compareByHeightIsChecked(self):
    if self.comparePeaksHeightCheckBox.isChecked():
      self.comparePeaksVolumeCheckBox.setChecked(False)
    else:
      self.comparePeaksHeightCheckBox.setChecked(False)
      self.comparePeaksVolumeCheckBox.setChecked(True)

  def compareByVolumeIsChecked(self):
    if self.comparePeaksVolumeCheckBox.isChecked():
      self.comparePeaksHeightCheckBox.setChecked(False)
    else:
      self.comparePeaksVolumeCheckBox.setChecked(False)
      self.comparePeaksHeightCheckBox.setChecked(True)


  def perform(self):
    '''
    STD only.
    Pick peaks, user decides when two peaks can be considered the same (reference vs sample) by the position.
    When defined as same, calculate the difference in height.
    '''
    self.settingArea.hide()
    excludedRegions = []
    noiseThreshold = self.noise.value()
    # self.matching = self.matchPeak.value()
    self.minNPeak =  self.numOfPeaks.value()
    self.minIntesityChange =  self.efficiency.value()


    for comboboxPair in (self.excludeRegions.comboBoxes):

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

    for sample in self.samples:  #  pick and filter the peaks in each sampleComponent and sample.
      for spectrum in sample.spectra:
        spectrum.peakLists[0].pickPeaks1dFiltered(ignoredRegions=excludedRegions, noiseThreshold=noiseThreshold)
      for sc in sample.sampleComponents:
        sc.substance.referenceSpectra[0].peakLists[0].pickPeaks1dFiltered(ignoredRegions=excludedRegions, noiseThreshold=noiseThreshold)

      matchedStdOffPeak = []
      matchedStdOnPeak = []


      stdOffPeaks = [stdOffPeak for stdOffPeak in sample.spectra[0].peakLists[0].peaks]
      stdOnPeaks = [stdOnPeak for stdOnPeak in sample.spectra[1].peakLists[0].peaks]

      components = [component for component in sample.sampleComponents]
      for stdOffPeak  in stdOffPeaks:
        for stdOnPeak in stdOnPeaks:
          if abs(stdOffPeak.position[0] - stdOnPeak.position[0]) <= 0.01 \
            and abs(stdOffPeak.height - stdOnPeak.height) > 25000000:
            matchedStdOffPeak.append(stdOffPeak)
            matchedStdOnPeak.append(stdOnPeak)





      for component in components:
        peakList = []
        for peak in component.substance.referenceSpectra[0].peakLists[0].peaks:
          peakList.append(peak.position[0])
        newPeakPositionsSampleComponents = list(self.nearPeaks(peakList))
        offPositions = [stdOff.position[0] for stdOff in matchedStdOffPeak]
        # offPositions2 = [(stdOff.pid, stdOff.position[0]) for stdOff in matchedStdOffPeak]
        # for i, stdOff in enumerate(matchedStdOffPeak):
        #   print((stdOff.height - matchedStdOnPeak[i].height)/stdOff.height, component)

        peakList2 = component.substance.referenceSpectra[0].peakLists[0]
        self.matching = self.matchPeak.value()
        # from sklearn import svm
        # import numpy
        # clf = svm.SVC()
        # positions = numpy.array([peak.position for peak in peakList2.peaks])
        # labels = numpy.array([peak.pid for peak in peakList2.peaks])
        # clf.fit(positions, labels)
        # tol = 0.008
        # for position in offPositions2:
        #   result = clf.predict(numpy.array(position[1]))
        #   matchedPosition = self.project.getByPid(result[0]).position
        #   if abs(matchedPosition[0]-position[1]) < tol:
        #     print(matchedPosition[0]-position[1], result[0], position[0])

        matchedPositions = [offPosition for scPosition in newPeakPositionsSampleComponents
                            for offPosition in offPositions if abs(offPosition-scPosition)<=0.025]

        newPeakList = component.substance.referenceSpectra[0].newPeakList(name='1HmatchedStdOffResonance')

        differenceHeightList = []
        efficiency = []

        positions = []

        for position in set(list(matchedPositions)):
          for stdOffPosition in set(list(matchedStdOffPeak)):
            for stdOnPosition in set(list(matchedStdOnPeak)):
              if abs(stdOffPosition.position[0] - stdOnPosition.position[0]) <= 0.01 and stdOffPosition.position[0] == position:
                differenceHeight = abs(stdOffPosition.height - stdOnPosition.height)
                eff = (abs(stdOffPosition.height - stdOnPosition.height))/stdOffPosition.height
                efficiency.append(eff)

                differenceHeightList.append(differenceHeight)

                newPeakListPosition = component.substance.referenceSpectra[0].peakLists[1].newPeak(position=[position], height=differenceHeight)

        if len(differenceHeightList)>1:
         minimumIntensityChange =  np.amin(differenceHeightList)
         meanIntensityChange = np.mean(differenceHeightList)
         maxIntensityChange = np.amax(differenceHeightList)

         if len(set(matchedPositions)) >= 4:
          substance = component.substance
          self.hit = sample.spectra[0].newSpectrumHit(substanceName=str(substance.name))
          self.hit.meritCode = 'Binding'
          self.scoringStd(self.hit, meanIntensityChange)
          print(efficiency, component)



      self.screenTable.setObjects(self.listOfSample)

  def nearPeaks(self, peaks):
    '''
    lists peaks within 0.03 ppm and returns their mean

    '''
    prev = None
    group = []
    for item in peaks:
      if not prev or abs(item - prev) <= 0.03:
        group.append(item)
      else:
        yield np.mean(group)
        group = [item]
      prev = item
    if group:
      yield np.mean(group)

  def pulldownMultiselectionChanged(self):
    print(self.pulldownMultiselection.getText())


  def scoringStd(self, hit, meanIntensityChange):

    if self.pulldownMultiselection.getSelected()[0] == "Select an option to display":
     try:
      if meanIntensityChange >= 200000000:
        self.hit.figureOfMerit = 0.9
        return self.hit.figureOfMerit

      if 180000000 <= meanIntensityChange < 200000000:
        self.hit.figureOfMerit = 0.8
        return self.hit.figureOfMerit

      if 170000000 <= meanIntensityChange < 180000000:
        self.hit.figureOfMerit = 0.7
        return self.hit.figureOfMerit

      if 160000000 <= meanIntensityChange < 170000000:
        self.hit.figureOfMerit = 0.6
        return self.hit.figureOfMerit

      if 150000000 <= meanIntensityChange < 160000000:
        self.hit.figureOfMerit = 0.5
        return self.hit.figureOfMerit

      if 140000000 <= meanIntensityChange < 150000000:
        self.hit.figureOfMerit = 0.4
        return self.hit.figureOfMerit

      if 130000000 <= meanIntensityChange < 140000000:
        self.hit.figureOfMerit = 0.3
        return self.hit.figureOfMerit

      if 120000000 <= meanIntensityChange < 130000000:
        self.hit.figureOfMerit = 0.2
        return self.hit.figureOfMerit

      if meanIntensityChange < 120000000:
        self.hit.figureOfMerit = 0.1
        return self.hit.figureOfMerit
     except:
      pass

  def minScoring(self, hit, minIntensityChange):
    try:
      if minIntensityChange >= 20000000:
        self.hit.figureOfMerit = 0.9

      if 18000000 <= minIntensityChange < 20000000:
        self.hit.figureOfMerit = 0.8

      if 17000000 <= minIntensityChange < 18000000:
        self.hit.figureOfMerit = 0.7

      if 16000000 <= minIntensityChange < 17000000:
        self.hit.figureOfMerit = 0.6

      if 15000000 <= minIntensityChange < 16000000:
        self.hit.figureOfMerit = 0.5

      if 14000000 <= minIntensityChange < 15000000:
        self.hit.figureOfMerit = 0.4

      if 13000000 <= minIntensityChange < 14000000:
        self.hit.figureOfMerit = 0.3

      if 12000000 <= minIntensityChange < 13000000:
        self.hit.figureOfMerit = 0.2

      if minIntensityChange < 12000000:
        self.hit.figureOfMerit = 0.1
    except:
      pass

  def maxScoring(self, hit, maxIntensityChange):
    print(maxIntensityChange)
    try:
      if maxIntensityChange >= 200000000:
        self.hit.figureOfMerit = 0.9

      if 180000000 <= maxIntensityChange < 200000000:
        self.hit.figureOfMerit = 0.8

      if 170000000 <= maxIntensityChange < 180000000:
        self.hit.figureOfMerit = 0.7

      if 160000000 <= maxIntensityChange < 170000000:
        self.hit.figureOfMerit = 0.6

      if 150000000 <= maxIntensityChange < 160000000:
        self.hit.figureOfMerit = 0.5

      if 140000000 <= maxIntensityChange < 150000000:
        self.hit.figureOfMerit = 0.4

      if 130000000 <= maxIntensityChange < 140000000:
        self.hit.figureOfMerit = 0.3

      if 120000000 <= maxIntensityChange < 130000000:
        self.hit.figureOfMerit = 0.2

      if maxIntensityChange < 120000000:
        self.hit.figureOfMerit = 0.1
    except:
      pass

  def hitsTable(self, row:int=None, col:int=None, obj:object=None):
    '''

    '''
    objectTable = self.screenTable
    sample = objectTable.getCurrentObject()
    hit = sample.spectrumHits
    self.hitAnalysisList.append(hit)
    self.hitAnalysisTable2.setObjects(self.hitAnalysisList[-1])
    self.referenceTable.setObjects([])

  def showMolecule(self, row:int=None, col:int=None, obj:object=None):
    '''

    '''
    # Extra hit widget
    self.hitIsConfirmedLabel = Label(self.peaksMoleculeAreaWidget, text="Hit confirmed?", grid=(1, 1), hAlign='c')
    self.hitIsConfirmed = PulldownList(self.peaksMoleculeAreaWidget,  grid=(2, 1))
    self.hitIsConfirmed.setData(['-','Yes', 'No'])
    self.hitIsConfirmed.setFixedWidth(148)

    objectTable = self.hitAnalysisTable2
    hit = objectTable.getCurrentObject()
    substance = self.project.getByPid('SU:'+hit.substanceName+'.H')

    peaks = substance.referenceSpectra[0].peakLists[1].peaks

    self.referenceList.append(peaks)
    self.referenceTable.setObjects(self.referenceList[-1])

    self.peaksMoleculeArea.show()
    self.peaksMoleculeAreaWidget.show()

    self.smiles = substance.smiles
    compound = importSmiles(substance.smiles)
    variant = list(compound.variants)[0]
    self.setCompound(compound, replace = True)
    x, y = self.getAddPoint()
    variant.snapAtomsToGrid(ignoreHydrogens=False)


    self.compoundView.centerView()
    self.compoundView.resetView()
    self.compoundView.updateAll()

  def setCompound(self, compound, replace=True):
    ''' Set the compound on the graphic scene. '''
    if compound is not self.compound:
      if replace or not self.compound:
        self.compound = compound
        variants = list(compound.variants)
        if variants:
          for variant2 in variants:
            if (variant2.polyLink == 'none') and (variant2.descriptor == 'neutral'):
              variant = variant2
              break
          else:
            for variant2 in variants:
              if variant2.polyLink == 'none':
                variant = variant2
                break
            else:
              variant = variants[0]
        else:
          variant =  Variant(compound)
          print(variant)
        self.variant = variant
        self.compoundView.setVariant(variant)

      else:
        variant = list(compound.variants)[0]
        x, y = self.getAddPoint()
        self.compound.copyVarAtoms(variant.varAtoms, (x,y))
        self.compoundView.centerView()
        self.compoundView.updateAll()

  def getAddPoint(self):
    ''' Set the compound on the specific position on the graphic scene. '''
    compoundView = self.compoundView
    globalPos = QtGui.QCursor.pos()
    pos = compoundView.mapFromGlobal(globalPos)
    widget = compoundView.childAt(pos)
    if widget:
      x = pos.x()
      y = pos.y()
    else:
      x = compoundView.width()/2.0
      y = compoundView.height()/2.0
    point = compoundView.mapToScene(x, y)
    return point.x(), point.y()

  def _getPeakHeight(self, peak):
    if peak.height:
      return peak.height*peak.peakList.spectrum.scale

  def showPeaks(self, peak=None, row=None, col=None):
    '''

    '''

    objectTable = self.referenceTable
    objectpeak = objectTable.getCurrentObject()

    displayed = self.project.getByPid('GD:user.View.1D:H')

    if peak:
      navigateToPeakPosition(self.project, peak=peak, selectedDisplays=[displayed.pid], markPositions=True)


  def displayHitOnly(self):
    '''
    Show on the sampleTable only sample with hits on it
    '''
    newSampleObjectTable = []

    if self.displayHitOnlyCheckBox.isChecked():
      for sample in self.screenTable.objects:
        if len(sample.spectrumHits)>=1:
          newSampleObjectTable.append(sample)
      self.screenTable.setObjects(newSampleObjectTable)
    else:
      self.screenTable.setObjects(self.listOfSample)


  def exportToXls(self):
    ''' Export a simple xlxs file from the results '''
    self.nameAndPath = ''
    fType = 'XLS (*.xlsx)'
    dialog = FileDialog(self, fileMode=1, acceptMode=0, preferences=self.preferences, filter=fType)
    filePath = dialog.selectedFiles()[0]
    self.nameAndPath = filePath

    sampleColumn = [str(sample.pid) for sample in self.project.samples]
    sampleHits = [str(sample.spectrumHits) for sample in self.project.samples]
    df = DataFrame({'Mixture name': sampleColumn, 'Sample Hits': sampleHits})
    df.to_excel(self.nameAndPath, sheet_name='sheet1', index=False)