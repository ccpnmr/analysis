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
__version__ = "$Revision: 3.0.0 $"
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
import shutil
import sys

from datetime import datetime
from ccpn.util.Update import isBinaryData, DELETEHASHCODE
from ccpn.framework.PathsAndUrls import ccpn2Url

from ccpn.util import Path
from ccpn.ui.gui.widgets import InputDialog
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.util.Logging import getLogger


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

    try:
        with open(filePath, 'rb') as fp:
            data = fp.read()
    except:
        getLogger().warning('error reading data, not Unicode')
        data = ''

    h = hashlib.md5()
    h.update(data)

    return h.hexdigest()


def downloadFile(serverScript, serverDbRoot, fileName):
    """Download a file from the server
    """
    from ccpn.util.Url import fetchHttpResponse

    # fileName = os.path.join(serverDbRoot, fileName)
    fileName = '/'.join([serverDbRoot, fileName])

    try:
        values = {'fileName': fileName}
        response = fetchHttpResponse('POST', serverScript, values, headers=None, proxySettings=None)
        data = response.data

        if isBinaryData(data):
            result = data
        else:
            result = data.decode('utf-8')

            if result.startswith(BAD_DOWNLOAD):
                ll = len(result)
                bd = len(BAD_DOWNLOAD)
                getLogger().warning(Exception(result[min(ll, bd):min(ll, bd + 50)]))
                return

        return result

    except Exception as es:
        getLogger().warning('Download error: %s' % str(es))


def uploadData(serverUser, serverPassword, serverScript, fileData, serverDbRoot, fileStoredAs):
    """Upload a file to the server
    """
    from ccpn.util.Url import fetchHttpResponse

    SERVER_PASSWORD_MD5 = b'c Wo\xfc\x1e\x08\xfc\xd1C\xcb~(\x14\x8e\xdc'

    # early check on password
    m = hashlib.md5()
    m.update(serverPassword.encode('utf-8'))
    if m.digest() != SERVER_PASSWORD_MD5:
        print('>>>>>>Incorrect Password')
        return

    ss = serverUser + ":" + serverPassword
    auth = base64.encodebytes(ss.encode('utf-8'))[:-1]
    authheader = 'Basic %s' % auth

    headers = {'Content-type' : 'application/x-www-form-urlencoded;charset=UTF-8',
               'Authorization': authheader}
    values = {'fileData': fileData, 'fileName': fileStoredAs, 'serverDbRoot': serverDbRoot}

    try:
        response = fetchHttpResponse('POST', serverScript, values, headers=headers, proxySettings=None)
        result = response.data.decode('utf-8')

        if result.startswith(BAD_DOWNLOAD) or not result.startswith('Ok'):
            ll = len(result)
            bd = len(BAD_DOWNLOAD)
            getLogger().warning(Exception(result[min(ll, bd):min(ll, bd + 50)]))
        else:
            print(result[0:min(50, len(result))])
            return result

    except Exception as es:
        getLogger().warning('Upload error: %s' % str(es))


def uploadFile(serverUser, serverPassword, serverScript, fileName, serverDbRoot, fileStoredAs):
    """Upload a file to the server
    """
    # fp = open(fileName, 'rU')
    try:
        with open(fileName, 'rb') as fp:
            fileData = fp.read()
    except Exception as es:
        getLogger().warning('error reading file,', str(es))
        fileData = ''

    if fileData:
        return uploadData(serverUser, serverPassword, serverScript, fileData, serverDbRoot, fileStoredAs)


def uploadFileForDelete(serverUser, serverPassword, serverScript, fileName, serverDbRoot, fileStoredAs):
    """Upload a file to the server
    """
    try:
        fileData = DELETEHASHCODE

    except Exception as es:
        getLogger().warning('error reading file,', str(es))
        fileData = ''

    if fileData:
        return uploadData(serverUser, serverPassword, serverScript, fileData, serverDbRoot, fileStoredAs)


def isBinaryData(data):
    """Check whether the byte-string is binary
    """
    if data:
        # check the first 1024 bytes of the file
        firstData = data[0:max(1024, len(data))]
        try:
            firstData = bytearray(firstData)
        except:
            firstData = bytearray(firstData, encoding='utf-8')

        # remove all characters that are considered as text
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        isBinary = bool(firstData.translate(None, textchars))

        return isBinary


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

        if not data:
            return

        fullFilePath = self.fullFilePath
        if os.path.isfile(fullFilePath):
            # backup what is there just in case
            shutil.copyfile(fullFilePath, fullFilePath + '__old')
        else:
            directory = os.path.dirname(fullFilePath)
            if not os.path.exists(directory):
                os.makedirs(directory)
        # with open(fullFilePath, 'w') as fp:
        #     fp.write(data)

        if isBinaryData(data):
            # always write binary files
            with open(fullFilePath, 'wb') as fp:
                fp.write(data)
        else:
            # backwards compatible check for half-updated - file contains DELETEHASHCODE as text
            if data and data.startswith(DELETEHASHCODE):
                try:
                    os.remove(fullFilePath)
                except OSError:
                    pass
            else:
                with open(fullFilePath, 'w', encoding='utf-8') as fp:
                    fp.write(data)


    def installDeleteUpdate(self):
        """Remove file as update action
        """
        # not sure if required in this module
        fullFilePath = self.fullFilePath
        try:
            os.remove(fullFilePath)
        except OSError:
            pass

    def commitUpdate(self, serverUser, serverPassword):

        uploadFile(serverUser, serverPassword, self.serverUploadScript, self.fullFilePath, self.serverDbRoot, self.fileStoredAs)
        self.fileHashCode = calcHashCode(self.fullFilePath)

    def commitDeleteUpdate(self, serverUser, serverPassword):

        uploadFileForDelete(serverUser, serverPassword, self.serverUploadScript, self.fullFilePath, self.serverDbRoot, self.fileStoredAs)
        self.fileHashCode = DELETEHASHCODE


