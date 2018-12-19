"""Utilities for path handling

Includes extensions of sys.path functions and CCPN-specific functionality

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
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
"""General path handling utilities. NB must be python 2.1 compliant!!!"""

#
# Convenient I/O functions
#

import importlib
import os
import shutil
import glob


dirsep = '/'
# note, cannot just use os.sep below because can have window file names cropping up on unix machines
winsep = '\\'

CCPN_API_DIRECTORY = 'ccpnv3'
CCPN_DIRECTORY_SUFFIX = '.ccpn'
CCPN_BACKUP_SUFFIX = '_backup'
CCPN_ARCHIVES_DIRECTORY = 'archives'
CCPN_SUMMARIES_DIRECTORY = 'summaries'
CCPN_LOGS_DIRECTORY = 'logs'

CCPN_PYTHON = 'miniconda/bin/python'


def normalisePath(path, makeAbsolute=None):
    """
    Normalises the path, e.g. removes redundant .. and slashes and
    makes sure path uses '/' rather than '\\' as can happen on Windows.
    """

    if os.sep == winsep:
        path = path.replace(dirsep, winsep)
        path = os.path.normpath(path)
        path = path.replace(winsep, dirsep)
    else:
        path = path.replace(winsep, dirsep)
        path = os.path.normpath(path)

    if makeAbsolute:
        if path and path[0] != dirsep:
            path = joinPath(os.getcwd(), path)

    return path


def unnormalisePath(path):
    """
    On Unix does nothing, on Windows replaces '/' with '\\'/
    """

    if os.sep != '/':
        path = path.replace('/', os.sep)

    return path


def joinPath(*args):
    """
    The same as os.path.join but normalises the result.
    """

    return normalisePath(os.path.join(*args))


def splitPath(path):
    """
    The same as os.path.split but with normalisation taken into account.
    """

    (head, tail) = os.path.split(unnormalisePath(path))
    head = normalisePath(head)

    return head, tail


def converseSplitPath(path):
    """
    Similar to splitPath but with head being the top directory and tail being the rest.
    """

    pair = splitPath(path)
    head = None
    tail = ''
    while pair[0] and pair[0] not in ('.', '/'):
        head = pair[0]
        tail = joinPath(pair[1], tail)
        pair = splitPath(head)

    if head is None:
        (head, tail) = pair

    return head, tail


def getPathToImport(moduleString):
    """Get absolute path to module (directory or file)"""
    module = importlib.import_module(moduleString)
    return os.path.dirname(module.__file__)


def getTopDirectory():
    """
    Returns the 'top' directory of the containing repository (ccpnv3).
    """

    return os.path.dirname(os.path.dirname(getPythonDirectory()))


def getPythonDirectory():
    """
    Returns the 'top' python directory, the one on the python path.
    """
    return os.path.dirname(getPathToImport('ccpn'))


def deletePath(path):
    """Removes path whether file or directory, taking into account whether symbolic link.
    """

    if not os.path.exists(path):
        return

    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    else:
        shutil.rmtree(path)


def commonSuperDirectory(*fileNames):
    """ Find lowest directory that contains all files in list
    NB does not normalise file names.

    Input: a list of file names
    Output: lowest directory that contains all files. Does *not* end with a file
    """
    return os.path.dirname(os.path.commonprefix(fileNames))


def checkFilePath(filePath, allowDir=True):
    msg = ''
    isOk = True

    if not filePath:
        isOk = False

    elif not os.path.exists(filePath):
        msg = 'Location "%s" does not exist' % filePath
        isOk = False

    elif not os.access(filePath, os.R_OK):
        msg = 'Location "%s" is not readable' % filePath
        isOk = False

    elif os.path.isdir(filePath):
        if allowDir:
            return isOk, msg
        else:
            msg = 'Location "%s" is a directory' % filePath
            isOk = False

    elif not os.path.isfile(filePath):
        msg = 'Location "%s" is not a regular file' % filePath
        isOk = False

    elif os.stat(filePath).st_size == 0:
        msg = 'File "%s" is of zero size ' % filePath
        isOk = False

    return isOk, msg


def suggestFileLocations(fileNames, startDir=None):
    """ From a list of files, return a common superdirectory and a list of
    relative file names. If any of the files do not exist, search for an
    alternative superdirectory that does contain the set of relative file names.
    Searches in either a superdirectory of the starting/current directory,
    or in a direct subdirectory.

    Input: list of file names

    Output: Superdirectory, list of relative file names.
    If no suitable location is found, superdirectory is returned as None
    """

    if not fileNames:
        return None, []

    # set up startDir
    if startDir is None:
        startDir = os.getcwd()
    startDir = normalisePath(startDir, makeAbsolute=True)

    # find common baseDir and paths
    files = [normalisePath(fp, makeAbsolute=True) for fp in fileNames]
    baseDir = commonSuperDirectory(*files)
    prefix = os.path.join(baseDir, '')
    lenPrefix = len(prefix)
    paths = [fp[lenPrefix:] for fp in files]

    if [fp for fp in files if not os.path.exists(fp)]:
        # some file not found.

        # look in superdirectories
        tail = 'junk'
        baseDir = startDir
        while tail:
            for path in paths:
                fp = os.path.join(baseDir, path)
                if not os.path.exists(fp):
                    # a file is not found. try new baseDir
                    break
            else:
                # this one is OK - stop searching
                break
            #
            baseDir, tail = os.path.split(baseDir)

        else:
            # No success - try in a subdirectory (one level) of startDir
            matches = glob.glob(os.path.join(startDir, '*', paths[0]))
            for aMatch in matches:
                baseDir = normalisePath(aMatch[:-len(paths[0])])
                for path in paths:
                    fp = os.path.join(baseDir, path)
                    if not os.path.exists(fp):
                        # a file is not found. try new baseDir
                        break
                else:
                    # this one is OK - stop searching
                    break
            else:
                # we give up
                baseDir = None
    #
    return baseDir, paths


def fetchDir(path, dirName):
    '''

    :param path: string of parent path where to add a new subdir
    :param dirName: str of the new sub dir
    :return: if not already existing, creates a new folder with the given name, return the full path as str
    '''
    if path is not None:
        newPath = os.path.join(path, dirName)
        if not os.path.exists(newPath):
            os.makedirs(newPath)
            return newPath
        else:
            return newPath
