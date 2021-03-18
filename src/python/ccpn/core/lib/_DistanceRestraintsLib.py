#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-18 13:29:08 +0000 (Thu, March 18, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2021-02-22 15:44:00 +0000 (Mon, February 22, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

###### WARNING: Private routines
##     Many routines are directly imported from V2 (ccpnmr2.5/python/ccpnmr/analysis/core/ConstraintBasic.py)
##     and input/output API objects.

import re, operator
import uuid
from math import sqrt
import numpy as np

from ccpn.util.Logging import getLogger
from ccpn.core.DataSet import DataSet
from ccpn.core.RestraintList import RestraintList
from ccpn.core.lib.ContextManagers import notificationEchoBlocking, undoBlockWithoutSideBar
from ccpnmodel.ccpncore.lib import V2Upgrade
from ccpnmodel.v_3_0_2.upgrade import getNmrMolSystems


longRangeTransfers = ('through-space',)

def _getMeanPeakIntensity(peakList, intensityType, minMerit):
    peaks = [x for x in peakList.peaks if x.figOfMerit >= minMerit]
    intensities = np.array([getattr(p, intensityType, None) for p in peaks])
    intensities = intensities[intensities != None]  # remove the Nones
    mean = np.mean(abs(intensities))
    return mean

def _getNoeDistance(intensity, params):
    """
    Get target, minimum and maximum distance for an NOE intensity Given ISPA
    parameters, errors and limits

    """
    refDist, negError, posError, absMin, absMax, power = params
    dist = refDist / (abs(intensity) ** (1 / power))
    dist = max(min(dist, absMax), absMin)
    minDist = max(absMin, dist - (negError * dist))
    maxDist = min(absMax, dist + (posError * dist))
    return dist, minDist, maxDist



def _getOnebondExpDimRefs(experiment):
  """
  Get pairs of experiment dimensions that are connected by onebond transfers
  """

  expDimRefs   = []
  expTransfers = []

  for expTransfer in experiment.sortedExpTransfers():
    if expTransfer.transferType in ('onebond',):
      expTransfers.append(expTransfer)

  for expTransfer in expTransfers:
    expDimRefs.append(expTransfer.sortedExpDimRefs())

  return expDimRefs

def _getOnebondDataDims(spectrum):
  """
  Get pairs of spectrum data dimensions that are connected by onebond transfers

  """

  dataDims = []
  expDimRefs = _getOnebondExpDimRefs(spectrum.experiment)

  for expDimRef0, expDimRef1 in expDimRefs:
    dataDim0 = spectrum.findFirstDataDim(expDim=expDimRef0.expDim)
    dataDim1 = spectrum.findFirstDataDim(expDim=expDimRef1.expDim)

    if dataDim0 and dataDim1:
      dataDims.append( [dataDim0,dataDim1] )

  return dataDims


def _getConstraintAtoms(constraint):
    """
    Get the atoms that may be assigned to the constrained resonances
    The outer most list is due to restraint ambiguity, the middle list
    is the list for different resonances and the inner list
    is for equivalent atoms.
    """

    atoms = []
    fixedResonances = []
    className = constraint.className

    if className == 'DihedralConstraint':
        fixedResonances.append(constraint.resonances)

    elif className in ('ChemShiftConstraint', 'CsaConstraint'):
        fixedResonances.append([constraint.resonance, ])

    else:
        for item in constraint.items:
            fixedResonances.append(item.resonances)

    for fixedResonanceList in fixedResonances:
        atomList = []
        for fixedResonance in fixedResonanceList:
            fixedResonanceSet = fixedResonance.resonanceSet

            if fixedResonanceSet:
                equivAtoms = {}

                for fixedAtomSet in fixedResonanceSet.atomSets:
                    for atom in fixedAtomSet.atoms:
                        equivAtoms[atom] = True

                atomList.append(equivAtoms.keys())

        if len(atomList) == len(fixedResonanceList):
            atoms.append(atomList)

    return atoms

def _getIndirectDataDims(dataSource):
    """
    Get the data dims of a spectrum that represent indirect
    (e.g. relayed NOESY) magnetisation transfers.
    """
    expDims = set()

    for expTransfer in dataSource.experiment.expTransfers:
        if expTransfer.transferType in longRangeTransfers:
            for expDimRef in expTransfer.expDimRefs:
                expDims.add(expDimRef.expDim)

    dataDims = dataSource.sortedDataDims()
    dataDims = [dd for dd in dataDims if dd.expDim in expDims]
    # Check for indirect transfers
    indirectDims = set()
    dataDimDict = {}
    for dataDim in dataSource.dataDims:
        for dataDimRef in dataDim.dataDimRefs:
            dataDimDict[dataDimRef.expDimRef] = dataDim

    expDimRefs = set(dataDimDict.keys())
    for expTransfer in dataSource.experiment.expTransfers:
        if expTransfer.expDimRefs.issubset(expDimRefs) and not expTransfer.isDirect:
            dataDims = [dataDimDict[edr] for edr in expTransfer.expDimRefs]
            indirectDims.add(tuple(dataDims))

    return indirectDims

def _getIndirectThroughSpaceIsotopes(experiment):
    """
    For a given experiment find the pairs of isotopes present along
    onbond transfers connected via a relayed (indirect) through space transfer.
    Returns pairs of isotopes, direct and indirect, for each experimental
    dimension. An isotope may be None if one side of the through space transfer is
    observed in experiment, e.g. H_hC.NOESY.
    """

    isotopesDict = {}

    expTransfer0 = experiment.findFirstExpTransfer(isDirect=False)
    refExperiment = experiment.refExperiment

    if expTransfer0 and refExperiment:
        expDimRefA, expDimRefB = expTransfer0.expDimRefs
        refExpDimRefA = expDimRefA.refExpDimRef
        refExpDimRefB = expDimRefB.refExpDimRef
        isotopesDict[expDimRefA] = (expDimRefA.findFirstIsotope(), None)
        isotopesDict[expDimRefB] = (expDimRefB.findFirstIsotope(), None)

        if refExpDimRefA and refExpDimRefB:

            # Get directly shift measured atom sites
            visibleSites = set()
            for expDim in experiment.expDims:
                for expDimRef in expDim.expDimRefs:
                    if not expDimRef.refExpDimRef:
                        continue

                    measurement = expDimRef.refExpDimRef.expMeasurement
                    if measurement.measurementType in ('Shift', 'shift', 'MQShift'):
                        visibleSites.update(measurement.atomSites)

            # Get atom sites at or onebond from expDimRefA
            measurementA = refExpDimRefA.expMeasurement
            atomSitesA = set(measurementA.atomSites)
            for atomSiteA in measurementA.atomSites:
                for expTransferA in atomSiteA.expTransfers:
                    if expTransferA.transferType == 'onebond':
                        atomSitesA.update(expTransferA.atomSites)

            # Get atom sites at or onebond from expDimRefB
            measurementB = refExpDimRefB.expMeasurement
            atomSitesB = set(measurementB.atomSites)
            for atomSiteB in measurementB.atomSites:
                for expTransferB in atomSiteB.expTransfers:
                    if expTransferB.transferType == 'onebond':
                        atomSitesB.update(expTransferB.atomSites)

            # Get long range atomSite pairs
            longRange = set()
            for expGraph in refExperiment.nmrExpPrototype.expGraphs:
                for expTransfer in expGraph.expTransfers:
                    if expTransfer.transferType in longRangeTransfers:
                        longRange.add(expTransfer.atomSites)

            # Get atom site pair where at least one is not direct
            # and pair is long range
            for atomSiteA in atomSitesA:
                for atomSiteB in atomSitesB:
                    if (atomSiteA not in visibleSites) or (atomSiteB not in visibleSites):
                        if frozenset([atomSiteA, atomSiteB]) in longRange:
                            if atomSiteA not in visibleSites:
                                isotope1 = expDimRefA.findFirstIsotope()
                                isotope2 = atomSiteA.isotope
                                isotopesDict[expDimRefA] = (isotope1, isotope2)

                            if atomSiteB not in visibleSites:
                                isotope1 = expDimRefB.findFirstIsotope()
                                isotope2 = atomSiteB.isotope
                                isotopesDict[expDimRefB] = (isotope1, isotope2)

                            break
                else:
                    continue
                break

    return isotopesDict


def _getBoundAtoms(atom):
    """Get a list of atoms bound to a given atom..
    .. describe:: Input
    """

    if hasattr(atom, 'boundAtoms'):
        return atom.boundAtoms

    atoms = []
    chemAtom = atom.chemAtom
    residue = atom.residue

    chemAtomDict = {}
    for atom2 in residue.atoms:
        # Only atoms specific to ChemCompVar :-)
        chemAtomDict[atom2.chemAtom] = atom2

    for chemBond in chemAtom.chemBonds:
        for chemAtom2 in chemBond.chemAtoms:
            if chemAtom2 is not chemAtom:
                atom2 = chemAtomDict.get(chemAtom2)
                if atom2:
                    atoms.append(atom2)

    linkEnd = residue.chemCompVar.findFirstLinkEnd(boundChemAtom=chemAtom)
    if linkEnd:
        molResLinkEnd = residue.molResidue.findFirstMolResLinkEnd(linkEnd=linkEnd)

        if molResLinkEnd:
            molResLink = molResLinkEnd.molResLink

            if molResLink:
                for molResLinkEnd2 in molResLink.molResLinkEnds:
                    if molResLinkEnd2 is not molResLinkEnd:
                        residue2 = residue.chain.findFirstResidue(molResidue=molResLinkEnd2.molResidue)

                        if residue2:
                            chemAtom2 = molResLinkEnd2.linkEnd.boundChemAtom
                            atom2 = residue2.findFirstAtom(chemAtom=chemAtom2)

                            if atom2:
                                atoms.append(atom2)
                        break

    atom.boundAtoms = atoms
    return atoms


