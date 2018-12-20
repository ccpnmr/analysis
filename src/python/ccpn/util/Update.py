"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 15:21:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import base64
import difflib
import hashlib
import os
import re
import shutil
import sys
import time
import urllib
from urllib.parse import urlencode
from urllib.request import urlopen

from datetime import datetime


ccpn2Url = 'http://www.ccpn.ac.uk'

from ccpn.util import Path


SERVER = ccpn2Url + '/'
SERVER_DB_ROOT = 'ccpNmrUpdate'
SERVER_DB_FILE = '__UpdateData.db'
# the reason to use a CGI script just to download a file is because of exception handling
# when you just fetch a URL you always get a response but how do you know it is valid
# (and not a 404 or whatever)
SERVER_DOWNLOAD_SCRIPT = 'cgi-bin/update/downloadFile'
SERVER_UPLOAD_SCRIPT = 'cgi-bin/updateadmin/uploadFile'

FIELD_SEP = '\t'
PATH_SEP = '__sep_'
WHITESPACE_AND_NULL = {'\x00', '\t', '\n', '\r', '\x0b', '\x0c'}

# require only . and numbers and at least one of these
# 23 Nov 2015: remove below RE because version can have letter in it, so just do exact match
###VERSION_RE = re.compile('^[.\d]+$')

BAD_DOWNLOAD = 'Exception: '


def lastModifiedTime(filePath):
    if not os.path.isfile(filePath):
        return 0

    if not os.access(filePath, os.R_OK):
        return 0

    return os.stat(filePath).st_mtime


def calcHashCode(filePath):
    if not os.path.isfile(filePath):
        return 0

    if not os.access(filePath, os.R_OK):
        return 0

    # fp = open(filePath, 'rU', encoding='utf-8')
    fp = open(filePath, 'rb')
    try:
        data = fp.read()
    except:
        data = ''

    h = hashlib.md5()
    # h.update(data.encode('utf-8'))
    h.update(data)

    return h.hexdigest()


def isBinaryFile(fileName):
    """Check whether the fileName is a binary file (not always guaranteed)
    Doesn't check for a fullPath
    Returns False if the file does not exist
    """
    if os.path.isfile(fileName):
        with open(fileName, 'rb') as fileObj:
            # read the first 1024 bytes of the file
            firstData = fileObj.read(1024)

            # remove all characters that are considered as text
            textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
            isBinary = bool(firstData.translate(None, textchars))

            return isBinary


def isBinaryData(data):
    """Check whether the byte-string is binary
    """
    if data:
        # check the first 1024 bytes of the file
        firstData = data[0:max(1024, len(data))]
        firstData = bytearray(firstData, encoding='utf-8')

        # remove all characters that are considered as text
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        isBinary = bool(firstData.translate(None, textchars))

        return isBinary


def downloadFile(serverScript, serverDbRoot, fileName):
    import ssl

    context = ssl._create_unverified_context()

    fileName = os.path.join(serverDbRoot, fileName)

    addr = '%s?fileName=%s' % (serverScript, fileName)
    try:
        response = urlopen(addr, context=context)

        data = response.read()  # just split for testing
        data = data.decode('utf-8')
        response.close()

        if data.startswith(BAD_DOWNLOAD):
            raise Exception(data[len(BAD_DOWNLOAD):])

        return data
    except:
        return None


def installUpdates(version):
    updateAgent = UpdateAgent(version)
    updateAgent.resetFromServer()
    updateAgent.installUpdates()


