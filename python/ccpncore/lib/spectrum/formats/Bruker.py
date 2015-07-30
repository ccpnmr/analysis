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
import os, sys

from ccpncore.lib.spectrum.Util import checkIsotope
# from memops.qtgui.MessageDialog import showError

FILE_TYPE = 'Bruker'

def readParams(filePath):

  if os.path.isdir(filePath):
    procs_file = os.path.join(filePath, 'procs')
    dirName = filePath
    
  else:
    dirName, file = os.path.split(filePath)
    if file == 'procs':
      procs_file = filePath
      
    else:
      filePath = os.path.join(dirName, 'procs')
      
      if os.path.isfile(filePath):
        procs_file = filePath
      else:
        msg = 'Could not find Bruker "procs" file "%s"' % filePath
        # showError('Error', msg % filePath)
        print(msg)
        return

  wordSize = 4
  isFloatData = False
  headerSize = 0
  blockHeaderSize = 0
  sampledValues = [] # TBD
  sampledSigmas = []
  pulseProgram = None # TBD
  
  files = set(os.listdir(dirName))
  procsFiles = ['procs']     
  
  numDim = 1
  while 'proc%ds' % (numDim+1) in files:
    numDim += 1
    procsFiles.append('proc%ds' % numDim)
  
  dimDicts = []
  for i, procsFile in enumerate(procsFiles):
    procsPath = os.path.join(dirName, procsFile)
    procsDict = {}
    
    paramFileObj = open(procsPath, 'rU')
    
    for line in paramFileObj:
      if line.startswith('##'):
        remainder = line[2:].strip()
        key, value = remainder.split('=')
        key = key.strip()
        value = value.strip()
        procsDict[key] = value
    
    dimDicts.append(procsDict)
    
  dataFile = os.path.join(dirName, '%d%s' % (numDim, numDim * 'r'))
  isBigEndian = dimDicts[0]['$BYTORDP'] == '1'
  if '$NC_proc' in dimDicts[0]:
    dataScale = pow(2, float(dimDicts[0]['$NC_proc']))
  else:
    dataScale = 1.0

  numPoints = [0] * numDim
  blockSizes = [0] * numDim
  refPpms = [0] * numDim
  refPoints = [0] * numDim
  specWidths = [0] * numDim
  specFreqs = [0] * numDim
  isotopes = [0] * numDim
  origNumPoints = [0] * numDim
  pointOffsets = [0] * numDim
  
  for i in range(numDim):
    dimDict = dimDicts[i]
    
    if int(float(dimDict.get('$FT_mod', 1))) == 0:
      msg = 'Bruker dimension %d not processed'
      # showError('Error', msg % (i+1))
      return

    numPoints[i] = int(dimDict['$SI'])
    blockSizes[i] = int(dimDict['$XDIM'])
    if blockSizes[i] == 0:
      blockSizes[i] = numPoints[i]
    else:
      # for 1D data blockSizes can be > numPoints, which is wrong
      blockSizes[i] = min(blockSizes[i], numPoints[i])
    origNumPoints[i] = int(dimDict.get('$FTSIZE', 0))
    pointOffsets[i] = int(dimDict.get('$STSR', 0))
    specWidths[i] = float(dimDict.get('$SW_p', 10000.0))
    specFreqs[i] = float(dimDict.get('$SF', 500.0))
    refPpms[i] = float(dimDict.get('$OFFSET', 0.0))
    refPoints[i] = float(dimDict.get('$refPoint', 0.0))
    isotopes[i] = checkIsotope(dimDict.get('$AXNUC', '<1H>')[1:-1])

  data = (FILE_TYPE, dataFile, numPoints, blockSizes,
          wordSize, isBigEndian, isFloatData,
          headerSize, blockHeaderSize,
          isotopes, specFreqs,
          specWidths, refPoints, refPpms,
          sampledValues, sampledSigmas,
            pulseProgram, dataScale)

  return data

