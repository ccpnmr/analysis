"""
Macro to assign the Ca/Cb/C NmrAtoms when doing the Pick & Assign step of a
backbone assignment.

This should work with any combination of HNCA, HNcoCA, HNCACB, HNcoCACB, HNCO and HNcaCO spectra.

REQUIREMENTS/USAGE:
1. Make sure your spectra have the correct Experiment Types associated with them (shortcut
   ET to set these).
2. Pick and Assign the peaks for an NmrResidue using the Pick and Assign module (PA), then
   run the macro before moving to the next residue. This is easiest if you associate the
   macro with a keyboard shortcut (you can do this with shortcut DU).

NOTE:
The macro assumes you have a relatively straight forward pattern of peaks. If you have
picked lots of noise peaks you may not get correct behaviour (make sure you adjust your
contour level before doing the 'Pick & Assign Selected' step). You will also have to make manual
corrections if there is peak overlap or there are missing peaks.
The macro can usually account for Serine, Threonine or Glycine peak patterns, but it worth checking these are correct
before you move on to the next residue or go on to the backbone assignment stage.

"""

##############################     Settings      #################################

assignIsotope = '13C'       # Isotope of dimension to be assigned
rootIsotope = '1H'         # Isotope of one of the root dimensions which has already been assigned
casPosCbsNeg = True # True if Ca peaks are positive and Cb peaks are negative in HNCACB,
                    # False if Cas are negative and Cb peaks are positive
glyHasCaSign = True  # True if Glycine Ca peaks in the HNCACB spectrum have the same sign as the other Ca peaks,
                    # False if Glycine Ca peaks in the HNCACB spectrum have the same sign as the other Cb peaks

iSpectra = ['H[N[CA]]', 'H[N[ca[CO]]]', 'H[N[{CA|ca[Cali]}]]']
                    # experiments containing both i and i-1 peaks

##############################    Start of the code      #################################

import sys
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from collections import defaultdict
from statistics import mean


def getAssignDim(peak):
    assignDim = [ind for ind, value in enumerate(peak.peakList.spectrum.isotopeCodes) if value == assignIsotope][0]
    return assignDim

def getAssignAxisCode(peak):
    assignDim = getAssignDim(peak)
    assignAxCde = peak.peakList.spectrum.axisCodes[assignDim]
    return assignAxCde

def assignNmrAtom(seqCode, atomName, offset):
    if offset == -1:
        newsc = ''.join((seqCode, '-1'))
        newnr = peakNmrChain.fetchNmrResidue(sequenceCode=newsc, residueType=None)
        newna = newnr.fetchNmrAtom(name=atomName, isotopeCode=assignIsotope)
        assignAxCde = getAssignAxisCode(peak)
        peak.assignDimension(axisCode=assignAxCde, value=newna)
    elif offset == 0:
        newna = peakNmrRes.fetchNmrAtom(name=atomName, isotopeCode=assignIsotope)
        assignAxCde = getAssignAxisCode(peak)
        peak.assignDimension(axisCode=assignAxCde, value=newna)

def storeDataForGlyCheck(peakShift, peak, atomType):
    glyCheckDict[atomType]['shifts'].append(peakShift)
    glyCheckDict[atomType]['peaks'].append(peak)

