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
__date__ = "$Date: 2017-03-21 10:55:49 +0000 (Tue, March 21, 2017) $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.lib.GuiGenerator import generateWidget


# # TODO: Move to ui.gui
# def _autoGenPluginGui(objMethod):
#   return generateWidget(objMethod,)  # add Container=CcpnModule bit
#
#
# # TODO: Move to ui.gui
# def _issueGuiInstantiatedMessage(objMethod):
#   print('Instantiated', str(objMethod))


class PluginModule(CcpnModule):
  # Populate self.mainWidget and self.settingsWidget
  # Everything else should be taken care of
  # set includeSettingsWidget depending on Klass.setting

  def __init__(self, interactor, *args, **kwargs):
    self.interactor = interactor
    if interactor.setting is not None:
      self.includeSettingsWidget = True

    super().__init__(name=interactor.PLUGINNAME)

    self._populateMainWidget()
    if interactor.setting is not None:
      self._populateSettingsWidget()

  def _populateMainWidget(self):
    generateWidget(self.interactor, widget=self.mainWidget)

  def _populateSettingsWidget(self):
    pass


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
  from unittest.mock import Mock, PropertyMock

  qtTestHarness = TestQt()

  application = Mock()
  application.colourScheme = 'dark'  # HACK!!!
  qtTestHarness.qtApp._ccpnApplication = application

  interactor = Mock()
  # type(interactor).PLUGINNAME = PropertyMock(return_value='TestI')  # PropertyMock's get attached to the class, not the instance
  interactor.PLUGINNAME = 'Test Plugin...Test'  # Same as above, but without checking
  interactor.params = [{'variable' : 'param1',
             'value'    : ('Fast', 'Slow'),
             'label'    : 'Param #1',
             'default'  : 'Fast'},                        # List

            {'variable' : 'param2',
             'value'    : False,
             'default'  : 0},                              # checkbox 0 unchecked 2 checked

            {'variable': 'param43',
             'value': (('White 1',False),('Red 2',True)),  #  RadioButtons
             'default': 'Red 2'},

            {'variable' : 'param3',
             'value'    : ('0', '4'),
             'default'  : 4},                                # List

            {'variable' : 'param4',                         # Spinbox
             'value'    : (0, 4),
             'default'  : (3)},

            {'variable' : 'param5',                         # Spinbox with default
             'value'    : (0, 4),
             'default'  : 2},

            {'variable' : 'param6',                         # Spinbox with stepsize
             'value'    : (0, 4),
             'stepsize' : 2,
             'default'  : 3},

            {'variable' : 'param7',                         # Spinbox with default and stepsize
             'value'    : (0, 4),
             'stepsize' : 2,
             'default'  : 2},

            {'variable' : 'param8',                         # Double Spinbox
             'value'    : (0., 1),
             'default'  : 0.3},

            {'variable' : 'param9',                         # Double Spinbox with default
             'value'    : (0., 1.),
             'default'  : 0.2},

            {'variable' : 'param10',                         # Double Spinbox with stepsize
             'value'    : (0., 1.),
             'stepsize' : 0.1,
             'default'  : 0.2},

            {'variable' : 'param11',                         # Double Spinbox with default and stepsize
             'value'    : (0., 1),
             'stepsize' : 0.1,
             'default'  : 0.2},

            {'variable': 'param12',                         # LineEdit
             'value': '',
             'default'  : 'param12'},

            {'variable': 'param13',
             'value': (('Ford', 'Focus'),                    # Mapped list
                       ('BMW', '320'),
                       ('Fiat', '500')
                      ),
             'default'  : 'Focus'},
            ]

  pluginModule = PluginModule(interactor)
  qtTestHarness.showWidget(pluginModule)
