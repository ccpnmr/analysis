"""

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"

__date__ = "$Date: 2017-03-24 10:20:58 +0000 (Fri, March 24, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.lib.GuiGenerator import generateWidget
from ccpn.ui.gui.lib.GuiGenerator import AUTOGEN_TAG
from ccpn.ui.gui.widgets.Button import Button

widgetGetters = {'CheckBox': 'get',  #returns Bool
                 'PulldownList':  'get'               ,
                 'LineEdit':      'get'               ,
                 'Label':         'get'               ,
                 'ListWidget':   'getSelectedObjects',  #returns list. Not Tested
                 'DoubleSpinbox': 'value'             ,
                 'Spinbox':       'value'             ,
                 'Slider':        'get'               ,
                 'RadioButton':   'isChecked'         ,  #returns Bool
                 'RadioButtons':  'getIndex'          ,  # returns int index of the checked RB
                 'ObjectTable':   'getSelectedObjects',  # returns int
                 'TextEditor':    'getText'           ,
                 'ToolButton':    'getText'           ,
                 }

class PluginModule(CcpnModule):

  def __init__(self, interactor, mainWindow, *args, **kwargs):
    self.interactor = interactor
    self._kwargs = {}

    if interactor.settings is not None:
      self.includeSettingsWidget = True

    super().__init__(mainWindow=mainWindow, name=interactor.PLUGINNAME)

    self._populateMainWidget()
    if interactor.settings is not None:
      self._populateSettingsWidget()


  def _populateMainWidget(self):
    generateWidget(self.interactor.params, widget=self.mainWidget, argsDict=self._kwargs)
    self.addRunButton()


  def _populateSettingsWidget(self):
    generateWidget(self.interactor.settings, widget=self.settingsWidget, argsDict=self._kwargs)


  def addRunButton(self):
    # TODO: put the run button at the bottom, not on the bottom right.
    self.goButton = Button(self.mainWidget, text='Run', callback=self._runButtonCallback)
    self.mainWidget.layout().addWidget(self.goButton)


  def _runButtonCallback(self):
    autogenTagLength = len(AUTOGEN_TAG)
    mainWidgetChildren = self.mainWidget.children()
    settingsWidgetChildren = self.settingsWidget.children()
    parameters = {}
    for widget in (mainWidgetChildren, settingsWidgetChildren):
      for child in widget:
        for subchild in child.children():
          n = subchild.objectName()
          if n.startswith(AUTOGEN_TAG):
            widgetType = subchild.__class__.__name__
            val = getattr(subchild, widgetGetters[widgetType])()
            parameters[n[autogenTagLength:]] = val
    # for k,v in parameters.items():
    #   print(k,v)
    self.interactor.run(**parameters)
    # self.interactor.run(**self._kwargs)


  def issueMessage(self, message):
    raise NotImplemented('Messages are not implemented yet.')



##################### Qt Testing code #########################

from PyQt4 import QtGui
from pyqtgraph.dockarea import Dock, DockArea



class TestQt:
  def __init__(self, w=100, h=100):
    self.qtApp = QtGui.QApplication([])

    self.qtMainWindow = QtGui.QMainWindow()
    pgDockArea = DockArea()
    self.qtMainWindow.setCentralWidget(pgDockArea)

    # layout = QtGui.QGridLayout()      # ejb
    # layout.setContentsMargins(15,15,15,15)
    # self.qtMainWindow.setLayout(layout)

    self.pgDock = Dock("Dock", size=(w, h))
    pgDockArea.addDock(self.pgDock)


  def showWidget(self, widget):
    self.pgDock.addWidget(widget)

    self.qtMainWindow.show()
    QtGui.QApplication.exec_()


if __name__ == '__main__':
  from unittest.mock import Mock
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea

  qtTestHarness = TestQt()

  application = Mock()
  # application = TestApplication()
  application.colourScheme = 'light'  # HACK!!!
  qtTestHarness.qtApp._ccpnApplication = application

  interactor = Mock()
  interactor.PLUGINNAME = 'Test Plugin...Test'  # Same as above, but without checking
  interactor.params = [{'variable' : 'param1',
                        'value'    : ('Fast', 'Slow'),
                        'label'    : 'Param #1',
                        'default'  : 'Fast'},                        # List

                       {'variable' : 'param2',
                        'value'    : False,
                        'default'  : 0},                              # checkbox 0 unchecked 2 checked

                       {'variable': 'param3',
                        'value': (('White 1',False),('Red 2',True)),  #  RadioButtons
                        'default': 'Red 2'},

                       {'variable' : 'param4',
                        'value'    : ('0', '4'),
                        'default'  : 4},                                # List

                       {'variable' : 'param5',                         # Spinbox
                        'value'    : (0, 4),
                        'default'  : (3)},

                       {'variable' : 'param6',                         # Spinbox with default
                        'value'    : (0, 4),
                        'default'  : 2},

                       {'variable' : 'param7',                         # Spinbox with stepsize
                        'value'    : (0, 4),
                        'stepsize' : 2,
                        'default'  : 3},

                       {'variable' : 'param8',                         # Spinbox with default and stepsize
                        'value'    : (0, 4),
                        'stepsize' : 2,
                        'default'  : 2},

                       {'variable' : 'param9',                         # Double Spinbox
                        'value'    : (0., 1),
                        'default'  : 0.3},

                       {'variable' : 'param10',                         # Double Spinbox with default
                        'value'    : (0., 1.),
                        'default'  : 0.2},

                       {'variable' : 'param11',                         # Double Spinbox with stepsize
                        'value'    : (0., 1.),
                        'stepsize' : 0.1,
                        'default'  : 0.2},

                       {'variable' : 'param12',                         # Double Spinbox with default and stepsize
                        'value'    : (0., 1),
                        'stepsize' : 0.1,
                        'default'  : 0.2},

                       {'variable': 'param13',                         # LineEdit
                        'value': '',
                        'default'  :'param13'},

                       {'variable': 'param14',
                        'value': (('Ford', 'Focus'),                    # Mapped list
                                  ('BMW', '320'),
                                  ('Fiat', '500')
                                 ),
                        'default'  : 'Focus'},
                      ]
  interactor.settings = [{'variable' : 'param1s',
                          'value'    : ('Fast', 'Slow'),
                          'label'    : 'Param #1',
                          'default'  : 'Fast'},                        # List

                         {'variable' : 'param2s',
                          'value'    : False,
                          'default'  : 0},                              # checkbox 0 unchecked 2 checked

                         {'variable': 'param3s',
                          'value': (('White 1',False),('Red 2',True)),  #  RadioButtons
                          'default': 'Red 2'},

                         {'variable' : 'param4s',
                          'value'    : ('0', '4'),
                          'default'  : 4},                                # List

                         {'variable' : 'param5s',                         # Spinbox
                          'value'    : (0, 4),
                          'default'  : (3)},

                         {'variable' : 'param6s',                         # Spinbox with default
                          'value'    : (0, 4),
                          'default'  : 2},

                         {'variable' : 'param7s',                         # Spinbox with stepsize
                          'value'    : (0, 4),
                          'stepsize' : 2,
                          'default'  : 3},

                         {'variable' : 'param8s',                         # Spinbox with default and stepsize
                          'value'    : (0, 4),
                          'stepsize' : 2,
                          'default'  : 2},

                         {'variable' : 'param9s',                         # Double Spinbox
                          'value'    : (0., 1),
                          'default'  : 0.3},

                         {'variable' : 'param10s',                         # Double Spinbox with default
                          'value'    : (0., 1.),
                          'default'  : 0.2},

                         {'variable' : 'param11s',                         # Double Spinbox with stepsize
                          'value'    : (0., 1.),
                          'stepsize' : 0.1,
                          'default'  : 0.2},

                         {'variable' : 'param12s',                         # Double Spinbox with default and stepsize
                          'value'    : (0., 1),
                          'stepsize' : 0.1,
                          'default'  : 0.2},

                         {'variable': 'param13s',                         # LineEdit
                          'value': '',
                          'default'  :'param13'},

                         {'variable': 'param14s',
                          'value': (('Ford', 'Focus'),                    # Mapped list
                                    ('BMW', '320'),
                                    ('Fiat', '500')
                                   ),
                          'default'  : 'Focus'},
                      ]

  def run(**kwargs):
    print('Run clicked, ', kwargs)
  interactor.run = run

  qtTestHarness.qtMainWindow.moduleArea = CcpnModuleArea(mainWindow=qtTestHarness.qtMainWindow)
  # print('GuiMainWindow.moduleArea: layout:', qtTestHarness.qtMainWindow.moduleArea.layout)  ## pyqtgraph object
  # qtTestHarness.qtMainWindow.moduleArea.setGeometry(0, 0, 1000, 800)
  # qtTestHarness.qtMainWindow.setCentralWidget(qtTestHarness.qtMainWindow.moduleArea)

  # pluginModule = PluginModule(interactor)       # ejb - original line

  # pluginModule = PluginModule(interactor=interactor
  #                             , application=application
  #                             , mainWindow=application.mainWindow)

  pluginModule = PluginModule(interactor=interactor
                              , application=application
                              , mainWindow=qtTestHarness.qtMainWindow)
  qtTestHarness.showWidget(pluginModule)

  # pluginModule.show()
  # pluginModule.raise_()

  # application.start()