class UpdateFile:

    def __init__(self, installLocation, serverDbRoot, filePath, fileServerTime=None,
                 fileStoredAs=None, fileHashCode=None, shouldInstall=True, shouldCommit=False,
                 isNew=False, serverDownloadScript=None, serverUploadScript=None):

        self.fullFilePath = os.path.join(installLocation, filePath)

        if fileServerTime:
            fileServerTime = float(fileServerTime)  # from server it comes as a string

        if not fileStoredAs:
            fileStoredAs = PATH_SEP.join(filePath.split('/'))

        if not fileHashCode:
            fileHashCode = calcHashCode(self.fullFilePath)

        self.installLocation = installLocation
        self.serverDbRoot = serverDbRoot
        self.filePath = filePath
        self.fileServerTime = fileServerTime
        self.fileStoredAs = fileStoredAs
        self.fileHashCode = fileHashCode
        self.shouldInstall = shouldInstall
        self.shouldCommit = shouldCommit
        self.isNew = isNew
        self.serverDownloadScript = serverDownloadScript
        self.serverUploadScript = serverUploadScript

        self.fileLocalTime = lastModifiedTime(self.fullFilePath)

        self.fileServerDateTime = str(datetime.fromtimestamp(fileServerTime)) if fileServerTime else ''
        self.fileLocalDateTime = str(datetime.fromtimestamp(self.fileLocalTime))
        self.fileName = os.path.basename(filePath)
        self.fileDir = os.path.dirname(filePath)

    def installUpdate(self):

        data = downloadFile(self.serverDownloadScript, self.serverDbRoot, self.fileStoredAs)

        fullFilePath = self.fullFilePath
        if os.path.isfile(fullFilePath):
            # backup what is there just in case
            shutil.copyfile(fullFilePath, fullFilePath + '__old')
        else:
            directory = os.path.dirname(fullFilePath)
            if not os.path.exists(directory):
                os.makedirs(directory)

        if isBinaryData(data):
            with open(fullFilePath, 'wb') as fp:
                fp.write(data)
        else:
            with open(fullFilePath, 'w', encoding='utf-8') as fp:
                fp.write(data)

        # fp = open(fullFilePath, 'w')
        # fp.write(data)
        # fp.close()

    def commitUpdate(self, serverUser, serverPassword):

        uploadFile(serverUser, serverPassword, self.serverUploadScript, self.fullFilePath, self.serverDbRoot,
                   self.fileStoredAs)
        self.fileHashCode = calcHashCode(self.fullFilePath)


