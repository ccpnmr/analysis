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
import os, sys, array, re

from ccpncore.lib.spectrum.Spectrum import checkIsotope
# from memops.qtgui.MessageDialog import showError

# Varian uses convention H1, C13, etc.
# CCPN uses convention 1H, 13C, etc.
nucVarianRe = re.compile('^([A-Z]+)(\d+)$')
nucCcpnRe = re.compile('^(\d+)([A-Z]+)$')

VNMR_FILE_HEADER_SIZE = 32
VNMR_BLOCK_HEADER_SIZE = 28

FILE_TYPE = 'Varian'

def readParams(filePath):

  dirName, fileName = os.path.split(filePath)

  if fileName == 'procpar':
    dataFile = os.path.join(dirName, 'datdir', 'phasefile')
  
  elif fileName == 'phasefile':
    dataFile = filePath
    dirName = os.path.dirname(dirName)
    filePath = os.path.join(dirName, 'procpar')

  wordSize = 4
  isFloatData = True

  sampledValues = []
  sampledSigmas = []
  pulseProgram = None
  dataScale = 1.0
  
  try:
    ccpnParams = parseProcparFile(filePath)
    dataFileParams = readDataFileHeader(dataFile)
  except (IOError, err):
    msg = 'Varian spectrum parameter read for %s failed: %s'
    # showError('Error', msg % (filePath, err))
    return
  
  blockSizes = []
  ndim = ccpnParams['ndim']
  numPoints = ccpnParams['npts']
  isotopes = ccpnParams['nuc']
  specFreqs = ccpnParams['sf']
  specWidths = ccpnParams['sw']
  refPoints = ccpnParams['refpt']
  refPpms = ccpnParams['refppm']
  
  if (dataFileParams['firstBlock'] == 0) and (ndim == 2):
    # in this case are using transposed data so everything is backwards
    # TBD: not sure what to do in 3D, etc.
    numPoints.reverse()
    isotopes.reverse()
    specFreqs.reverse()
    specWidths.reverse()
    refPoints.reverse()
    refPpms.reverse()

  blockSize = dataFileParams['np'] * dataFileParams['ntraces']
  blockHeaderSize = dataFileParams['nbheaders'] * VNMR_BLOCK_HEADER_SIZE
  headerSize = VNMR_FILE_HEADER_SIZE 
  headerSize += dataFileParams['firstBlock']*(4*blockSize+blockHeaderSize)

  if ndim ==  1:
    blockSizes = [blockSize,]
  else:
    blockSizes = [1] * ndim
    blockSizes[0] = numPoints[0]
    blockSizes[1] = blockSize // numPoints[0]  # TBD: is it always a multiple??
  
  isBigEndian = sys.byteorder == 'big'
  if dataFileParams['swapped']:
    isBigEndian = not isBigEndian

  data = (FILE_TYPE, dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
          pulseProgram, dataScale)

  return data

def varian2ccpn(varianNuc):

  match = nucVarianRe.match(varianNuc)
  if match:
    return match.group(2) + match.group(1)
  else:
    return None

def ccpn2varian(ccpnNuc):

  match = nucCcpnRe.match(ccpnNuc)
  if match:
    return match.group(2) + match.group(1)
  else:
    return None

def getInt(field, msg, line, n):

  try:
    value = int(field)
  except (ValueError, e):
    raise IOError('line number %d: field "%s" = %s is not an integer:\n  %s' % (n, msg, field, line))

  return value

def getFloat(field, msg, line, n):

  try:
    value = float(field)
  except (ValueError, e):
    raise IOError('line number %d: field "%s" = %s is not a real number:\n  %s' % (n, msg, field, line))

  return value

def getString(line):

  line = line.strip()
  if line.startswith('"'):
    line = line[1:]
  if line.endswith('"'):
    line = line[:-1]

  return line

