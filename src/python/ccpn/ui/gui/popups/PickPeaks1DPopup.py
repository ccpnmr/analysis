"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

import decimal
from functools import partial
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from collections import OrderedDict
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.SpectraSelectionWidget import SpectraSelectionWidget

Estimated = 'Estimated'
Manual = 'Manual'

class ExcludeRegions(Widget):
  '''This creates a widget group to exclude Regions from the Spectrum when automatically peak picking '''
  selectionLabelDefault = "Select Regions or \nsolvents to exclude"

  solvents = {'Acetic Acid-d4': [0, 0, 2.14, 2.0, 11.75, 11.65],
              'Acetone-d6 & Water': [0, 0, 2.15, 2.0, 2.90, 2.80],
              'Acetonitrile-d3 & water': [0, 0, 2.20, 1.94],
              'Benzene-d6 & water': [0, 0, 0.60, 0.50, 7.25, 7.15],
              'Chloroform-d': [0, 0, 1.60, 1.50, 7.35, 7.25],
              'Deuterium Oxide': [0, 0, 4.75, 4.65],
              'Dichloromethane-d2 & water': [0, 0, 1.60, 1.50, 5.42, 5.32],
              'Dimethyl Sulfoxide-d6': [0, 0, 2.60, 2.50, 3.40, 3.30],
              'Dimethylformamide-d7 & water': [0, 0, 8.11, 8.01, 2.99, 2.91, 2.83, 2.73, 3.60, 3.50],
              'p-Dioxane-d8 & water': [0, 0, 2.60, 2.50, 3.63, 3.50],
              'Tetrachloromethane-d2 & water': [0, 0, 1.70, 1.60, 6.10, 6.00],
              'Ethanol-d6 & water': [0, 0, 1.21, 1.11, 3.66, 3.56, 5.40, 5.29],
              'Methanol-d4': [0, 0, 3.40, 3.30, 4.90, 4.80],
              'Pyridine-d5 & water': [0, 0, 8.74, 8.84, 7.68, 7.58, 7.32, 7.22, 5.10, 5.00],
              'Trifluoroacetic acid-d': [0, 0, 11.60, 11.50],
              'Tetrahydrofuran-d8 & water': [0, 0, 3.68, 3.58, 2.60, 2.50, 1.83, 1.73],
              'New regions': [0, 0, 0.2, 0.1],
              'Toulene-d8 & water': [0, 0, 7.18, 6.98, 2.19, 2.09, 2.50, 2.40, 5.10, 5.00],
              'Trifluoroethanol-d3 & water': [0, 0, 5.12, 5.02, 3.98, 3.88],
              'Carbon Tetrachloride & water ': [0, 0, 1.20, 1.10],
              'Water': [0, 0, 5, 4.5]}

  def __init__(self, parent=None, selectionLabel=selectionLabelDefault, labelAlign='c',  **kwds):

    super().__init__(parent, setLayout=True, **kwds)

    self.pulldownSolvents = PulldownList(self, grid=(0, 1), headerText='-- Select --', hAlign=labelAlign)
    self.pulldownSolvents.select('Water')
    self.pulldownSolvents.activated[str].connect(self._addRegions)
    for solvent in sorted(self.solvents):
      self.pulldownSolvents.addItem(solvent)
    self.SolventsLabel = Label(self, selectionLabel, grid=(0, 0), hAlign=labelAlign)
    self.scrollArea = ScrollArea(self, setLayout=True, grid=(2, 0), gridSpan=(2,2))
    self.scrollArea.setWidgetResizable(True)
    self.scrollAreaWidgetContents = Frame(self, setLayout=True)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.regioncount = 0
    self.excludedRegions = []
    self.excludedSolvents = []
    self.comboBoxes = []

  def _addRegions(self, pressed):
    '''   '''

    widgetList = []
    for solvent in sorted(self.solvents):
      solventValues = [(),()]
      if pressed == ('%s' %solvent):
        solventValues[0] += (solvent,)
        self.solventType = Label(self.scrollAreaWidgetContents, text=solvent, grid=(self.regioncount,0))
        self.closebutton = Button(self.scrollAreaWidgetContents,'Remove from selection', grid=(self.regioncount,1),)#hAlign='l')
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
          self.spin = DoubleSpinbox(self.scrollAreaWidgetContents, grid=(self.position),)# hAlign='c')
          self.spin.setSingleStep(0.01)
          self.spin.setMinimum(-20)
          self.spin.setPrefix('ppm')
          self.spin.setValue(values)
          widgetList.append(self.spin)
          solventValues[1]+= (self.spin,)
      self.excludedSolvents.append(solventValues)
    self.comboBoxes.append(widgetList)
    self.closebutton.clicked.connect(partial(self._deleteRegions, self.positions))


  def getSolventsAndValues(self):
    self.excludedSolvents = [x for x in self.excludedSolvents if len(x[0])>0]
    solventsAndValues = []
    for item in self.excludedSolvents:
      try:
        solvent, widgets = item
        values = [round(widget.value(),2) for widget in widgets]
        values.insert(0, 0)
        values.insert(0, 0)
        solventsAndValues.append(((solvent[0]),values))
      except:
        pass
    return OrderedDict(solventsAndValues)

  def _getExcludedRegions(self):
    excludedRegions = []
    self.excludedSolvents = [x for x in self.excludedSolvents if len(x[0]) > 0]
    for item in self.excludedSolvents:
      solvent, widgets = item
      try: # try because widgets can be dinamically deleted
        self.values = [round(widget.value(), 2) for widget in widgets]
        pairedValues = list(self._chunks(self.values, 2))
        excludedRegions.append(pairedValues)
      except:
        pass
    if len(excludedRegions)>0:
      return [item for sublist in excludedRegions for item in sublist]

  def _set(self):
    pass
    # import  copy
    # originalSolvents = copy.deepcopy(self.solvents)
    # for solvent in sorted(self.params.keys()):
    #   try:
    #     self.solvents = self.params
    #     self._addRegions(solvent)
    #   except:
    #     pass
    # self.solvents = originalSolvents

  def _chunks(self, l, n):
    """Yield successive n-sized chunks from list. Needed this format!"""
    for i in range(0, len(l), n):
      yield sorted(l[i:i + n], key=float, reverse=True)

  def _deleteRegions(self, positions):
    '''   '''
    for position in positions:
      widget1 = self.scrollAreaWidgetContents.layout().itemAtPosition(*position).widget()
      if widget1 is self.solventType:
        widget1.hide()
      else:
        widget1.deleteLater()


