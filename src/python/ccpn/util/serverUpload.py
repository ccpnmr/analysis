#!/usr/bin/python
"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import cgi
import os
import sys
import errno

# for debugging
import cgitb


cgitb.enable()
htmlContent = 'Content-type: text/plain\r\n\r\n'
baseDirectory = '/local/data/ccpn/update'
dbFile = '__UpdateData.db'
dbFile = os.path.join(baseDirectory, dbFile)
form = cgi.FieldStorage()
FILECHECKSIZE = 1024


def isBinary(data):
    """Check whether the byte-string is binary
    """
    if data:
        fData = data[0:min(FILECHECKSIZE, len(data))]
        try:
            fData = bytearray(fData)
        except:
            fData = bytearray(fData, encoding='utf-8')

        allChars = bytearray(range(0, 256))
        textChars = bytearray(set([7, 8, 9, 10, 12, 13, 27]) | set(range(0x20, 0x100)) - set([0x7f]))
        isBinary = bool(fData.translate(allChars, textChars))

        return isBinary


def isBinaryFile(fileName):
    """Check whether the fileName is a binary file (not always guaranteed)
    Doesn't check for a fullPath
    Returns False if the file does not exist or there is an error loading file
    """
    if os.path.isfile(fileName):
        with open(fileName, 'rb') as fileObj:
            # read the first FILECHECKSIZE bytes of the file
            fData = fileObj.read(FILECHECKSIZE)

            return isBinary(fData)


def mkdir_p(path):
    """Create the path for the file
    """
    try:
        os.makedirs(path)
    except os.error as es:
        if es.errno != errno.EEXIST:
            raise


def uploadFile():
    """Read fileData from the storage and write to file
    """
    fileName = '<None>'
    ty = '<None>'
    try:
        ty = os.environ['REQUEST_METHOD'] + ':' + os.environ['QUERY_STRING']

        fileStoredAs = form['fileName'].value
        fileData = form['fileData'].value
        serverDbRoot = form['serverDbRoot'].value

        # generate the correct path from the fileName
        fileName = fileStoredAs.replace('__temp_', '/')
        fileName = os.path.join(baseDirectory, serverDbRoot, fileName)
        dirName = os.path.dirname(fileName)
        if dirName:
            mkdir_p(dirName)

        if isBinary(fileData):
            with open(fileName, 'wb') as fp:
                fp.write(fileData)
            msg = 'OkBinary'
        else:
            with open(fileName, 'w') as fp:
                fp.write(fileData)
            msg = 'OkText'

        # TBD: update db file
        # msg = 'Ok'

    except Exception as es:
        msg = 'Exception: %s %s %s %s' % (str(fileName), str(es), str(form), str(ty))

    try:
        os.chmod(fileName, 0o664)  # does not work for db file
    except:
        pass

    sys.stdout.write(htmlContent)
    sys.stdout.write(msg)


if __name__ == '__main__':
    uploadFile()