class UpdateAgent(object):

    def __init__(self, version, showError=None, showInfo=None, askPassword=None,
                 serverUser=None, server=SERVER, serverDbRoot=SERVER_DB_ROOT, serverDbFile=SERVER_DB_FILE,
                 serverDownloadScript=SERVER_DOWNLOAD_SCRIPT, serverUploadScript=SERVER_UPLOAD_SCRIPT):

        if not showError:
            # showError = MessageDialog.showError
            showError = lambda title, msg: print(msg)

        if not showInfo:
            # showInfo = MessageDialog.showInfo
            showInfo = lambda title, msg: print(msg)

        # if not askPassword:
        #  askPassword = InputDialog.askPassword

        self.version = version
        self.showError = showError
        self.showInfo = showInfo
        self.askPassword = askPassword
        self.serverUser = serverUser  # None for downloads, not None for uploads
        self.server = server
        self.serverDbRoot = '%s%s' % (serverDbRoot, version)
        self.serverDbFile = serverDbFile
        self.serverDownloadScript = serverDownloadScript
        self.serverUploadScript = serverUploadScript
        # self.serverDownloadScript = '%s%s' % (server, serverDownloadScript)
        # self.serverUploadScript = '%s%s' % (server, serverUploadScript)

        self.installLocation = Path.getTopDirectory()
        self.updateFiles = []
        self.updateFileDict = {}

    def checkNumberUpdates(self):
        self.fetchUpdateDb()
        return len(self.updateFiles)

    def fetchUpdateDb(self):
        """Fetch list of updates from server."""

        self.updateFiles = updateFiles = []
        self.updateFileDict = updateFileDict = {}
        serverDownloadScript = '%s%s' % (self.server, self.serverDownloadScript)
        serverUploadScript = '%s%s' % (self.server, self.serverUploadScript)
        data = downloadFile(serverDownloadScript, self.serverDbRoot, self.serverDbFile)

        if not data:
            return

        if data.startswith(BAD_DOWNLOAD):
            raise Exception('Could not download database file from server')

        lines = data.split('\n')
        if lines:
            version = lines[0].strip()
            # if not VERSION_RE.match(version):
            #  raise Exception('First line of server database file = %s, does not match a version number' % version)

            if version != self.version:
                raise Exception('Server database version = %s != %s = program version' % (version, self.version))

            for line in lines[1:]:
                line = line.rstrip()
                if line:
                    (filePath, fileTime, fileStoredAs, fileHashCode) = line.split(FIELD_SEP)
                    if self.serverUser or self.isUpdateDifferent(filePath, fileHashCode):
                        updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime,
                                                fileStoredAs, fileHashCode, serverDownloadScript=serverDownloadScript,
                                                serverUploadScript=serverUploadScript)
                        updateFiles.append(updateFile)
                        updateFileDict[filePath] = updateFile

    def isUpdateDifferent(self, filePath, fileHashCode):
        """See if local file is different from server file."""

        currentFilePath = os.path.join(self.installLocation, filePath)
        if os.path.exists(currentFilePath):
            currentHashCode = calcHashCode(currentFilePath)
            isDifferent = (currentHashCode != fileHashCode)
        # below means that updates in new directories will be missed
        elif os.path.exists(os.path.dirname(currentFilePath)):
            isDifferent = True
        else:
            # this is a hack so that updates that don't belong are excluded
            isDifferent = False

        return isDifferent

    def resetFromServer(self):

        try:
            self.fetchUpdateDb()
        except Exception as e:
            self.showError('Update error', 'Could not fetch updates: %s' % e)

    def addFiles(self, filePaths):

        serverDownloadScript = '%s%s' % (self.server, self.serverDownloadScript)
        serverUploadScript = '%s%s' % (self.server, self.serverUploadScript)
        installLocation = self.installLocation
        installErrorCount = 0
        existsErrorCount = 0
        for filePath in filePaths:
            if filePath.startswith(installLocation):
                filePath = filePath[len(installLocation) + 1:]
                if filePath in self.updateFileDict:
                    updateFile = self.updateFileDict[filePath]
                    updateFile.shouldCommit = True
                    print('File %s already in updates' % filePath)
                    existsErrorCount += 1
                else:
                    updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, shouldCommit=True,
                                            isNew=True, serverDownloadScript=serverDownloadScript,
                                            serverUploadScript=serverUploadScript)
                    self.updateFiles.append(updateFile)
                    self.updateFileDict[filePath] = updateFile
            else:
                print('Ignoring "%s", not on installation path "%s"' % (filePath, installLocation))
                installErrorCount += 1

        if installErrorCount > 0:
            self.showError('Add file error', '%d file%s not added because not on installation path %s' % (
                installErrorCount, installErrorCount > 1 and 's' or '', installLocation))

        if existsErrorCount > 0:
            self.showError('Add file error',
                           '%d file%s not added because already in update list (but now selected for committal)' % (
                               existsErrorCount, existsErrorCount > 1 and 's' or ''))

    def haveWriteAccess(self):
        """See if can write files to local installation."""

        testFile = os.path.join(self.installLocation, '__write_test__')
        try:
            fp = open(testFile, 'w')
            fp.close()
            os.remove(testFile)
            return True
        except:
            return False

    def installChosen(self):
        """Download chosen server files to local installation."""

        updateFiles = [updateFile for updateFile in self.updateFiles if updateFile.shouldInstall]
        if not updateFiles:
            self.showError('No updates', 'No updates for installation')
            return

        if self.haveWriteAccess():
            n = 0
            for updateFile in updateFiles:
                try:
                    print('Installing %s' % (updateFile.fullFilePath))
                    updateFile.installUpdate()
                    n += 1
                except Exception as e:
                    print('Could not install %s: %s' % (updateFile.fullFilePath, e))

            ss = n != 1 and 's' or ''
            if n != len(updateFiles):
                self.showError('Update problem',
                               '%d update%s installed, %d not installed, see console for error messages' % (
                                   n, ss, len(updateFiles) - n))
            else:
                self.showInfo('Update%s installed' % ss, '%d update%s installed successfully' % (n, ss))
        else:
            self.showError('No write permission', 'You do not have write permission in the CCPN installation directory')

        self.resetFromServer()

    def installUpdates(self):

        for updateFile in self.updateFiles:
            updateFile.shouldInstall = True

        self.installChosen()

    def diffUpdates(self, updateFiles=None, write=sys.stdout.write):

        if updateFiles is None:
            updateFiles = []

        serverDownloadScript = '%s%s' % (self.server, self.serverDownloadScript)
        for updateFile in updateFiles:
            fullFilePath = updateFile.fullFilePath
            write(60 * '*' + '\n')
            write('Diff for %s\n' % fullFilePath)
            if os.path.exists(fullFilePath):
                if updateFile.isNew:
                    write('No server copy of file\n')
                else:
                    haveDiff = False
                    localLines = open(fullFilePath, 'rU', encoding='utf-8').readlines()
                    serverData = downloadFile(serverDownloadScript, self.serverDbRoot, updateFile.fileStoredAs)
                    if serverData:
                        serverLines = serverData.splitlines(True)
                        for line in difflib.context_diff(localLines, serverLines, fromfile='local', tofile='server'):
                            haveDiff = True
                            write(line)
                        if haveDiff:
                            write('\n')
                        else:
                            write('No diff\n')
                    else:
                        write('No file on server')
            else:
                write('No local copy of file\n')


if __name__ == '__main__':
    applicationVersion = __version__.split()[1]  # ejb - read from the header
    installUpdates(applicationVersion)
