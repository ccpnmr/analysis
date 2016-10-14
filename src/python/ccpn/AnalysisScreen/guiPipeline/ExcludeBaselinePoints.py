from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from collections import OrderedDict
import pyqtgraph as pg
from functools import partial
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

class ExcludeBaselinePoints(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(ExcludeBaselinePoints, self)
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
    return 'Exclude Baseline Points'

  def runMethod(self):
    print('Running ',  self.name())

  def applicationsSpecific(self):
    return ['AnalysisMetabolomics']

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QHBoxLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):

    self.pointLabel = Label(self, 'Exclusion Points ')
    self.pointBox1 = Spinbox(self, max=100000000000, min=-100000000000)
    self.pointBox2 = Spinbox(self,  max=100000000000, min=-100000000000)

    self.pickOnSpectrumButton = Button(self,  toggle=True, icon='icons/target3+', hPolicy='fixed')
    self.pickOnSpectrumButton.setChecked(False)
    self.multiplierLabel = Label(self, 'Baseline Multipler', )
    self.multiplierBox = DoubleSpinbox(self, )

    self.mainLayout.addWidget(self.pointLabel)
    self.mainLayout.addWidget(self.pointBox1)
    self.mainLayout.addWidget(self.pointBox2)
    self.mainLayout.addWidget(self.pickOnSpectrumButton)
    self.mainLayout.addWidget(self.multiplierLabel)
    self.mainLayout.addWidget(self.multiplierBox)

    self._widgetActions()

  def _widgetActions(self):
    self.pickOnSpectrumButton.toggled.connect(self.togglePicking)
    self.linePoint1 = pg.InfiniteLine(angle=0, pos=self.pointBox1.value(), movable=True, pen=(255, 0, 100))
    self.linePoint2 = pg.InfiniteLine(angle=0, pos=self.pointBox2.value(), movable=True, pen=(255, 0, 100))
    if self.current.strip is not None:
      self.current.strip.plotWidget.addItem(self.linePoint1)
      self.current.strip.plotWidget.addItem(self.linePoint2)
    else:
      print('No Strip found. Plot a spectrum first')
    self.pointBox1.setValue(self.linePoint1.pos().y())
    self.pointBox2.setValue(self.linePoint2.pos().y())
    self.linePoint1.hide()
    self.linePoint1.sigPositionChanged.connect(partial(self.lineMoved, self.pointBox1, self.linePoint1))
    self.linePoint2.hide()
    self.linePoint2.sigPositionChanged.connect(partial(self.lineMoved, self.pointBox2, self.linePoint2))
    self.pointBox1.valueChanged.connect(partial(self.setLinePosition, self.linePoint1, self.pointBox1))
    self.pointBox2.valueChanged.connect(partial(self.setLinePosition, self.linePoint2, self.pointBox2))

  def togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self.turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self.turnOffPositionPicking()

  def turnOnPositionPicking(self):
    print('picking on')
    self.linePoint1.show()
    self.linePoint2.show()

  def turnOffPositionPicking(self):
    print('picking off')
    self.linePoint1.hide()
    self.linePoint2.hide()

  def lineMoved(self, box, linePoint):
    box.setValue(linePoint.pos().y())

  def setLinePosition(self, linePoint, pointBox):
    linePoint.setPos(pointBox.value())

  def getWidgetsParams(self):
    pointBox1 = self.pointBox1.value()
    pointBox2 = self.pointBox2.value()
    multiplierBox = self.multiplierBox.value()

    params = OrderedDict([
                          ('pointBox1', pointBox1),
                          ('pointBox2', pointBox2),
                          ('multiplierBox', multiplierBox),
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
