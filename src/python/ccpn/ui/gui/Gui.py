"""Module Documentation here
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9315 $"

#=========================================================================================
# Start of code
#=========================================================================================

import sys

from ccpn.util import Register

from ccpn.ui.gui.widgets.SplashScreen import SplashScreen

from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup

class Gui:
  
  def __init__(self, framework):
    
    self.framework = framework
    
    self.application = None
    self.mainWindow = None
    
  def start(self):
    """Start the program execution"""
    
    # On the Mac (at least) it does not matter what you set the applicationName to be,
    # it will come out as the executable you are running (e.g. "python3")
    self.application = Application(framework.applicationName, framework.applicationVersion, organizationName='CCPN', organizationDomain='ccpn.ac.uk')
    self.application.setStyleSheet(getStyleSheet(framework.preferences))

    self._checkRegistered()
    Register.updateServer(Register.loadDict(), framework.applicationVersion)

    # show splash screen
    splash = SplashScreen()
    self.application.processEvents()  # needed directly after splashScreen show to show something

    sys.stderr.write('==> Done, %s is starting\n' % framework.applicationName )

    splash.finish(self.mainWindow)
    
    self.application.start()
    
  def _checkRegistered(self):
    """Check if registered and if not popup registration and if still no good then exit"""
    
    # checking the registration; need to have the app running, but before the splashscreen, as it will hang
    # in case the popup is needed.
    # We want to give some feedback; sometimes this takes a while (e.g. poor internet)
    sys.stderr.write('==> Checking registration ... \n')
    sys.stderr.flush()  # It seems to be necessary as without the output comes after the registration screen
    if not self.isRegistered()
      self._showRegisterPopup()
      if not self._isRegistered():
        sys.stderr.write('\n### INVALID REGISTRATION, terminating\n')
        sys.exit(1)
    sys.stderr.write('==> Registered to: %s (%s)\n' %
                     (self.registrationDict['name'], self.registrationDict['organisation']))
                     
                     
  def _isRegistered(self):
    """return True if registered"""
    
    return not Register.isNewRegistration(Register.loadDict())

  def _showRegisterPopup(self):
    """Display registration popup"""
    
    popup = RegisterPopup(version=self.framework.applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    self.application.processEvents()

