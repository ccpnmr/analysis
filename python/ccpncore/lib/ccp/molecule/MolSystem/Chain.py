"""Functions to be copied automatically into ccpn.api.ccp.molecule.MolSystem.Chain

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


def renumberChainSeqCodes(self:'Chain', firstSeqCode:int=1, skipZeroSeqCode:bool=False):
  """Reset chain numbering to sequential integers starting at firstSeqCode """

  seqCode = firstSeqCode
  for residue in self.sortedResidues():
    if seqCode == 0 and skipZeroSeqCode:
      seqCode = 1
    residue.seqCode = seqCode
    residue.seqInsertCode = None
    seqCode += 1


def expandMolSystemAtoms(self:'Chain'):
  """Add extra atoms to chain corresponding to AtomSets
  Called on V2 upgrade, or on finalisation of chain."""

  # Set elementSymbol and add missing atoms (lest something breaks lower down)
  for residue in self.sortedResidues():
    chemCompVar = residue.chemCompVar
    for chemAtom in chemCompVar.findAllChemAtoms(className='ChemAtom'):
      atom = residue.findFirstAtom(name=chemAtom.name)
      if atom is None:
        residue.newAtom(name=chemAtom.name, atomType='single',
                        elementSymbol=chemAtom.elementSymbol)
      else:
        atom.elementSymbol = chemAtom.elementSymbol

  # Set boundAtoms for existing atoms within residue
  for residue in self.sortedResidues():
    chemCompVar = residue.chemCompVar
    for atom in residue.atoms:
      chemAtom = chemCompVar.findFirstChemAtom(name=atom.name, className='ChemAtom')
      if chemAtom is not None:
        boundChemAtoms = set(x for y in chemAtom.chemBonds for x in y.chemAtoms)
        for boundChemAtom in boundChemAtoms:
          if boundChemAtom is not chemAtom and boundChemAtom.className == 'ChemAtom':
            boundAtom = residue.findFirstAtom(name=boundChemAtom.name)
            if boundAtom is not None and boundAtom not in atom.boundAtoms:
              atom.addBoundAtom(boundAtom)

    # Add boundAtoms for MolResLinks
      for molResLink in self.molecule.molResLinks:
        ff = self.findFirstResidue
        atoms = [ff(seqId=x.molResidue.serial).findFirstAtom(name=x.linkEnd.boundChemAtom.name)
                 for x in molResLink.molResLinkEnds]
        if atoms[1] not in atoms[0].boundAtoms:
          atoms[0].addBoundAtom(atoms[1])

    # Add boundAtoms for MolSystemLinks
    for linkEnd in residue.sortedMolSystemLinkEnds():
      molSystemLink = linkEnd.molSystemLink
      atoms = [x.residue.findFirstAtom(name=x.linkEnd.boundChemAtom.name)
               for x in molSystemLink.molSystemLinkEnds]
      if atoms[1] not in  atoms[0].boundAtoms:
        atoms[0].addBoundAtom(atoms[1])

    # NB we do NOT add boundAtoms for NonCovalentBonds

    # Add extra atoms corresponding to ChemAtomSets
    chemCompVar = residue.chemCompVar
    # AQUA is good on pseudoatom names
    pseudoNamingSystem = chemCompVar.chemComp.findFirstNamingSystem(name='AQUA')

    # Map from chemAtomSet to equivalent Atom
    casMap = {}

    # map from chemAtomSet.name to nonStereo names
    nonStereoNames = {}

    for chemAtomSet in chemCompVar.chemAtomSets:

      # get nests of connected chemAtomSets
      if not chemAtomSet.chemAtomSet:
        # get nested chemAtomSets, starting at topmost set
        localSets = [chemAtomSet]
        for cas in localSets:
          localSets.extend(cas.chemAtomSets)

        # Process in reverse order, guaranteeing that contained sets are always ready
        for cas in reversed(localSets):
          chemContents = cas.sortedChemAtoms()
          # NB the fact that chemAtoms and chemAtomSets are sorted (by name) is used lower down
          if chemContents:
            # contents are real atoms
            components = [residue.findFirstAtom(name=x.name) for x in chemContents]
          else:
            chemContents = cas.sortedChemAtomSets()
            components = [casMap[x] for x in chemContents]
          elementSymbol = chemContents[0].elementSymbol

          commonBound = frozenset.intersection(*(x.boundAtoms for x in components))

          # Add 'equivalent' atom
          newName = cas.name.replace('*', '%')
          newAtom = residue.newAtom(name=newName, atomType='equivalent',
                                    elementSymbol=elementSymbol,atomSetName=cas.name,
                                    components=components, boundAtoms=commonBound)
          casMap[cas] = newAtom

          # NBNB the test on '#' count is a hack to exclude Tyr/Phe HD#|HE#
          hackExclude = newName.count('%') >= 2

          # Add 'pseudo' atom for proton
          if elementSymbol == 'H':
            newName = None
            if pseudoNamingSystem:
              atomSysName = pseudoNamingSystem.findFirstAtomSysName(atomName=cas.name,
                                                                    atomSubType=cas.subType)
              if atomSysName:
                newName = atomSysName.sysName

            if newName is None:
              # No systematic pseudoatom name found - make one.
              # NBNB this will give names like MD1, QG1, MD2 for cases like Ile delta,
              # where the standard says MD, QG, MG.
              # But all the standard cases are covered by the pseudoNamingSystem ('AQUA')
              # Can we get away with this, or do we have to rename on a per-residue basis
              # for the special cases?
              startChar = 'Q'
              if (len(cas.chemAtoms) == 3 and cas.isEquivalent
                  and components[0].findFirstBoundAtom().elementSymbol == 'C'):
                if len(set(x.findFirstBoundAtom() for x in components)) == 1:
                  # This is a methyl group
                  # The second 'if' is likely unnecessary in practice, but let us be correct here
                  startChar = 'M'

              newName = startChar + cas.name.strip('*')[1:]

            if len(newName) > 1:
              # Make pseudoatom, except for 'H*'
              residue.newAtom(name=newName, atomType='pseudo', elementSymbol=elementSymbol,
                              atomSetName=cas.name, components=components, boundAtoms=commonBound)

          # Add 'nonstereo atoms
          if not cas.isEquivalent and len(components) == 2 and not hackExclude:
            # NB excludes cases with more than two non-equivalent components
            # But then I do not think there are any in practice.
            # and anyway we do not have a convention for them.
            nonStereoNames[cas.name] = newNames = []
            starpos = cas.name.find('*')
            for ii,component in enumerate(components):
              # NB components are sorted by key, which means by name
              newChar = 'XY'[ii]
              ll = list(component.name)
              if len(ll) > starpos:
                ll[starpos] = newChar
              else:
                # Necessary for cases like H2'/H2''
                ll.append(newChar)
              newName = ''.join(ll)
              newNames.append(newName)
              if residue.findFirstAtom(name=newName) is not None:
                print ("WARNING, new atom already exists: %s %s %s %s"
                       % (residue.chain.code, residue.seqId, residue.ccpCode, newName))
              else:
                residue.newAtom(name=newName, atomType='nonstereo', elementSymbol=elementSymbol,
                                atomSetName=cas.name, components=components, boundAtoms=commonBound)


    # NBNB Now we need to set boundAtoms for non-single Atoms.
    # We need to set:
    # HG*-CG* etc.
    # HGX*-CGX etc. - can be done from previous by char substitution
    eqvTypeAtoms = [x for x in residue.sortedAtoms() if x.atomType == 'equivalent']
    for ii,eqvAtom in enumerate(eqvTypeAtoms):
      components = eqvAtom.sortedComponents()
      for eqvAtom2 in eqvTypeAtoms[ii+1:]:
        components2 = eqvAtom2.sortedComponents()
        if len(components) == len(components2):
          if all((x in components2[jj].boundAtoms) for jj,x in enumerate(components)):
            # All components of one are bound to a component of the other
            # NB this relies on the sorted components being ordered to match the bonds
            # but you should expect that both cases are sorted by branch index
            # CG1,CG2 matching HG1*,HG2* etc.

            # Add bond between equivalent atoms
            eqvAtom.addBoundAtom(eqvAtom2)

            nsNames1 = nonStereoNames.get(eqvAtom.atomSetName)
            nsNames2 = nonStereoNames.get(eqvAtom2.atomSetName)
            if nsNames1 and nsNames2:
              # Non-stereoAtoms are defined for both - add X,Y bonds
              # NB We rely on names being sorted (X then Y in both cases)
              for kk,name in enumerate(nsNames1):
                atom2 = residue.findFirstAtom(name=nsNames2[kk])
                residue.findFirstAtom(name=name).addBoundAtom(atom2)

            break

def renameChain(self:'Chain', newCode:str):
  """Rename chain in place, fixing all stored references to the chainCode"""
  molSystem = self.molSystem
  oldCode = self.code
  if newCode == oldCode:
    return
  if molSystem.findFirstChain(code=newCode) is not None:
    raise ValueError ("Cannot rename to Chain %s, chain with that name already exists" % newCode)

  root = self.root
  root.__dict__['override'] = True

  # Set up for undo
  undo = self.root._undo
  if undo is not None:
    undo.increaseBlocking()

  ###if 1:
  try:
    # relink StructureEnsembles
    for structureEnsemble in molSystem.structureEnsembles:

      # reset chainCode

      # NBNB TBD FIXME when we finish settling structures, this should NOT happen

      for coordChain in structureEnsemble.coordChains:
        if coordChain.code == oldCode:
          parentDict = structureEnsemble.__dict__['coordChains']
          del parentDict[oldCode]
          coordChain.code = newCode
          parentDict[newCode] = coordChain

    # Fix NmrCalc instances
    # Not wrapped, so no need for notifiers
    for nmrCalcStore in molSystem.root.sortedNmrCalcStores():
      for run in nmrCalcStore.sortedRuns():
        for obj in run.findAllData(molSystemCode=molSystem.code):
          className = obj.className
          if className in ('MolSystemData', 'MolResidueData'):
            chainCodes = list(obj.chainCodes)
            if oldCode in chainCodes:
              for ii,code in chainCodes:
                if code == oldCode:
                  chainCodes[ii] = newCode
            obj.chainCodes = chainCodes

    # Fix self
    parentDict = molSystem.__dict__['chains']
    del parentDict[oldCode]
    self.code = newCode
    parentDict[newCode] = self

  finally:
    # reset override and set isModified
    root.__dict__['override'] = False
    self.__dict__['isModified'] = True
    if undo is not None:
      undo.decreaseBlocking()


  # Fix NmrChains - DOne outside overr8ide to trigger rename notifiers for NmrChains
  for nmrProject in molSystem.nmrProjects:
    nmrChain = nmrProject.findFirstNmrChain(code=oldCode)
    if nmrChain:
      # parentDict = nmrProject.__dict__['nmrChains']
      # del parentDict[oldCode]
      nmrChain.code = newCode
      # parentDict[newCode] = nmrChain

  if undo is not None:
    undo.newItem(renameChain, renameChain, undoArgs=(self, oldCode), redoArgs=(self, newCode))

  # call notifiers:
  # NBNB the import MUST be inside a function as we can get circular import problems otherwise

  # NBNB TBD FIXME We should have notifiers here to update graphics.