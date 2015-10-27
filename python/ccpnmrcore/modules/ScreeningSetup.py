__author__ = 'luca'

import sys
from PyQt4 import QtCore, QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.Label import Label
from ccpncore.gui.ScrollArea import ScrollArea
from ccpncore.gui.Button import Button
from ccpncore.gui.Spinbox import Spinbox

from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.DoubleSpinbox import DoubleSpinbox
from ccpncore.gui.CheckBox import CheckBox
from ccpncore.gui.Table import ObjectTable, Column
from ccpncore.gui.CompoundView import CompoundView, Variant, importSmiles
from ccpnmrcore.popups.SampleSetupPopup import solvents, SamplePopup, ExcludeRegions
Qt = QtCore.Qt
Qkeys = QtGui.QKeySequence

experimentType = ["STD.H", "T2-filtered.H", "Water-LOGSY.H",  "H", "Other"]
# what about: SLAPSTIC, TINS, Tr-NOEs, NOE Pumping


multiselection = ["Select an option to display", "Minimum change with protein",
                  "Maximum change with protein", "Average change with protein",
                  "Minimum change with protein and inhibitor",
                  "Maximum change with protein and inhibitor",
                  "Average change with protein and inhibitor"]

class ScreeningSetup(CcpnDock, Base):

  def __init__(self, project, **kw):
    super(ScreeningSetup, self)
    CcpnDock.__init__(self, name='Screening')
    self.project = project
    self.smiles = ''

    # Setting for four different areas where to fit properly the widgets
    self.scrollArea1 = ScrollArea(self)

    self.scrollArea1.setWidgetResizable(True)
    self.scrollArea1.setMaximumSize(2000,220)
    self.scrollAreaWidgetContents = QtGui.QWidget()
    self.scrollArea1.setWidget(self.scrollAreaWidgetContents)
    self.layout.addWidget(self.scrollArea1, 0, 0, 1, 0)
    self.scrollArea1.setStyleSheet(" border-style: outset; border-width: 0px; border-color: beige;"
                                   "border-radius: 1px;  ")

    self.scrollArea2 = ScrollArea(self)
    self.scrollArea2.setStyleSheet(" border-style: outset; border-width: 1px; border-color: beige;"
                                   "border-radius: 1px;  ")
    self.scrollArea2.setWidgetResizable(True)
    self.scrollAreaWidgetContents2 = QtGui.QWidget()
    self.scrollArea2.setWidget(self.scrollAreaWidgetContents2)
    self.layout.addWidget(self.scrollArea2, 3, 0, 6, 4)

    self.scrollArea3 = ScrollArea(self)
    self.scrollArea3.setStyleSheet(" border-style: outset; border-width: 1px; border-color: beige;"
                                   "border-radius: 1px;  ")
    self.scrollArea3.setWidgetResizable(True)
    self.scrollAreaWidgetContents3 = QtGui.QWidget()
    self.scrollArea3.setWidget(self.scrollAreaWidgetContents3)
    self.layout.addWidget(self.scrollArea3, 3, 4, 6, 4)

    self.scrollArea4 = ScrollArea(self)
    self.scrollArea4.setStyleSheet(" border-style: outset; border-width: 1px; border-color: beige;"
                                   "border-radius: 1px;  ")
    self.scrollArea4.setWidgetResizable(True)
    self.scrollAreaWidgetContents4 = QtGui.QWidget()
    self.scrollArea4.setWidget(self.scrollAreaWidgetContents4)
    self.layout.addWidget(self.scrollArea4, 9, 0, 2, 0)
    self.scrollArea4.hide()
    self.scrollAreaWidgetContents4.hide()
    self.excludeRegions =  ExcludeRegions(self.scrollAreaWidgetContents, grid=(3, 1), gridSpan=(3,3))
    self.excludeRegions.hide()


    # Widget in the first scrolling area.
    pulldownExpTypeLabel = Label(self.scrollAreaWidgetContents, text="ExpType:", grid=(0, 0), hAlign='r')
    self.pulldownExpType = PulldownList(self.scrollAreaWidgetContents, grid=(0, 1))
    self.pulldownExpType.setData(experimentType)

    efficencyLabel = Label(self.scrollAreaWidgetContents, text="Efficency", grid=(0, 2), hAlign='r')
    self.efficiency = Spinbox(self.scrollAreaWidgetContents, grid=(0, 3), hAlign='l')
    self.efficiency.setSuffix(" %")

    numOfPeaksLabel = Label(self.scrollAreaWidgetContents, text="Num of peaks", grid=(0, 4), hAlign='r')
    self.numOfPeaks = Spinbox(self.scrollAreaWidgetContents, grid=(0, 5))


    noiseLabel = Label(self.scrollAreaWidgetContents, text="Noise threshold", grid=(0, 6), hAlign='r')
    self.noise = DoubleSpinbox(self.scrollAreaWidgetContents, grid=(0, 7), hAlign='l')
    self.noise.setMaximum(10000000)

    # perform button
    self.performButton = Button(self.scrollAreaWidgetContents, grid=(0, 9), hAlign='l', text='Perform', callback=self.perform)
    self.performButton.setMinimumSize(90,50)
    self.moreButton = Button(self.scrollAreaWidgetContents, grid=(0, 8), hAlign='l', text='More Options')
    self.moreButton.setCheckable(True)
    self.moreButton.clicked[bool].connect(self.moreSetting)

    # Widget in the second scrolling area (First Table).
    # Hit Only CheckBox
    self.displayHitOnlyLabel = Label(self.scrollAreaWidgetContents2, text="Show Only Hits", grid=(0, 0), hAlign='l')
    self.displayHitOnlyCheckBox = CheckBox(self.scrollAreaWidgetContents2, grid=(0, 0), hAlign='c', checked=True)

    # Hit Table
    test = []
    for sample in self.project.samples:
      if len(sample.spectra) > 1:
        test.append(sample)

    columns = [Column('Reference', lambda sample:str(sample.pid)),
               Column('Sample', lambda sample:str(sample.pid)),
               Column('Efficiency', lambda sample: int(sample.minScore)),
               Column('Hits',lambda sample: (int(len(sample.peakCollections))))]

    screenTable = ObjectTable(self.scrollAreaWidgetContents2, columns, callback=None, objects=[], grid=(1, 0))
    screenTable.setObjects(test)

    # Widget in the third scrolling area.
    # Analysis hit table
    self.pulldownMultiselection = PulldownList(self.scrollAreaWidgetContents3, grid=(0, 0))
    self.pulldownMultiselection.setData(multiselection)


    hitAnalysisList = []
    columnsHit= [Column('Substance',''),
               Column('Status', ''),
               Column('Scoring', '')]

    hitAnalysisTable2 = ObjectTable(self.scrollAreaWidgetContents3, columnsHit,
                               callback=self.showPeaks, objects=[],
                               grid=(1, 0))
    hitAnalysisTable2.setObjects(hitAnalysisList)


    # this will be split again in 3 tables
    self.referenceTableLabel = Label(self.scrollAreaWidgetContents4, text="Peak List", grid=(1, 0), hAlign='c')

    referenceList = []
    columnsReference= [Column('Number',''),
              Column('Position', ''),
              Column('Height Ref', ''),
              Column('Height Sample', ''),
              Column('Diff Height', '')]

    referenceTable = ObjectTable(self.scrollAreaWidgetContents4, columnsReference,
                                 callback=None, objects=[], grid=(2, 0) )
    referenceTable.setObjects(referenceList)

    # showPeakList
    self.showPeakListButton = Button(self.scrollAreaWidgetContents3, grid=(3, 0), hAlign='l',
                                     text=' Show Hits PeakList and Structure')
    self.showPeakListButton.setCheckable(True)
    self.showPeakListButton.clicked[bool].connect(self.showPeakList)

    self.exportButton = Button(self.scrollAreaWidgetContents3, grid=(3, 0), hAlign='r',
                                     text='Export results')

    menuExportButton = QtGui.QMenu(self)
    menuExportButton.addAction('PDF')
    menuExportButton.addAction('Lookup')
    menuExportButton.addAction('Print')
    self.exportButton.setMenu(menuExportButton)

  # extra settings
  def moreSetting(self, pressed):

    if pressed:
      self.moreButton.setText('Hide more...')

      # excludeRegions
      self.excludeRegionsButton = Button(self.scrollAreaWidgetContents,text="Show Exclude Regions", grid=(3, 0), hAlign='r')
      self.excludeRegionsButton.setCheckable(True)
      self.excludeRegionsButton.clicked[bool].connect(self.showIgnoreRegions)

      # # comparePeaksHeightCheckBox
      self.comparePeaksLabel = Label(self.scrollAreaWidgetContents, text="Compare Peaks by", grid=(3, 4), hAlign='l')
      self.comparePeaksHeightLabel = Label(self.scrollAreaWidgetContents, text="Height", grid=(3, 5), hAlign='l')
      self.comparePeaksHeightCheckBox = CheckBox(self.scrollAreaWidgetContents, grid=(3, 5), hAlign='r', checked=True)
      self.comparePeaksHeightCheckBox.toggled.connect(self.compareByHeightIsChecked)

      # compare PeaksVolumeCheckBox
      self.comparePeaksVolumeLabel = Label(self.scrollAreaWidgetContents, text="Volume", grid=(3, 6), hAlign='l')
      self.comparePeaksVolumeCheckBox = CheckBox(self.scrollAreaWidgetContents, grid=(3, 6), hAlign='r', checked=False)
      self.comparePeaksVolumeCheckBox.toggled.connect(self.compareByVolumeIsChecked)

      ## Not For Now
      # matchPeakLabel = Label(self.scrollAreaWidgetContents, text="Matching peaks:", grid=(0, 2), hAlign='r')
      # self.matchPeak = DoubleSpinbox(self.scrollAreaWidgetContents, grid=(0, 3))
      # self.matchPeak.setRange(0.00, 1)
      # self.matchPeak.setSingleStep(0.01)
      # self.matchPeak.setSuffix(" ppm")

    else: # hide all extra setting widget
      self.moreButton.setText('Show more')
      self.comparePeaksLabel.hide()
      self.comparePeaksHeightLabel.hide()
      self.comparePeaksHeightCheckBox.hide()
      self.comparePeaksVolumeLabel.hide()
      self.comparePeaksVolumeCheckBox.hide()
      self.excludeRegionsButton.hide()
      self.showIgnoreRegions(pressed)

  def showIgnoreRegions(self, pressed): #from SampleSetupPopup
    if pressed:
      self.excludeRegionsButton.setText("Hide Exclude Regions")
      self.excludeRegions.show()

    else:
      self.excludeRegionsButton.setText("Show Exclude Regions")
      self.excludeRegions.hide()

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


  def showPeakList(self, pressed):

    if pressed:
      self.scrollArea4.show()
      self.scrollAreaWidgetContents4.show()

      self.showPeakListButton.setText('Hide Hits PeakList and Structure')
      self.moleculeStructureLabel = Label(self.scrollAreaWidgetContents4, text="Hit Structure", grid=(1, 3), hAlign='c')
      compoundView = CompoundView(self.scrollAreaWidgetContents4,  grid=(2, 3))
      self.compoundView = compoundView

    else:
      self.showPeakListButton.setText(' Show Hits PeakList and Structure')
      self.scrollArea4.hide()
      self.scrollAreaWidgetContents4.hide()


  def perform(self):
    pass

  def showPeaks(self):
    print('not yet')