def parseProcparFile(procparFile):

  params = {}
  params['procparFile'] = procparFile

  fp = open(procparFile, 'rU')

  try:

    line1 = fp.readline().rstrip()
    n = 1
    while line1:

      # Subtype (integer)
      #  0: undefined
      #  1: real
      #  2: string
      #  3: delay
      #  4: flag
      #  5: frequency
      #  6: pulse
      #  7: integer

      # Basictype (integer)
      #  0: undefined
      #  1: real
      #  2: string

      fields = line1.split()
      if len(fields) != 11:
        raise IOError('line number %d: need 11 fields, have %d:\n  %s' % (n, len(fields), line1))

      parname = fields[0]
      subtype = getInt(fields[1], 'subtype', line1, n)
      basictype = getInt(fields[2], 'basictype', line1, n)
      active = getInt(fields[9], 'active', line1, n)

      if params.has_key(parname):
        raise IOError('line number %d: name = %s is a repeat:\n  %s' % (n, parname, line1))

      if subtype not in range(8):
        raise IOError('line number %d: subtype = %d, must be in range 0-7:\n  %s' % (n, subtype, line1))

      if basictype not in range(3):
        raise IOError('line number %d: basictype = %d, must be in range 0-2:\n  %s' % (n, basictype, line1))

      if basictype == 0:
        raise IOError('line number %d: basictype = %d, do not know how to deal with case 0:\n  %s' % (n, basictype, line1))

      if active not in (0, 1):
        raise IOError('line number %d: active = %d, must be 0 or 1:\n  %s' % (n, active, line1))

      line2 = fp.readline().rstrip()
      n += 1
      fields = line2.split()
      if len(fields) < 2:
        raise IOError('line number %d: need at least 2 fields, have %d:\n  %s' % (n, len(fields), line2))
      value_len = getInt(fields[0], 'value_len', line2, n)
 
      if basictype == 1:  # (real)
        if len(fields) != (1+value_len):
          raise IOError('line number %d: need %d fields, have %d:\n  %s' % (n, 1+value_len, len(fields), line2))
        if value_len == 1:
          for getVal in (getInt, getFloat):
            try:
              value = getVal(fields[1], 'value', line2, n)
              break
            except:
              pass
          else:
            value = getString(fields[1])
        else:
          value = []
          for field in fields[1:]:
            for getVal in (getInt, getFloat):
              try:
                val = getVal(field, 'value', line2, n)
                break
              except:
                pass
            else:
              val = getString(field)
            value.append(val)

      else: # basictype == 2 (string)
        value = getString(' '.join(fields[1:]))
        if value_len > 1:
          value = [value]
          for m in range(1, value_len):
            line2 = fp.readline().rstrip()
            n += 1
            value.append(getString(line2))

      params[parname] = value

      line3 = fp.readline().rstrip()
      n += 1

      line1 = fp.readline().rstrip()
      n += 1

  finally:
    fp.close()

  dd = {}
  dd['ndim'] = getNumDim(params)
  dd['npts'] = getNumPoints(params)
  dd['sf'] = getSpecFreq(params)
  dd['sw'] = getSpecWidth(params)
  dd['nuc'] = getNuclei(params)
  dd['refppm'] = getRefPpm(params)
  dd['refpt'] = getRefPoint(params)
  params['ccpnParams'] = dd

  return dd

# a lot of below is based on Sparky vnmr2ucsf code
# but in 3D they always transpose D2 and D3, so that needs looking at

def getNumDim(procparParams):

  ndim = 1
  for key in ('ni', 'ni2', 'ni3'):
    val = procparParams.get(key)
    if val and val > 1:
      ndim += 1
    else:
      break

  return ndim

def getNumPoints(procparParams):

  ndim = getNumDim(procparParams)

  keys = ('fn', 'fn1', 'fn2', 'fn3')
  # /2 because it looks like Varian needs that factor
  npts = [procparParams.get(keys[i])/2 for i in range(ndim)]

  return npts

# this follows instructions from Peter Howe
# axis is the display axis, so might not be set or might be wrong
# but this seems to be the only way to get at the isotope
# and Varian do H1, C13, etc., instead of 1H, 13C, etc.
def getNuclei(procparParams):

  ndim = getNumDim(procparParams)

  # below maps axis character to key to use to determine isotope
  axisMap = {'p': 'tn', 'd': 'dn', '1': 'dn', '2': 'dn2', '3': 'dn3','4': 'dn4'}

  axis = procparParams.get('axis')
  if axis and len(axis) >= ndim:
    nuclei = [procparParams.get(axisMap.get(x, 'tn'), 'H1') for x in axis[:ndim]]
  else:
    nuclei = ndim * ['H1']

  nuclei = [varian2ccpn(x) for x in nuclei]

  return nuclei

