
from collections import OrderedDict





from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox, PipelineDropArea

transparentStyle = "background-color: transparent; border: 0px solid transparent"

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

class StdSpectrumCreator(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(StdSpectrumCreator, self)
    PipelineBox.__init__(self, name=name,)
    if parent is not None:
      self.pipelineModule = parent
    self.project = project
    self.saveIcon = Icon('icons/save')
    self.application = self.project._appBase
    self.directoryPath = self.application.preferences.general.dataPath + '/'
    self._setMainLayout()
    self._createWidgets()
    self.params = params

    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Std Spectrum Creator'

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):

    self.createSTDlabel = Label(self, text='Create STDs from')
    self.saveButton =  Button(self, icon=self.saveIcon, callback=self._getSaveDirectory)
    self.saveButton.setStyleSheet(transparentStyle)
    self.labelSpectra = Label(self, text='OFF Resonance and  On Resonance Spectra')
    self.labelSave = Label(self, text='Save STDs in ')
    self.lineEditPath = LineEdit(self, text=str(self.directoryPath))

    self.mainLayout.addWidget(self.createSTDlabel,0,0)
    self.mainLayout.addWidget(self.labelSpectra,0,1)
    self.mainLayout.addWidget(self.labelSave, 2, 0)
    self.mainLayout.addWidget(self.lineEditPath, 2, 1)
    self.mainLayout.addWidget(self.saveButton,2,2)



  def _getSaveDirectory(self):
    dialog = FileDialog(fileMode=FileDialog.Directory, text='Save in ',
                        acceptMode=FileDialog.AcceptSave, preferences=self.application.preferences.general)
    self.directoryPath = dialog.selectedFile()
    if self.directoryPath is not None:
      self.lineEditPath.setText(str(self.directoryPath)+'/')

  def _createSpectrumDifference(self):
    from ccpn.AnalysisScreen.lib.Screening import createStdDifferenceSpectrum
    createStdDifferenceSpectrum(self.project, self.lineEditPath.text())


  def getWidgetsParams(self):
    self.params = OrderedDict([
                               ('lineEditPath', self.lineEditPath.text())
                              ])
    return self.params

  def runMethod(self):
    print('Running ',  self.name())
    self._createSpectrumDifference()

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