class PickPeak1DPopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None, title='Pick 1D Peak', **kwds):
    CcpnDialog.__init__(self, parent, setLayout=False, windowTitle=title, **kwds)

    self.mainWindow = mainWindow
    if self.mainWindow is None: #This allows opening the popup for graphical tests
      self.project = None
    else:
      self.project = self.mainWindow.project
      self.application = self.mainWindow.application

    self._setMainLayout()
    self._setTabs()
    self._setWidgets()
    self._addWidgetsToLayout()

  def _setMainLayout(self):
    self.mainLayout = QtWidgets.QGridLayout()
    self.setLayout(self.mainLayout)
    self.resize(300, 400)

  def _setTabs(self):
    self.tabWidget = QtWidgets.QTabWidget()
    self.tabGeneralSetup = Frame(self, setLayout=False)
    self.tabGeneralSetupLayout = QtWidgets.QGridLayout()
    self.tabGeneralSetup.setLayout(self.tabGeneralSetupLayout)
    self.excludedRegionsTab = ExcludeRegions(self)
    self.tabWidget.addTab(self.tabGeneralSetup, 'General')
    self.tabWidget.addTab(self.excludedRegionsTab, 'Exclude Regions')


  def _setWidgets(self):

    self.spectraSelectionWidget = SpectraSelectionWidget(self, mainWindow=self.mainWindow)

    self.noiseLevelLabel = Label(self, text='Noise Level Threshold')
    self.noiseLevelRadioButtons = RadioButtons(self,
                                               texts=[Estimated, Manual],
                                               selectedInd=0,
                                               callback=self._noiseLevelCallBack,
                                               tipTexts=None)

    self.noiseLevelFactorLabel = Label(self, text='Noise Level Factor')
    self.noiseLevelFactorSpinbox = DoubleSpinbox(self, value=10.0, min=0.01, step=0.1)



    self.noiseLevelSpinbox = DoubleSpinbox(self)
    self.noiseLevelSpinbox.hide()
    self.noiseLevelSpinbox.setValue(10000)
    self.noiseLevelSpinbox.setMaximum(10000000)

    self.maximumFilterSize = Label(self, text="Select Maximum Filter Size")
    self.maximumFilterSizeSpinbox = Spinbox(self, value=5.0, min=0, max=100)

    modes = ['wrap','reflect', 'constant', 'nearest', 'mirror' ]
    self.maximumFilterMode = Label(self, text="Select Maximum Filter Mode")
    self.maximumFilterModePulldownList = PulldownList(self, texts=modes)

    self.pickCancelButtons = ButtonList(self,
                                        texts=['Cancel', 'Find Peaks'],
                                        callbacks=[self.reject, self._pickFromSelectedSpectra],
                                        tipTexts=[None, None],
                                        direction='h', hAlign='c')
    self.pickNegativeLabel = Label(self, text='Pick negative peaks')
    self.pickNegativeCheckBox = CheckBox(self, checked=True)

  def _addWidgetsToLayout(self):
    self.mainLayout.addWidget(self.tabWidget, 0, 0, 1, 2)
    self.tabGeneralSetupLayout.addWidget(self.spectraSelectionWidget, 1, 0, 1, 2)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelLabel, 2, 0)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelRadioButtons, 2, 1)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelFactorLabel, 3, 0)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelFactorSpinbox, 3, 1)
    self.tabGeneralSetupLayout.addWidget(self.noiseLevelSpinbox, 3, 1)

    self.tabGeneralSetupLayout.addWidget(self.maximumFilterSize, 4, 0)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterSizeSpinbox, 4, 1)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterMode, 5, 0)
    self.tabGeneralSetupLayout.addWidget(self.maximumFilterModePulldownList, 5, 1)
    self.tabGeneralSetupLayout.addWidget(self.pickNegativeLabel, 6, 0)
    self.tabGeneralSetupLayout.addWidget(self.pickNegativeCheckBox, 6, 1)
    self.mainLayout.addWidget(self.pickCancelButtons, 10, 1)


  def _noiseLevelCallBack(self):
    selected = self.noiseLevelRadioButtons.get()
    if selected == Estimated:
      self.noiseLevelSpinbox.hide()
      self.noiseLevelFactorSpinbox.show()
      self.noiseLevelFactorLabel.show()
    else:
      self.noiseLevelSpinbox.show()
      self.noiseLevelFactorSpinbox.hide()
      self.noiseLevelFactorLabel.hide()


  def _getNoiseThreshold(self):
    selected = self.noiseLevelRadioButtons.get()
    values = (0, self.noiseLevelSpinbox.value())
    for selection, value in zip(self.noiseLevelRadioButtons.texts, values):
      if selected == str(selection):
        return value

  def _pickFromSelectedSpectra(self):

    spectra = list(set(self.spectraSelectionWidget._getSelectedSpectra()+self.spectraSelectionWidget._getSpectrumGroupsSpectra()))
    negativePeaks = self.pickNegativeCheckBox.get()
    size = self.maximumFilterSizeSpinbox.value()
    mode = self.maximumFilterModePulldownList.getText()
    ignoredRegions = self.excludedRegionsTab._getExcludedRegions()
    noiseThreshold = self._getNoiseThreshold()
    noiseThresholdFactor = self.noiseLevelFactorSpinbox.value()
    for spectrum in spectra:
      spectrum.peakLists[0].pickPeaks1dFiltered(size=size, mode=mode, excludeRegions=ignoredRegions,
                                                factor=noiseThresholdFactor,
                                                positiveNoiseThreshold=noiseThreshold, negativePeaks=negativePeaks)
    self.accept()



if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication

  app = TestApplication()
  popup = PickPeak1DPopup(mainWindow=None)
  popup.show()
  popup.raise_()
  app.start()