def getPrimaryDataDimRef(freqDataDim):
    """
    get dataDimRef child with lowest expDimRef.serial
    """
    dataDimRefs = freqDataDim.dataDimRefs
    if dataDimRefs:
        ll = [(x.expDimRef.serial, x) for x in dataDimRefs]
        ll.sort()
        return ll[0][1]
    else:
        return None

def _getDataDimRefFromPeakDim(peakDim):
    dataDimRef = None
    for i, dim in enumerate(peakDim.parent.sortedPeakDims()):
        if dim == peakDim:
            freqDataDim = peakDim.parent.parent.parent.sortedDataDims()[i]
            dataDimRef = getPrimaryDataDimRef(freqDataDim)
            if dataDimRef == peakDim.dataDimRef:
                return dataDimRef
    return dataDimRef

def _setPeakDataDimRef(peak):
    for peakDim in peak.peakDims:
        if not peakDim.dataDimRef:
            peakDim.dataDimRef = _getDataDimRefFromPeakDim(peakDim)


def _getBoundResonances(resonance, recalculate=False, contribs=None, doWarning=False,
                        recursiveCall=False):
    """
    Find all resonances that have a single bond connection to the input resonance
    Option to recalculate given assignment status (e.g. if something changes)
    Option to specify peakDimContribs to search

    """
    if (not recalculate) and resonance.covalentlyBound:
        return list(resonance.covalentlyBound)

    resonances = set()  # Linked by bound atoms irrespective of spectra
    pairResonances = set()  # prochiral or other pairs that can not be determined imemdiately
    resonanceSet = resonance.resonanceSet

    funnyResonances = set()

    if resonanceSet:
        # residue  = resonanceSet.findFirstAtomSet().findFirstAtom().residue
        atomSets = resonanceSet.atomSets

        for atomSet in atomSets:
            # for atom in atomSet.atoms:
            atom = atomSet.findFirstAtom()

            for atom2 in _getBoundAtoms(atom):
                atomSet2 = atom2.atomSet

                if atomSet2 and atomSet2.resonanceSets:

                    usePaired = False
                    if len(atomSets) > 1:
                        chemAtomSet = atom2.chemAtom.chemAtomSet
                        if chemAtomSet:
                            usePaired = (chemAtomSet.isProchiral or
                                         (chemAtomSet.chemAtomSet and chemAtomSet.chemAtomSet.isProchiral))

                    for resonanceSet2 in atomSet2.resonanceSets:
                        for resonance2 in resonanceSet2.resonances:
                            if resonance2 is resonance:  # should not happen
                                if resonance not in funnyResonances:
                                    print('WARNING: in _getBoundResonances(): resonance %d tried to be linked to itself' % resonance.serial)
                                    funnyResonances.add(resonance)
                            elif usePaired:
                                pairResonances.add(resonance2)
                            else:
                                resonances.add(resonance2)

    if not contribs:
        contribs = resonance.peakDimContribs

    expResonances = set()
    foundBothPaired = False
    for contrib in contribs:
        peakDim = contrib.peakDim
        if not peakDim.dataDimRef:
            dataDimRef = _getDataDimRefFromPeakDim(peakDim)
            expDimRef1 = dataDimRef.expDimRef
        else:
            expDimRef1 = peakDim.dataDimRef.expDimRef

        expTransfers = expDimRef1.expTransfers

        for expTransfer in expTransfers:
            if expTransfer.transferType in ('onebond', 'CP'):
                expDimRef2 = None

                for expDimRef in expTransfer.expDimRefs:
                    if expDimRef is not expDimRef1:
                        expDimRef2 = expDimRef
                        break

                if expDimRef2:
                    for peakDim2 in peakDim.peak.peakDims:
                        if not peakDim2.dataDimRef:
                            _dataDimRef = _getDataDimRefFromPeakDim(peakDim2)
                            _expDimRef2 = _dataDimRef.expDimRef
                        else:
                            _expDimRef2 = peakDim2.dataDimRef.expDimRef

                        if peakDim2.dataDimRef and (_expDimRef2 is expDimRef2):
                            expBound = set()

                            for contrib2 in peakDim2.peakDimContribs:
                                if (not contrib.peakContribs) and (not contrib2.peakContribs):
                                    resonance2 = contrib2.resonance

                                    if resonance is not resonance2:
                                        expBound.add(resonance2)

                                else:
                                    for peakContrib in contrib.peakContribs:
                                        if peakContrib in contrib2.peakContribs:
                                            resonance2 = contrib2.resonance

                                            if resonance is not resonance2:
                                                expBound.add(resonance2)

                                            break

                            if len(expBound) > 1:
                                # Ambiguity
                                for bound in expBound:
                                    # Leave the covalently bound one
                                    if bound in resonances:
                                        break

                                else:
                                    aSet = set(x for x in expBound if x in resonance.covalentlyBound)
                                    if aSet and aSet != pairResonances:
                                        # Resonances found. Previously linked.
                                        # Not the pairResonances. Use them
                                        expResonances.update(aSet)

                                    else:
                                        # check presence of prochiral pairs
                                        ll = [x for x in pairResonances if x in expBound]
                                        if len(pairResonances) == 2 and len(ll) == 2:
                                            foundBothPaired = True
                                        elif ll:
                                            # found some prochiral pair resonances - use them
                                            expResonances.update(ll)
                            else:
                                expResonances.update(expBound)

    if foundBothPaired and not [x for x in expResonances if x in pairResonances]:
        # particular special case.
        # Resonnce is bound to both prochiral altrnatives but always as a pair.

        if recursiveCall:
            # This was called from elsewhere. We could resolve nothing, so send back to caller
            pass

        else:
            # call for sister resonances and see
            resons = resonanceSet.sortedResonances()
            newResonances = set()
            if len(resons) > 1:
                # there are sister resonances
                resons.remove(resonance)
                for reson in resons:
                    boundResons = _getBoundResonances(reson, recalculate=True, contribs=contribs,
                                                      doWarning=False, recursiveCall=True)
                    ll = [x for x in pairResonances if x not in boundResons]
                    if not ll:
                        # One sister was bound to both. Incorrect data. Bind to both here too
                        newResonances.update(pairResonances)
                        break
                    elif len(ll) < len(pairResonances):
                        # Some resonances were taken. Use the free ones.
                        newResonances.update(ll)

            if newResonances:
                expResonances.update(newResonances)
            else:
                # No data anywhere to resolve which is which. Match on serials
                pairResonList = list(sorted(pairResonances, key=operator.attrgetter('serial')))
                rr = pairResonList[resonanceSet.sortedResonances().index(resonance)]
                expResonances.add(rr)

    resonances.update(expResonances)

    # if doWarning and (resonance.isotopeCode == '1H') and (len(resonances) > 1):
    #  pass

    if resonances:
        resonance.setCovalentlyBound(resonances)
    else:
        resonance.setCovalentlyBound([])

    return list(resonances)


def _setQuickShiftList(shift):
    """
    Sets up a list of lists of shifts for a shift list
    accessed by shift.value: quicker than searching all
    """

    shiftList = shift.parentList
    if not hasattr(shiftList, 'quickShifts'):

        shiftList.quickShifts = {}
        for shift2 in shiftList.measurements:
            isotope = shift2.resonance.isotopeCode

            quickShiftDict = shiftList.quickShifts.get(isotope, {})
            if not quickShiftDict:
                shiftList.quickShifts[isotope] = quickShiftDict

            # WARNING: this key function has to be same as below and in findMatchingShifts
            key = int(round(10 * shift2.value))
            if quickShiftDict.get(key) is None:
                quickShiftDict[key] = []
            quickShiftDict[key].append(shift2)
            shift2.quickShiftIndex = key

    isotope = shift.resonance.isotopeCode
    quickShiftDict = shiftList.quickShifts.get(isotope, {})
    if not quickShiftDict:
        shiftList.quickShifts[isotope] = quickShiftDict

    oldKey = hasattr(shift, 'quickShiftIndex') and shift.quickShiftIndex

    if shift.isDeleted:
        if oldKey is not False:
            try:
                quickShiftDict[oldKey].remove(shift)
            except:
                pass
            del shift.quickShiftIndex
        return

    # WARNING: this key function has to be same as above and in findMatchingShifts
    key = int(round(10 * shift.value))
    if oldKey is not False and key == oldKey:
        return

    if oldKey is not False:
        # remove old key
        try:
            quickShiftDict[oldKey].remove(shift)
        except ValueError as e:
            print('Warning: Quick shift index value failure', e)
        except KeyError as e:
            print('Warning: Quick shift index key failure', e)

    if quickShiftDict.get(key) is None:
        quickShiftDict[key] = []

    quickShiftDict[key].append(shift)
    shift.quickShiftIndex = key

def _findMatchingShifts(dataDimRef, position, tolerance, findAssigned=False):
    """
    For a dataDimRef give the NMR shifts within a tolerance
    (which may be specified) to a given position with an option
    to find only shifts with resonances assigned to atoms

    """

    shiftList = dataDimRef.expDimRef.expDim.experiment.shiftList
    unit = shiftList.unit
    isotopes = dataDimRef.expDimRef.isotopeCodes

    dataDim = dataDimRef.dataDim
    # if not tolerance:
    #     tolerance = getAnalysisDataDim(dataDim).assignTolerance

    if unit != 'point':
        position = unit_converter[('point', unit)](position, dataDimRef)

    possibilities = []

    if not shiftList.measurements:
        return possibilities

    if not hasattr(shiftList, 'quickShifts'):
        _setQuickShiftList(shiftList.findFirstMeasurement())

    # WARNING: this key function has to be same as in setQuickShiftList
    keyMin = int(round(10 * (position - tolerance)))
    keyMax = int(round(10 * (position + tolerance)))
    keyRange = range(keyMin, keyMax + 1)

    for isotope in isotopes:
        quickShiftDict = shiftList.quickShifts.get(isotope, {})
        if quickShiftDict:
            for key in keyRange:
                shifts = quickShiftDict.get(key)
                if shifts is not None:
                    for shift in shifts:
                        if findAssigned and (not shift.resonance.resonanceSet):
                            continue

                        tryResonance = shift.resonance
                        if tryResonance.isDeleted:
                            continue

                        difference = abs(position - shift.value)
                        if difference < tolerance:
                            possibilities.append(shift)

    return possibilities

