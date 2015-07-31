"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import os
from collections.abc import Sequence

from ccpncore.util.Path import checkFilePath

ISOTOPE_DICT = {'H':'1H',
                'C':'13C',
                'N':'15N',
                'P':'31P',
                'Si':'29Si',
                'F':'19F',
                'O':'17O',
                'Br':'79Br'}

STANDARD_ISOTOPES = set(ISOTOPE_DICT.values())

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

def checkIsotope(text):

  text = text.strip()

  if not text:
    return '1H'

  if text in STANDARD_ISOTOPES:
    return text

  if text in ISOTOPE_DICT:
    return ISOTOPE_DICT[text]

  for isotope in STANDARD_ISOTOPES:
    if isotope in text:
      return isotope

  else:
    return ISOTOPE_DICT.get(text[0].upper(), '1H')

# def getSpectrumFileFormat(filePath):
#
#   isOk, msg = checkFilePath(filePath)
#   if not isOk:
#     print (msg)
#     return
#
#   if os.path.isdir(filePath):
#     fileNames = os.listdir(filePath)
#
#     if 'memops' in fileNames:
#       return CCPN
#     elif 'procs' in fileNames or 'pdata':
#       return BRUKER
#     elif 'procpar' in fileNames:
#       return VARIAN
#     else:
#       return
#
#   fileObj = open(filePath, 'rb')
#   firstData = fileObj.read(1024)
#   testData = set([c for c in firstData]) - WHITESPACE_AND_NULL
#   if min([ord(chr(c)) for c in testData]) < 32:
#     # probably binary
#
#     if b'UCSF NMR' in firstData:
#       return UCSF
#
#     refBytes = [ 0x40, 0x16, 0x14, 0x7b ]
#     qBytes = [ ord(chr(c)) for c in firstData[8:12] ]
#
#     if qBytes == refBytes:
#       return NMRPIPE
#
#     qBytes.reverse()
#     if qBytes == refBytes:
#       return NMRPIPE
#
#     refBytes = ['34','18','AB','CD']
#     qBytes = ["%02X" % ord(chr(c)) for c in firstData[:4]]
#
#     if qBytes == refBytes:
#       return NMRVIEW
#
#     qBytes.reverse()
#     if qBytes == refBytes:
#       return NMRVIEW
#
#     dirName, fileName = os.path.split(filePath)
#     if fileName in ('1r','2rr','3rrr','4rrrr'):
#       return BRUKER
#
#     if fileName == 'phasefile':
#       return VARIAN
#
#     if fileName.endswith('.spc'):
#       return AZARA
#
#     from array import array
#
#     vals = array('i')
#     vals.fromstring(firstData[:4])
#     if (0 < vals[0] < 6) and (vals[1] == 1):
#       return FELIX
#
#     vals.byteswap()
#     if (0 < vals[0] < 6) and (vals[1] == 1):
#       return FELIX
#
#   else:
#     if b'##TITLE' in firstData:
#       return BRUKER
#
#     if b'Version .....' in firstData:
#       return XEASY
#
#     fileObj.close()
#     fileObj = open(filePath, 'rU')
#     lines = ''.join([l.strip() for l in fileObj.readlines() if l[0] != '!'])
#
#     if ('ndim ' in lines) and ('file ' in lines) and ('npts ' in lines) and ('block ' in lines):
#       return AZARA
#
#     dirName, fileName = os.path.split(filePath)
#     if fileName == 'procpar':
#       return VARIAN

def mapAxisCodes(newCodes:Sequence, referenceCodes:Sequence) -> list:
  """reorder newCodes so that they best match referenceCodes
  Returns list of length referenceCodes with newCodes put in the matching slot.
  IF newCodes are shorter than referenceCodes, the unused slots are filled with '-'
  All newCodes must map, and if a match cannot be found returns None """

  default = '-'
  result = [default] * len(referenceCodes)

  # NBNB TBD - this is functional but must be MUCH expanded

  # map identical residues
  remainder = []
  for code in newCodes:
    if code in referenceCodes:
      result[referenceCodes.index(code)] = code
    else:
      remainder.append(code)

  # match on nuclei (based on first letter only, random choice for duplicates)
  for code in remainder:
    for ii, ref in referenceCodes:
      if ref[0] == code[0] and result[ii] == default:
        result[ii] = code
      else:
        return []
  #
      return result