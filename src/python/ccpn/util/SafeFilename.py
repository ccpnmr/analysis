"""
Functions to append a number to the end of a filename if it already exists
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-06-16 16:28:31 +0000 (Fri, June 16, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import itertools
import errno
import os
import sys

def _iter_incrementing_file_names(path):
  """
  Iterate incrementing file names. Start with path and add '(n)' before the
  extension, where n starts at 1 and increases.

  :param path: Some path
  :return: An iterator.
  """
  yield path
  prefix, ext = os.path.splitext(path)
  for i in itertools.count(start=1, step=1):
    yield prefix + '({0})'.format(i) + ext

def safeOpen(path, mode):
  """
  Open path, but if it already exists, add '(n)' before the extension,
  where n is the first number found such that the file does not already
  exist.
  Returns an open file handle.

  Usage:  with safeOpen(path, [options]) as ...

  :param path: filepath and filename.
  :return: Open file handle... be sure to close!
  """
  flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

  if 'b' in mode and sys.platform.system() == 'Windows' and hasattr(os, 'O_BINARY'):
    flags |= os.O_BINARY

  for filename in _iter_incrementing_file_names(path):
    try:
      file_handle = os.open(filename, flags)
    except OSError as e:
      if e.errno == errno.EEXIST:
        pass
      else:
        raise
    else:
      return os.fdopen(file_handle, mode)