def _isResidueInRange(residue, residueRanges, dataDim):
    """
    Determine if a residue is in a residue range table for a given data dim. The
    range table lists residue bounds (first and last residue objects) for a chain
    appropriate to a list of data dims (often bonded).
    """

    for (dataDims, chain, startResidue, endResidue) in residueRanges:
        if dataDim in dataDims:
            if residue.chain is chain:
                if residue.seqCode >= startResidue.seqCode:
                    if residue.seqCode <= endResidue.seqCode:
                        return True

    return False


def _isShiftInRange(shiftValue, shiftRanges):
    """
    Determine whether a chemical shift value is contained within
    one of the input ranges.

    Float (Nmr.Shift.value), List of Tuples of Floats (min, max range bounds)

    """

    for (minVal, maxVal) in shiftRanges:
        if shiftValue >= minVal:
            if shiftValue <= maxVal:
                return True

    return False

def _findPeakConstraintPairs(peak, residueRanges=None, distDataDims=None, distIndices=None, indirectDims=None):

  spectrum = peak.peakList.dataSource
  experiment = spectrum.experiment
  nmrProject = experiment.nmrProject

  if distDataDims is None:
    distDataDims = _getThroughSpaceDataDims(spectrum)

  if distIndices is None:
    distIndices  = [dd.dim-1 for dd in distDataDims]

  if indirectDims is None:
    indirectDims = {}
    for dataDims in _getIndirectDataDims(spectrum):
      if  set(dataDims) == set(distDataDims):
        isotopesDict = _getIndirectThroughSpaceIsotopes(experiment)

        for dataDim in dataDims:
          expDimRef = dataDim.expDim.sortedExpDimRefs()[0]
          indirectDims[dataDim.dim] = isotopesDict[expDimRef]

  resonances0 = []
  resonances1 = []

  distDim0, distDim1 = distDataDims
  peakDims = peak.sortedPeakDims()

  if peakDims[distIndices[0]].peakDimContribs and peakDims[distIndices[1]].peakDimContribs:
    peakDim0 = peakDims[distIndices[0]]
    for contrib in peakDim0.peakDimContribs:
      resonance = contrib.resonance
      if resonance.resonanceSet:
        if residueRanges:
          residue = resonance.resonanceSet.findFirstAtomSet().findFirstAtom().residue
          if _isResidueInRange(residue, residueRanges, distDim0):
            resonances0.append( (contrib.resonance, []) )
        else:
          resonances0.append( (contrib.resonance, []) )

    if peakDim0.dim in indirectDims and indirectDims[peakDim0.dim][1]:
      isotopeA, isotopeB = indirectDims[peakDim0.dim]
      chemElement = isotopeB.chemElement

      for resonance, indirect in resonances0:

        isotopeCode = '%d%s' % (isotopeB.massNumber, chemElement.symbol)

        # Use _getBoundResonances, to get from Cga to Hga* (and not also Hgb*)
        resonancesA = set(x for x in _getBoundResonances(resonance, recalculate=True)
                          if x.isotopeCode == isotopeCode
                          and x.resonanceSet)

        # get covalently bound atomSets
        atoms = set()
        for atomSet in resonance.resonanceSet.atomSets:
          atoms.update(_getBoundAtoms(atomSet.findFirstAtom()))

        atomSets = set(a.atomSet for a in atoms if a.atomSet and \
                       a.chemAtom.chemElement is chemElement)

        if resonancesA:
          # remove covalently impossible resonances
          resonanceSets = set(y for x in atomSets for y in x.resonanceSets)
          resonancesA = set(x for x in resonancesA
                            if x.resonanceSet in resonanceSets)

        if not resonancesA:
          # make new resonances to fit covalent atoms.
          for atomSet in atomSets:
            resonanceB = nmrProject.newResonance(isotopeCode=isotopeCode)
            print('Not implemented yet.', 'Needs to assignAtomsToRes')
            # TODO assignAtomsToRes
            # assignAtomsToRes([atomSet,], resonanceB)
            # resonancesA.add(resonanceB)

        indirect.extend(resonancesA)

    peakDim1 = peakDims[distIndices[1]]
    for contrib in peakDim1.peakDimContribs:
     resonance = contrib.resonance
     if resonance.resonanceSet and (resonance not in resonances0):
       if residueRanges:
         residue = resonance.resonanceSet.findFirstAtomSet().findFirstAtom().residue
         if _isResidueInRange(residue, residueRanges, distDim1):
           resonances1.append( (contrib.resonance, []) )
       else:
         resonances1.append( (contrib.resonance, []) )

    if peakDim1.dim in indirectDims and indirectDims[peakDim1.dim][1]:
      isotopeA, isotopeB = indirectDims[peakDim1.dim]
      chemElement = isotopeB.chemElement

      for resonance, indirect in resonances1:

        isotopeCode = '%d%s' % (isotopeB.massNumber, chemElement.symbol)

        resonancesA = set(x for x in _getBoundResonances(resonance, recalculate=True)
                          if x.isotopeCode == isotopeCode
                          and x.resonanceSet)

        atoms = set()
        for atomSet in resonance.resonanceSet.atomSets:
          atoms.update(_getBoundAtoms(atomSet.findFirstAtom()))

        atomSets = set(a.atomSet for a in atoms if a.atomSet and \
                       a.chemAtom.chemElement is chemElement)

        if resonancesA:
          # remove covalently impossible resonances
          resonanceSets = set(y for x in atomSets for y in x.resonanceSets)
          resonancesA = set(x for x in resonancesA
                            if x.resonanceSet in resonanceSets)

        if not resonancesA:
          for atomSet in atomSets:
            resonanceB = nmrProject.newResonance(isotopeCode=isotopeCode)
            # TODO assignAtomsToRes
            print('Not implemented yet.', 'Needs to assignAtomsToRes')
            # assignAtomsToRes([atomSet,], resonanceB)
            # resonancesA.add(resonanceB)
        indirect.extend(resonancesA)

  return resonances0, resonances1



def _pnt2ppm(pnt, dataDimRef):
  freqDataDim = dataDimRef.dataDim
  npoints = freqDataDim.numPointsOrig
  sw = freqDataDim.spectralWidthOrig
  sf = dataDimRef.expDimRef.sf
  refpt = dataDimRef.refPoint
  refppm = dataDimRef.refValue
  t = - npoints * sf / float(sw)
  ppm = (pnt - refpt)/t + refppm
  return ppm

def _ppm2pnt(ppm, dataDimRef):
  freqDataDim = dataDimRef.dataDim
  npoints = freqDataDim.numPointsOrig
  sw = freqDataDim.spectralWidthOrig
  sf = dataDimRef.expDimRef.sf
  refpt = dataDimRef.refPoint
  refppm = dataDimRef.refValue
  t = - npoints * sf / float(sw)
  pnt = t*(ppm - refppm) + refpt
  return pnt

def _hz2pnt(hz, dataDimRef):
  freqDataDim = dataDimRef.dataDim
  npoints = freqDataDim.numPointsOrig
  sw = freqDataDim.spectralWidthOrig
  sf = dataDimRef.expDimRef.sf
  refpt = dataDimRef.refPoint
  refppm = dataDimRef.refValue
  t = - npoints / float(sw)
  pnt = t*(hz - sf*refppm) + refpt
  return pnt

def _pnt2hz(pnt, dataDimRef):
  freqDataDim = dataDimRef.dataDim
  npoints = freqDataDim.numPointsOrig
  sw = freqDataDim.spectralWidthOrig
  sf = dataDimRef.expDimRef.sf
  refpt = dataDimRef.refPoint
  refppm = dataDimRef.refValue
  t = - npoints / float(sw)
  hz = (pnt - refpt)/t + sf*refppm
  return hz

unit_converter = {}
unit_converter[('ppm', 'point')] = _ppm2pnt
unit_converter[('point', 'ppm')] = _pnt2ppm
unit_converter[('Hz', 'point')] = _hz2pnt
unit_converter[('point', 'Hz')] = _pnt2hz


def _getPeakDimFullShiftRange(peakDim):
    """
    Give the min and max possible chem shifts for a peak dim
    based on set min/max epDim frequencies or full spec with

    """

    dataDimRef = peakDim.dataDimRef
    dataDim = peakDim.dataDim
    if not dataDimRef:
        values = dataDim.pointValues
        return [min(values), max(values)]

    expDimRef = dataDim.expDim.findFirstExpDimRef()
    shiftList = expDimRef.expDim.experiment.shiftList
    unit = shiftList.unit

    if expDimRef.minAliasedFreq is None:
        if unit == 'point':
            minShift = dataDim.numPointsOrig
        else:
            minShift = unit_converter[('point', unit)](dataDim.numPointsOrig, dataDimRef)

    else:
        minShift = expDimRef.minAliasedFreq

    if expDimRef.maxAliasedFreq is None:
        if unit == 'point':
            maxShift = 0
        else:
            maxShift = unit_converter[('point', unit)](0, dataDimRef)

    else:
        maxShift = expDimRef.maxAliasedFreq

    shiftRange = [minShift, maxShift]
    shiftRange.sort()

    return shiftRange

