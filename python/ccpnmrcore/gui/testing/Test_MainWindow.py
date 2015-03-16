"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.gui.MainWindow import MainWindow

class MainWindowTest(Testing):

  def __init__(self, *args, **kw):
    from ccpncore.util import Translation
    Translation.setTranslationLanguage('Dutch')
    # TBD: project / spectrum not used currently
    Testing.__init__(self, 'Ccpn1Dtesting', *args, **kw)
    self.spectrumName = '1D'

  def test_mainWindow(self):

    mainWindow = MainWindow()
