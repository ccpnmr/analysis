"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:02 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.util import Logging
from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting

class LoggingTest(CoreTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def _create_logger(self, name='loggingTest', mode='a'):
    return Logging.createLogger(name, self.project, mode=mode)

  def test_getLogger(self):
    logger = self._create_logger()
    assert logger is Logging.getLogger()

  def test_logMessage(self):
    logger = self._create_logger(mode='w')
    message1 = 'Watch out!'
    logger.warning(message1) # will log
    message2 = 'I told you so'
    logger.info(message2) # will not log
    logPath = logger.logPath
    logger.shutdown()

    logLines = open(logPath).readlines()

    assert len(logLines) == 2

    logLine = logLines[0].rstrip()
    n = logLine.rindex(':')
    msg = logLine[n+1:].strip()

    assert msg == message1, '"%s" versus "%s"' % (msg, message1)


