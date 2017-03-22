"""

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-07-09 14:17:30 +0100 (Sat, 09 Jul 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, TJ Ragan, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-03-21 15:38:37 +0000 (Tue, March 21, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.lib.GuiGenerator import generateWidget
from ccpn.ui.gui.widgets.Button import Button



class PluginModule(CcpnModule):

  def __init__(self, interactor, *args, **kwargs):
    self.interactor = interactor
    self._kwargs = {}

    if interactor.settings is not None:
      self.includeSettingsWidget = True

    super().__init__(name=interactor.PLUGINNAME)

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
    self.goButton = Button(self.mainWidget, text='Run',
                           callback=partial(self.interactor.run, **self._kwargs))
    self.mainWidget.layout().addWidget(self.goButton)


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

    self.pgDock = Dock("Dock", size=(w, h))
    pgDockArea.addDock(self.pgDock)


  def showWidget(self, widget):
    self.pgDock.addWidget(widget)

    self.qtMainWindow.show()
    QtGui.QApplication.exec_()


if __name__ == '__main__':
  from unittest.mock import Mock

  qtTestHarness = TestQt()

  application = Mock()
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

  pluginModule = PluginModule(interactor)
  qtTestHarness.showWidget(pluginModule)
