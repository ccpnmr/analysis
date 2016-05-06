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
# import collections

import os
from ccpncore.lib.Io import Formats as ioFormats
from ccpncore.lib.Io import Fasta as fastaIo
from ccpncore.lib.Io import Pdb as pdbIo
from ccpncore.lib.spectrum.formats.Lookup import readXls,readCsv

# def loadSpectrum(project:object, filePath:str, reReadSpectrum:object=None):
#   """Load spectrum from file a filePath"""
#
#   if reReadSpectrum is not None:
#     # NBNB TBD Rasmus - this is clearly not working yet
#     raise NotImplementedError("reReadSpectrum parameter not implemented yet")
#
#   if reReadSpectrum:
#     spectrum = reReadSpectrum
#     # NBNB TBD BROKEN - spectrum is overwritten lower down
#   else:
#     dataSource = project._apiNmrProject.loadDataSource(filePath)
#     if not dataSource:
#       return None
#
#   # NBNB TBD BROKEN - dataSource is not always set.
#   spectrum = project._data2Obj[dataSource]
#
#   return spectrum

def loadData(self:'Project', path:str) -> (list,None):
  """Load data from path, determining type first."""

  dataType, subType, usePath = ioFormats.analyseUrl(path)

  # urlInfo is list of triplets of (type, subType, modifiedUrl),

  # e.g. ('Spectrum', 'Bruker', newUrl)
  if dataType is None:
    print("Skipping: file data type not recognised for %s" % usePath)
  elif not os.path.exists(usePath):
    print("Skipping: no file found at %s" % usePath)
  elif dataType == 'Text':
    # Special case - you return the text instead of a list of Pids
    return open(usePath).read()
  else:

    funcname = 'load' + dataType
    if funcname == 'loadProject':
      return [self.loadProject(usePath, subType)]

    # elif funcname == 'loadLookupFile':
    #   return project.loadLookupFile(usePath, subType)

    elif hasattr(self, funcname):
      pids = getattr(self, funcname)(usePath, subType)
      return pids
    else:
      print("Skipping: project has no function %s" % funcname)

  return None

# Data loaders and dispatchers
def loadSequence(self:"Project", path:str, subType:str) -> list:
  """Load sequence(s) from file into Wrapper project"""

  if subType == ioFormats.FASTA:
    sequences = fastaIo.parseFastaFile(path)
  else:
    raise ValueError("Sequence file type %s is not recognised" % subType)

  chains = []
  for sequence in sequences:
    chains.append(self.createSimpleChain(sequence=sequence[1], compoundName=sequence[0],
                                          molType='protein'))
  #
  return chains

def loadStructure(self:"Project", path:str, subType:str) -> list:
  """Load Structure ensemble(s) from file into Wrapper project"""

  if subType == ioFormats.PDB:
    apiEnsemble = pdbIo.loadStructureEnsemble(self._apiNmrProject.molSystem, path)
  else:
    raise ValueError("Structure file type %s is not recognised" % subType)
  #
  return [self._data2Obj[apiEnsemble]]

def loadProject(self:"Project", path:str, subType:str) -> "Project":
  """Load project from file into application and return the new project"""

  if subType == ioFormats.CCPN:
    return self._appBase.loadProject(path)
  else:
    raise ValueError("Project file type %s is not recognised" % subType)

def loadSpectrum(self:"Project", path:str, subType:str) -> list:
  """Load spectrum from file into application"""

  apiDataSource = self._wrappedData.loadDataSource(path, subType)
  if apiDataSource is None:
    return []
  else:
    self.resetAssignmentTolerances(apiDataSource)
    return [self._data2Obj[apiDataSource]]

#
#
def loadLookupFile(self:"Project", path:str, subType:str, ):
  """Load data from a look-up file, csv or xls ."""

  if subType == ioFormats.CSV:
    readCsv(self, path=path)

  elif subType == ioFormats.XLS:
    readXls(self, path=path)


def resetAssignmentTolerances(self:"Project", apiDataSource):

  spectrum = self._data2Obj[apiDataSource]
  tolerances = [[]] * spectrum.dimensionCount
  for ii, isotopeCode in enumerate(spectrum.isotopeCodes):
    if isotopeCode == '1H':
      tolerance = max([0.02, spectrum.spectralWidths[ii]/spectrum.pointCounts[ii]])
      tolerances[ii] = tolerance
    elif isotopeCode == '13C' or isotopeCode == '15N':
      tolerance = max([0.2, spectrum.spectralWidths[ii]/spectrum.pointCounts[ii]])
      tolerances[ii] = tolerance
    else:
      tolerance = max([0.2, spectrum.spectralWidths[ii]/spectrum.pointCounts[ii]])
      tolerances[ii] = tolerance

  spectrum.assignmentTolerances = tolerances


def uniqueSubstanceName(self:"Project", name:str=None, defaultName:str='Molecule') -> str:
  """add integer suffixed to name till it is unique"""

  apiComponentStore = self._wrappedData.sampleStore.refSampleComponentStore
  apiProject =apiComponentStore.root

  # ensure substance name is unique
  if name:
    i = 0
    result = name
    formstring = name + '_%d'
  else:
    formstring = defaultName + '_%d'
    i = 1
    result =  formstring % (name,i)
  while (apiProject.findFirstMolecule(name=result) or
         apiComponentStore.findFirstComponent(name=result)):
    i += 1
    result = '%s_%d' % (name,i)
  if result != name and name != defaultName:
    self._logger.warning(
    "CCPN molecule named %s already exists. New molecule has been named %s" %
    (name,result))
  #
  return result