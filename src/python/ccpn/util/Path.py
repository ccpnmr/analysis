"""Utilities for path handling

Includes extensions of sys.path functions and CCPN-specific functionality

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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
import datetime

dirsep = '/'
# note, cannot just use os.sep below because can have window file names cropping up on unix machines
winsep = '\\'

#This does not belong here and should go to PathsAndUrls;
# However, the 'Api.py' and Implementation relies on this so it should stay
CCPN_API_DIRECTORY = 'ccpnv3'
CCPN_DIRECTORY_SUFFIX = '.ccpn'
CCPN_BACKUP_SUFFIX = '_backup'
CCPN_ARCHIVES_DIRECTORY = 'archives'
CCPN_SUMMARIES_DIRECTORY = 'summaries'
CCPN_LOGS_DIRECTORY = 'logs'

CCPN_PYTHON = 'miniconda/bin/python'
# from ccpn.framework.PathsAndUrls import CCPN_API_DIRECTORY, CCPN_DIRECTORY_SUFFIX, \
#     CCPN_BACKUP_SUFFIX, CCPN_ARCHIVES_DIRECTORY, CCPN_LOGS_DIRECTORY,  CCPN_SUMMARIES_DIRECTORY


from pathlib import Path as _Path_, _windows_flavour, _posix_flavour


class Path(_Path_):
    """Subclassed for compatibility, convenience and enhancements
    """

    # sub classing is broken
    # From: https://codereview.stackexchange.com/questions/162426/subclassing-pathlib-path
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour

    @property
    def basename(self):
        """the name of self without any suffixes
        """
        return self.name.split('.')[0]

    def addTimeStamp(self):
        """Return a Path instance with path.timeStamp.suffix profile"""
        now = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
        return self.parent / (self.stem + '.' + str(now) + self.suffix)

    @property
    def version(self):
        suffixes = self.suffixes
        version = 0
        if len(suffixes) > 0:
            try:
                version = int(suffixes[0][1:])
            except:
                version = 0
        return version

    def incrementVersion(self):
        """Return a Path instance with path.version.suffix profile"""
        suffixes = self.suffixes
        version = 0
        if len(suffixes) > 0:
            try:
                version = int(suffixes[0][1:])
                suffixes.pop(0)
            except:
                version = 0
        version += 1
        suffixes.insert(0, '.' + str(version))
        return self.parent / (self.basename + ''.join(suffixes))

    def normalise(self):
        return Path(os.path.normpath(self.asString()))  # python <= 3.4; strings only

    def open(self, *args, **kwds):
        """Subclassing to catch any long file name errors that allegedly can occur on windows"""
        try:
            fp = super().open(*args, **kwds)
        except FileNotFoundError:
            if len(self.asString()) > 256:
                raise FileNotFoundError('Error opening file "%s"; potentially path length (%d) is too large. Consider moving the file'
                                        % (self, len(self.asString()))
                                        )
            else:
                raise FileNotFoundError('Error opening file "%s"' % self)
        return fp

    def globList(self, pattern='*'):
        """Return a list rather then a generator
        """
        return [p for p in self.glob(pattern=pattern)]

    def removeDir(self):
        """Recursively remove content of self and sub-directories
        """
        if not self.is_dir():
            raise ValueError('%s is not a directory' % self)
        _rmdirs(str(self))

    def fetchDir(self, dirName):
        """Return and if needed create dirName in self
        :return: Path instance of self / dirName
        """
        if not self.is_dir():
            raise ValueError('%s is not a directory' % self)
        result = self / dirName
        if not result.exists():
            result.mkdir()
        return result

    def removeFile(self):
        """Remove file represented by self.
        """
        if self.is_dir():
            raise ValueError('%s is a directory' % self)
        self.unlink()

    def assureSuffix(self, suffix):
        """Return Path instance with an assured suffix; adds suffic if not present.
        NB: does not change suffix if there is one (like with_suffix does)
        """
        if self.suffix != suffix:
            return self + suffix
        else:
            return self

    def withoutSuffix(self):
        """Return self without suffix
        """
        if len(self.suffixes) > 0:
            return self.with_suffix('')
        else:
            return self

    def withSuffix(self, suffix):
        """Return self with suffix; inverse of withoutSuffix()
        partially copies with_suffix, but does not allow for empty argument
        """
        if suffix is None or len(suffix) == 0:
            raise ValueError('No suffix defined')
        return self.with_suffix(suffix=suffix)

    def split3(self):
        """Return a tuple of (.parent, .stem, .suffix) strings
        """
        return (str(self.parent), str(self.stem), str(self.suffix))

    def split2(self):
        """Return a tuple (.parent, .name) strings
        """
        return (str(self.parent), str(self.name))

    def asString(self):
        "Return self as a string"
        return str(self)

    def startswith(self, prefix):
        "Return True if self starts with prefix"
        path = self.asString()
        return path.startswith(prefix)

    def __len__(self):
        return len(self.asString())

    def __eq__(self, other):
        return (str(self).strip() == str(other).strip())

    def __ne__(self, other):
        return not (str(self).strip() == str(other).strip())

    def __add__(self, other):
        return Path(self.asString() + other)


def _rmdirs(path):
    """Recursively delete path and contents; maybe not very fast
    From: https://stackoverflow.com/questions/303200/how-do-i-remove-delete-a-folder-that-is-not-empty-with-python
    """
    path = Path(path)
    # using glob(*) because interdir() created occasional 'directory not empty' crashes (OS issue; Mac hidden files
    # or timing problems?). Maybe need to fallback on ccpn.util.LocalShutil
    for sub in path.glob('*'):
        if sub.is_dir():
            _rmdirs(sub)  # sub is a directory
        else:
            sub.unlink()  # removes files and links
    path.rmdir()


def aPath(path):
    """Return a ~-expanded, left/right spaces-stripped, normalised Path instance"""
    return Path(str(path).strip()).expanduser().normalise()



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
