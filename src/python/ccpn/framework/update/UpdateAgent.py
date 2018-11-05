import base64
import difflib
import hashlib
import os
import re
import shutil
import sys
import ssl
import time
import urllib
from urllib.parse import urlencode, quote
from urllib.request import urlopen
import urllib3.contrib.pyopenssl
import certifi

from datetime import datetime

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

    # fp = open(filePath, 'rU', encoding='utf-8')
    fp = open(filePath, 'rb')
    try:
        data = fp.read()
    except:
        getLogger().warning('error reading data, not Unicode')
        data = ''
    fp.close()

    h = hashlib.md5()
    # h.update(data.encode('utf-8'))
    h.update(data)

    return h.hexdigest()


def downloadFile(serverScript, serverDbRoot, fileName):
    """Download a file from the server
    """
    fileName = os.path.join(serverDbRoot, fileName)

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    headers = {'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8'}
    body = urlencode({'fileName': fileName}, quote_via=quote).encode('utf-8')

    urllib3.contrib.pyopenssl.inject_into_urllib3()
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where(),
                               timeout=urllib3.Timeout(connect=5.0, read=5.0),
                               retries=urllib3.Retry(1, redirect=False))

    try:
        response = http.request('POST', serverScript,
                                headers=headers,
                                body=body,
                                preload_content=False)
        result = response.read().decode('utf-8')

        if result.startswith(BAD_DOWNLOAD):
            getLogger().warning(Exception(result[len(BAD_DOWNLOAD):]))
        else:
            return result
    except Exception as es:
        getLogger().warning('Download error: %s' % str(es))


def uploadData(serverUser, serverPassword, serverScript, fileData, serverDbRoot, fileStoredAs):
    """Upload a file to the server
    """
    SERVER_PASSWORD_MD5 = b'c Wo\xfc\x1e\x08\xfc\xd1C\xcb~(\x14\x8e\xdc'

    # early check on password
    m = hashlib.md5()
    m.update(serverPassword.encode('utf-8'))
    if m.digest() != SERVER_PASSWORD_MD5:
        raise Exception('incorrect password')

    ss = serverUser + ":" + serverPassword
    auth = base64.encodebytes(ss.encode('utf-8'))[:-1]
    authheader = 'Basic %s' % auth

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    headers = {'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
               'Authorization': authheader}
    body = urlencode({'fileData': fileData, 'fileName': fileStoredAs, 'serverDbRoot': serverDbRoot},
                     quote_via=quote).encode('utf-8')

    urllib3.contrib.pyopenssl.inject_into_urllib3()
    http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                               ca_certs=certifi.where(),
                               timeout=urllib3.Timeout(connect=5.0, read=5.0),
                               retries=urllib3.Retry(1, redirect=False))

    try:
        response = http.request('POST', serverScript,
                                headers=headers,
                                body=body,
                                preload_content=False)
        result = response.read().decode('utf-8')

        if result.startswith(BAD_DOWNLOAD):
            getLogger().warning(Exception(result[len(BAD_DOWNLOAD):]))
        else:
            return result

    except Exception as es:
        getLogger().warning('Upload error: %s' % str(es))


def uploadFile(serverUser, serverPassword, serverScript, fileName, serverDbRoot, fileStoredAs):
    """Upload a file to the server
    """
    # fp = open(fileName, 'rU')
    fp = open(fileName, 'rb')
    try:
        fileData = fp.read()
    except:
        getLogger().warning('error reading file, not unicode')
        fileData = ''
    fp.close()

    return uploadData(serverUser, serverPassword, serverScript, fileData, serverDbRoot, fileStoredAs)


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
        fp = open(fullFilePath, 'w')
        fp.write(data)
        fp.close()

    def commitUpdate(self, serverUser, serverPassword):

        uploadFile(serverUser, serverPassword, self.serverUploadScript, self.fullFilePath, self.serverDbRoot, self.fileStoredAs)
        self.fileHashCode = calcHashCode(self.fullFilePath)


class UpdateAgent(object):

    def _init(self, version, showError=None, showInfo=None, askPassword=None,
              serverUser=None, server=SERVER, serverDbRoot=SERVER_DB_ROOT, serverDbFile=SERVER_DB_FILE,
              serverDownloadScript=SERVER_DOWNLOAD_SCRIPT, serverUploadScript=SERVER_UPLOAD_SCRIPT):

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
                    if self.serverUser or self.isUpdateDifferent(filePath, fileHashCode):
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
                print('Committing %s' % (updateFile.fullFilePath))
                updateFile.commitUpdate(self.serverUser, serverPassword)
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
