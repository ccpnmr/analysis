from ccpncore.util.Testing import Testing
from ccpncore.util import Logging

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

    logLine = logLines[0]
    n = logLine.rindex(':')
    msg = logLine[n+1:]

    assert msg == message1


