
from collections import OrderedDict

from PyQt4 import QtGui
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
import decimal
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox, PipelineDropArea


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

class MatchPeaksToReference(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(MatchPeaksToReference, self)
    PipelineBox.__init__(self, name=name,)
    self.project = project
    self.saveIcon = Icon('icons/save')
    self.application = self.project._appBase
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if parent is not None:
      self.pipelineModule = parent
    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Match Peaks To Reference'

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):

    self.experimentTypeLabel = Label(self, text='Select experiment Type')
    self.experimentTypeRadioButtons = RadioButtons(self,
                                            texts=['STD', 'WLogsy', '1H'],
                                            selectedInd=0,
                                            tipTexts=None)

    self.minimumDistanceLabel = Label(self, text='Minimum Distance between two peaks (ppm)')
    self.minimumDistanceLineEdit = LineEdit(self, text=str(0.005))
    self.minimumDistanceLineEdit.setMaximumWidth(100)

    self.showHitModuleLabel = Label(self, text='Show Hit Module')
    self.showHitModuleCheckBox = CheckBox(self, checked = True)

    self.mainLayout.addWidget(self.experimentTypeLabel, 0, 0)
    self.mainLayout.addWidget(self.experimentTypeRadioButtons, 0, 1)
    self.mainLayout.addWidget(self.minimumDistanceLabel ,1,0)
    self.mainLayout.addWidget(self.minimumDistanceLineEdit ,1,1)
    self.mainLayout.addWidget(self.showHitModuleLabel, 2, 0)
    self.mainLayout.addWidget(self.showHitModuleCheckBox, 2, 1)

  def getWidgetsParams(self):
    minimumDistanceLineEdit  =  self.minimumDistanceLineEdit.get()
    experimentTypeRadioButtons = self.experimentTypeRadioButtons.getIndex()
    showHitModuleCheckBox = self.showHitModuleCheckBox.get()

    params = OrderedDict([
                          ('minimumDistanceLineEdit', minimumDistanceLineEdit),
                          ('experimentTypeRadioButtons', experimentTypeRadioButtons),
                          ('showHitModuleCheckBox', showHitModuleCheckBox),
                          ])
    self.params = params
    return params


  def runMethod(self):
    print('Running ',  self.methodName())
    self._matchPosition()
    if self.showHitModuleCheckBox.isChecked():
      self._showHitsModule()


  def applicationsSpecific(self):
    return ['AnalysisScreen',]

  def _setParams(self):
    for widgetName, value in self.params.items():
      try:
        widget = getattr(self, str(widgetName))
        if widget.__class__.__name__ in WidgetSetters.keys():
          setWidget = getattr(widget, WidgetSetters[widget.__class__.__name__])
          setWidget(value)
        else:
          print('Value not set for %s in %s. Insert it on the "WidgetSetters" dictionary ' %(widget, self.name()))
      except:
        print('Impossible to restore %s value for %s. Check paramas dictionary in getWidgetParams' %(widgetName, self.name()))

  def _matchPosition(self):

    if self.experimentTypeRadioButtons.get() == 'STD':
      from ccpn.AnalysisScreen.lib.Screening import matchSTDToReference
      matchSTDToReference(self.project, self.minimumDistanceLineEdit.text())



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
    return efficiency

  def _showHitsModule(self):
    if len(self.project.spectrumHits)>0:
      from ccpn.AnalysisScreen.modules.ShowScreeningHits import ShowScreeningHits
      showScreeningHits = ShowScreeningHits(parent=self.application.ui.mainWindow, project=self.project)
      showScreeningHitsModule = self.application.ui.mainWindow.moduleArea.addModule(showScreeningHits, position='bottom')
      spectrumDisplay = self.application.ui.mainWindow.createSpectrumDisplay(self.project.spectra[0])

      self.application.ui.mainWindow.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=showScreeningHitsModule)
      self.application.ui.mainWindow.moduleArea.guiWindow.deleteBlankDisplay()

      self.project.strips[0].viewBox.autoRange()

      currentDisplayed = self.project.strips[0]
      for spectrumView in currentDisplayed.spectrumViews:
        spectrumView.delete()

