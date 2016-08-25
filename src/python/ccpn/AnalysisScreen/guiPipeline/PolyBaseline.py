
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
import pyqtgraph as pg

from collections import OrderedDict
from functools import partial


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

class PolyBaseline(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(PolyBaseline, self)
    PipelineBox.__init__(self, name=name,)
    self.project = project
    self.current = self.project._appBase.current

    if parent is not None:
      self.pipelineModule = parent
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Poly Baseline'

  def applicationsSpecific(self):
    return ['AnalysisMetabolomics',]

  def runMethod(self):
    print('Running ',  self.name())

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):

    self.polyBaselineWidget = PolyBaselineWidget(project=self.project)
    self.mainLayout.addWidget(self.polyBaselineWidget,0,0)


  def getWidgetsParams(self):

    orderNumber = self.polyBaselineWidget.orderBox.value()
    orderBoxesValues = [x.value() for x in self.polyBaselineWidget.controlPointBoxList]

    self.params = OrderedDict([
                              ('orderNumber', orderNumber),
                              ('orderBoxesValues', orderBoxesValues)
                              ])
    return self.params



  def _setParams(self):
    try:
      self.polyBaselineWidget.orderBox.setValue(self.params['orderNumber'])
      for widget, value in zip(self.polyBaselineWidget.controlPointBoxList,self.params['orderBoxesValues']):
        widget.setValue(value)
    except:
      pass

# This widget has been simply copied from the old Metabolomics GuiPipeline.

from ccpn.ui.gui.widgets.Base import Base
class PolyBaselineWidget(QtGui.QWidget, Base):

  def __init__(self, parent=None, project=None, **kw):
    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.current = project._appBase.current
    self.orderLabel = Label(self, 'Order ', grid=(0, 0))
    self.orderBox = Spinbox(self, grid=(0, 1))
    self.orderBox.setMinimum(2)
    self.orderBox.setMaximum(5)
    if self.current.spectrumGroup is not None:
      self.controlPointMaximum = max([spectrum.spectrumLimits[0][1] for spectrum in self.current.spectrumGroup.spectra])
      self.controlPointMinimum = min([spectrum.spectrumLimits[0][0] for spectrum in self.current.spectrumGroup.spectra])
    else:
      self.controlPointMaximum = None
      self.controlPointMinimum = None

    self.controlPointStepSize = 0.01
    # self.orderBox.setValue(2)
    self.orderBox.valueChanged.connect(self.updateLayout)
    self.controlPointsLabel = Label(self, 'Control Points ', grid=(0, 2))
    self.pickOnSpectrumButton = Button(self, grid=(0, 9), toggle=True, icon='icons/target3+',hPolicy='fixed')
    self.pickOnSpectrumButton.setChecked(False)
    self.pickOnSpectrumButton.toggled.connect(self.togglePicking)
    # self.mySignal1.connect(self.setSpinBoxSelected)
    self.currentBox = None
    self.linePoints = []


    self.updateLayout(self.orderBox.value())



  def updateLayout(self, value=None):
    if value < 6:
      for j in range(self.layout().rowCount()):
        for k in range(3, self.layout().columnCount()-1):
          item = self.layout().itemAtPosition(j, k)
          if item:
            if item.widget():
              item.widget().hide()
            self.layout().removeItem(item)
      self.controlPointBoxList = []
      self.controlPointBox1 = DoubleSpinbox(self, grid=(0, 3), showButtons=False,
                                            max=self.controlPointMaximum, min=self.controlPointMinimum)
      self.controlPointBox1.setSingleStep(self.controlPointStepSize)
      self.controlPointBoxList.append(self.controlPointBox1)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 4))
      self.controlPointBox2 = DoubleSpinbox(self, grid=(0, 5), showButtons=False,
                                            max=self.controlPointMaximum, min=self.controlPointMinimum)
      self.controlPointBox2.setSingleStep(self.controlPointStepSize)
      self.controlPointBoxList.append(self.controlPointBox2)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 6))
      self.controlPointBox3 = DoubleSpinbox(self, grid=(0, 7), showButtons=False,
                                            max=self.controlPointMaximum, min=self.controlPointMinimum)
      self.controlPointBox3.setSingleStep(self.controlPointStepSize)
      self.controlPointBoxList.append(self.controlPointBox3)
      self.ppmLabel = Label(self, 'ppm', grid=(0, 8))
      if 2 < value <= 5:
        gridArray = [3+x for x in range(2*(value-2))]
        for i in range(0, len(gridArray), 2):
          self.controlPointBox = DoubleSpinbox(self, grid=(1, gridArray[i]), showButtons=False,
                                               max=self.controlPointMaximum, min=self.controlPointMinimum)
          self.controlPointBox.setSingleStep(self.controlPointStepSize)
          self.controlPointBoxList.append(self.controlPointBox)
          self.ppmLabel = Label(self, 'ppm', grid=(1, gridArray[i+1]))
    else:
      pass


  def setValueInValueList(self):
    self.valueList = [controlPointBox.value() for controlPointBox in self.controlPointBoxList]


  def togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self.turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self.turnOffPositionPicking()

  def turnOnPositionPicking(self):
    print('picking on')
    self.current.registerNotify(self.setPositions, 'cursorPosition')

  def turnOffPositionPicking(self):
    print('picking off')
    self.current.unRegisterNotify(self.setPositions, 'cursorPosition')

  def setPositions(self, positions):
    if len(self.linePoints) < len(self.controlPointBoxList):
      line = pg.InfiniteLine(angle=90, pos=self.current.cursorPosition[0], movable=True, pen=(0, 0, 100))
      line.sigPositionChanged.connect(self.lineMoved)
      self.current.strip.plotWidget.addItem(line)
      self.linePoints.append(line)
      for i, line in enumerate(self.linePoints):
        self.controlPointBoxList[i].setValue(line.pos().x())
    else:
      print('No more lines can be added')


  def lineMoved(self, line):
    lineIndex = self.linePoints.index(line)
    self.controlPointBoxList[lineIndex].setValue(line.pos().x())


  def getParams(self):
    return {'function': 'polyBaseLine',
            'controlPoints': [x.value() for x in self.controlPointBoxList]}