def _getAliasedPeakDimPositions(peakDim, shiftRanges=None, ppm=None):
    """
    Give all the aliased/unaliased positions of a peakDim either in a
    specified shift range or the full range for the dimension type.
    Units for the shift ranges are ppm. Note this function uses the
    peakDim.realValue, i.e. center of couplings for main assignment.
    Use the PeakBasic version if the actual extremum location should
    be used. Optional ppm argument if main position is not the one
    to be considered, e.g. in reduced dimensionality or MQ.

    .. describe:: Input

    Nmr.PeakDim, List of (Tuples of Floats (MinShift,MaxShift) )

    .. describe:: Output

    List of Floats (Nmr.PeakDim.positions)
    """

    if not shiftRanges:
        shiftRanges = [_getPeakDimFullShiftRange(peakDim), ]

    positions = []
    dataDimRef = peakDim.dataDimRef

    if dataDimRef:
        sw = dataDimRef.dataDim.numPointsOrig

        if ppm is None:
            ppm = peakDim.realValue

        points = points0 = _ppm2pnt(ppm, dataDimRef)
        while _isShiftInRange(ppm, shiftRanges):
            positions.append(points)
            points -= sw
            ppm = _pnt2ppm(points, dataDimRef)

        points = points0 + sw
        while _isShiftInRange(ppm, shiftRanges):
            positions.append(points)
            points += sw
            ppm = _pnt2ppm(points, dataDimRef)

    else:
        positions.append(peakDim.position)

    return positions

def _findMatchingPeakDimShifts(peakDim, shiftRanges=None, tolerance=None,
                               aliasing=True, findAssigned=False, ppm=None):
    """
    For peakDim give the NMR shifts within a tolerance
    (which may be specified) of its position in a given set of ranges
    with options if the peakDim position might be aliased
    and to find only shifts with resonances assigned to atoms.
    Obeys molSystem assignments for atom linked peaks - these
    must match the peakDim's experiment molSystems.
    Option to pas in an alternative ppm value if the main peakDim value
    is not to be used (e.g. reduced dimensionality MQ etc).

    .. describe:: Input

    Nmr.PeakDim, List of Tuples (Float, Float) Float, Boolean, Boolean, Float

    .. describe:: Output

    List of Nmr.Shifts
    """

    shifts = []
    dataDimRef = peakDim.dataDimRef

    if not dataDimRef:
        return shifts

    if ppm is None:
        ppm = peakDim.realValue

    unit = dataDimRef.expDimRef.unit
    dataDim = dataDimRef.dataDim
    peakDimPos = unit_converter[(unit, 'point')](ppm, dataDimRef)

    if aliasing:
        positions = _getAliasedPeakDimPositions(peakDim, shiftRanges, ppm)
        if peakDimPos not in positions:
            positions.append(peakDimPos)
    else:
        positions = [peakDimPos, ]

    for position in positions:
        shifts.extend(_findMatchingShifts(dataDimRef, position,
                                          tolerance=tolerance,
                                          findAssigned=findAssigned))

    molSystems = peakDim.peak.peakList.dataSource.experiment.molSystems

    if molSystems:
        outShifts = []
        for shift in shifts:
            resonanceSet = shift.resonance.resonanceSet

            if resonanceSet:
                atom = resonanceSet.findFirstAtomSet().findFirstAtom()
                molSystem = atom.topObject

                if molSystem not in molSystems:
                    continue

            outShifts.append(shift)

    else:
        outShifts = shifts

    return outShifts

def _getPeakDimTolerance(peakDim, minTol, maxTol, multiplier):
    """
    Finds the shift matching tolerance for a peak dim based on its line width.
    Defaults to the minimum tolerance if no line width is present.

    .. describe:: Input
    Nmr.PeakDim, Float, Float, Float (Nmr,PeakDim.lineWidth to tolerance factor)
    Float (PPM tolerance)
    """

    tolerance = None
    if peakDim.dataDimRef:
        # works in ppm
        tolerance = minTol
        if peakDim.lineWidth:
            zeroVal = _pnt2ppm(0, peakDim.dataDimRef)
            width = _pnt2ppm(multiplier * peakDim.lineWidth, peakDim.dataDimRef)
            width -= zeroVal
            tolerance = min(maxTol, max(minTol, width))

    return tolerance

def _makeAPINmrConstraintStore(nmrProject):
    """
    Make a new NMR constraint top object for a project which will contain
    constraints and violations.
    """

    apiNmrConstraintStore = nmrProject.root.newNmrConstraintStore(nmrProject=nmrProject)
    apiNmrConstraintStore.quickResonances = {}
    apiNmrConstraintStore.quickAtomSets = {}
    return apiNmrConstraintStore

def _getThroughSpaceDataDims(dataSource):
    """
    Get the data dims of a spectrum that represent through-space
    magnetisation transfers.
    """
    expDims = set()
    for expTransfer in dataSource.experiment.expTransfers:
        if expTransfer.transferType in longRangeTransfers:
            for expDimRef in expTransfer.expDimRefs:
                expDims.add(expDimRef.expDim)

    dataDims = dataSource.sortedDataDims()
    dataDims = [dd for dd in dataDims if dd.expDim in expDims]

    return dataDims

def _getResonanceLabellingFraction(*args, **kwargs):
    # print('LabellingFraction Not implemented yet in V3 ')
    return

def _getResonancePairLabellingFraction(*args, **kwargs):
    # print('LabellingFraction Not implemented yet in V3 ')
    return

def _isValidFixedResonance(fixedResonance):

  resonance = fixedResonance.resonance
  if not resonance:
    return False

  resonanceSet = resonance.resonanceSet
  if not resonanceSet:
    return False

  fixedResonanceSet = fixedResonance.resonanceSet
  if not fixedResonanceSet:
    return False

  atoms = set()
  for atomSet in resonanceSet.atomSets:
    atoms.update(atomSet.atoms)

  for fixedAtomSet in fixedResonanceSet.atomSets:
    fixedAtoms = set(fixedAtomSet.atoms)
    if not fixedAtoms.issubset(atoms):
      return False

  return True


def _areAtomsBound(atom1, atom2):
    """Dertemine whether two atoms are bonded together
    .. describe:: Input

    MolSystem.Atom, MolSystem.Atom

    .. describe:: Output

    Boolean
    """

    if not hasattr(atom1, 'isAtomBound'):
        atom1.isAtomBound = {}
    elif atom1.isAtomBound.get(atom2):
        return atom1.isAtomBound[atom2]

    if not hasattr(atom2, 'isAtomBound'):
        atom2.isAtomBound = {}
    elif atom2.isAtomBound.get(atom1):
        return atom2.isAtomBound[atom1]

    isBound = False

    if atom1 is not atom2:
        residue1 = atom1.residue
        residue2 = atom2.residue

        if residue2.chain is residue1.chain:
            if residue2 is not residue1:

                linkEnd1 = residue1.chemCompVar.findFirstLinkEnd(boundChemAtom=atom1.chemAtom)
                if not linkEnd1:
                    isBound = False

                else:
                    linkEnd2 = residue2.chemCompVar.findFirstLinkEnd(boundChemAtom=atom2.chemAtom)
                    if not linkEnd2:
                        isBound = False

                    else:
                        molResLinkEnd1 = residue1.molResidue.findFirstMolResLinkEnd(linkEnd=linkEnd1)
                        if not molResLinkEnd1:
                            isBound = False

                        else:
                            molResLinkEnd2 = residue2.molResidue.findFirstMolResLinkEnd(linkEnd=linkEnd2)
                            if not molResLinkEnd2:
                                isBound = False

                            elif molResLinkEnd2 in molResLinkEnd1.molResLink.molResLinkEnds:
                                isBound = True

                            else:
                                isBound = False

            else:
                if atom1.chemAtom is not None:
                    for chemBond in atom1.chemAtom.chemBonds:
                        if atom2.chemAtom in chemBond.chemAtoms:
                            isBound = True
                            break

    atom1.isAtomBound[atom2] = isBound
    atom2.isAtomBound[atom1] = isBound

    return isBound


def _areResonancesBound(resonance1, resonance2):
    """
    Determine whether two resonances are assigned to directly bonded atoms

    .. describe:: Input

    Nmr.Resonance, Nmr.Resonance

    .. describe:: Output

    Boolean
    """

    if resonance1 is resonance2:
        return False

    resonanceSet1 = resonance1.resonanceSet
    resonanceSet2 = resonance2.resonanceSet

    if resonanceSet1 and resonanceSet2:

        atomSets1 = resonanceSet1.atomSets
        atomSets2 = resonanceSet2.atomSets

        bound1 = resonance1.covalentlyBound
        bound2 = resonance2.covalentlyBound

        # Have to look through everything to get the right equiv
        # & prochiral pair - Val CGa HGb: check both atomSets for each
        # Phe Ce* He*: check both atoms (only one atomSet each)
        for atomSet1 in atomSets1:
            for atom1 in atomSet1.atoms:
                for atomSet2 in atomSets2:
                    for atom2 in atomSet2.atoms:
                        if _areAtomsBound(atom1, atom2):
                            # Val Cgb - Hgb* can appear bound,
                            # so check resonance links
                            if (resonance1.isotopeCode == '1H') and (len(atomSets2) > 1):
                                if bound1 and resonance2 not in bound1:
                                    continue

                            elif (resonance2.isotopeCode == '1H') and (len(atomSets1) > 1):
                                if bound2 and resonance1 not in bound2:
                                    continue

                            return True

        return False

def _transferCovalentlyBound(sourceResonance, targetResonance):
    """
    Set targetResonance.covalentlyBound to match sourceResonance.covalentlyBound
    Uses serial for Resonance, and resonanceSerial for FixedResonance
    """

    if sourceResonance.className == 'FixedResonance':
        covalentSerials = set(x.resonanceSerial
                              for x in sourceResonance.covalentlyBound)
        if None in covalentSerials:
            covalentSerials.remove(None)
    else:
        # normal resonance, make sure we update status
        covalentSerials = set(x.serial for x in _getBoundResonances(sourceResonance,
                                                                    recalculate=True))

    topObj = targetResonance.topObject
    if targetResonance.className == 'FixedResonance':
        boundRes = set(topObj.findFirstFixedResonance(resonanceSerial=x)
                       for x in covalentSerials)
    else:
        boundRes = set(topObj.findFirstResonance(serial=x)
                       for x in covalentSerials)
    if None in boundRes:
        boundRes.remove(None)

    targetResonance.covalentlyBound = boundRes

