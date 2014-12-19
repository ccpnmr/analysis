"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from ccpncore.util import Logging
from ccpncore.util.Testing import Testing

class LoggingTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1a', *args, **kw)

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

    assert len(logLines) == 1

    logLine = logLines[0].rstrip()
    n = logLine.rindex(':')
    msg = logLine[n+1:]

    assert msg == message1, '"%s" versus "%s"' % (msg, message1)


