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

import difflib
import hashlib
import os
import shutil
import sys
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
SERVER_DOWNLOADCHECK_SCRIPT = 'cgi-bin/register/downloadFileCheckV3'

FIELD_SEP = '\t'
PATH_SEP = '__sep_'
WHITESPACE_AND_NULL = {'\x00', '\t', '\n', '\r', '\x0b', '\x0c'}

# require only . and numbers and at least one of these
# 23 Nov 2015: remove below RE because version can have letter in it, so just do exact match
###VERSION_RE = re.compile('^[.\d]+$')

BAD_DOWNLOAD = 'Exception: '
DELETEHASHCODE = '<DELETE>'
TERMSANDCONDITIONS = 'termsConditions'


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
    try:
        with open(filePath, 'rb') as fp:
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
        try:
            firstData = bytearray(firstData)
        except:
            firstData = bytearray(firstData, encoding='utf-8')

        # remove all characters that are considered as text
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        isBinary = bool(firstData.translate(None, textchars))

        return isBinary


def fetchUrl(url, data=None, headers=None, timeout=2.0, decodeResponse=True):
    """Fetch url request from the server
    """
    from ccpn.util.Url import fetchHttpResponse
    from ccpn.util.UserPreferences import UserPreferences

    try:
        _userPreferences = UserPreferences(readPreferences=True)
        proxySettings = None
        if _userPreferences.proxyDefined:
            proxyNames = ['useProxy', 'proxyAddress', 'proxyPort', 'useProxyPassword',
                          'proxyUsername', 'proxyPassword']
            proxySettings = {}
            for name in proxyNames:
                proxySettings[name] = _userPreferences._getPreferencesParameter(name)

        response = fetchHttpResponse('POST', url, data, headers=headers, proxySettings=proxySettings)

        # if response:
        #     ll = len(response.data)
        #     print('>>>>>>responseUpdate', proxySettings, response.data[0:min(ll, 20)])

        return response.data.decode('utf-8') if decodeResponse else response
    except:
        print('Error fetching Url.')


def downloadFile(serverScript, serverDbRoot, fileName):
    """Download a file from the server
    """
    fileName = os.path.join(serverDbRoot, fileName)

    try:
        values = {'fileName': fileName}
        response = fetchUrl(serverScript, values, decodeResponse=False)
        data = response.data

        if isBinaryData(data):
            result = data
        else:
            result = data.decode('utf-8')

            if result.startswith(BAD_DOWNLOAD):
                ll = len(result)
                bd = len(BAD_DOWNLOAD)
                print(str(Exception(result[min(ll, bd):min(ll, bd + 50)])))
                return

        return result

    except Exception as es:
        print('Error downloading file from server.')


def installUpdates(version, dryRun=True):
    updateAgent = UpdateAgent(version, dryRun=dryRun)
    updateAgent.resetFromServer()
    updateAgent.installUpdates()
    if updateAgent._check():
        updateAgent._resetMd5()


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
        """Install updated file
        """
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

        try:
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

        except Exception as es:
            pass

    def installDeleteUpdate(self):
        """Remove file as update action
        """
        fullFilePath = self.fullFilePath
        try:
            os.remove(fullFilePath)
        except OSError:
            pass

    # def commitUpdate(self, serverUser, serverPassword):
    #
    #     uploadFile(serverUser, serverPassword, self.serverUploadScript, self.fullFilePath, self.serverDbRoot,
    #                self.fileStoredAs)
    #     self.fileHashCode = calcHashCode(self.fullFilePath)