def _makeFixedResonance(nmrConstraintStore, resonance):
    """
    Make a new fixed resonance for an NMR constraint top object based on a normal
    resonance. The fixed resonance will preserve assignment information at the
    time of constraint generation.
    NB should work equally well for fixedResonance input
    """

    fixedResonance = nmrConstraintStore.newFixedResonance(resonanceSerial=resonance.serial,
                                                          isotopeCode=resonance.isotopeCode,
                                                          name=resonance.name)
    _transferCovalentlyBound(resonance, fixedResonance)
    return fixedResonance


def _getFixedAtomSet(nmrConstraintStore, atoms):
    """
    Finds or creates a fixed set of atoms that is used in an NMR
    constraint head object (equivalent to one NmrConstraint file).
    Creating fixed atom sets allows assignments to change but
    old constraints to be preserved.
    """

    atom = list(atoms)[0]

    if not hasattr(nmrConstraintStore, 'quickAtomSets'):
        nmrConstraintStore.quickAtomSets = {}

    fixedAtomSet = nmrConstraintStore.quickAtomSets.get(atoms)

    if not fixedAtomSet:
        fixedAtomSet = nmrConstraintStore.findFirstFixedAtomSet(atoms=atoms)

    if not fixedAtomSet:
        atomSet = atom.atomSet
        if atomSet:
            fixedAtomSet = nmrConstraintStore.newFixedAtomSet(atoms=atomSet.atoms, name=atomSet.name)
        else:
            fixedAtomSet2 = atom.findFirstFixedAtomSet(atoms=atoms)
            if fixedAtomSet2:
                fixedAtomSet = nmrConstraintStore.newFixedAtomSet(atoms=fixedAtomSet2.atoms, name=fixedAtomSet2.name)

    nmrConstraintStore.quickAtomSets[atoms] = fixedAtomSet

    return fixedAtomSet

def _getFixedResonance(nmrConstraintStore, resonance):
    """
    Find or create a fixed resonance for an NMR constraint top object equivalent
    to the input normal resonance. The fixed resonance will preserve assignment
    information at the time of constraint generation.
    NB should work equally well for fixedResonance input
    """

    if not resonance:
        return None

    if not hasattr(nmrConstraintStore, 'quickResonances'):
        quickDict = {}
        nmrConstraintStore.quickResonances = quickDict
    else:
        quickDict = nmrConstraintStore.quickResonances

    serial = resonance.serial
    fixedResonance = quickDict.get(serial)

    if fixedResonance and fixedResonance.isDeleted:
        del quickDict[serial]
        fixedResonance = None

    if not fixedResonance:
        fixedResonance = nmrConstraintStore.findFirstFixedResonance(resonanceSerial=serial)

    # if fixedResonance and not _isValidFixedResonance(fixedResonance):
    #     # we should not delete but it is no longer validly pointing to resonance
    #     fixedResonance.resonanceSerial = None
    #     fixedResonance = None

    if not fixedResonance:
        fixedResonance = _makeFixedResonance(nmrConstraintStore, resonance)
        fixedResonances = [fixedResonance, ]

        if resonance.resonanceSet:
            fixedAtomSets = []
            for atomSet in resonance.resonanceSet.atomSets:
                fixedAtomSets.append(_getFixedAtomSet(nmrConstraintStore, atomSet.atoms))

            for resonance2 in resonance.resonanceSet.resonances:
                if resonance2 is not resonance:
                    fixedResonance2 = _makeFixedResonance(nmrConstraintStore, resonance2)
                    quickDict[resonance2.serial] = fixedResonance2
                    fixedResonances.append(fixedResonance2)

            nmrConstraintStore.newFixedResonanceSet(atomSets=fixedAtomSets, resonances=fixedResonances)

    quickDict[resonance.serial] = fixedResonance

    return fixedResonance

def _getDistMinMax(intensityValue, intensityScale, resonances0, resonances1, distanceFunction, normalise=True, labelling=None):

  if normalise:
    isoCorr0 = 0.0
    isoCorr1 = 0.0

    weight0 = 1.0/len(resonances0)
    weight1 = 1.0/len(resonances1)

    for resonance, indirect in resonances0:
      resonanceSet = resonance.resonanceSet

      propAtoms = 1.0

      if indirect:
        propAtoms = 0.0
        for resonanceB in indirect:
          if labelling:
            frac = max(0.1, _getResonancePairLabellingFraction(resonance, resonanceB, labelling) or 1.0)
          else:
            frac = 1.0

          propAtoms += frac

      elif labelling:
        propAtoms *= max(0.1, _getResonanceLabellingFraction(resonance, labelling) or 1.0)

      fac = weight0/propAtoms
      isoCorr0 +=  fac

    for resonance, indirect in resonances1:
      resonanceSet = resonance.resonanceSet

      propAtoms = 1.0

      if indirect:
        propAtoms = 0.0
        for resonanceB in indirect:
          if labelling:
            frac = max(0.1, _getResonancePairLabellingFraction(resonance, resonanceB, labelling) or 1.0)
          else:
            frac = 1.0

          propAtoms += frac

      elif labelling:
        propAtoms *= max(0.1, _getResonanceLabellingFraction(resonance, labelling) or 1.0)

      fac = weight1/propAtoms
      isoCorr1 += fac

  else:
    isoCorr0 = 1
    isoCorr1 = 1

  (dist,minDist,maxDist) = distanceFunction(intensityValue*isoCorr0*isoCorr1/intensityScale)

  return (dist,minDist,maxDist)


def _getAtomSetsDistance(atomSets1, atomSets2, structure, model=None, method='noe'):
    """
    Find the distance between two atom sets in a specified structure or ensemble
    of structures. Distances for multi atom atom sets are calculated using the
    NOE sum method by default. A model may be specified if the structure
    ensemble has many models, otherwise all models in the ensemble will be
    considered and an avergate distance is returned. The method can be either
    "noe" for NOE sum, "min" for minimum distance or "max" for maximum distance.

    .. describe:: Input

    Nmr.AtomSet, Nmr.AtomSet, MolStructure.StructureEnsemble,
    MolStructure.Model or None, Word

    .. describe:: Output

    Float (distance)
    """

    if model:
        models = [model, ]
    else:
        models = structure.models

    atomSets1 = set(atomSets1)
    atomSets2 = set(atomSets2)

    assert atomSets1 and atomSets2 and structure

    if atomSets1 == atomSets2:
        if len(atomSets1) == 2:
            atomSets0 = list(atomSets1)
            for resonanceSet in atomSets0[0].resonanceSets:
                if resonanceSet in atomSets0[1].resonanceSets:  # Prochiral
                    atomSets1 = [atomSets0[0], ]
                    atomSets2 = [atomSets0[1], ]
                    break

        if atomSets1 == atomSets2:  # Not prochiral
            return 0.0

    ensembleCoords = []
    ensembleCoordsAppend = ensembleCoords.append

    for model in models:
        coordList1 = []
        coordList2 = []
        coordList1Append = coordList1.append
        coordList2Append = coordList2.append

        for atomSet in atomSets1:
            for coord in _getAtomSetCoords(atomSet, structure, model):
                coordList1Append(coord)

        for atomSet in atomSets2:
            for coord in _getAtomSetCoords(atomSet, structure, model):
                coordList2Append(coord)

        if coordList1 and coordList2:
            ensembleCoordsAppend((coordList1, coordList2))

    if not ensembleCoords:
        return 0.0

    numPairs = float(len(atomSets1) * len(atomSets2))
    noeEnsemble = 0.0
    minDist2 = None
    maxDist2 = None

    n = 0.0
    for coords1, coords2 in ensembleCoords:
        noeSum = 0.0

        for coord1 in coords1:
            x = coord1.x
            y = coord1.y
            z = coord1.z

            for coord2 in coords2:
                dx = x - coord2.x
                dy = y - coord2.y
                dz = z - coord2.z
                dist2 = (dx * dx) + (dy * dy) + (dz * dz)

                if dist2 > 0:

                    if method == 'noe':
                        noeSum += dist2 ** -3.0

                    else:
                        if (minDist2 is None) or (dist2 < minDist2):
                            minDist2 = dist2

                        if (maxDist2 is None) or (dist2 > maxDist2):
                            maxDist2 = dist2

        noeEnsemble += sqrt(noeSum / numPairs)
        n += 1.0

    if method == 'min':
        return sqrt(minDist2)
    elif method == 'max':
        return sqrt(maxDist2)
    elif (noeEnsemble > 0.0) and n:
        noeEnsemble /= n
        return noeEnsemble ** (-1 / 3.0)

