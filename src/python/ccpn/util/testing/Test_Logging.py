"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
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
    msg = logLine[n+1:]

    assert msg == message1, '"%s" versus "%s"' % (msg, message1)


