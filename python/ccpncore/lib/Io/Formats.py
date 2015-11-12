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

from ccpncore.util.Path import checkFilePath
from ccpncore.util import Common as commonUtil

# Spectrum formats
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
NMRSTAR = 'NMR-STAR'

# Sequence formats
FASTA = 'Fasta'

#  Look-up formats
CSV = 'csv'
XLS = 'xls'

DataTypes = ['Project', 'Spectrum', 'Text', 'Sequence', 'LookupFile']

def analyseUrl(filePath):
  """ Analyse filePath, and return (dataType, subType, usePath) tuple

  Note:
  For Bruker and Varian Spectrum data, the usePath returned is the directory containing the spectrum
  """

  isOk, msg = checkFilePath(filePath)
  if not isOk:
    print (msg)
    return (None, None, filePath)

  # Deal with directories as input
  if os.path.isdir(filePath):

    # url is a directory
    fileNames = os.listdir(filePath)



    if 'memops' in fileNames:

      # CCPN Project
      return ('Project', CCPN, filePath)

    elif 'procs' in fileNames:

      # 'Bruker processed spectrum'
      return ('Spectrum', BRUKER, filePath)

    elif 'procpar' in fileNames:

      # Varian processed spectrum
      return ('Spectrum', VARIAN, filePath)


    else:
      print('else')
      fileNames = os.listdir(filePath)

      for dirp, dirn, file in  os.walk(filePath):
        for name in file:
          path = os.path.join(dirp, name)

          if path.endswith('procs'):
            filePath = path
            print(filePath)
            # return ('Spectrum', BRUKER, filePath)
      #
      # for(dirpath, dirnames, filename) in os.walk(filePath):
      #   for name in filename:
      #
      #     path = os.path.join(dirpath, name)
      #     if path.endswith('procs'):
      #       filePath = path
      #       return ('Spectrum', BRUKER, filePath)

      # NBNB FIXME TBD this needs sorting

    # No match
    return (None, None, filePath)

  # Set up for further analysis
  dirName, fileName = os.path.split(filePath)


  # Check for binary files
  fileObj = open(filePath, 'rb')
  firstData = fileObj.read(1024)
  testData = set([c for c in firstData]) - commonUtil.WHITESPACE_AND_NULL
  isBinary = (min([ord(chr(c)) for c in testData]) < 32)

  # Deal with binary files
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


  # Test Lookup format
  # import csv
  # if filePath.endswith('.csv'):
  #   print('is a look up csv')
  #   csv_in = open(filePath, 'r')
  #   reader = csv.reader(csv_in)
  #   for row in reader:
  #    if row[0].split('/')[-1] == 'procs':
  #      filename = row[0].split('/')
  #      filename.pop()
  #      Filename = '/'.join(filename)
  #      print(Filename, 'filename path in format.py')




  if filePath.endswith('.csv'):
    return ('LookupFile', CSV, filePath)

  if filePath.endswith('.xls'):
    return ('LookupFile', XLS, filePath)


  else:
    # Text file
    # if b'##TITLE' in firstData:
    #   return ('Spectrum', BRUKER, dirName)
    #
    # if b'Version .....' in firstData:
    #   # NBNB TBD FIXME what data is this?
    #   return (None, XEASY, filePath)

    fileObj.close()
    text = open(filePath, 'rU').read()
    textblock = '\n'.join([line.strip() for line in text.splitlines()
                           if not (line and line[0] == '!')])

    # NBNB FIXME TBD This assumes that comments are given by '!' in the first char.
    # IS THAT ALWAYS THE CASE?

    if filePath.endswith('.fasta') or text.startswith('>'):
      # FASTA file
      return ('Sequence', FASTA, filePath)

    if textblock.startswith('##TITLE'):
      return ('Spectrum', BRUKER, dirName)

    if textblock.startswith('Version .....'):
      # NBNB TBD FIXME what data is this?
      return (None, XEASY, filePath)

    if fileName == 'procpar':
      return ('Spectrum', VARIAN, dirName)

    if (fileName.endswith('.par') and ('ndim ' in textblock) and ('file ' in textblock) and
        ('npts ' in textblock) and ('block ' in textblock)):
      spectrumPath = filePath[:-4]
      if os.path.isfile(spectrumPath):
        return ('Spectrum', AZARA, spectrumPath)





    # Default - return as plain text
    return ('Text', None, filePath)

  # No match
  return (None, None, filePath)