def _newDistanceRestraintsFromPeakList(peakList,
                                       intensityType='height',
                                       normalise=True,
                                       labelling=True,
                                       params = (3.2, 0.2, 0.2, 1.72, 8.0, 6.0),
                                       residueRanges=None,
                                       minMerit=0.0,

                                       ):
    """
    This function was imported from v2. All objects are in V2 terms.

    :param peakList: v2 peakList object
    :param intensityType:
    :param normalise:
    :param labelling:
    :param params: tuple of (refDist, negError, posError, absMin, absMax, power)
                    used for calculating the NOEdistances
    :param residueRanges:
    :param minMerit:
    :param scale:
    :return: distanceConstraint v2 object

    scaling not ported yet from v2

    """
    scaleDict = {} # not implemented yet
    spectrum = peakList.dataSource
    experiment = spectrum.experiment

    distDataDims = _getThroughSpaceDataDims(spectrum)
    distIndices = [dd.dim - 1 for dd in distDataDims]

    if len(distDataDims) != 2:
        msg = 'Experiment appears to not have two through-space linked dimensions. '
        msg += 'Check experiment type and dim-dim transfer settings.'
        raise RuntimeError(msg)

    distDim0, distDim1 = distDataDims
    if labelling is True:
        labelling = experiment

    if not residueRanges:
        residueRanges = None

    workingPeaks = [x for x in peakList.sortedPeaks() if x.figOfMerit >= minMerit]
    mean = _getMeanPeakIntensity(peakList, intensityType, minMerit)

    if not mean:
        msg = 'Cannot make restraints: peak %s is zero on average.' % intensityType
        msg += ' Maybe intensities are missing or the peak list is empty'
        raise RuntimeError(msg)

    constraintSet = _makeAPINmrConstraintStore(peakList.topObject)
    distConstraintList = constraintSet.newDistanceConstraintList()
    distConstraintList.addExperimentSerial(experiment.serial)
    newConstraint = distConstraintList.newDistanceConstraint
    distanceFunction = lambda val: _getNoeDistance(val, params)

    indirectDims = {}
    for dataDims in _getIndirectDataDims(spectrum):
        if set(dataDims) == set(distDataDims):
            isotopesDict = _getIndirectThroughSpaceIsotopes(experiment)

            for dataDim in dataDims:
                expDimRef = dataDim.expDim.sortedExpDimRefs()[0]
                indirectDims[dataDim.dim] = isotopesDict[expDimRef]
    _constraints = []
    for peak in workingPeaks:
        if peak.figOfMerit < minMerit:
            continue
        intensity = getattr(peak, intensityType, None)
        if not intensity:
            continue
        intensityValue = abs(intensity)
        _setPeakDataDimRef(peak)
        resonances0, resonances1 = _findPeakConstraintPairs(peak, residueRanges, distDataDims, distIndices, indirectDims)
        # print('>> resonances0', resonances0, resonances1)

        if resonances0 and resonances1:
            peakDims = peak.sortedPeakDims()
            peakDim0 = peakDims[distIndices[0]]
            peakDim1 = peakDims[distIndices[1]]

            # Filter by correlated contributions
            contribFilter = set()
            for peakContrib in peak.peakContribs:
                contribs = peakContrib.peakDimContribs
                for contrib0 in contribs:
                    if contrib0.peakDim is peakDim0:
                        for contrib1 in contribs:
                            if contrib1.peakDim is peakDim1:
                                resonancesF = (contrib0.resonance, contrib1.resonance)
                                contribFilter.add(resonancesF)
            # print('>> if contribFilter', contribFilter)
            peakMean = scaleDict.get(peak)
            if peakMean is None:
                if peak in scaleDict:  # in this case the peak is in the dict but with a value of None
                    continue  # and that means that we should skip this peak
                peakMean = mean
            (dist, minDist, maxDist) = _getDistMinMax(intensityValue, peakMean, resonances0, resonances1,
                                                      distanceFunction,
                                                      normalise=normalise, labelling=labelling)
            error = abs(maxDist - minDist)
            fResonancePairs = set()
            for resonance0, indirect0 in resonances0:
                resonances0 = indirect0 or [resonance0, ]

                fixedResonances0 = [_getFixedResonance(constraintSet, r) for r in resonances0]

                for resonance1, indirect1 in resonances1:

                    if contribFilter:
                        if (resonance0, resonance1) not in contribFilter:
                            continue

                    resonances1A = indirect1 or [resonance1, ]
                    fixedResonances1 = [_getFixedResonance(constraintSet, r) for r in resonances1A]

                    for fixedRes0 in fixedResonances0:
                        for fixedRes1 in fixedResonances1:
                            if fixedRes0 is not fixedRes1:
                                fResonancePairs.add(frozenset([fixedRes0, fixedRes1]))

            if fResonancePairs:
                # Otherwise you generate restraints between nothing and nothing
                constraint = newConstraint(weight=1.0, origData=intensityValue, targetValue=dist,
                                           upperLimit=maxDist, lowerLimit=minDist, error=error)
                rpc = constraint.newConstraintPeakContrib(experimentSerial=experiment.serial,
                                                          dataSourceSerial=spectrum.serial,
                                                          peakListSerial=peakList.serial,
                                                          peakSerial=peak.serial)

                for fixedRes0, fixedRes1 in fResonancePairs:
                    dci = constraint.newDistanceConstraintItem(resonances=[fixedRes0, fixedRes1])
                _constraints.append(constraint)

    return distConstraintList




