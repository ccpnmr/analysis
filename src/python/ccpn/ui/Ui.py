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

import sys

from ccpn.core.Project import Project
from ccpn.ui._implementation import _name2DataClass as _graphicsDataClassMap

from ccpn.util import Register

class Ui:
  """Superclass for all user interface classes"""

  # Remapping of core classes to equivalent Ui classes - used for set-up in subclasses
  _coreClass2UiClass = {}

  @classmethod
  def _setUp(cls):
    """Set up graphics data classes and link up all data wrapper classes"""

    # NBNB TODO we could recode this in C as a gatekeeper

    # link up graphics data classes
    for cc in _graphicsDataClassMap.values():
      cc = cls._coreClass2UiClass.get(cc, cc)
      parentClass = cc._parentClass
      if parentClass is not None:
        parentClass._childClasses.append(cc)

    # Link up classes
    Project._linkWrapperClasses()

  def initialize(self):
    """UI operations done after every project load/create"""
    pass

  def start(self):
    """Start the program execution"""

    # self._checkRegistered()
    # Register.updateServer(Register.loadDict(), self.framework.applicationVersion)

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
                     (self.framework._registrationDict.get('name'),
                      self.framework._registrationDict.get('organisation')))

  @property
  def _isRegistered(self):
    """return True if registered"""
    return not Register.isNewRegistration(Register.loadDict())

class NoUi(Ui):
  
  def __init__(self, framework):
    
    self.framework = framework
    
    self.application = None
    self.mainWindow = None

  setUp = Ui._setUp

  def _showRegisterPopup(self):
    """Display registration popup"""

    sys.stderr.write('\n### Please register, using another application\n')
    # popup = RegisterPopup(version=self.framework.applicationVersion, modal=True)
    # popup.show()
    # popup.raise_()
    # popup.exec_()
    # self.application.processEvents()

