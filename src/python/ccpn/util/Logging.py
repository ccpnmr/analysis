"""CCPN logger handling

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-22 15:44:51 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Wayne Boucher $"
__date__ = "$Date: 2017-03-17 12:22:34 +0000 (Fri, March 17, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import datetime
import functools
import logging
import os
import time
import inspect
from ccpn.util.Path import aPath


DEBUG1 = logging.DEBUG  # = 10
DEBUG2 = 9
DEBUG3 = 8
INFO = logging.INFO
WARNING = logging.WARNING

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
LOG_FIELD_WIDTH = 90

logger = None

#DEFAULT_LOGGER_NAME = 'defaultLogger'
defaultLogger = logging.getLogger('defaultLogger')
defaultLogger.propagate = False


def getLogger():
    global logger, defaultLogger

    if not logger:
        defaultLogger._loggingCommandBlock = 0
        return defaultLogger

    logger._loggingCommandBlock = 0
    return logger


def _logCaller(logger, fmsg):
    # create the postfix to the error message as (Module:function:lineNo)
    # this replaces the formatting which contains the wrong information for decorated functions
    _file, _line, _func, _ = logger.findCaller(stack_info=False)
    _fileLine = f'({aPath(_file).basename}.{_func}:{_line})'
    _msg = '; '.join(fmsg)
    return f'{_msg:<{LOG_FIELD_WIDTH}}    {_fileLine}'


def _debugGLError(MESSAGE, logger, msg, *args, **kwargs):
    # inspect.stack can be very slow - but needs more stack info than below
    stk = inspect.stack()
    stk = [stk[st][3] for st in range(min(3, len(stk)), 0, -1)]
    fmsg = ['[' + '/'.join(stk) + '] ' + msg]
    if args: fmsg.append(', '.join([str(arg) for arg in args]))
    if kwargs: fmsg.append(', '.join([str(ky) + '=' + str(kwargs[ky]) for ky in kwargs.keys()]))
    _msg = _logCaller(logger, fmsg)
    # increase the stack level to account for the partial wrapper
    logger.log(MESSAGE, _msg, stacklevel=2)


def _message(MESSAGE, logger, msg, includeInspection=True, *args, **kwargs):
    fmsg = [msg]
    if args: fmsg.append(', '.join([str(arg) for arg in args]))
    if kwargs: fmsg.append(', '.join([str(ky) + '=' + str(kwargs[ky]) for ky in kwargs.keys()]))
    _msg = _logCaller(logger, fmsg) if includeInspection else '; '.join(fmsg)
    # increase the stack level to account for the partial wrapper
    logger.log(MESSAGE, _msg, stacklevel=2)


def createLogger(loggerName, memopsRoot, stream=None, level=None, mode='a',
                 removeOldLogsDays=MAX_LOG_FILE_DAYS):
    """Return a (unique) logger for this memopsRoot and with given programName, if any.
       Puts log output into a log file but also optionally can have output go to
       another, specified, stream (e.g. a console)
    """

    global logger

    assert mode in ('a', 'w'), 'for now mode must be "a" or "w"'

    #TODO: remove Api calls
    from ccpnmodel.ccpncore.lib.Io import Api as apiIo

    repositoryPath = apiIo.getRepositoryPath(memopsRoot, 'userData')
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
        for handler in tuple(logger.handlers):
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

    logger.debugGL = functools.partial(_debugGLError, DEBUG1, logger)
    logger.echoInfo = functools.partial(_message, INFO, logger, includeInspection=False)
    logger.info = functools.partial(_message, INFO, logger)
    logger.debug1 = functools.partial(_message, DEBUG1, logger)
    logger.debug = logger.debug1
    logger.debug2 = functools.partial(_message, DEBUG2, logger)
    logger.debug3 = functools.partial(_message, DEBUG3, logger)
    logger.warning = functools.partial(_message, WARNING, logger)

    logging.addLevelName(DEBUG2, 'DEBUG2')
    logging.addLevelName(DEBUG3, 'DEBUG3')

    return logger


def _setupHandler(handler, level):
    """Add a stream handler for this logger.
    """

    handler.setLevel(level)

    # define a simple logging message, extra information is inserted in _logCaller
    _format = '%(levelname)-7s: %(message)s'

    formatter = logging.Formatter(_format)
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def _removeOldLogFiles(logPath, removeOldLogsDays=MAX_LOG_FILE_DAYS):
    """Remove old log files.
    """

    logDirectory = os.path.dirname(logPath)
    logFiles = [os.path.join(logDirectory, x) for x in os.listdir(logDirectory)]
    logFiles = [logFile for logFile in logFiles if logFile != logPath and not os.path.isdir(logFile)]

    currentTime = time.time()
    removeTime = currentTime - removeOldLogsDays * 24 * 3600
    for logFile in logFiles:
        mtime = os.path.getmtime(logFile)
        if mtime < removeTime:
            os.remove(logFile)


def setLevel(logger, level=logging.INFO):
    """Set the logger level (including for the handlers)
    """

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