def _makeAmbigDistConstraints(peakList, tolerances, chemShiftRanges, constraintSet=None,
                             testOnly=False, labelling=None, minLabelFraction=0.1,
                             residueRanges=None, minMerit=0.0,
                             intensityType='volume', ignoreDiagonals=True, doAliasing=True,
                             structure=None, maxDist=None,
                             scale=None, params=None, peakCategories=None):
    """
    Makes a constraint list with constraints by matching known shifts
    in given range and within specified tolerances to a NOESY peak
    list. Optional labelling scheme/mixture and labelling threshold to filter
    according to a given set of residue isotopomers.
    Constraints will be put in a new NMR constraint store object
    if none is specified. Peaks are catergorised into various lists.
    A structure and max distance can be used to filter contributions.
    The scale option is the value by which peak intensities are scaled
    for NOE table/function lookup. Params relate to the generic NOE
    distance function if neither these nor a distance function is
    specified a lookuptable is used


    .PeakList (NOESY),
    List of (Nmr.DataDim, Float, Float, Float) (shift tolerances),
    List of (Nmr.DataDim, String (isotope code), Float, Float) (chem shift ranges)
    Nmr.NmrConstraintStore, Boolean (test only),
    ChemCompLabel.LabelingScheme or True (automatic from experiment MolLabel), Float,
    Function (to get distances from NOEs),  Nmr.PeakIntensity.intensityType,
    List of (List of Nmr.DataDims, Nmr.Chain, Integer, Integer) (residue ranges),
    Float (min Peak.figOfMerit), ProgressBar (Analysis popup),
    Boolean, Boolean, MolStructure.StructureEnsemble, Float
    Float, List of Floats (distance function parameters)
    Dict (for Category Name:Lists of Nmr.Peaks)


    """


    if peakCategories is None:
        peakCategories = {}

    assignedPeaks = peakCategories['Assigned'] = []
    diagonalPeaks = peakCategories['Diagonal'] = []
    unmatchedPeaks = peakCategories['Unmatchable'] = []
    poorMeritPeaks = peakCategories['Poor Merit'] = []
    outOfRangePeaks = peakCategories['Out of range'] = []
    distalPeaks = peakCategories['Too Distal'] = []

    # peaks = peakList.peaks
    spectrum = peakList.dataSource
    experiment = spectrum.experiment
    nmrProject = experiment.nmrProject
    distDataDims = _getThroughSpaceDataDims(spectrum)
    distIndices = [dd.dim - 1 for dd in distDataDims]

    if len(distDataDims) != 2:
        msg = 'Experiment appears to not have two through-space linked dimensions. '
        msg += 'Check experiment type and dim-dim transfer settings.'
        raise RuntimeError(msg)

    distDim1, distDim2 = distDataDims

    if labelling is True:
        labelling = experiment

    if not residueRanges:
        residueRanges = None

    bondedDims = {}
    for dataDim1, dataDim2 in _getOnebondDataDims(spectrum):
        bondedDims[dataDim1] = dataDim2
        bondedDims[dataDim2] = dataDim1

    if testOnly:
        distConstraintList = None
    else:
        if not constraintSet:
            constraintSet = _makeAPINmrConstraintStore(experiment.topObject)
        distConstraintList = constraintSet.newDistanceConstraintList()
        distConstraintList.addExperimentSerial(experiment.serial)
        newConstraint = distConstraintList.newDistanceConstraint
        print(distConstraintList,'distConstraintList')


    tolDict = {}
    for (dataDim, minT, maxT, multi) in tolerances:
        tolDict[dataDim] = (minT, maxT, multi)

    chemShiftRangesDict = {}
    for (dataDim, iso, minShift, maxShift) in chemShiftRanges:
        if chemShiftRangesDict.get(dataDim) is None:
            chemShiftRangesDict[dataDim] = []

        chemShiftRangesDict[dataDim].append([minShift, maxShift])
        if tolDict.get(dataDim) is None:
            msg = 'No tolerance set for dataDim %s of dataSource %s' % (dataDim, spectrum)
            raise Exception(msg)

    # go through peaks
    # if not assigned in all the Hydrogen dims or H + bonded dim

    # Check for indirect transfers
    indirectDims = {}
    for dataDims in _getIndirectDataDims(spectrum):
        if set(dataDims) == set(distDataDims):
            isotopesDict = _getIndirectThroughSpaceIsotopes(experiment)

            for dataDim in dataDims:
                expDimRef = dataDim.expDim.sortedExpDimRefs()[0]
                indirectDims[dataDim.dim] = isotopesDict[expDimRef]

    workingPeaks = []
    for peak in peakList.sortedPeaks():
        # make sure there is datadimRef
        _setPeakDataDimRef(peak)
        # filter out diagonals
        if ignoreDiagonals:
            peakDims = peak.sortedPeakDims()
            peakDim1 = peakDims[distIndices[0]]
            peakDim2 = peakDims[distIndices[1]]
            ppm1 = peakDim1.realValue
            ppm2 = peakDim2.realValue

            delta = abs(ppm1 - ppm2)

            if (delta <= tolDict[distDim1][0]) or (delta <= tolDict[distDim2][0]):
                dataDimA = bondedDims.get(distDim1)
                dataDimB = bondedDims.get(distDim2)

                if dataDimA and dataDimB:
                    peakDimA = peak.findFirstPeakDim(dataDim=dataDimA)
                    peakDimB = peak.findFirstPeakDim(dataDim=dataDimB)
                    ppmA = _pnt2ppm(peakDimA.position, peakDimA.dataDimRef)
                    ppmB = _pnt2ppm(peakDimB.position, peakDimB.dataDimRef)

                    delta2 = abs(ppmA - ppmB)
                    if (delta2 <= tolDict[dataDimA][0]) or (delta2 <= tolDict[dataDimB][0]):
                        diagonalPeaks.append(peak)
                        continue

                else:
                    diagonalPeaks.append(peak)
                    continue

        if peak.figOfMerit < minMerit:
            poorMeritPeaks.append(peak)
            continue

        workingPeaks.append(peak)

    mean = _getMeanPeakIntensity(peakList, intensityType=intensityType, minMerit=minMerit)
    if scale:  # neither Zero nor None
        mean = scale

    if not mean:
        msg = 'Cannot make restraints: peak %s is zero on average.' % intensityType
        msg += ' Maybe intensities are missing or the peak list is empty'
        raise RuntimeError(msg)

    distanceFunction = lambda val: _getNoeDistance(val, params)


    for peak in workingPeaks:

        intensity = getattr(peak, intensityType, None)
        if not intensity:
            continue
        intensityValue = abs(intensity)

        outOfRange = 0

        unassignedPeakDims = []
        peakDims = peak.sortedPeakDims()

        outOfShiftRange = False
        for peakDim in peakDims:
            inRange = _isShiftInRange(peakDim.realValue, chemShiftRangesDict[peakDim.dataDim])
            if chemShiftRanges and not inRange:
                outOfShiftRange = True
                break

        if outOfShiftRange:
            unmatchedPeaks.append(peak)
            continue

        # n = 0
        for i in distIndices:
            peakDim = peakDims[i]
            if not peakDim.peakDimContribs:
                unassignedPeakDims.append(peakDim)

        # filter out assigned peaks
        if not unassignedPeakDims:
            assignedPeaks.append(peak)
            continue

        peakResonances = []
        for i in distIndices:
            resonances = []
            peakDim = peakDims[i]
            dataDim = peakDim.dataDim

            if peakDim in unassignedPeakDims:
                # isotope    = dataDim.expDim.findFirstExpDimRef().isotopeCodes[0]
                # peakDimPos = peakDim.position + (peakDim.numAliasing*dataDim.numPointsOrig)
                (minT, maxT, multi) = tolDict[dataDim]
                tolerance = _getPeakDimTolerance(peakDim, minT, maxT, multi)

                bondedDim = bondedDims.get(peakDim.dataDimRef.dataDim)

                if bondedDim:
                    # check that both bonded dim possibilities are within tolerances

                    shifts = _findMatchingPeakDimShifts(peakDim,
                                                        chemShiftRangesDict[dataDim],
                                                        tolerance=tolerance,
                                                        aliasing=doAliasing,
                                                        findAssigned=True)

                    if shifts:
                        for peakDim2 in peakDims:
                            if peakDim2.dataDimRef.dataDim is bondedDim:

                                shifts2 = []
                                if peakDim2.peakDimContribs:
                                    for contrib in peakDim2.peakDimContribs:
                                        shift = contrib.resonance.findFirstShift(parentList=experiment.shiftList)
                                        if shift:
                                            shifts2.append(shift)

                                else:
                                    dataDim2 = peakDim2.dataDim
                                    (minT, maxT, multi) = tolDict[dataDim2]
                                    tolerance2 = _getPeakDimTolerance(peakDim2, minT, maxT, multi)

                                    shifts2 = _findMatchingPeakDimShifts(peakDim2,
                                                                         chemShiftRangesDict[dataDim2],
                                                                         tolerance=tolerance2,
                                                                         aliasing=doAliasing,
                                                                         findAssigned=True)

                                for shift in shifts:
                                    resonance = shift.resonance

                                    for shift2 in shifts2:
                                        resonance2 = shift2.resonance

                                        if _areResonancesBound(resonance, resonance2):
                                            if residueRanges:
                                                residue = resonance.resonanceSet.findFirstAtomSet().findFirstAtom().residue
                                                if _isResidueInRange(residue, residueRanges, dataDim):
                                                    resonances.append((resonance, resonance2, []))
                                                else:
                                                    outOfRange += 1
                                            else:
                                                resonances.append((resonance, resonance2, []))
                                            break

                else:

                    shifts = _findMatchingPeakDimShifts(peakDim,
                                                        chemShiftRangesDict[dataDim],
                                                        tolerance=tolerance,
                                                        aliasing=doAliasing,
                                                        findAssigned=True)

                    for shift in shifts:
                        resonance = shift.resonance

                        if residueRanges:
                            residue = resonance.resonanceSet.findFirstAtomSet().findFirstAtom().residue
                            if _isResidueInRange(residue, residueRanges, dataDim):
                                resonances.append((resonance, None, []))
                            else:
                                outOfRange += 1
                        else:
                            resonances.append((resonance, None, []))

            else:
                # this dim is assigned
                for contrib in peakDim.peakDimContribs:
                    resonance = contrib.resonance
                    resonanceSet = resonance.resonanceSet

                    if resonanceSet:
                        if residueRanges:
                            residue = resonanceSet.findFirstAtomSet().findFirstAtom().residue
                            if _isResidueInRange(residue, residueRanges, dataDim):
                                resonances.append((resonance, None, []))
                            else:
                                outOfRange += 1
                        else:
                            resonances.append((resonance, None, []))

            # Deal with indirect transfers

            if peakDim.dim in indirectDims and indirectDims[peakDim.dim][1]:
                isotopeA, isotopeB = indirectDims[peakDim.dim]
                chemElement = isotopeB.chemElement

                for resonance, bound, indirect in resonances:

                    isotopeCode = '%d%s' % (isotopeB.massNumber, chemElement.symbol)

                    # Use getBoundResonance to get from e.g. Cga to Hga* and not Hgb*
                    resonancesA = set(x for x in _getBoundResonances(resonance, recalculate=True)
                                      if x.isotopeCode == isotopeCode
                                      and x.resonanceSet)

                    # get covalently bound atomSts
                    atoms = set()
                    for atomSet in resonance.resonanceSet.atomSets:
                        atoms.update(_getBoundAtoms(atomSet.findFirstAtom()))

                    atomSets = set(a.atomSet for a in atoms if a.atomSet and \
                                   a.chemAtom.chemElement is chemElement)

                    if resonancesA:
                        # remove covalently impossible resonances
                        resonanceSets = set(y for x in atomSets for y in x.resonanceSets)
                        resonancesA = set(x for x in resonancesA
                                          if x.resonanceSet in resonanceSets)

                    # if not resonancesA:
                    #     # make new resonances for covanlently bound atoms
                    #     for atomSet in atomSets:
                    #         resonanceB = nmrProject.newResonance(isotopeCode=isotopeCode)
                    #         assignAtomsToRes([atomSet, ], resonanceB)
                    #         resonancesA.add(resonanceB)

                    indirect.extend(resonancesA)

            # Store resonances for this dim

            peakResonances.append(resonances)

        if peakResonances[0] and peakResonances[1]:
            distal = False

            resonancePairs = set()
            for resonance0, bound0, indirect0 in peakResonances[0]:
                resonanceSet0 = resonance0.resonanceSet

                for resonance1, bound1, indirect1 in peakResonances[1]:
                    if resonance1 is resonance0:
                        continue

                    if labelling:
                        if bound0:
                            fraction0 = _getResonancePairLabellingFraction(resonance0,
                                                                          bound0,
                                                                          labelling)
                        else:
                            fraction0 = _getResonanceLabellingFraction(resonance0,
                                                                      labelling)
                        if fraction0 < minLabelFraction:
                            continue

                        if bound1:
                            fraction1 = _getResonancePairLabellingFraction(resonance1,
                                                                          bound1,
                                                                          labelling)
                        else:
                            fraction1 = _getResonanceLabellingFraction(resonance1,
                                                                      labelling)

                        if fraction1 < minLabelFraction:
                            continue

                    if structure and resonanceSet0 and (maxDist is not None):
                        resonanceSet1 = resonance1.resonanceSet

                        if resonanceSet1:
                            atomSets0 = list(resonanceSet0.atomSets)
                            atomSets1 = list(resonanceSet1.atomSets)
                            dist = _getAtomSetsDistance(atomSets0, atomSets1, structure, method='noe')

                            if dist > maxDist:
                                distal = True
                                continue

                    resonances0 = indirect0 or [resonance0, ]
                    resonances1 = indirect1 or [resonance1, ]

                    for resonanceA in resonances0:
                        for resonanceB in resonances1:
                            if resonanceA is not resonanceB:
                                resonancePairs.add(frozenset([resonanceA, resonanceB]))

            if not resonancePairs:
                unmatchedPeaks.append(peak)

                if distal:
                    distalPeaks.append(peak)

            elif not testOnly:
                resonances0 = [(resonance, indirect) for resonance, bound, indirect in peakResonances[0]]
                resonances1 = [(resonance, indirect) for resonance, bound, indirect in peakResonances[1]]
                (dist, minDistL, maxDistL) = _getDistMinMax(intensityValue, mean, resonances0, resonances1,
                                                           distanceFunction, labelling=labelling)
                error = abs(maxDistL - minDistL)
                constraint = newConstraint(weight=1.0, origData=intensityValue,
                                           targetValue=dist, upperLimit=maxDistL,
                                           lowerLimit=minDistL, error=error)

                constraint.newConstraintPeakContrib(experimentSerial=experiment.serial,
                                                    dataSourceSerial=spectrum.serial,
                                                    peakListSerial=peakList.serial,
                                                    peakSerial=peak.serial)

                for resonance0, resonance1 in resonancePairs:
                    fixedResonance0 = _getFixedResonance(constraintSet, resonance0)
                    fixedResonance1 = _getFixedResonance(constraintSet, resonance1)
                    constraint.newDistanceConstraintItem(resonances=[fixedResonance0, fixedResonance1])


        elif outOfRange > 1:
            outOfRangePeaks.append(peak)
        else:
            unmatchedPeaks.append(peak)
    return distConstraintList