"""
  termDict = {'AQ':'acquisition time in seconds',
              'AMP':'amplitude of pulses',
              'AQ_mod':'acquisition mode',
              'AQSEQ':'3D acquisition order',
              'AUNM':'name of an acquisition AU program',
              'BF(1-8)':'basic frequency for frequency channel f(1-8)',
              'BYTORDP':'Byte order (endianness)',
              'CNST':'constant used in pulse programs',
              'CPDPRG(1-8)':'names of CPD programs',
              'D':'time delays',
              'DDR':'digital digitizer resolution',
              'DE':'pre-scan delay',
              'DECIM':'decimation factor of the digital filter',
              'DIGMOD':'digitizer mode',
              'DIGTYP':'digitizer type',
              'DQDMODE':'sign of the frequency shift during digital quadrature detection',
              'DR':'digitizer resolution',
              'DS':'number of dummy scans',
              'DSLIST':'dataset list',
              'DSPFIRM':'firmware used for digital filtering',
              'DW':'dwell time',
              'DWOV':'oversampling dwell time',
              'EXP':'experiment performed',
              'FCUCHAN':'routing between logical frequency channels and FCU s',
              'FnMODE':'Acquisition mode of the indirect dimensions (2D and 3D)',
              'FW':'analog filter width',
              'FIDRES':'FID resolution',
              'FQ1LIST':'irradiation frequency lists',
              'GP031':'gradient parameter table',
              'GRDPROG':'gradient program name',
              'HDDUTY':'homodecoupling duty cycle (in percent)',
              'HPMOD':'routing between high power amplifiers and preamplifier modules',
              'HPPRGN':'high power preamplifier gain',
              'INP':'increment for pulse P',
              'IN':'increment for delay D',
              'L':'loop counter',
              'LOCNUC':'lock nucleus',
              'MASR':'MAS spin rate',
              'NBL':'number of blocks (of acquisition memory)',
              'ND0':'number of delays D0',
              'ND10':'number of delays D10',
              'NS':'number of scans',
              'NUC(1-8)':'nucleus for frequency channel f(1-8)',
              'O(1-8)':'irradiation frequency offset for frequency channel f(1-8) in Hz',
              'O(1-8)P':'irradiation frequency offset for frequency channel f(1-8) in ppm',
              'OVERFLW':'data overflow check',
              'P':'pulse length',
              'PARMODE':'dimensionality of the raw data',
              'PHCOR':'correction angle for phase programs',
              'PCPD':'CPD pulse length',
              'PH_ref':'receiver phase correction',
              'PL':'power level',
              'POWMOD':'power mode',
              'PRECHAN':'routing between Switchbox outputs and Preamplifier modules',
              'PROSOL':'copy prosol parameters to corresponding acquisition parameters',
              'PRGAIN':'high power preamplifier gain',
              'PULPROG':'pulse program used for the acquisition',
              'QNP':'QNP nucleus selection',
              'RECCHAN':'receiver channel',
              'RG':'receiver gain',
              'RO':'sample rotation frequency in Hz',
              'RSEL':'routing between FCU s and amplifiers',
              'SEOUT':'SE 451 receiver unit output to be used',
              'SFO(1-8)':'irradiation (carrier) frequencies for channel f(1-8)',
              'SP07':'shaped pulse parameter table',
              'SOLVENT':'the sample solvent',
              'SW':'spectral width in ppm',
              'SW_h':'spectral width in Hz',
              'SWIBOX':'routing between Switchbox inputs and Switchbox outputs',
              'TD':'time domain; number of raw data points',
              'TD0':'loop counter for multidimensional experiments',
              'TE':'demand temperature on the temperature unit',
              'V9':'maximum variation of a delay',
              'VALIST':'variable amplitude (power) list',
              'VCLIST':'variable counter list',
              'VDLIST':'variable delay list',
              'VPLIST':'variable pulse list',
              'VTLIST':'variable temperature list',
              'WBST':'number of wobble steps',
              'WBSW':'wobble sweep width',
              'ZGOPTNS':'acquisition (zg) options',
              }
 
"""
