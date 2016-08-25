'''
Use this file as a template to build new pipeline method boxes. Duplicate this file and do the appropriate changes.
Adding a new file in this folder (guiPipeline) will automatically make the method available for selection in the 'ccpn pipeline module'.

To get it working keep unmodified the following function names:

 - methodName
 - runMethod
 - applicationsSpecific
 - getWidgetsParams

They are called from the pipelineModule and the 'methodName' from the __init__ script in this folder.



methodName : ----------- is used to set the text in the selection pulldown in the pipelineModule and set the box name
                         in the pipelineArea.

runMethod : ------------ is used as callback from the pipelineModule 'goButton' to run the method algorithm/s

applicationsSpecific : - is used to define if the method is specific for an application or more then one.
                         This guarantee a filter for the selection pulldown in the pipelineModule.
                         If an [] the method is still loaded but does not appear int the pullDown. You can still
                         get while running analysis from the pipeline settings --> methods filter .

getWidgetsParams: -----  is used to save the params in the box within a pipeline and restore them accordingly.
                         The dictionary keys are used to getAttributes, so use the same as the widget variable name,
                         and the values are the function call to get the widget value. Dont't add str or int for the dict values.
                         Eg:
                         Widget ->        testCheckBox = CheckBox()
                         params Dict ->  {'testCheckBox' : testCheckBox.get()}


WidgetSetters:  -------- Common used ccpn widgets and the function calls to set their values. Add if missing any.
'''



'''
from PyQt4 import QtGui
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Label import Label
from collections import OrderedDict
from ccpn.ui.gui.widgets.PipelineWidgets import PipelineBox


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

class MethodTemplate(PipelineBox):
  def __init__(self, parent=None, name=None, params=None, project=None, **kw):
    super(MethodTemplate, self)
    PipelineBox.__init__(self,name=name,)
    if parent is not None:
      self.pipelineModule = parent
    self.project = project
    self._setMainLayout()
    self._createWidgets()
    self.params = params
    self.pipelineBoxName = name #don't use self.name = name. You can get the name also by self.name() from PyQtGraph
    if self.params is not None:
      self._setParams()

  def methodName(self):
    return 'Method Template'

  def runMethod(self):
    print('Running ',  self.pipelineBoxName)

  def applicationsSpecific(self):
    return ['AnalysisScreen','AnalysisMetabolomics']

  def _setMainLayout(self):
    self.mainFrame = QtGui.QFrame()
    self.mainLayout = QtGui.QGridLayout()
    self.mainFrame.setLayout(self.mainLayout)
    self.layout.addWidget(self.mainFrame, 0,0,0,0)

  def _createWidgets(self):
    self.testLabel = Label(self, 'This is a template',)
    self.testCheckBox = CheckBox(self, checked=True)
    self.mainLayout.addWidget(self.testLabel, 1, 0)
    self.mainLayout.addWidget(self.testCheckBox, 1, 1)


  def getWidgetsParams(self):
    testCheckBox = self.testCheckBox.get()

    params = OrderedDict([
                          ('testCheckBox', testCheckBox),
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


'''
