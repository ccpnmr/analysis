
from collections import OrderedDict
from PyQt4 import QtGui , QtCore
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea

from collections import OrderedDict


WidgetSetters = OrderedDict([
                            ('CheckBox',      'setChecked'),
                            ('PulldownList',  'set'       ),
                            ('LineEdit',      'setText'   ),
                            ('Label',         'setText'   ),
                            ('DoubleSpinbox', 'setValue'  ),
                            ('Spinbox',       'setValue'  ),
                            ('Slider',        'setValue'  ),
                            ('RadioButtons',  'setIndex'  ),
                            ('TextEditor',    'setText'   ),
                           ])

class PeakPicker1D(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(PeakPicker1D, self)
    PipelineBox.__init__(self, name=name, )
    self.project = project
    self.application = self.project._appBase
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if self.params is not None:
      self._setParams()

    if parent is not None:
      self.pipelineModule = parent

  def methodName(self):
    return 'Peak picker 1D'

  def applicationsSpecific(self):
    return ['AnalysisScreen', 'AnalysisMetabolomics']

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):
    self.selectSpectraOption = RadioButtons(self,
                                            texts=['Spectra', 'Groups'],
                                            selectedInd=0,
                                            callback=self.showSpectraOption,
                                            tipTexts=None)

    self.pickNegativeCheckBox = CheckBox(self, text='Pick negative peaks', checked=True)

    self.mainLayout.addWidget(self.selectSpectraOption)
    self.mainLayout.addWidget(self.pickNegativeCheckBox)
    self._setSelectionScrollArea()
    self._addSpectrumCheckBoxes()
    self._addSpectrumGroupsCheckBoxes()

  def _setSelectionScrollArea(self):
    self.scrollAreaWidgetContents = QtGui.QFrame()
    self.scrollArea = ScrollArea(self)
    self.scrollArea.setWidget(self.scrollAreaWidgetContents)
    self.scrollArea.setWidgetResizable(True)
    self.mainLayout.addWidget(self.scrollArea)

  def getWidgetsParams(self):
    self.params = OrderedDict([
                          ('pickNegativeCheckBox', self.pickNegativeCheckBox.get()),
                          ('selectSpectraOption', self.selectSpectraOption.getIndex()),
                          ('spCheckBoxes', [cb.text() for cb in self.allCheckBoxes if cb.isChecked()]),
                          ('sgCheckBoxes', [cb.text() for cb in self.allSG_CheckBoxes if cb.isChecked()])
                          ])
    return self.params


  def runMethod(self):
    print('Running ',  self.methodName())
    self._pickPeaks(self._getAllSelectedSpectra())


  def _setParams(self):
    for widgetName, value in self.params.items():
      try:
        if widgetName == 'spCheckBoxes':
          self.updateSpectraCheckBoxes(value, self.allCheckBoxes)
        elif widgetName == 'sgCheckBoxes':
          self.updateSpectraCheckBoxes(value, self.allSG_CheckBoxes)

        widget = getattr(self, str(widgetName))
        if widget.__class__.__name__ in WidgetSetters.keys():
          setWidget = getattr(widget, WidgetSetters[widget.__class__.__name__])
          setWidget(value)
          if widgetName == 'selectSpectraOption':
            self.showSpectraOption()
        else:
          if widgetName != 'spCheckBoxes' and  widgetName != 'sgCheckBoxes':
            print('Value not set for %s in %s. Insert it on the "WidgetSetters" dictionary ' %(widget, self.name()))
      except:
        if widgetName != 'spCheckBoxes' and widgetName != 'sgCheckBoxes':
          print('Impossible to restore %s value for %s. Check paramas dictionary in getWidgetParams' %(widgetName, self.name()))


  def showSpectraOption(self):
    if self.selectSpectraOption.get() == 'Spectra':
      for cb in self.allCheckBoxes:
        self.spectrumCheckBox.show()
        self.spGroupsCheckBox.hide()
        cb.show()
      for sg in self.allSG_CheckBoxes:
        sg.hide()

    else:
      self.spectrumCheckBox.hide()
      for cb in self.allCheckBoxes:
        cb.hide()
      for sg in self.allSG_CheckBoxes:
        sg.show()
      self.spGroupsCheckBox.show()

  def _addSpectrumCheckBoxes(self):
    self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text='Select All',grid=(0, 0))
    self.spectrumCheckBox.stateChanged.connect(self._checkAllSpectra)
    self.allCheckBoxes = []
    for i, spectrum in enumerate(self.project.spectra):
      self.spectrumCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(spectrum.id), grid=(i+1, 0))
      self.allCheckBoxes.append(self.spectrumCheckBox)

  def _addSpectrumGroupsCheckBoxes(self):
    self.spGroupsCheckBox = CheckBox(self.scrollAreaWidgetContents, text='Select All SG', grid=(0, 0))
    self.spGroupsCheckBox.hide()
    self.spGroupsCheckBox.stateChanged.connect(self._checkAllSpectrumGroups)
    self.allSG_CheckBoxes = []
    for i, sg in enumerate(self.project.spectrumGroups):
      self.spectrumGroupCheckBox = CheckBox(self.scrollAreaWidgetContents, text=str(sg.pid), grid=(i + 1, 0))
      self.allSG_CheckBoxes.append(self.spectrumGroupCheckBox)
      self.spectrumGroupCheckBox.hide()

  def _checkAllSpectrumGroups(self, state):
    if len(self.allSG_CheckBoxes) > 0:
      for sg in self.allSG_CheckBoxes:
        if state == QtCore.Qt.Checked:
          sg.setChecked(True)
        else:
          sg.setChecked(False)

  def _checkAllSpectra(self, state):
    if len(self.allCheckBoxes) > 0:
      for cb in self.allCheckBoxes:
        if state == QtCore.Qt.Checked:
          cb.setChecked(True)
        else:
          cb.setChecked(False)

  def _getSelectedSpectra(self):
    spectra = []
    for cb in self.allCheckBoxes:
      if cb.isChecked():
        spectrum = self.project.getByPid('SP:' + str(cb.text()))
        spectra.append(spectrum)
    return spectra


  def _getSpectrumGroupsSpectra(self):
    spectra = []
    for sg in self.allSG_CheckBoxes:
      if sg.isChecked():
        spectrumGroup = self.project.getByPid(str(sg.text()))
        if len(spectrumGroup.spectra)>0:
          spectra.append(spectrumGroup.spectra)
    if len(spectra)>0:
      return list([item for sublist in spectra for item in sublist])
    else:
      return spectra

  def _getAllSelectedSpectra(self):
    return list(set(self._getSelectedSpectra() + self._getSpectrumGroupsSpectra()))


  def updateSpectraCheckBoxes(self, ids, checkBoxes):
    for id in ids:
      for cb in checkBoxes:
        if cb.text() == id:
          cb.setChecked(True)

  def _pickPeaks(self, spectra):
    negativePeaks = self.pickNegativeCheckBox.get()
    ignoredRegions = self._getIgnoredRegions()
    for spectrum in spectra:
      spectrum.peakLists[0].pickPeaks1dFiltered(ignoredRegions=ignoredRegions, negativePeaks=negativePeaks)

  def _getIgnoredRegions(self):
    ignoredRegions = []
    if self.pipelineModule is not None:
      currentPipeline = OrderedDict(self.pipelineModule.currentRunningPipeline)
      for box, value in currentPipeline.items():
        if box.methodName() == 'Exclude Signal Free Regions':
          ignoredRegions += value
      if len(ignoredRegions)>0:
        return ignoredRegions