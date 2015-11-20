"""Pdb IO functions

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

from ccpncore.lib.Io import PyMMLibPDB as PdbLib
from ccpncore.util.Types import List, Tuple
from ccpncore.lib.spectrum import Spectrum as spectrumLib

class PdbRecordProcessor(PdbLib.RecordProcessor):
  """Class for custom record processing"""

  def process_ATOM(self, rec):
    """fix atom record - make only globally acceptable changes, special-case stuff is for later"""

    name = rec['name']
    if name[0].isdigit():
      # move leading digit to end of atom name
      rec['name'] = name[1:] + name[0]

    if not rec['chainID'].strip():
      # replace empty chainID with seqID if length is suitable
      seqId = rec['seqID'].strip()
      if len(seqId) == 1:
        rec['chainID'] = seqId
      else:
        # May not be necessary, but just in case
        rec['chainID'] = ' '


def readPdbRecorsds(fil):
  """Read file or input stream, and return of PDBRecords, one per model
  Header records are given in the first list"""

  pdbFile = PdbLib.PDBFile()
  pdbFile.load_file(fil)
  recordProcessor = PdbLib.RecordProcessor()
  recordProcessor.process_pdb_records(pdbFile)
  #
  return pdbFile


def readModelRecords(fil) -> Tuple[List[PdbLib.PDBRecord], List[List[PdbLib.PDBRecord]]]:
  """Read file or input stream, and return list-of-lists-of PDBRecords, one per model
  All records are given in the first list, subsequent lists contain only ATOM records"""

  pdbFile = readPdbRecorsds(fil)

  model = []
  header = []
  data = []
  for rec in pdbFile:
    if rec._name == 'ENDMDL':
      # put model into result and make a new one
      data.append(model)
      model = []
    elif rec._name in('ATOM  ', 'HETATM'):
      # Always append ATOM and HETATM records
      model.append(rec)
    elif not data:
      # For the first model only append all records, in case we want them later
      header.append(rec)
  #
  if model:
    # Special case: ENDMDL record missing
    # Only arrive here if we have had ATOM records since the last ENDMDL record (or beginning)
    data.append(model)
  #
  return header, data

def loadStructureEnsemble(molSystem:"MolSystem", fil) -> "StructureEnsemble":
  """Load PDB file into new structure ensemble matching MolSystem
  NB MolSystem is a required parameter for the data model,
  but there is no requirement that the data match"""

  # TBD further data extraction, use of header, match chains to existing one, make new chains?? ...

  header, data = readModelRecords(fil)

  if data:
    atomCount = len(data[0])
    modelCount = len(data)
    if any(x for x in data[1:] if len(x) != atomCount):
      raise ValueError("Multiple models have different atom counts in PDB file %s - loading aborted")


    # NBNB TBD check that names match in different models

    memopsRoot = molSystem.root
    nextId = max(x.ensembleId for x in molSystem.structureEnsembles) + 1
    apiEnsemble = memopsRoot.newStructureEnsemble(molSystem=molSystem, ensembleId = nextId)

    for rec in data[0]:
      chain = (apiEnsemble.findFirstCoordChain(code=rec['chainID']) or
               apiEnsemble.newChain(code=rec['chainID']))
      residue = (chain.findFirstResidue(seqCode=rec['resSeq'], seqInsertCode=rec['iCode'] or ' ') or
                 chain.newResidue(seqCode=rec['resSeq'], seqInsertCode=rec['iCode'] or ' ',
                                  code3Letter=rec['resName']))

      # NBNB Heuristic. We need an elementName
      elementName = rec['element'] or spectrumLib.name2ElementSymbol(rec['name']) or 'Unknown'
      # NBNB wil likely break with altLocated atoms. Meanwhile do it right
      residue.newAtom(name=rec['name'], altLocationCode=rec['altLoc'],
                      elementName=elementName.title())

    coordinates = []
    addCoordinate = coordinates.append
    occupancies = []
    addOccupancy = occupancies.append
    bFactors = []
    addBFactor = bFactors.append
    # NBNB TBD Add atomNames array

    # Gather data
    # NBNB TBD atomNameData need doing
    for model in data:
      for rec in model:
        addCoordinate(rec['x'])
        addCoordinate(rec['y'])
        addCoordinate(rec['z'])
        addOccupancy(rec['occupancy'])
        addBFactor(rec['tempFactor'])

    # Set data
    apiEnsemble.newDataMatrix(name='coordinates', shape=(modelCount, atomCount,3), data=coordinates)
    apiEnsemble.newDataMatrix(name='occupancies', shape=(modelCount, atomCount), data=occupancies)
    apiEnsemble.newDataMatrix(name='bFactors', shape=(modelCount, atomCount), data=bFactors)

    #
    return apiEnsemble

  else:
    print("WARNING, no ATOM data in PDB file %s - loading aborted" % fil)





