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

# for debugging
import cgitb


cgitb.enable()
contentType = 'Content-type: text/plain\r\n\r\n'
baseDirectory = '/local/data/ccpn/update'
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


def downloadFile():
    """Read file from the filePath and return the contents
    """
    try:
        fileName = '<None>'
        if 'fileName' in form:
            fileName = form['fileName'].value

            path = os.path.join(baseDirectory, fileName)

            # check whether the file is binary
            if isBinaryFile(path):
                with open(path, 'rb') as fp:
                    data = fp.read()
            else:
                with open(path, 'r') as fp:
                    data = fp.read()

        else:
            data = str(form)

    except Exception as es:
        data = 'Exception: %s %s %s\n' % (str(fileName), str(form), str(es))

    sys.stdout.write(contentType)
    sys.stdout.write(data)


if __name__ == '__main__':
    downloadFile()