def checkForGly(glyDict):
    cas_1 = glyDict['CA-1']['shifts']
    cbs_1 = glyDict['CB-1']['shifts']
    cas0 = glyDict['CA0']['shifts']
    cbs0 = glyDict['CB0']['shifts']
    if glyHasCaSign:
        if len(cbs_1) == 0 and 48.5 > mean(cas0) > 40.0:
            # this is an i Glycine
            for pk in glyDict['CB0']['peaks']:
                assignDim = getAssignDim(pk)
                nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue.getOffsetNmrResidue(-1)
                na = nr.fetchNmrAtom(name='CB', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)
    else:
        if len(cas_1) == 0 and 48.5 > mean(cbs_1) > 40.0:
            # this is an i-1 Glycine
            for pk in glyDict['CB-1']['peaks']:
                assignDim = getAssignDim(pk)
                nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue.mainNmrResidue
                na = nr.fetchNmrAtom(name='CA', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)
        elif len(cas_1) == 0 and 48.5 > mean(cbs0) > 40.0:
            # this is an i Glycine
            for pk in glyDict['CB0']['peaks']:
                assignDim = getAssignDim(pk)
                nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue
                na = nr.fetchNmrAtom(name='CA', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)
            for pk in glyDict['CA0']['peaks']:
                assignDim = getAssignDim(pk)
                nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue.getOffsetNmrResidue(-1)
                na = nr.fetchNmrAtom(name='CA', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)



def storeDataForGSTCheck(peakShift, peak, atomType):
    gstCheckDict[atomType]['shifts'].append(peakShift)
    gstCheckDict[atomType]['peaks'].append(peak)

def checkForGST(gstDict):
    cas = gstDict['CA-1']['shifts']
    cbs = gstDict['CB-1']['shifts']
    peaks = gstDict['CA-1']['peaks'] + gstDict['CB-1']['peaks']
    if len(cas) == 0 and len(cbs) != 0:
        # this is a Glycine
        for pk in peaks:
            assignDim = getAssignDim(pk)
            nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue
            if 48.5 > pk.ppmPositions[assignDim] > 40.0:
                na = nr.fetchNmrAtom(name='CA', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)
            na = nr.fetchNmrAtom(name='CB', isotopeCode=assignIsotope)
            if not na.assignedPeaks:
                na.delete()
    elif len(cbs) == 0 and len(cas) >= 2:
        # this is a Serine or Threonine
        for pk in peaks:
            assignDim = getAssignDim(pk)
            if pk.ppmPositions[assignDim] > mean(cas):
                nr = pk.assignmentsByDimensions[assignDim][0].nmrResidue
                na = nr.fetchNmrAtom(name='CB', isotopeCode=assignIsotope)
                assignAxCde = getAssignAxisCode(pk)
                pk.assignDimension(axisCode=assignAxCde, value=na)


### Main Macro starts ###

if len(current.peaks) == 0:
    showWarning('No Peaks selected', 'Please make sure you have selected some peaks with '
                                     'assigned root (NH) resonances.')
    sys.exit()

