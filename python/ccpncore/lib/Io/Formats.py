"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os
from collections.abc import Sequence

from ccpncore.util.Path import checkFilePath


WHITESPACE_AND_NULL =  set(['\x00', '\t', '\n', '\r', '\x0b', '\x0c'])


AZARA = 'Azara'
BRUKER = 'Bruker'
FELIX = 'Felix'
NMRPIPE = 'NmrPipe'
NMRVIEW = 'NmrView'
UCSF = 'UCSF'
VARIAN = 'Varian'
XEASY = 'XEASY'

ANSIG = 'ANSIG'
AUTOASSIGN = 'AutoAssign'
CCPN = 'CCPN'
SPARKY = 'Sparky'
NMRDRAW = 'NMRDraw'
XEASY = 'XEASY'
NMRSTAR = 'NMR-STAR'

def analyseUrl(filePath):

  isOk, msg = checkFilePath(filePath)
  if not isOk:
    print (msg)
    return (None, None, None)

  # Deal with diredtories as input
  if os.path.isdir(filePath):
    # url is a directory
    fileNames = os.listdir(filePath)

    if 'memops' in fileNames:
      # CCPN Project
      return ('Project', CCPN, filePath)

    elif 'procs' in fileNames or 'pdata':
      # Bruker processed spectrum
      return ('Spectrum', BRUKER, filePath)

    elif 'procpar' in fileNames:
      # Varian processed spectrum
      return ('Spectrum', VARIAN, filePath)
    else:
      return (None, None, None)

  # Check foro binary files
  fileObj = open(filePath, 'rb')
  firstData = fileObj.read(1024)
  testData = set([c for c in firstData]) - WHITESPACE_AND_NULL
  isBinary = (min([ord(chr(c)) for c in testData]) < 32)


  if isBinary:
    # probably binary

    # UCSF spectrum
    if b'UCSF NMR' in firstData:
      return ('Spectrum', UCSF, filePath)

    refBytes = [ 0x40, 0x16, 0x14, 0x7b ]
    qBytes = [ ord(chr(c)) for c in firstData[8:12] ]

    # NMRPIPE spectrum
    if qBytes == refBytes:
      return ('Spectrum', NMRPIPE, filePath)

    qBytes.reverse()
    if qBytes == refBytes:
      return ('Spectrum', NMRPIPE, filePath)

    # NMRVIEW spectrum
    refBytes = ['34','18','AB','CD']
    qBytes = ["%02X" % ord(chr(c)) for c in firstData[:4]]

    if qBytes == refBytes:
      return ('Spectrum', NMRVIEW, filePath)

    qBytes.reverse()
    if qBytes == refBytes:
      return ('Spectrum', NMRVIEW, filePath)

    # BRUKER file
    dirName, fileName = os.path.split(filePath)
    if fileName in ('1r','2rr','3rrr','4rrrr'):
      return ('Spectrum', BRUKER, dirName)

    if fileName == 'phasefile':
      return ('Spectrum', VARIAN, dirName)

    if fileName.endswith('.spc'):
      return ('Spectrum', AZARA, filePath)

    from array import array

    vals = array('i')
    vals.fromstring(firstData[:4])
    if (0 < vals[0] < 6) and (vals[1] == 1):
      return ('Spectrum', FELIX, filePath)

    vals.byteswap()
    if (0 < vals[0] < 6) and (vals[1] == 1):
      return ('Spectrum', FELIX, filePath)

  else:
    # Text file
    if b'##TITLE' in firstData:
      return BRUKER

    if b'Version .....' in firstData:
      return XEASY

    fileObj.close()
    fileObj = open(filePath, 'rU')
    lines = ''.join([l.strip() for l in fileObj.readlines() if l[0] != '!'])

    if ('ndim ' in lines) and ('file ' in lines) and ('npts ' in lines) and ('block ' in lines):
      return AZARA

    dirName, fileName = os.path.split(filePath)
    if fileName == 'procpar':
      return VARIAN