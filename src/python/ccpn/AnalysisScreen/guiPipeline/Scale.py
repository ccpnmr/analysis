
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from collections import OrderedDict
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

class Scale(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(Scale, self)
    PipelineBox.__init__(self, name=name, )
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
    return 'Scale'

  def runMethod(self):
    print('Running ',  self.name())

  def applicationsSpecific(self):
    return ['AnalysisScreen','AnalysisMetabolomics']

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0, 0, 0, 0)

  def _createWidgets(self):
    self.methodLabel = Label(self, 'Method ',)
    self.methodPulldown = PulldownList(self,)
    methods = ['Unit Variance', 'Pareto']
    self.methodPulldown.setData(methods)

    self.mainLayout.addWidget(self.methodLabel, 0, 0)
    self.mainLayout.addWidget(self.methodPulldown, 0, 1)

  def getWidgetsParams(self):
    methodPulldown = self.methodPulldown.currentText()


    params = OrderedDict([
                          ('methodPulldown', methodPulldown),

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
