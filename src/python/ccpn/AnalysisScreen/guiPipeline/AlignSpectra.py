
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox, PipelineDropArea
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

class AlignSpectra(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(AlignSpectra, self)
    PipelineBox.__init__(self, name=name,)
    self.project = project
    self.current = self.project._appBase.current
    self.spectra = [spectrum.pid for spectrum in self.project.spectra]
    if parent is not None:
      self.pipelineModule = parent
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Align Spectra'

  def applicationsSpecific(self):
    return ['AnalysisMetabolomics']

  def runMethod(self):
    print('Running ',  self.name())

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):
    self.spectrumLabel = Label(self, 'Spectrum',)
    self.spectrumPulldown = PulldownList(self,)
    self.spectrumPulldown.setData(self.spectra)

    self.mainLayout.addWidget(self.spectrumLabel, 0, 0)
    self.mainLayout.addWidget(self.spectrumPulldown, 0, 1)

  def getWidgetsParams(self):
    spectrumPulldown = self.spectrumPulldown.currentText()

    params = OrderedDict([
                          ('spectrumPulldown', spectrumPulldown),
                          ])
    self.params = params
    return params


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
