
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
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

class AlignToReference(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(AlignToReference, self)
    PipelineBox.__init__(self, name=name)
    self.project = project
    # self.current = self.project._appBase.current
    self.spectra = [spectrum.pid for spectrum in self.project.spectra]
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    if self.params is not None:
      self._setParams()
    if parent is not None:
      self.pipelineModule = parent

  def methodName(self):
    return 'Align To Reference'

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

    self.pickOnSpectrumButton = Button(self,  toggle=True, icon='icons/target3+',hPolicy='fixed')
    self.pickOnSpectrumButton.setChecked(False)
    self.pickOnSpectrumButton.toggled.connect(self.togglePicking)
    self.region1 = DoubleSpinbox(self,)
    self.region2 = DoubleSpinbox(self, )
    self.regionBoxes = [self.region1, self.region2]
    self.linePoints = []
    self.lr = None
    self.referenceLabel = Label(self, "Reference",)
    self.referencePulldown = PulldownList(self, )
    self.referenceBox = DoubleSpinbox(self, )


    self.mainLayout.addWidget(self.pickOnSpectrumButton)
    self.mainLayout.addWidget(self.region1)
    self.mainLayout.addWidget(self.region2)
    self.mainLayout.addWidget(self.referenceLabel)
    self.mainLayout.addWidget(self.referencePulldown)
    self.mainLayout.addWidget(self.referenceBox)

  def togglePicking(self):
    if self.pickOnSpectrumButton.isChecked():
      self.turnOnPositionPicking()
    elif not self.pickOnSpectrumButton.isChecked():
      self.turnOffPositionPicking()

  def turnOnPositionPicking(self):
    print('picking on')
    # self.current.registerNotify(self.setPositions, 'cursorPosition')
    # if self.lr:
    #   self.current.strip.plotWidget.addItem(self.lr)

  def turnOffPositionPicking(self):
    print('picking off')
    # self.current.unRegisterNotify(self.setPositions, 'cursorPosition')
    # self.current.strip.plotWidget.removeItem(self.lr)


  def setPositions(self, positions):
    if len(self.linePoints) < 2:
      line = pg.InfiniteLine(angle=90, pos=self.current.cursorPosition[0], movable=True, pen=(0, 0, 100))
      self.current.strip.plotWidget.addItem(line)
      self.linePoints.append(line)
      for i, line in enumerate(self.linePoints):
        self.regionBoxes[i].setValue(line.pos().x())
    if len(self.linePoints) == 2:
      for linePoint in self.linePoints:
        self.current.strip.plotWidget.removeItem(linePoint)
      if not self.lr:
        self.lr = pg.LinearRegionItem(values=[self.linePoints[0].pos().x(), self.linePoints[1].pos().x()])

        self.current.strip.plotWidget.addItem(self.lr)
        self.lr.sigRegionChanged.connect(self.updateRegion)

  def updateRegion(self):
    region = self.lr.getRegion()
    self.regionBoxes[0].setValue(region[1])
    self.regionBoxes[1].setValue(region[0])


  def getWidgetsParams(self):
    region1 = self.region1.value()
    region2 = self.region2.value()
    referencePulldown = self.referencePulldown.currentText()
    referenceBox = self.referenceBox.value()

    params = OrderedDict([
                              ('region1', region1),
                              ('region2', region2),
                              ('referencePulldown', referencePulldown),
                              ('referenceBox', referenceBox),
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
