"""Functions to be copied automatically into ccpn.api.ccp.molecule.Molecule.molecule

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

from ccpncore.lib.chemComp import Io as chemCompIo
from ccpncore.lib.molecule import MoleculeQuery
from ccpncore.lib.molecule.MoleculeModify import _getLinearChemCompData
from ccpncore.memops.ApiError import ApiError
from ccpncore.util import CopyData, Undo


def clone(molecule, newName:str=None):
  """Make a new molecule based upon the sequence of an existing one
  .. describe:: Input

  Molecule.Molecule

  .. describe:: Output

  Molecule.Molecule
  """
  defaultString =  'Molecule %d'

  project = molecule.root
  ii = len(project.molecules) + 1
  newName = newName or defaultString % ii
  while project.findFirstMolecule(name=newName) is not None:
    ii += 1
    newName = defaultString % ii
  newMolecule = CopyData.copySubTree(molecule, project, topObjectParameters={'name':newName,},
                                     maySkipCrosslinks=True )

  return newMolecule


def extendOneLetterMolResidues(molecule, sequence:str, molType:str='protein', startNumber:int=1,
                            isCyclic:bool=False):
  """Descrn: Adds MolResidues for a sequence of code1Letter to Molecule, using molType.
             Consecutive protein or DNA/RNA residues are connected, other residues remain unlinked
     Inputs: Ccp.Molecule.Molecule,
             Word (Sequence string, of one-letter codes),
             Word (molType: 'protein', 'DNA', or 'RNA'
             Int (first MolResidue.seqCode)
             bool (is molecule cyclic?)
     Output: List of new Ccp.Molecule.MolResidues
  """
  if not sequence:
    raise ValueError("Attempt to append empty residue sequence")

  root = molecule.root

  oldMolResidues = molecule.molResidues
  if oldMolResidues:
    nn = max([x.seqCode for x in oldMolResidues]) + 1
    startNumber = max(startNumber, nn)

  # Sequence string. Use molType and assume one-letter codes
  if not molType in MoleculeQuery.LINEAR_POLYMER_TYPES:
    raise ValueError("molType %s must be one of:  %s"
                     % (molType, MoleculeQuery.LINEAR_POLYMER_TYPES))

  # upcase, as all one-letter codes are upper case
  sequence = sequence.upper()

  ll = [root.findFirstChemComp(molType=molType, code1Letter=x, className="StdChemComp")
        for x in sequence]
  if None in ll:
    ii = ll.index(None)
    raise ValueError("Illegal %s code %s at position %s in sequence: %s"
                     % (molType, sequence[ii], ii, sequence))

  if len(ll) == 1:
    chemComp = ll[0]
    chemCompVar  = (chemComp.findFirstChemCompVar(linking='none') or
                    chemComp.findFirstChemCompVar()) # just a default
    molResidues = [molecule.newMolResidue(seqCode=startNumber, chemCompVar=chemCompVar)]

  else:
    seqInput= [(molType,x.ccpCode) for x in ll]
    molResidues = extendLinearSequence(molecule, seqInput, seqCodeStart=startNumber,
                                    isCyclic=isCyclic)

  #
  return molResidues


def extendMolResidues(molecule, sequence:list, startNumber:int=1, isCyclic:bool=False):
  """Descrn: Adds MolResidues for a sequence of residueNames to Molecule.
             Consecutive protein or DNA/RNA residues are connected, other residues remain unlinked
     Inputs: Ccp.Molecule.Molecule,
             List of Words (residueName),
             Int (first MolResidue.seqCode)
             bool (is molecule cyclic?)
     Output: List of new Ccp.Molecule.MolResidues
  """

  root = molecule.root

  if not sequence:
    return []

  # Reset startNumber to match pre-existing MOlResidues
  oldMolResidues = molecule.molResidues
  if oldMolResidues:
    nn = max([x.seqCode for x in oldMolResidues]) + 1
    startNumber = max(startNumber, nn)

  # Convert to sequence of (molType, ccpCode) and check for known residueNames
  residueName2chemCompId = MoleculeQuery.fetchStdResNameMap(root)
  seqInput = [residueName2chemCompId.get(x) for x in sequence]
  if None in seqInput:
    ii = seqInput.index(None)
    raise ValueError("Unknown residueName %s at position %s in sequence"
                     % (sequence[ii], ii))

  # Divide molecule in stretches by type, and add the residues one stretch at a time
  result = []

  offset1 = 0
  while offset1 < len(seqInput):
    molType1, ccpCode = seqInput[offset1]

    if molType1 in MoleculeQuery.LINEAR_POLYMER_TYPES:
      # Linear polymer stretch - add to stretch
      offset2 = offset1 + 1
      while offset2 < len(seqInput):
        molType2 = seqInput[offset2][0]
        if (molType2 in MoleculeQuery.LINEAR_POLYMER_TYPES
            and (molType1 == 'protein') == (molType2 == 'protein')):
          # Either both protein or both RNA/DNA
          offset2 += 1
        else:
          break

      if offset2 - offset1 > 1:
        result.extend(extendLinearSequence(molecule, seqInput[offset1:offset2],
                                        seqCodeStart=startNumber+offset1, isCyclic=isCyclic))
        offset1 = offset2
        # End of stretch. Skip ret of loop and go on to next residue
        continue

    # No linear polymer stretch was found. Deal with residue by itself
    # assert  molType1 not in LINEAR_POLYMER_TYPES or offset2 - offset1 == 1
    chemComp = chemCompIo.fetchChemComp(root, molType1, ccpCode)
    if chemComp:
      chemCompVar  = (chemComp.findFirstChemCompVar(linking='none') or
                      chemComp.findFirstChemCompVar()) # just a default

      result.append(molecule.newMolResidue(seqCode=startNumber+offset1, chemCompVar=chemCompVar))
      offset1 += 1

    else:
      raise ValueError('ChemComp %s,%s cannot be found.' % (molType1, ccpCode))

  #
  return result


def extendLinearSequence(molecule, sequence:list, seqCodeStart:int=1,
                       isCyclic:bool=False):
  """Descrn: Add residues to molecule. Fast method, which uses 'override' mode.
             sequence is a list of (molType,ccpCode) tuples - so can make mixed-type
             linear polymers; All ChemComps must have next and prev links to fit a
             linear polymer seqCodes start from seqCodeStart, serial from next
             free serial (or 1). FIrst residue is 'start' and last is 'end', unlesss isCyclic
    Inputs: Molecule.molecule, List of Tuples of Strings (molType, ccpCode), Int, Boolean
     Output: List of Molecule.MolResidues
  """
  logger = molecule.root._logger

  if len(sequence) < 2:
    raise ApiError("Sequence %s too short for function" % sequence)


  # set up
  project = molecule.root
  chemCompData = {}

  molResidues = []
  molResLinkEnds = []
  molResLinks = []

  # get starting serial
  serialDict = molecule.__dict__.setdefault('_serialDict', {})
  serial = serialDict.get('molResidues', 0)

  root = molecule.root
  root.__dict__['override'] = True

  # Set up for undo
  undo = molecule.root._undo
  if undo is not None:
    undo.increaseBlocking()

  ###if 1:
  try:
    # first residue
    if isCyclic:
      seqCode = seqCodeStart - 1
      doSequence = sequence
    else:
      seqCode = seqCodeStart
      serial += 1
      doSequence = sequence[1:-1]

      molType, ccpCode = sequence[0]
      molResData, otherLinkCodes = _getLinearChemCompData(project, molType,
                                                        ccpCode, 'start')

      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)
      molResidues.append(molResidue)

      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
            molResLinkEnds.append(linkEnd)

    # middle residues
    for seqTuple in doSequence:
      molType,ccpCode = seqTuple
      seqCode += 1
      serial += 1
      if seqTuple in chemCompData:
        molResData,otherLinkCodes = chemCompData[seqTuple]
      else:
        molResData,otherLinkCodes = _getLinearChemCompData(project, molType,
                                                          ccpCode, 'middle')
        chemCompData[seqTuple] = (molResData,otherLinkCodes)

      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)
      molResidues.append(molResidue)

      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if not molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
            molResLinkEnds.append(linkEnd)

    # last residue
    if not isCyclic:
      seqCode += 1
      serial += 1
      (molType,ccpCode) = sequence[-1]
      molResData,otherLinkCodes = _getLinearChemCompData(project, molType,
                                                        ccpCode, 'end')

      molResidue = molecule.newMolResidue(seqCode=seqCode, serial=serial,
                                          **molResData)
      molResidues.append(molResidue)

      if otherLinkCodes:
        for linkCode in otherLinkCodes:
          # TBC these mostly seem to exist already...
          if molResidue.findFirstMolResLinkEnd(linkCode=linkCode):
            continue

          linkEnd = molResidue.newMolResLinkEnd(linkCode=linkCode)
          molResLinkEnds.append(linkEnd)

    # make links
    for second in range(1,len(sequence)):
      first = second -1
      nextLinkEnd = molResidues[first].findFirstMolResLinkEnd(linkCode='next')
      molResLinkEnds.append(nextLinkEnd)
      prevLinkEnd = molResidues[second].findFirstMolResLinkEnd(linkCode='prev')
      molResLinkEnds.append(prevLinkEnd)
      molResLinks.append(
       molecule.newMolResLink(molResLinkEnds=[nextLinkEnd,prevLinkEnd])
      )

    if isCyclic:
      # cyclising link
      nextLinkEnd = molResidues[-1].findFirstMolResLinkEnd(linkCode='next')
      molResLinkEnds.append(nextLinkEnd)
      prevLinkEnd = molResidues[0].findFirstMolResLinkEnd(linkCode='prev')
      molResLinkEnds.append(prevLinkEnd)
      molResLinks.append(
       molecule.newMolResLink(molResLinkEnds=[nextLinkEnd,prevLinkEnd])
      )

    # final validity check
    molecule.checkAllValid()

  except:
    # clean up
    try:
      while molResLinks:
        molResLink = molResLinks.pop()
        molResLink.delete()
      while molResidues:
        molResidue = molResidues.pop()
        molResidue.delete()
    except:
      logger.error("Error in clean-up after precious error")

  finally:
    # reset override and set isModified
    root.__dict__['override'] = False
    molecule.__dict__['isModified'] = True
    if undo is not None:
      undo.decreaseBlocking()

  if undo is not None and (molResidues or molResLinks):
    undo.newItem(Undo.deleteAll, extendLinearSequence, undoArgs=(molResidues+molResLinks,),
                 redoArgs=(molecule, sequence),
                 redoKwargs = {'seqCodeStart':seqCodeStart, 'isCyclic':isCyclic})

  # call notifiers:
  # NBNB the im port MUST be inside a function as we can get circular import problems otherwise
  from ccpncore.api.ccp.molecule import Molecule
  for clazz, objs in (
   (Molecule.MolResidue, molResidues),
   (Molecule.MolResLinkEnd, molResLinkEnds),
   (Molecule.MolResLink, molResLinks),
  ):
    notifiers = clazz._notifies.get('__init__')
    if notifiers:
      for notify in notifiers:
        for obj in objs:
          notify(obj)

  return molResidues