def _getAtomSetCoords(atomSet, structure, model=None):
    """Find the coordinates corresponding to an NMR atom set in a given model
    of a given structure structure. The model defaults to an arbitrary one
    if none is specified.
    """

    if not model:
        model = structure.findFirstModel()

    key = '%s:%s:%d:%d' % (atomSet,  # Could be real AtomSet or a ConstraintSet one!
                           structure.molSystem.code,
                           structure.ensembleId,
                           model.serial)

    if not hasattr(structure, 'coordDict'):
        structure.coordDict = {}

    else:
        coordList = structure.coordDict.get(key)

        if coordList:
            return coordList

    atom = atomSet.findFirstAtom()
    residue = atom.residue
    chain = residue.chain
    coordChain = structure.findFirstCoordChain(code=chain.code)
    if not coordChain:
        # showWarning('Warning', 'Couldn\'t find coordinate chain')
        return []

    coordResidue = coordChain.findFirstResidue(seqId=residue.seqId)
    if not coordResidue:
        data = (residue.ccpCode, residue.seqCode)
        msg = 'Couldn\'t find coordinate residue %s %d' % data
        print(msg)
        # showWarning('Warning', msg)
        return []

    coordList = []
    findAtom = coordResidue.findFirstAtom

    for atom in atomSet.atoms:
        coordAtom = findAtom(name=atom.name)

        if coordAtom:
            coord = coordAtom.newCoord(model=model)
            coordList.append(coord)

    if not coordList:
        data = (chain.code, residue.ccpCode, residue.seqCode, atomSet.name)
        print('Couldn\'t find coordinate atoms %s %s %d %s' % data)
        return []

    structure.coordDict[key] = coordList

    return coordList

def _getRestraintsMapping(constraintSet, molSystem=None):
    nmrConstraintStore = constraintSet
    if not molSystem:
        if len(list(getNmrMolSystems(constraintSet.nmrProject)))>0:
            molSystem = list(getNmrMolSystems(constraintSet.nmrProject))[-1] #double check this, incase more than 1.

    mainMolSystemChains = molSystem.sortedChains()
    chainMap = {}
    for ch in mainMolSystemChains:
        chainMap[ch] = ch
    assignmentMap = V2Upgrade.mapUnAssignedFixedResonances(nmrConstraintStore)
    for resonance, tt in V2Upgrade.mapAssignedResonances(nmrConstraintStore, chainMap=chainMap,molSystem=molSystem).items():
      residue, name = tt
      if residue is None:
        assignmentMap[resonance] = (None, None, None, name)
      else:
        chainCode = residue.chain.code
        sequenceCode = str(residue.seqCode) + (residue.seqInsertCode or '').strip()
        residueType = residue.molResidue.chemComp.code3Letter
        assignmentMap[resonance] = (chainCode, sequenceCode, residueType, name)

    assignment2Resonance = {}
    resonanceMap = {}
    for resonance, assignment in assignmentMap.items():
      resonance.chainCode = assignment[0]
      resonance.sequenceCode = assignment[1]
      resonance.residueType = assignment[2]
      resonance.name = assignment[3]
      oldResonance = assignment2Resonance.get(assignment)
      if oldResonance is None:
        assignment2Resonance[assignment] = resonance
      elif oldResonance.serial > resonance.serial:
        # We want only one
        assignment2Resonance[assignment] = resonance
        resonanceMap[oldResonance] = resonance
      else:
        resonanceMap[resonance] = oldResonance
    return assignmentMap, resonanceMap



###########################################################################
############################## V3 #########################################
###########################################################################

def _newDataSet(project, name=None, **kwargs):
    name = name or 'my%s'%DataSet.className
    # name = _incrementObjectName(project, DataSet._pluralLinkName, name)
    name = DataSet._uniqueName(project=project, name=name)
    ds = project.newDataSet(name=name, **kwargs)
    return ds

def _newDistanceRestraintList(project, dataset=None, name=None):
    name  = name or 'my%s'%RestraintList.className
    # name = _incrementObjectName(project, RestraintList._pluralLinkName, name)
    name = RestraintList._uniqueName(project=project, name=name)
    if not dataset:
        dataset = _newDataSet(project, name=name)
    return dataset.newRestraintList(restraintType='Distance', name=name)

def _newV3DistanceRestraint(v3PeakList,
                            v3RestraintList=None,
                            newDsName=None,
                            intensityType='height',
                            normalise=True,
                            labelling=True,
                            refDist=3.2, negError=0.2, posError=0.2, absMin=1.72, absMax=8.0, power=6,
                            residueRanges=None,
                            minMerit=0.0,
                            **kwargs,
                            ):

    project = v3PeakList.project
    if not v3RestraintList:
        v3RestraintList = _newDistanceRestraintList(project, name=newDsName)

    # get the needed V2 objects
    v2PeakList = v3PeakList._wrappedData
    params = (refDist, negError, posError, absMin, absMax, power)
    tempDistConstraintList = _newDistanceRestraintsFromPeakList(v2PeakList,
                                                                intensityType=intensityType,
                                                                normalise=normalise,
                                                                labelling=labelling,
                                                                params=params,
                                                                residueRanges=residueRanges,
                                                                minMerit=minMerit)
    tempConstraintSet = tempDistConstraintList.topObject
    tempV3Dataset = project._data2Obj.get(tempConstraintSet)
    assignmentMap, resonanceMap = _getRestraintsMapping(tempConstraintSet)

    # get the V3 objects
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            for tempConstraint in tempDistConstraintList.sortedConstraints():
                dd = dict((x, getattr(tempConstraint, x)) for x in
                          ('targetValue', 'error', 'upperLimit', 'lowerLimit', 'weight'))
                newV3Restraint = v3RestraintList.newRestraint(peaks=tempConstraint.peaks)
                rc = newV3Restraint.newRestraintContribution(**dd)
                for constraintItem in tempConstraint.sortedItems():
                    _assignments = []
                    for x in constraintItem.resonances:
                        _assignment = assignmentMap[resonanceMap.get(x, x)]
                        _assignment = [x if x is not None else '' for x in _assignment  ]
                        _assignments.append(_assignment)
                    assignments = ['.'.join(ss) for ss in _assignments]
                    rc.addRestraintItem(assignments)
            project.deleteObjects(*[tempV3Dataset]) # delete the temp ConstrainList


def _newV3AmbigDistRestraints(v3PeakList,
                            v3RestraintList=None,
                            minTolerances = (0.1, 0.1, 0.1),
                            maxTolerances = (0.1, 0.1, 0.1),
                            chemShiftRangesDim1 = ((-4.0, 20.0)),
                            chemShiftRangesDim2 = ((-4.0, 4.85)),
                            chemShiftRangesDim3 = ((0, 250.0)),
                            toleranceFactor = 1,
                            intensityType='height',
                            refDist=3.2, negError=0.2, posError=0.2, absMin=1.72, absMax=8.0, power=6,
                            residueRanges=None,
                            ignoreDiagonals=True,
                            doAliasing=True,
                            minMerit=0.0,
                            maxDist=20.0
                            ):

    project = v3PeakList.project
    if not v3RestraintList:
        v3RestraintList = _newDistanceRestraintList(project)

    # get the needed V2 objects
    v2PeakList = v3PeakList._wrappedData
    params = (refDist, negError, posError, absMin, absMax, power)
    tolerances = []
    chemShiftRanges = []
    shiftRanges = [chemShiftRangesDim1, chemShiftRangesDim2, chemShiftRangesDim3]
    for dataDim, minT, maxT in zip(v2PeakList.dataSource.sortedDataDims(), minTolerances, maxTolerances):
        tolerances.append([dataDim, minT, maxT, toleranceFactor])
    for dataDim, shiftRange in zip(v2PeakList.dataSource.sortedDataDims(), shiftRanges):
        expDimRef = dataDim.expDim.findFirstExpDimRef(serial=1)
        isotopeCodes = expDimRef.isotopeCodes
        chemShiftRanges.append([dataDim, isotopeCodes[:1], *shiftRange])
    temAmbDistConstList = _makeAmbigDistConstraints(v2PeakList, tolerances, chemShiftRanges,
                             testOnly=False,
                             residueRanges=residueRanges,
                             minMerit=minMerit,
                             intensityType=intensityType,
                             ignoreDiagonals=ignoreDiagonals,
                             doAliasing=doAliasing,
                             maxDist=maxDist,
                             params=params)

    tempConstraintSet = temAmbDistConstList.topObject
    tempV3Dataset = project._data2Obj.get(tempConstraintSet)
    assignmentMap, resonanceMap = _getRestraintsMapping(tempConstraintSet)

    # get the V3 objects
    with undoBlockWithoutSideBar():
        with notificationEchoBlocking():
            for tempConstraint in temAmbDistConstList.sortedConstraints():
                dd = dict((x, getattr(tempConstraint, x)) for x in
                          ('targetValue', 'error', 'upperLimit', 'lowerLimit', 'weight'))
                newV3Restraint = v3RestraintList.newRestraint(peaks=tempConstraint.peaks)
                rc = newV3Restraint.newRestraintContribution(**dd)
                for constraintItem in tempConstraint.sortedItems():
                    _assignments = (assignmentMap[resonanceMap.get(x, x)] for x in constraintItem.resonances)
                    assignments = ['.'.join(ss) for ss in _assignments]
                    rc.addRestraintItem(assignments)
            project.deleteObjects(*[tempV3Dataset]) # delete the temp ConstrainList



# Temporary functions

def _tempAtomAndResonanceSets(project):
    """

    AtomSets and resonanceSets are needed for the V2-DistanceRestraint Calculation machinery to work.
    :param project:
    :return: atomSets, resonanceSets from nmrAtom.atom
    Use before calling _newV3DistanceRestraint.
    """
    if project._wrappedData.resonanceSets: # already in the projects. Don't create new.
        return [], []
    atomSets  = []
    resonanceSets = []
    for i in project.nmrAtoms:
        nmrProject = project._wrappedData
        v3Atom = i.atom
        resonance = i._wrappedData
        if v3Atom:
            atom = v3Atom._wrappedData
            atomSet = nmrProject.newAtomSet(name=atom.name, atoms=[atom])
            nrs = nmrProject.newResonanceSet(resonances=[resonance], atomSets=[atomSet])
            atomSets.append(atomSet)
            resonanceSets.append(nrs)
    return atomSets, resonanceSets

def _deleteTempAtomAndResonanceSets(project, atomSets, resonanceSets):
    """
    :param project:
    :param atomSets: V2 objects
    :param resonanceSets: V2 objects
    :return:  removes the objects from the project. Called after creating distanceRestraints.
    """
    project.deleteObjects(*atomSets)
    project.deleteObjects(*resonanceSets)