def getSpecFreq(procparParams):

  nucKeys = ('tn', 'dn', 'dn2', 'dn3')
  sfKeys = ('sfrq', 'dfrq', 'dfrq2', 'dfrq3')

  nuclei = getNuclei(procparParams)
  nuclei = [ccpn2varian(x) for x in nuclei]

  sf = []
  for nucleus in nuclei:
    for (n, key) in enumerate(nucKeys):
      val = procparParams.get(key)
      if nucleus == val:
        break
    else:
      n = 0  # arbitrary
    sf.append(procparParams.get(sfKeys[n]))

  return sf

def getSpecWidth(procparParams):

  ndim = getNumDim(procparParams)

  keys = ('sw', 'sw1', 'sw2', 'sw3')
  sw = [procparParams.get(keys[i]) for i in range(ndim)]

  return sw

def getRefPoint(procparParams):

  #npts = getNumPoints(procparParams)
  #refpt = [1.0+0.5*float(x) for x in npts]

  ndim = getNumDim(procparParams)
  refpt = ndim * [1.0]

  return refpt

def getRefPpm(procparParams):

  ndim = getNumDim(procparParams)

  keys = ('rfl', 'rfl1', 'rfl2', 'rfl3')
  refloc = [procparParams.get(keys[i]) for i in range(ndim)]

  keys = ('rfp', 'rfp1', 'rfp2', 'rfp3')
  reffreq = [procparParams.get(keys[i]) for i in range(ndim)]

  sw = getSpecWidth(procparParams)
  sf = getSpecFreq(procparParams)

  refppm = [((sw[n] + reffreq[n] - refloc[n]) / sf[n]) for n in range(ndim)]

  return refppm

# file header and block header status bits
VNMR_S_DATA         = 1 << 0    # 0 = no data, 1 = data
VNMR_S_SPEC         = 1 << 1    # 0 = FID, 1 = spectrum
VNMR_S_32           = 1 << 2    # *
VNMR_S_FLOAT        = 1 << 3    # 0 = integer, 1 = floating point
VNMR_S_COMPLEX      = 1 << 4    # 0 = real, 1 = complex
VNMR_S_HYPERCOMPLEX = 1 << 5    # 1 = hypercomplex

# file header status bits
VNMR_S_ACQPAR       = 1 << 7    # 0 = not Acqpar, 1 = Acqpar
VNMR_S_SECND        = 1 << 8    # 0 = first FT, 1 = second FT
VNMR_S_TRANSF       = 1 << 9    # 0 = regular, 1 = transposed
VNMR_S_NP           = 1 << 11   # 1 = np dimension is active
VNMR_S_NF           = 1 << 12   # 1 = nf dimension is active
VNMR_S_NI           = 1 << 13   # 1 = ni dimension is active
VNMR_S_NI2          = 1 << 14   # 1 = ni2 dimension is active

# block header status bits
VNMR_S_MORE_BLOCKS  = 1 << 7    # 0 = absent, 1 = present
VNMR_S_NP_COMPLEX   = 1 << 8    # 0 = real, 1 = complex
VNMR_S_NF_COMPLEX   = 1 << 9    # 0 = real, 1 = complex
VNMR_S_NI_COMPLEX   = 1 << 10   # 0 = real, 1 = complex
VNMR_S_NI2_COMPLEX  = 1 << 11   # 0 = real, 1 = complex

def readDataFileHeader(dataFile):

  params = {}
  params['dataFile'] = dataFile

  fp = open(dataFile, 'rb')

  try:
    header = fp.read(VNMR_FILE_HEADER_SIZE)
  finally:
    fp.close()

  if len(header) != VNMR_FILE_HEADER_SIZE:
    raise IOError('dataFile is of size %d < %d, which is header size' % (len(header), VNMR_FILE_HEADER_SIZE))

  x = array.array('i')  # integer
  y = array.array('H')  # unsigned short
  x.fromstring(header)
  y.fromstring(header)
  ebytes = x[3] 
  swapped = False
  if ebytes < 1 or ebytes > 8:
    x.byteswap()
    y.byteswap()
    swapped = True

  params['nblocks'] = x[0]    # number of blocks in file
  params['ntraces'] = x[1]    # number of traces per block
  params['np'] = x[2]         # number of elements per trace
  params['ebytes'] = x[3]     # number of bytes per element
  params['tbytes'] = x[4]     # number of bytes per trace
  params['bbytes'] = x[5]     # number of bytes per block
  params['vers_id'] = y[12]   # software version, file_id status bits
  params['status'] = y[13]    # status of whole file
  params['nbheaders'] = x[7]  # number of block headers per block

  params['swapped'] = swapped

  status = params['status']
  params['s_data'] = (status & VNMR_S_DATA) and True or False
  params['s_spec'] = (status & VNMR_S_SPEC) and True or False
  params['s_32'] = (status & VNMR_S_32) and True or False
  params['s_float'] = (status & VNMR_S_FLOAT) and True or False
  params['s_complex'] = (status & VNMR_S_COMPLEX) and True or False
  params['s_hypercomplex'] = (status & VNMR_S_HYPERCOMPLEX) and True or False
  params['s_acqpar'] = (status & VNMR_S_ACQPAR) and True or False
  params['s_secnd'] = (status & VNMR_S_SECND) and True or False
  params['s_transf'] = (status & VNMR_S_TRANSF) and True or False
  params['s_np'] = (status & VNMR_S_NP) and True or False
  params['s_nf'] = (status & VNMR_S_NF) and True or False
  params['s_ni'] = (status & VNMR_S_NI) and True or False
  params['s_ni2'] = (status & VNMR_S_NI2) and True or False
  
  if params['s_data']:
    determineFirstDataBlock(params)
  else:
    params['firstBlock'] = 0

  return params