class UpdateAgent(object):

    def _init(self, version, showError=None, showInfo=None, askPassword=None,
              serverUser=None, server=SERVER, serverDbRoot=SERVER_DB_ROOT, serverDbFile=SERVER_DB_FILE,
              serverDownloadScript=SERVER_DOWNLOAD_SCRIPT, serverUploadScript=SERVER_UPLOAD_SCRIPT,
              dryRun=True):

        if not showError:
            showError = MessageDialog.showError

        if not showInfo:
            showInfo = MessageDialog.showInfo

        if not askPassword:
            askPassword = InputDialog.askPassword

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
        #self.serverDownloadScript = '%s%s' % (server, serverDownloadScript)
        #self.serverUploadScript = '%s%s' % (server, serverUploadScript)

        self.installLocation = Path.getTopDirectory()
        self.updateFiles = []
        self.updateFileDict = {}
        self._dryRun = dryRun

    def checkNumberUpdates(self):
        self.fetchUpdateDb()
        return len(self.updateFiles)

    def fetchUpdateDb(self):
        """Fetch list of updates from server. Specificallly for updateAdmin
        """
        self.updateFiles = updateFiles = []
        self.updateFileDict = updateFileDict = {}
        serverDownloadScript = '%s%s' % (self.server, self.serverDownloadScript)
        serverUploadScript = '%s%s' % (self.server, self.serverUploadScript)
        data = downloadFile(serverDownloadScript, self.serverDbRoot, self.serverDbFile)

        # if data.startswith(BAD_DOWNLOAD):
        #     raise Exception('Could not download database file from server')
        if not data:
            return

        lines = data.split('\n')
        if lines:
            version = lines[0].strip()
            #if not VERSION_RE.match(version):
            #  raise Exception('First line of server database file = %s, does not match a version number' % version)

            if version != self.version:
                raise Exception('Server database version = %s != %s = program version' % (version, self.version))

            for line in lines[1:]:
                line = line.rstrip()
                if line:
                    (filePath, fileTime, fileStoredAs, fileHashCode) = line.split(FIELD_SEP)

                    # specifically fro updateAdmin, so show ALL files in the list

                    # if fileHashCode == DELETEHASHCODE:
                    #     # delete file
                    #     if os.path.exists(os.path.join(self.installLocation, filePath)) or fileTime in [0, '0', '0.0']:
                    #
                    #         # if still exists then need to add to update list
                    #         updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime,
                    #                                 fileStoredAs, fileHashCode, serverDownloadScript=serverDownloadScript,
                    #                                 serverUploadScript=serverUploadScript)
                    #         updateFiles.append(updateFile)
                    #         updateFileDict[filePath] = updateFile
                    #
                    # elif self.serverUser or self.isUpdateDifferent(filePath, fileHashCode):
                    #
                    #     # file exists, is modified and needs updating
                    #     updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime, fileStoredAs, fileHashCode,
                    #                             serverDownloadScript=serverDownloadScript, serverUploadScript=serverUploadScript)
                    #     updateFiles.append(updateFile)
                    #     updateFileDict[filePath] = updateFile
                    #
                    # elif fileTime in [0, '0', '0.0']:
                    #   file exists, is modified and needs updating
                    #
                    updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime, fileStoredAs, fileHashCode,
                                            serverDownloadScript=serverDownloadScript, serverUploadScript=serverUploadScript)
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
                    updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, shouldCommit=True, isNew=True,
                                            serverDownloadScript=serverDownloadScript, serverUploadScript=serverUploadScript)
                    self.updateFiles.append(updateFile)
                    self.updateFileDict[filePath] = updateFile
            else:
                print('Ignoring "%s", not on installation path "%s"' % (filePath, installLocation))
                installErrorCount += 1

        if installErrorCount > 0:
            self.showError('Add file error', '%d file%s not added because not on installation path %s' % (
                installErrorCount, installErrorCount > 1 and 's' or '', installLocation))

        if existsErrorCount > 0:
            self.showError('Add file error', '%d file%s not added because already in update list (but now selected for committal)' % (
                existsErrorCount, existsErrorCount > 1 and 's' or ''))

    def haveWriteAccess(self):
        """See if can write files to local installation."""

        testFile = os.path.join(self.installLocation, '__write_test__')
        try:
            with open(testFile, 'w'):
                pass
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

            # check that the last file to be updated is the Version.py
            _allowVersionUpdate = True if (len(updateFiles) == 1 and updateFiles[0].filePath == 'src/python/ccpn/framework/Version.py') else False

            for updateFile in updateFiles:

                # double-check that it is the last file
                if not _allowVersionUpdate and updateFile.filePath == 'src/python/ccpn/framework/Version.py':
                    continue

                try:
                    if not self._dryRun:
                        if updateFile.fileHashCode == DELETEHASHCODE:
                            print('Install Updates: Removing %s' % (updateFile.fullFilePath))
                            updateFile.installDeleteUpdate()
                        else:
                            print('Install Updates: Installing %s' % (updateFile.fullFilePath))
                            updateFile.installUpdate()
                    else:
                        if updateFile.fileHashCode == DELETEHASHCODE:
                            print('Install Updates: dry-run Removing %s' % (updateFile.fullFilePath))
                        else:
                            print('Install Updates: dry-run Installing %s' % (updateFile.fullFilePath))

                    n += 1

                except Exception as e:
                    print('Could not install %s: %s' % (updateFile.fullFilePath, e))

            ss = n != 1 and 's' or ''
            if n != len(updateFiles):
                self.showError('Update problem', '%d update%s installed, %d not installed, see console for error messages' % (n, ss, len(updateFiles) - n))
            else:
                self.showInfo('Update%s installed' % ss, '%d update%s installed successfully' % (n, ss))
        else:
            self.showError('No write permission', 'You do not have write permission in the CCPN installation directory')

        self.resetFromServer()

    def installUpdates(self):

        for updateFile in self.updateFiles:
            updateFile.shouldInstall = True

        self.installChosen()

    def commitChosen(self):
        """Copy chosen local files to server."""

        updateFiles = [updateFile for updateFile in self.updateFiles if updateFile.shouldCommit]
        if not updateFiles:
            self.showError('No updates', 'No updates chosen for committing')
            return

        serverPassword = self.askPassword('Password', 'Enter password for %s on server' % self.serverUser)

        if not serverPassword:
            return

        n = 0
        for updateFile in updateFiles:
            try:
                if os.path.exists(updateFile.fullFilePath):
                    print('Committing %s' % (updateFile.fullFilePath))
                    updateFile.commitUpdate(self.serverUser, serverPassword)

                else:
                    # file is to be deleted - add empty file
                    print('Committing file to be deleted %s' % (updateFile.fullFilePath))
                    updateFile.commitDeleteUpdate(self.serverUser, serverPassword)

                n += 1

            except Exception as e:
                raise
                # seem to need str(e) below because o/w HTTPError (from bad pwd) not printed out
                print('Could not commit %s: %s' % (updateFile.fullFilePath, str(e)))

        ss = '' if n == 1 else 's'
        if n != len(updateFiles):
            self.showError('Commit problem', '%d update%s committed, %d not committed, see console for error messages' % (n, ss, len(updateFiles) - n))
            return

        try:
            self.commitUpdateDb(serverPassword, updateFiles)
        except Exception as e:
            self.showError('Commit problem', 'Commit of database to server exception: %s' % e)
            return

        self.showInfo('Update%s committed' % ss, '%d update%s committed successfully' % (n, ss))

        self.resetFromServer()

    def commitUpdateDb(self, serverPassword, updateFiles):

        # in theory this could be done at the server end, only that would mean looking
        # through the existing db file to see which file timestamps needed updating
        # and then appending new files, so much more complicated (but less bandwidth)
        xx = [self.version]
        for updateFile in self.updateFiles:
            fileTime = updateFile.fileLocalTime if updateFile in updateFiles else updateFile.fileServerTime
            text = '\t'.join((updateFile.filePath, '%.f' % fileTime, updateFile.fileStoredAs, updateFile.fileHashCode))
            xx.append(text)

        fileData = '\n'.join(xx) + '\n'

        serverUploadScript = '%s%s' % (self.server, self.serverUploadScript)
        return uploadData(self.serverUser, serverPassword, serverUploadScript, fileData, self.serverDbRoot, self.serverDbFile)

    def _actionUpdateDb(self, serverPassword, serverScript, actionFile):

        # in theory this could be done at the server end, only that would mean looking
        # through the existing db file to see which file timestamps needed updating
        # and then appending new files, so much more complicated (but less bandwidth)

        serverUploadScript = '%s%s' % (self.server, serverScript)
        return uploadData(self.serverUser, serverPassword, serverUploadScript, actionFile, self.serverDbRoot, '')

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
                    with open(fullFilePath, 'rU', encoding='utf-8') as fp:
                        localLines = fp.readlines()
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
