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
"""Logger and message handler"""

LICENSE = """
======================COPYRIGHT/LICENSE START==========================

Logging.py: Utility code for CCPN code generation framework

Copyright (C) 2014  (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

A copy of this license can be found in ../../../license/LGPL.license

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================
"""

import datetime
import logging
import os
import time

# this code assumes we only have one project open at a time
# when a new logger is created the handlers for the old one are closed

# note that cannot do logger = getLogger() at top of a module because it almost certainly
# will not be what one wants. instead one has to do it at runtime, e.g. in a constructor
# inside a class or in a non-class function

# in general the application should call createLogger() before anyone calls getLogger()
# but getLogger() can be called first for "short term" or "testing" use

MAX_LOG_FILE_DAYS = 7

logger = None

DEFAULT_LOGGER_NAME = 'defaultLogger'

def getLogger():

  global logger

  if not logger:
    logger = logging.getLogger(DEFAULT_LOGGER_NAME)

  return logger

def createLogger(loggerName, project, stream=None, level=logging.WARNING, mode='a', removeOldLogsDays=MAX_LOG_FILE_DAYS):
  """Return a (unique) logger for this project and with given programName, if any.
     Puts log output into a log file but also optionally can have output go to
     another, specified, stream (e.g. a console)
  """

  global logger

  assert mode in ('a', 'w'), 'for now mode must be "a" or "w"'

  if logger:
    # there seems no way to close the logger itself
    for handler in logger.handlers:
      handler.close()

  repository = project.findFirstRepository(name='userData')
  if not repository:
    raise Exception('no userData repository found')

  today = datetime.date.today()
  fileName = 'log_%s_%02d%02d%02d.txt' % (loggerName, today.year, today.month, today.day)

  logDirectory = os.path.join(repository.url.path, 'logs')
  logPath = os.path.join(logDirectory, fileName)

  if os.path.exists(logDirectory):
    if os.path.exists(logPath) and os.path.isdir(logPath):
      raise Exception('log file "%s" is a directory' % logPath)
  else:
    os.makedirs(logDirectory)

  _removeOldLogFiles(logPath, removeOldLogsDays)

  logger = logging.getLogger(loggerName)
  logger.logPath = logPath  # just for convenience
  logger.shutdown = logging.shutdown  # just for convenience but tricky

  fp = open(logPath, 'a')
  _addStreamHandler(logger, fp, level)

  if stream:
    _addStreamHandler(logger, stream, level)

  return logger

def _addStreamHandler(logger, stream, level=logging.WARNING):
  """Add a stream handler for this logger."""

  handler = logging.StreamHandler(stream)
  handler.setLevel(level)

  format = '%(levelname)s:%(module)s:%(funcName)s:%(asctime)s:%(message)s'
  formatter = logging.Formatter(format)
  handler.setFormatter(formatter)

  logger.addHandler(handler)

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
