"""Module Documentation here

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

from ccpncore.lib.spectrum.Util import DEFAULT_ISOTOPE_DICT
from ccpncore.lib.molecule import Labelling

def findLinkedResidue(residue, linkCode:str='prev'):
  """find residue linked to current with link of type 'linkCode' (defaults to 'prev')
  Use 'prev' to find previous residue, 'next' to find next residue"
  .. describe:: Input

  MolSystem.Residue

  .. describe:: Output

  MolSystem.Residue
  """
  newMolResidue = None
  linkEnd = residue.molResidue.findFirstMolResLinkEnd(linkCode=linkCode)
  if linkEnd is not None:
    for otherEnd in linkEnd.molResLink.molResLinkEnds:
      if otherEnd is not linkEnd:
        newMolResidue = otherEnd.molResidue
        break

  if newMolResidue is None:
    return None
  else:
    return residue.chain.findFirstResidue(seqId=newMolResidue.serial)





# NBNB TBD FIXME update this to work.

def getResidueObservableAtoms(residue, refExperiment=None, labelling=None,
                              minFraction:float=0.1, jCouplingBonds=(1,2,3),
                              usePermissiveShifts:bool=False,
                              chemElements=('H','C','N','F','P')):
  """
  Determine which atoms of a chem comp varient would give rise to
  observable resonances considering a given reference experiment
  and/or an isotope labelling scheme. Can specify minimum fraction of
  an isotope to consider something observable and the chemical elements which
  you are observing. Boolean option to match database min and max
  chemical shift bounds to atom sites, rather than randon coil shift
  values (default).

  .. describe:: Input

  MolSystem.Residue, NmrExpPrototype.RefExperiment,
  ChemCompLabel.LabelingScheme or LabeledMolecule.LabeledMixture,
  Float, Boolean, List of Words

  .. describe:: Output

  List of ChemComp.ChemAtoms
  """

  if not jCouplingBonds:
    jCouplingBonds = (0,)

  atomSiteDict   = {}
  isotopomerDict = {}
  atomSitesAll   = {}

  if refExperiment:
    for atomSite in refExperiment.nmrExpPrototype.atomSites:
      isotope = atomSite.isotopeCode
      if not isotope in atomSitesAll:
        atomSitesAll[isotope] = []

      atomSitesAll[isotope].append(atomSite)

  isotopeDict = {}

  if atomSitesAll:
    isotopes = atomSitesAll.keys()

  else:
    isotopes = []
    for element in chemElements:
      isotope = DEFAULT_ISOTOPE_DICT.get(element)

      if isotope:
        isotopes.append(isotope)

  for isotope in isotopes:
    element = isotope

    while element[0] in '0123456789':
      element = element[1:]

    isotopeDict[element] = isotope


  filteredAtoms = []
  nextMolResiduen= residue.molResidue.nextMolResidue

  prevResidue = residue.findLinkedResidue('prev')
  nextResidue = residue.findLinkedResidue('next')

  natAbundance = residue.root.findFirstLabelingScheme(name='NatAbun')

  #print residue.seqCode, residue.ccpCode, refExperiment.name
  for residue0 in (prevResidue,residue,nextResidue):
    isotopomers = None

    if residue0:
      resId = residue0.molResidue.serial
      atoms = residue0.atoms

      # Compile isotopomers for this residue
      if labelling and (labelling.className == 'LabelingScheme'):
        chemComp   = residue0.chemCompVar.chemComp
        ccpCode    = chemComp.ccpCode
        molType    = chemComp.molType
        chemCompLabel = labelling.findFirstChemCompLabel(ccpCode=ccpCode,
                                                         molType=molType)

        if not chemCompLabel:
          chemCompLabel = natAbundance.findFirstChemCompLabel(ccpCode=ccpCode,
                                                              molType=molType)


        if chemCompLabel:
          isotopomers  = chemCompLabel.isotopomers
          isotopomerDict[residue0] = isotopomers


    else:
      atoms = []

    #atoms0 = [] # Those which make it through the filter
    for atom in atoms:
      chemAtom = atom.chemAtom
      isotope  = isotopeDict.get(chemAtom.elementSymbol)

      if not isotope:
        continue

      if chemAtom.waterExchangeable:
        continue

      if isotopomers:
        fractionDict = Labelling._getIsotopomerSingleAtomFractions(isotopomers,atom.name,
                                                                  chemAtom.subType)
        # Exclude if no isotope incorporation above threshold
        fraction = fractionDict.get(isotope, minFraction)
        if fraction < minFraction:
          continue

      elif labelling:
        fractionDict = Labelling._singleAtomFractions(labelling, resId, atom.name)
        if not fractionDict:
          continue

        fraction = fractionDict.get(isotope, minFraction)
        if fraction < minFraction:
          continue


      atomSitesIsotope = atomSitesAll.get(isotope)
      if atomSitesIsotope:
        setSize = None

        if usePermissiveShifts:
          shifts = getChemicalShiftBounds(chemAtom)
          if not shifts:
            shifts = [getRandomCoilShift(chemAtom),]

        else:
          shifts = [getRandomCoilShift(chemAtom),]

        for atomSite in atomSitesIsotope:

          maxShift = atomSite.maxShift
          if (maxShift is not None) and (shifts[0] > maxShift):
            continue

          minShift = atomSite.minShift
          if (minShift is not None) and (shifts[-1] < minShift):
            continue

          if setSize is None:
            setSize     = 1
            chemAtomSet = chemAtom.chemAtomSet

            if chemAtomSet:
              setSize = len(chemAtomSet.chemAtoms)

          minNumber =  atomSite.minNumber
          if setSize < minNumber:
            continue

          maxNumber = atomSite.maxNumber
          if maxNumber and (setSize>maxNumber):
            continue

          numberStep = atomSite.numberStep
          if (setSize-minNumber) % numberStep != 0:
            continue

          if atomSiteDict.get(atomSite) is None:
            atomSiteDict[atomSite] = []
          atomSiteDict[atomSite].append(atom)

          #print 'AS', atomSite.name, atom.name

      filteredAtoms.append(atom)


  if refExperiment:
    #print refExperiment.name

    # Atom sites which are possibly visible given dims
    observableAtomSites = {}
    for refExpDim in refExperiment.refExpDims:
      for refExpDimRef in refExpDim.refExpDimRefs:
        for atomSite in refExpDimRef.expMeasurement.atomSites:
          observableAtomSites[atomSite] = True

    # Get prototype graph atomSite routes

    graphRoutes = []
    for expGraph in refExperiment.nmrExpPrototype.expGraphs:
      expSteps = [(es.stepNumber, es) for es in expGraph.expSteps]
      expSteps.sort()
      routes = []
      stepNumber, expStep = expSteps[0]

      for atomSite in expStep.expMeasurement.atomSites:
        route = [(atomSite,None,stepNumber)]
        routes.append(route)

      while True:
        routes2 = []

        for route in routes:
          atomSiteA, null, stepA = route[-1]
          #print atomSiteA.name, step

          for expTransfer in atomSiteA.expTransfers:
            atomSites = list(expTransfer.atomSites)
            atomSites.remove(atomSiteA)
            atomSiteB = atomSites[0]

            if not expTransfer.transferToSelf:
              if atomSiteB is atomSiteA:
                continue

            for stepB, expStepB in expSteps:
              if stepA > stepB:
                continue

              if atomSiteB in expStepB.expMeasurement.atomSites:
                routes2.append( route[:] + [(atomSiteB,expTransfer,stepB)] )
                #print ['%s %d' % (a[0].name, a[2]) for a in routes2[-1]]
                break

        if routes2:
          routes = routes2
        else:
          break

      for route in routes:
        atomRoutes = []
        lastAtomSite = route[-1][0]

        for i in range(len(route)-1):
          atomSiteA, null, stepA = route[i]
          atomSiteB, expTransfer, stepB = route[i+1]
          transferType = expTransfer.transferType

          #print stepA, atomSiteA.name, stepB, atomSiteB.name, transferType

          if atomRoutes:
            atomsA = [r[-1][0] for r in atomRoutes]
          else:
            atomsA = atomSiteDict[atomSiteA]

          atomRoutes2 = []
          for atomA in atomsA:
            for atomB in atomSiteDict[atomSiteB]:
              if isotopomerDict:
                chemAtomA = atomA.chemAtom
                chemAtomB = atomB.chemAtom
                subTypeA  = chemAtomA.subType
                subTypeB  = chemAtomB.subType
                isotopeA  = isotopeDict[chemAtomA.elementSymbol]
                isotopeB  = isotopeDict[chemAtomB.elementSymbol]
                residueA  = atomA.residue
                residueB  = atomB.residue

                if residueA is residueB:
                  isotopomersA = isotopomerDict.get(residueA)
                  atomNames    = (atomA.name, atomB.name)
                  subTypes     = (subTypeA, subTypeB)
                  pairDict     = Labelling._getIsotopomerAtomPairFractions(isotopomersA, atomNames,
                                                                          subTypes)
                  fraction     = pairDict.get((isotopeA, isotopeB), minFraction)

                  if fraction  < minFraction:
                    continue

                else:
                  isotopomersA = isotopomerDict.get(residueA)
                  isotopomersB = isotopomerDict.get(residueB)

                  if isotopomersB and isotopomersA:
                    fractionDictA = Labelling._getIsotopomerSingleAtomFractions(isotopomersA,
                                                                               atomA.name, subTypeA)
                    fractionDictB = Labelling._getIsotopomerSingleAtomFractions(isotopomersB,
                                                                               atomB.name, subTypeB)
                    fraction = fractionDictA.get(isotopeA, 1.0) * fractionDictB.get(isotopeB, 1.0)

                    if fraction < minFraction:
                      continue

              elif labelling:
                chemAtomA = atomA.chemAtom
                chemAtomB = atomB.chemAtom
                isotopeA  = isotopeDict[chemAtomA.elementSymbol]
                isotopeB  = isotopeDict[chemAtomB.elementSymbol]
                residueA = atomA.residue
                residueB = atomB.residue
                molResidueA = residueA.molResidue
                molResidueB = residueB.molResidue
                resIds = (molResidueA.serial, molResidueB.serial)
                atomNames = (atomA.name, atomB.name)

                pairDict = Labelling._atomPairFractions(labelling, resIds, atomNames)
                fraction = pairDict.get((isotopeA, isotopeB), minFraction)

                if fraction  < minFraction:
                  continue

              addAtom = False
              if transferType in longRangeTransfers:
                addAtom = True

              elif transferType in ('onebond','CP') and areAtomsBound(atomA, atomB):
                addAtom = True

              elif transferType == 'TOCSY'and areAtomsTocsyLinked(atomA, atomB):
                addAtom = True

              elif transferType == 'Jcoupling':
                numBonds = getNumConnectingBonds(atomA, atomB, limit=max(jCouplingBonds))
                if numBonds in jCouplingBonds:
                  addAtom = True

              elif transferType == 'Jmultibond' and not areAtomsBound(atomA, atomB):
                numBonds = getNumConnectingBonds(atomA, atomB, limit=max(jCouplingBonds))
                if numBonds in jCouplingBonds:
                  addAtom = True

              if addAtom:
                grown = True
                #print 'AB', atomA.name, atomA.residue.seqCode,'+', atomB.name, atomB.residue.seqCode
                if not atomRoutes:
                  atomRoutes2.append( [(atomA,atomSiteA),(atomB,atomSiteB),] )
                  #print atomA.name, atomB.name

                else:
                  for atomRoute in atomRoutes:
                    atomRoutes2.append( atomRoute[:] + [(atomB,atomSiteB),] )
                  #print '+', atomB.name


          atomRoutes = []
          for atomRoute in atomRoutes2:
            if atomRoute[-1][1] is lastAtomSite:
              atomRoutes.append(atomRoute)

        graphRoutes.append(atomRoutes)


    observableAtoms = set()
    for routes in graphRoutes:
      for route in routes:

        for atomB, atomSiteB in route:
          if atomB.residue is residue: # Must have one atom from this residue
            for atomA, atomSiteA in route:
              if observableAtomSites.get(atomSiteA):
                observableAtoms.add(atomA)
            break

  else:
    observableAtoms = filteredAtoms

  return list(observableAtoms)

