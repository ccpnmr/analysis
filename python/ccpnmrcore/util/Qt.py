"""Qt related utility functions

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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

from ccpncore.lib.spectrum import Util as spectrumUtil

def interpretEvent(event):
  """ Interpret drop event and return (type, data)
  """

  if event.mimeData().hasUrls():
    filePaths = [url.path() for url in event.mimeData().urls()]
    return ('urls', filePaths)

  elif event.mimeData().hasJson():
    # NBNB TBD QTTBD hasJson and getJson have to be emulated.
    jsonData = event.mimeData.getJson()

    data = jsonData.get('ccpnmr-pids')
    if data is not None:
      # data is list of string pids
      return ('pids',data)

    data = jsonData.get('ccpnmr-io')
    if data is not None:
      #data is nef-like json structure copying CCPN obeject content, for import
      return ('ccpnmr-io',data)

  elif event.mimeData().hasText():
    return('text', event.mimeData().text)

  return (None, None)


pidTypeMap = {}
import ccpn
import ccpnmr
for package in ccpn, ccpnmr:
  for tag in dir(package):
    obj = getattr(package, tag)
    if hasattr(obj, 'shortClassName'):
      shortClassName = getattr(obj, 'shortClassName')
      if shortClassName:
        #NBNB TBD QTTBD FIXME - also picks up subclasses
        pidTypeMap[shortClassName] = obj.__name__


def getCommonType(pids):

  from ccpncore.util import Pid

  types = set(pidTypeMap.get(Pid.Pid(x).type, Pid.Pid(x).type) for x in pids)
  if len(types) == 1:
    return types.pop()
  else:
    return 'mixed'


def analyseUrls(urls):
  """Returns list of urlInfo triplets:  (type, subType, corrected Url) """

  pluralTypes = {
    'PeakList':'PeakLists',
    'Spectrum':'Spectra',
    # ...
  }

  urlInfo = []

  commonTypes = set()
  for url in urls:

    fileType, subType, newUrl = analyseUrl(url)
    if fileType is not None and newUrl.exists():
      urlInfo.append((fileType, subType, newUrl))
      commonTypes.add(fileType)

  if not urlInfo:
    tag = None
  elif len(commonTypes) == 1:
    tag = commonTypes.pop()
    if len(urlInfo) > 1:
      tag = pluralTypes.get(tag, tag)
  else:
    tag = 'Mixed'

  return (tag, urlInfo)


def analyseUrl(url):
  """Analyse url name, location, pre-read file and analyse contents
  Function must be able to classify ANY droppable url of ANY type that cna be handled
  Function may convert Url to a different Url,
  so that different inputs (e.g. .spc and .spc.par files) can lead to a standardised output.
  """

  # Analyse and pre-read file here.
  fileType = None
  subType = None
  modifiedUrl = None

  spectrumType = spectrumUtil.getSpectrumFileFormat(url)

  if spectrumType is not None:

    if spectrumType == spectrumUtil.CCPN:
      # NBNB QTTBD TBD
      # Expand on this
      return ('Project', 'CCPN', url)

    else:
      # NBNB QTTBD TBD
      # Expand on this
      return ('Spectrum',spectrumType, url)

  # e.g. ('Spectrum', 'Bruker', containingDirectory)
  # or ('Structure', 'PDB', fileName)
  # or ('PeakList', 'XEASY', fileName)
  # or ('Project', 'CCPN', topProjectDirectory)
  # or ('Project', 'SPARKY', projectFile)
  # or ('Data', 'NEF', fileName)
  # or ('Text', None, fileName)

  return (fileType, subType, modifiedUrl)