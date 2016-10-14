from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from collections import OrderedDict
import pyqtgraph as pg
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

class WhittakerSmooth(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):

    super(WhittakerSmooth, self)
    PipelineBox.__init__(self,name=name,)
    if parent is not None:
      self.pipelineModule = parent
    self.linePoints = []
    self.points = []
    self.project = project
    self.current = self.project._appBase.current
    self.spectra = [spectrum.pid for spectrum in self.project.spectra]

    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Whittaker Smooth'

  def runMethod(self):
    print('Running ',  self.name())

  def applicationsSpecific(self):
    return ['AnalysisMetabolomics']

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0,0,0)

  def _createWidgets(self):
    self.pickOnSpectrumButton = Button(self, toggle=True, icon='icons/target3+', hPolicy='fixed')
    self.pickOnSpectrumButton.setChecked(False)
    self.pickOnSpectrumButton.toggled.connect(self.togglePicking)

    self.checkBoxLabel = Label(self, 'Auto',)
    self.checkBox = CheckBox(self,)
    self.checkBox.setChecked(False)
    self.aLabel = Label(self, 'a ' )
    self.aBox = DoubleSpinbox(self)

    self.mainLayout.addWidget( self.pickOnSpectrumButton, 0, 0)
    self.mainLayout.addWidget(self.checkBoxLabel, 0, 1)
    self.mainLayout.addWidget(self.checkBox, 0, 2)
    self.mainLayout.addWidget(self.aLabel, 0, 3)
    self.mainLayout.addWidget(self.aBox, 0, 4)

  def togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self.turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self.turnOffPositionPicking()

  def turnOnPositionPicking(self):
    print('picking on')
    self.current.registerNotify(self.setPositions, 'cursorPosition')
    for linePoint in self.linePoints:
      self.current.strip.plotWidget.addItem(linePoint)

  def turnOffPositionPicking(self):
    print('picking off')
    self.current.unRegisterNotify(self.setPositions, 'cursorPosition')
    for linePoint in self.linePoints:
      self.current.strip.plotWidget.removeItem(linePoint)

  def setPositions(self, positions):
    line = pg.InfiniteLine(angle=90, pos=self.current.cursorPosition[0], movable=True, pen=(0, 0, 100))
    self.current.strip.plotWidget.addItem(line)
    self.linePoints.append(line)
    self.points.append(line.pos().x())

  def getWidgetsParams(self):
    checkBox = self.checkBox.get()
    aBox = self.aBox.value()

    params = OrderedDict([
                          ('checkBox', checkBox),
                          ('aBox', aBox),
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
