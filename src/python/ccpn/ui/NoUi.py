"""Default framework no-user-interface UI implementation
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import importlib
import sys

from ccpn.core.Project import Project
from ccpn.ui import _implementation

from ccpn.util import Register


class NoUi:
  
  def __init__(self, framework):
    
    self.framework = framework
    
    self.application = None
    self.mainWindow = None

  def setUp(self):
    """Set up and connect UI classes before start"""

    class2file = _implementation._class2file

    for className in _implementation._importOrder:
      module = importlib.import_module('ccpn.ui._implementation.%s'
                                        % class2file.get(className, className))
      cls = getattr(module, className)
      parentClass = cls._parentClass
      if parentClass is not None:
        parentClass._childClasses.append(cls)

    # Link in classes
    Project._linkWrapperClasses()

  def start(self):
    """Start the program execution"""

    self._checkRegistered()
    Register.updateServer(Register.loadDict(), self.framework.applicationVersion)

    sys.stderr.write('==> NoUi interface is ready\n' )
    
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
                     (self.framework.registrationDict['name'],
                      self.framework.registrationDict['organisation']))
                     
  @property
  def _isRegistered(self):
    """return True if registered"""
    return True
    return not Register.isNewRegistration(Register.loadDict())

  def _showRegisterPopup(self):
    """Display registration popup"""

    sys.stderr.write('\n### Please register, using another application\n')
    # popup = RegisterPopup(version=self.framework.applicationVersion, modal=True)
    # popup.show()
    # popup.raise_()
    # popup.exec_()
    # self.application.processEvents()

