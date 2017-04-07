"""Default application no-user-interface UI implementation
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
__dateModified__ = "$dateModified: 2017-04-07 11:40:37 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"

__date__ = "$Date: 2017-03-22 13:00:57 +0000 (Wed, March 22, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import typing

from ccpn.core.Project import Project
from ccpn.ui._implementation import _uiImportOrder
from ccpn.core import _coreClassMap

from ccpn.util import Register

class Ui:
  """Superclass for all user interface classes"""

  # Factory functions for UI-specific instantiation of wrapped graphics classes
  _factoryFunctions = {}

  def __init__(self, application):

    self.application = application

    self.mainWindow = None

    self.pluginModules = []

  def addMenu(self, name, position=None):
    '''
    Add a menu specification for the top menu bar.
    '''
    if position is None:
      position = len(self._menuSpec)
    self._menuSpec.insert(position, (str(name), []))

  @classmethod
  def setUp(cls):
    """Set up graphics data classes, cleaning up previous settings"""

    for className in _uiImportOrder:
      # Remove ui-specific settings. Will be reset as necessary in subclasses
      _coreClassMap[className]._factoryFunction = cls._factoryFunctions.get(className)


  def initialize(self, mainWindow):
    """UI operations done after every project load/create"""
    pass

  def start(self):
    """Start the program execution"""

    # self._checkRegistered()
    # Register.updateServer(Register.loadDict(), self.application.applicationVersion)

    sys.stderr.write('==> %s interface is ready\n' % self.__class__.__name__)

  def _checkRegistered(self):
    """Check if registered and if not popup registration and if still no good then exit"""

    # checking the registration; need to have the app running, but before the splashscreen, as it will hang
    # in case the popup is needed.
    # We want to give some feedback; sometimes this takes a while (e.g. poor internet)
    sys.stderr.write('==> Checking registration ... \n')
    sys.stderr.flush()  # It seems to be necessary as without the output comes after the registration screen
    if not self._isRegistered:
      self._showRegisterPopup()
      if not self._isRegistered:
        sys.stderr.write('\n### INVALID REGISTRATION, terminating\n')
        sys.exit(1)
    sys.stderr.write('==> Registered to: %s (%s)\n' %
                     (self.application._registrationDict.get('name'),
                      self.application._registrationDict.get('organisation')))


  def echoCommands(self, commands:typing.List[str]):
    """Echo commands strings, one by one, to logger.
    Overwritten in subclasses to handle e.g. console putput
    """

    logger = self.application.project._logger

    for command in commands:
      logger.info(command)


  @property
  def _isRegistered(self):
    """return True if registered"""
    return not Register.isNewRegistration(Register.loadDict())

class NoUi(Ui):

  def _showRegisterPopup(self):
    """Display registration popup"""

    sys.stderr.write('\n### Please register, using another application\n')
    # popup = RegisterPopup(version=self.application.applicationVersion, modal=True)
    # popup.show()
    # popup.raise_()
    # popup.exec_()
    # self.application.processEvents()

class TestUi(NoUi):

  def __init__(self, application):

    Ui.__init__(self, application)
    application._consoleOutput = []


  def echoCommands(self, commands:typing.List[str]):
    """Echo commands strings, one by one, to logger
    and store them in internal list for perusal
    """

    self.application._consoleOutput.extend(commands)

    logger = self.application.project._logger

    for command in commands:
      logger.info(command)