class UpdateAgent(object):

    def __init__(self, version, showError=None, showInfo=None, askPassword=None,
                 serverUser=None, server=SERVER, serverDbRoot=SERVER_DB_ROOT, serverDbFile=SERVER_DB_FILE,
                 serverDownloadScript=SERVER_DOWNLOAD_SCRIPT, serverUploadScript=SERVER_UPLOAD_SCRIPT,
                 dryRun=True):

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
        self._serverDownloadCheckScript = SERVER_DOWNLOADCHECK_SCRIPT
        self.serverUploadScript = serverUploadScript
        # self.serverDownloadScript = '%s%s' % (server, serverDownloadScript)
        # self.serverUploadScript = '%s%s' % (server, serverUploadScript)

        self.installLocation = Path.getTopDirectory()
        self.updateFiles = []
        self.updateFileDict = {}
        self._found = None
        self._dryRun = dryRun

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

                    if fileHashCode == DELETEHASHCODE:
                        # delete file
                        if os.path.exists(os.path.join(self.installLocation, filePath)):

                            # if still exists then need to add to update list
                            updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime,
                                                    fileStoredAs, fileHashCode, serverDownloadScript=serverDownloadScript,
                                                    serverUploadScript=serverUploadScript)
                            updateFiles.append(updateFile)
                            updateFileDict[filePath] = updateFile

                    elif self.serverUser or self.isUpdateDifferent(filePath, fileHashCode):

                        # file exists, is modified and needs updating
                        updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, fileTime,
                                                fileStoredAs, fileHashCode, serverDownloadScript=serverDownloadScript,
                                                serverUploadScript=serverUploadScript)
                        updateFiles.append(updateFile)
                        updateFileDict[filePath] = updateFile

                    elif fileTime in [0, '0', '0.0']:

                        # file exists, is modified and needs updating
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

    def _check(self):
        """Check the checkSum from the gui
        """
        try:
            self._checkMd5()
        except:
            pass
        finally:
            return self._found is not None and 'valid' not in self._found

    def _checkMd5(self):
        """Check the checkSum status on the server
        """
        serverDownloadScript = '%s%s' % (self.server, self._serverDownloadCheckScript)

        try:
            self._numAdditionalUpdates = 0
            self._found = 'invalid'
            from ccpn.util.Register import userAttributes, loadDict, _otherAttributes, _insertRegistration

            registrationDict = loadDict()
            val2 = _insertRegistration(registrationDict)
            values = {}
            for attr in userAttributes + _otherAttributes:
                value = []
                for c in registrationDict[attr]:
                    value.append(c if 32 <= ord(c) < 128 else '_')
                values[attr] = ''.join(value)
            values.update(val2)
            values['version'] = self.version

            self._found = fetchUrl(serverDownloadScript, values, timeout=2.0, decodeResponse=True)
            if isinstance(self._found, str):
                # file returns with EOF chars on the end
                self._found = self._found.rstrip('\r\n')

        except:
            self.showError('Update error', 'Could not check details on server.')

    def _resetMd5(self):
        # only write the file if it is non-empty
        if self._found:
            # from ccpn.util.UserPreferences import userPreferencesDirectory, ccpnConfigPath
            from ccpn.framework.PathsAndUrls import userPreferencesDirectory, ccpnConfigPath

            fname = ''.join([c for c in map(chr, (108, 105, 99, 101, 110, 99, 101, 75, 101, 121, 46, 116, 120, 116))])
            lfile = os.path.join(userPreferencesDirectory, fname)
            if not os.path.exists(lfile):
                lfile = os.path.join(ccpnConfigPath, fname)
            with open(lfile, 'w', encoding='UTF-8') as fp:
                fp.write(self._found)

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

                    self.showInfo('Add Files', 'File %s already in updates' % filePath)
                    existsErrorCount += 1
                else:
                    updateFile = UpdateFile(self.installLocation, self.serverDbRoot, filePath, shouldCommit=True,
                                            isNew=True, serverDownloadScript=serverDownloadScript,
                                            serverUploadScript=serverUploadScript)
                    self.updateFiles.append(updateFile)
                    self.updateFileDict[filePath] = updateFile
            else:
                self.showInfo('Ignoring Files', 'Ignoring "%s", not on installation path "%s"' % (filePath, installLocation))
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

        n = 0
        updateFilesInstalled = []

        if self.haveWriteAccess():

            # check that the last file to be updated is the Version.py
            _allowVersionUpdate = True if (len(updateFiles) == 1 and updateFiles[0].filePath == 'src/python/ccpn/framework/Version.py') else False

            for updateFile in updateFiles:

                # double-check that it is the last file
                if not _allowVersionUpdate and updateFile.filePath == 'src/python/ccpn/framework/Version.py':
                    continue

                try:
                    if not self._dryRun:
                        if updateFile.fileHashCode == DELETEHASHCODE:
                            self.showInfo('Install Updates', 'Removing %s' % (updateFile.fullFilePath))
                            updateFile.installDeleteUpdate()

                        else:
                            self.showInfo('Install Updates', 'Installing %s' % (updateFile.fullFilePath))
                            updateFile.installUpdate()
                    else:
                        if updateFile.fileHashCode == DELETEHASHCODE:
                            self.showInfo('Install Updates', 'dry-run Removing %s' % (updateFile.fullFilePath))
                        else:
                            self.showInfo('Install Updates', 'dry-run Installing %s' % (updateFile.fullFilePath))

                    n += 1
                    updateFilesInstalled.append(updateFile)
                except Exception as e:
                    self.showError('Install Error', 'Could not install %s: %s' % (updateFile.fullFilePath, e))

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

        return updateFilesInstalled

    def installUpdates(self):

        for updateFile in self.updateFiles:
            updateFile.shouldInstall = True

        return self.installChosen()

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


if __name__ == '__main__':
    from ccpn.framework.Version import applicationVersion
    # applicationVersion = __version__.split()[1]  # ejb - read from the header
    installUpdates(applicationVersion, dryRun=False)