def determineFirstDataBlock(dataFileParams):

  for firstBlock in (0, dataFileParams['nblocks']):
    dataFileParams['firstBlock'] = firstBlock
    params = readDataBlockHeader(dataFileParams)
    if params['s_data']:
      break
  else:
    dataFileParams['firstBlock'] = 0  # arbitrary
 
def readDataBlockHeader(dataFileParams, block=0):

  dataFile = dataFileParams['dataFile']
  nbheaders = dataFileParams['nbheaders']
  nblocks = dataFileParams['nblocks']
  np = dataFileParams['np']
  ntraces = dataFileParams['ntraces']
  swapped = dataFileParams['swapped']
  firstBlock = dataFileParams['firstBlock']

  if block < 0 or block >= nblocks:
    raise IOError('block = %d, must be in range 0 to %d' % (block, nblocks-1))

  block += firstBlock

  block_size = 4 * np * ntraces
  offset = VNMR_FILE_HEADER_SIZE + block*(nbheaders*VNMR_BLOCK_HEADER_SIZE+block_size)

  params = {}

  fp = open(dataFile, 'rb')

  try:
    fp.seek(offset)
    header = fp.read(VNMR_BLOCK_HEADER_SIZE)
    if nbheaders == 2:
      header1 = fp.read(VNMR_BLOCK_HEADER_SIZE)
    else:
      header1 = None
  finally:
    fp.close()

  if len(header) != VNMR_BLOCK_HEADER_SIZE:
    raise IOError('header for block %d only read as size %d, expecting %d' % (block, len(header), VNMR_BLOCK_HEADER_SIZE))

  if header1 and len(header1) != VNMR_BLOCK_HEADER_SIZE:
    raise IOError('header1 for block %d only read as size %d, expecting %d' % (block, len(header1), VNMR_BLOCK_HEADER_SIZE))

  x = array.array('i')  # integer
  y = array.array('H')  # unsigned short
  z = array.array('f')  # float
  x.fromstring(header)
  y.fromstring(header)
  z.fromstring(header)
  if swapped:
    x.byteswap()
    y.byteswap()
    z.byteswap()

  params['scale'] = y[0]
  params['status'] = y[1]
  params['index'] = y[2]
  params['mode'] = y[3]
  params['ctcount'] = x[2]
  params['lpval'] = z[3]
  params['rpval'] = z[4]
  params['lvl'] = z[5]
  params['tlt'] = z[6]

  status = params['status']
  params['s_data'] = (status & VNMR_S_DATA) and True or False
  params['s_spec'] = (status & VNMR_S_SPEC) and True or False
  params['s_32'] = (status & VNMR_S_32) and True or False
  params['s_float'] = (status & VNMR_S_FLOAT) and True or False
  params['s_complex'] = (status & VNMR_S_COMPLEX) and True or False
  params['s_hypercomplex'] = (status & VNMR_S_HYPERCOMPLEX) and True or False

  if header1:
    y = array.array('H')  # unsigned short
    z = array.array('f')  # float
    y.fromstring(header1)
    z.fromstring(header1)
    if swapped:
      y.byteswap()
      z.byteswap()

    params['status1'] = y[1]
    params['index'] = y[2]
    params['lpval1'] = z[3]
    params['rpval1'] = z[4]

  return params