with undoBlock():
    pkDict = defaultdict(list)
    GlyCheck = False
    glyCheckDict = {'CA-1': {'shifts': [], 'peaks': []},
                    'CB-1': {'shifts': [], 'peaks': []},
                    'CA0': {'shifts': [], 'peaks': []},
                    'CB0': {'shifts': [], 'peaks': []}}
    GSTCheck = False
    gstCheckDict = {'CA-1': {'shifts': [], 'peaks': []},
                    'CB-1': {'shifts': [], 'peaks': []}}

    for peak in current.peaks:
        rootDim = [ind for ind, value in enumerate(peak.peakList.spectrum.isotopeCodes) if value == rootIsotope][0]
        # Check peak root dim is assigned
        if peak.assignmentsByDimensions[rootDim]:
            peakNmrRes = peak.assignmentsByDimensions[rootDim][0].nmrResidue
            peakNmrChain = peak.assignmentsByDimensions[rootDim][0].nmrResidue.nmrChain
        else:
            showWarning('Missing Root Assignment', 'Please make sure all your peaks have '
                                                   'their root NH NmrAtoms assigned')
            sys.exit()
        # Put peaks into pkDict
        peakExptType = peak.peakList.spectrum.experimentType
        if peakExptType is not None:
            if peakExptType not in pkDict:
                pkDict[peakExptType] = [peak]
            else:
                pkDict[peakExptType].append(peak)
        elif peakExptType is None:
            showWarning('Missing Experiment Type', 'Please make sure all '
                                                   'your spectra have an Experiment Type '
                                                   'associated with them (use shortcut ET '
                                                   'to set these)')
            sys.exit()

    for expt in pkDict:
        if expt in iSpectra:
            allPeaks = sorted(pkDict[expt], key=lambda x: x.height if x.height else 0, reverse=True)
            highestPeak = allPeaks[0]
            lowestPeak = allPeaks[-1]
        for peak in pkDict[expt]:
            assignDim = getAssignDim(peak)
            peakNmrRes = peak.assignmentsByDimensions[rootDim][0].nmrResidue
            peakSeqCode = peakNmrRes.sequenceCode
            peakShift = peak.ppmPositions[assignDim]

            if expt == 'H[N[CA]]':
                if peak == highestPeak:
                    assignNmrAtom(peakSeqCode, atomName='CA', offset=0)
                else:
                    assignNmrAtom(peakSeqCode, atomName='CA', offset=-1)
            elif expt == 'H[N[co[CA]]]':
                assignNmrAtom(peakSeqCode, atomName='CA', offset=-1)
            elif expt == 'H[N[ca[CO]]]':
                if peak == highestPeak:
                    assignNmrAtom(peakSeqCode, atomName='C', offset=0)
                else:
                    assignNmrAtom(peakSeqCode, atomName='C', offset=-1)
            elif expt == 'H[N[CO]]':
                assignNmrAtom(peakSeqCode, atomName='C', offset=-1)
            elif expt == 'H[N[{CA|ca[Cali]}]]':
                if peak == highestPeak:
                    if casPosCbsNeg:
                        assignNmrAtom(peakSeqCode, atomName='CA', offset=0)
                        storeDataForGlyCheck(peakShift, peak, atomType='CA0')
                    else:
                        assignNmrAtom(peakSeqCode, atomName='CB', offset=0)
                        storeDataForGlyCheck(peakShift, peak, atomType='CB0')
                elif peak == lowestPeak:
                    if casPosCbsNeg:
                        assignNmrAtom(peakSeqCode, atomName='CB', offset=0)
                        storeDataForGlyCheck(peakShift, peak, atomType='CB0')
                    else:
                        assignNmrAtom(peakSeqCode, atomName='CA', offset=0)
                        storeDataForGlyCheck(peakShift, peak, atomType='CA0')
                elif peak.height > 0:
                    if casPosCbsNeg:
                        assignNmrAtom(peakSeqCode, atomName='CA', offset=-1)
                        storeDataForGlyCheck(peakShift, peak, atomType='CA-1')
                    else:
                        assignNmrAtom(peakSeqCode, atomName='CB', offset=-1)
                        storeDataForGlyCheck(peakShift, peak, atomType='CB-1')
                elif peak.height < 0:
                    if casPosCbsNeg:
                        assignNmrAtom(peakSeqCode, atomName='CB', offset=-1)
                        storeDataForGlyCheck(peakShift, peak, atomType='CB-1')
                    else:
                        assignNmrAtom(peakSeqCode, atomName='CA', offset=-1)
                        storeDataForGlyCheck(peakShift, peak, atomType='CA-1')
                GlyCheck = True
            elif expt == 'H[N[co[{CA|ca[C]}]]]' or expt == 'h{CA|Cca}coNH':
                if peakShift >= 47.0:
                    assignNmrAtom(peakSeqCode, atomName='CA', offset=-1)
                    storeDataForGSTCheck(peakShift, peak, atomType='CA-1')
                elif peakShift < 47.0:
                    assignNmrAtom(peakSeqCode, atomName='CB', offset=-1)
                    storeDataForGSTCheck(peakShift, peak, atomType='CB-1')
                GSTCheck = True

    if GlyCheck:
        checkForGly(glyCheckDict)
    if GSTCheck:
        checkForGST(gstCheckDict)
