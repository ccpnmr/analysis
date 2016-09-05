"""CCPN logger handling

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
"""Logger and message handler"""


import datetime
import logging
import os
import time

defaultLogLevel = logging.INFO
# defaultLogLevel = logging.DEBUG

# this code assumes we only have one project open at a time
# when a new logger is created the handlers for the old one are closed

# note that cannot do logger = getLogger() at top of a module because it almost certainly
# will not be what one wants. instead one has to do it at runtime, e.g. in a constructor
# inside a class or in a non-class function

# in general the application should call createLogger() before anyone calls getLogger()
# but getLogger() can be called first for "short term", "setup" or "testing" use; it then returns
# the default logger

MAX_LOG_FILE_DAYS = 7

logger = None

#DEFAULT_LOGGER_NAME = 'defaultLogger'
defaultLogger = logging.getLogger('defaultLogger')
defaultLogger.propagate = False

def getLogger():

  global logger, defaultLogger

  if not logger:
    return defaultLogger

  return logger


def createLogger(loggerName, project, stream=None, level=None, mode='a',
                 removeOldLogsDays=MAX_LOG_FILE_DAYS):
  """Return a (unique) logger for this project and with given programName, if any.
     Puts log output into a log file but also optionally can have output go to
     another, specified, stream (e.g. a console)
  """

  global logger

  assert mode in ('a', 'w'), 'for now mode must be "a" or "w"'

  from ccpnmodel.ccpncore.lib.Io import Api as apiIo
  repositoryPath = apiIo.getRepositoryPath(project, 'userData')
  logDirectory = os.path.join(repositoryPath, 'logs')

  today = datetime.date.today()
  fileName = 'log_%s_%02d%02d%02d.txt' % (loggerName, today.year, today.month, today.day)

  logPath = os.path.join(logDirectory, fileName)

  if os.path.exists(logDirectory):
    if os.path.exists(logPath) and os.path.isdir(logPath):
      raise Exception('log file "%s" is a directory' % logPath)
  else:
    os.makedirs(logDirectory)

  _removeOldLogFiles(logPath, removeOldLogsDays)

  if logger:
    # there seems no way to close the logger itself
    # and just closing the handler does not work
    # (and certainly do not want to close stdout or stderr)
    for handler in logger.handlers:
      logger.removeHandler(handler)
  else:
    logger = logging.getLogger(loggerName)
    logger.propagate = False

  logger.logPath = logPath  # just for convenience
  logger.shutdown = logging.shutdown  # just for convenience but tricky

  if level is None:
    level = defaultLogLevel

  logger.setLevel(level)

  handler = logging.FileHandler(logPath, mode=mode)
  _setupHandler(handler, level)

  if stream:
    handler = logging.StreamHandler(stream)
    _setupHandler(handler, level)

  return logger

def _setupHandler(handler, level):
  """Add a stream handler for this logger."""

  # handler = logging.StreamHandler(stream)
  handler.setLevel(level)

  #format = '%(levelname)s:%(module)s:%(funcName)s:%(asctime)s:%(message)s'
  format = '%(levelname)s:%(module)s:%(funcName)s: %(message)s'
  formatter = logging.Formatter(format)
  handler.setFormatter(formatter)

  logger.addHandler(handler)

# def _addStreamHandler(logger, stream, level=logging.WARNING):
#   """Add a stream handler for this logger."""
#
#   handler = logging.StreamHandler(stream)
#   handler.setLevel(level)
#
#   format = '%(levelname)s:%(module)s:%(funcName)s:%(asctime)s:%(message)s'
#   formatter = logging.Formatter(format)
#   handler.setFormatter(formatter)
#
#   logger.addHandler(handler)

def _removeOldLogFiles(logPath, removeOldLogsDays=MAX_LOG_FILE_DAYS):
  """Remove old log files."""

  logDirectory = os.path.dirname(logPath)
  logFiles = [os.path.join(logDirectory, x) for x in os.listdir(logDirectory)]
  logFiles = [logFile for logFile in logFiles if logFile != logPath and not os.path.isdir(logFile)]

  currentTime = time.time()
  removeTime = currentTime - removeOldLogsDays * 24 * 3600
  for logFile in logFiles:
    # print ('### checking', logFile)
    mtime = os.path.getmtime(logFile)
    if mtime < removeTime:
      os.remove(logFile)
