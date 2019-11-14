"""

This macro isn't an automated Backbone Assignment routine. It simply adds the initial NmrAtom labels to a project containing:
15N-HSQC and HNCACB spectra (optionally also CBCACONH, HNCA and HNCOCA spectra).
The results should be carefully inspected afterwards and amended as needed.

The macro uses the picking peak routines present in CcpNmr AnalysisAssign V3 to peak pick the HSQC first and
label it with incremental numbered NmrResidues.
It then picks restricted peaks for all the 3Ds. This step is currently the weakest point, as peaks can be wrongly picked
or missed completely - how well this works will mainly depend on your restricted pick tolerances/limits and the
contour level at which you pick the peaks. This macro is best suited to spectra with relatively uniform peak intensities.
Spectra which have some very intense and some very weak strips will inevitably pick too many peaks in some strips and
too few in others.
The macro guesses the "i-1" and "i" assignments from the peak heights in the HNCACB or HNCA specta based on the
strongest peaks (absolute height).
It does not take the CBCACONH into consideration. The CAi-1 and CB i-1 carbon NmrAtoms are simply propagated to the
CBCACONH from the HNCACB if the two spectral peaks are within certain tolerances.

The macro then searches for "i-1"s which are present in same spectra but missing and expected in others and copies them.
It deletes obsolete peaks assigned to carbon if properly reassigned to CA or/and CB i-1
Finally, unassigned peaks are deleted.

Users can set certain parameters in the "User's  Parameters" section. Read the comments for descriptions.

This macro is not optimised for speed and tested only using spectra from the CCPN Sec5 Backbone Assignment tutorial.
Modify as you need and share your macros on the forum: https://www.ccpn.ac.uk/forums

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: LucaM $"
__dateModified__ = "$dateModified: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: LucaM $"
__date__ = "$Date: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
#=========================================================================================
__title__ = "Auto pick and assign for triple resonance backbone assignment"
#=========================================================================================


##################################################################################################
#####################################    User's  Parameters  #####################################
##################################################################################################

# Replace with your spectra names. Leave empty quotes '' if don't have
HSQC_spectrumName = 'hsqc'
HNCACB_spectrumName = 'hncacb'
HNCA_spectrumName = 'hnca'
HNCOCA_spectrumName = 'hncoca'
CBCACONH_spectrumName = 'cbcaconh'
#_________________________________________________________________________________________________

# NB: Not recommended changing these labels. Used throughout the code for several operations not only for labeling the peaks on display
# labels used to create nmrAtoms, NB on the current version 3.0.0 changing H to Hn and N to Nh
# might break the assignment prediction for sequential matches! It could work on other labelling eg 13C but not tested)
    #- Assignement can be made only if compatible axis codes. Eg nmrAtom H to one axisCode H(+anyLetter),
    #- if two axes starting with H in the same spectrum then will fail
H  = 'H'
N  = 'N'
CA = 'CA'
CB = 'CB'
C  = 'C'
CH = 'CH'
#_________________________________________________________________________________________________

nmrChainName = '@-' # use the default. Change this name to create a different one
#_________________________________________________________________________________________________

# Picking parameters: HSQC
minDropFactor = 0.01  # (1%) # pick more then less, unlabeled peaks will be deleted afterwards
from collections import OrderedDict as od # Ignore this line as User's option, rest of import are set further down
HSQC_limits = od(((H, [6,11]),  (N, [100,134]) )) # ppm limits where to find the signal on HSQC
#_________________________________________________________________________________________________

# regions of search on 3D. Crucial if picking too little or too much!
# H and N limits +/- to the HSQC position for restricted  peak picking
# C: the actual region of search. All in ppm.
HNCA_limits   =   od(((H, [0.05, 0.05]),   (N, [1, 1]), (C, [40,80])))
HNCOCA_limits =   od(((H, [0.05, 0.05]),   (N, [1, 1]), (C, [40,80])))
HNCACB_limits =   od(((H, [0.05, 0.05]),   (N, [1, 1]), (C, [10,80])))
CBCACONH_limits = od(((H, [0.05, 0.05]),   (N, [1, 1]), (C, [10,80])))

# tolerances in ppm for matching peaks across different Experiment types. Used when propagating assignments.
tolerances   =   od(((H, 0.1),  (N, 2), (C, 4)))
#_________________________________________________________________________________________________

# Contours, in case you don't want them set from display ...
setContours       =   False # set False if not needed, else True
hsqcContours      =  (64194.19080018526, -64194.19080018526) # positive and negative Contours values
hncaContours      =  (5835252.217157302, -5835252.217157302)
hncocaContours    =  (15051295.29692141, -15051295.29692142)
hncacbContours    =  (13094258.00380035, -13094258.00380035)
cbcaconhContours  =  (8161392.113049264, -8161392.113049264)
#_________________________________________________________________________________________________

HSQC_alreadyAssigned = False             # True if you already picked and assigned nmrAtoms on the HSQC. Peaks need to be in the last peakList.
CA_in_HNCACB_isPositive = True           # Assign CA i-1 to positive peaks in the HNCACB, False Assign CB i-1 to positive
Propagate_HNCACB_to_CBCACONH = True      # Replace assignment from C to CA and CB (i-1 nmrAtom) from the HNCACB to CBCACONH if relative peaks within tolerances
CopyExpectedPeaksFromOtherSpectra = True # Try to find missing Ca i-1 and Cb i-1 from other spectra if one or more are missing and propagate peak and assignment across.
Correct_CBCACONH_assignments = True      # Guess missing NmrAtom. eg. if CA and C are present but not CB, swap the C with CB and vice-versa for CA.

##################################################################################################
#######################################  start of the code #######################################
##################################################################################################

# imports
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar, notificationEchoBlocking
from ccpn.ui.gui.widgets.MessageDialog import _stoppableProgressBar, showWarning
from ccpn.core.lib.AssignmentLib import _assignNmrAtomsToPeaks, assignAlphas,assignBetas
from ccpn.util.Common import makeIterableList
from collections import defaultdict
import numpy as np

# get spectra objects
hsqc = project.getByPid('SP:'+ HSQC_spectrumName)
hnca = project.getByPid('SP:'+ HNCA_spectrumName)
hncoca = project.getByPid('SP:'+ HNCOCA_spectrumName)
hncacb = project.getByPid('SP:'+ HNCACB_spectrumName)
cbcaconh = project.getByPid('SP:'+ CBCACONH_spectrumName)


if not hsqc: #not point in continue if not at least the HSQC!
    showWarning('Error', 'hsqc has to be in the project for this macro')
    raise ValueError

# get nmrChain object
nmrChain = project.fetchNmrChain(nmrChainName)

# set Contours
application.preferences.general.peakDropFactor = minDropFactor
if setContours:
    if hnca: hnca.positiveContourBase, hnca.negativeContourBase = hncaContours[0],  hncaContours[1]
    if hncoca: hncoca.positiveContourBase, hncoca.negativeContourBase = hncocaContours[0],  hncocaContours[1]
    if hncacb: hncacb.positiveContourBase, hncacb.negativeContourBase = hncacbContours[0],  hncacbContours[1]
    if cbcaconh: cbcaconh.positiveContourBase, cbcaconh.negativeContourBase = cbcaconhContours[0],  cbcaconhContours[1]

def pickPeaksHSQC():
    """
    picks on the last peakList of the HSQC. should be always one as default.
    :return:  peaks
    """
    with notificationEchoBlocking():
        peakList = hsqc.peakLists[-1]
        peaks = peakList.pickPeaksRegion(regionToPick=HSQC_limits, doPos=True, doNeg=False,
                                         minDropFactor=minDropFactor,estimateLineWidths=True)
        return peaks

def addLabelsHSQC():
    """
    adds label for each hsqc peak
    """
    hsqcPeaks = hsqc.peakLists[-1].peaks
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for peak in _stoppableProgressBar(hsqcPeaks, title='Labelling HSQC...'):
                nmrResidue = nmrChain.fetchNmrResidue()
                hNmrAtom = nmrResidue.fetchNmrAtom(name=H)
                nNmrAtom = nmrResidue.fetchNmrAtom(name=N)
                _assignNmrAtomsToPeaks([peak], [hNmrAtom, nNmrAtom])


def _orderPeaksByHeight(peaks):
    """
    :param peaks: sort peaks in descending height. First the strongest....
    :type peaks:
    :return:
    :rtype:
    """
    aPeaks = np.array(peaks)
    heights = np.array([abs(j.height) for j in aPeaks])
    indices = heights.argsort()
    return list(aPeaks[indices[::-1]])

def _assignByHeights(nmrResidue, peaks, label='CA', propagateNmrAtoms=[]):

    """
    The easiest way to estimate "i-1" and "i" by peak heights
    nmrResidue: Obj nmrResidue.
    peaks: obj peaks to be assigned.
    label: str of label to assign. E.g. CA or CB
    propagateNmrAtoms: nmrAtoms  E.G H,N atoms to be propagated to the peak(s)
    Assigns "i" and "i-1" NmrAtoms by peak height.
    The peak with the max height will be the "i"
    The peak with the min height will be the "i-1"
    If only one peak, then it is assigned to "i" by default.
    """
    lowestP = [i for i in peaks if abs(i.height) == min([abs(j.height) for j in peaks])]
    highestP = [i for i in peaks if abs(i.height) == max([abs(j.height) for j in peaks])]

    if highestP:
        i_NmrAtom = nmrResidue.fetchNmrAtom(name=label)
        _assignNmrAtomsToPeaks(highestP, propagateNmrAtoms+[i_NmrAtom])
    if highestP == lowestP:
        return
    elif lowestP:
        i_m_1_NmrResidue = nmrResidue.nmrChain.fetchNmrResidue(nmrResidue.sequenceCode + '-1')
        i_m_1_NmrAtom = i_m_1_NmrResidue.fetchNmrAtom(name=label)
        _assignNmrAtomsToPeaks(lowestP, propagateNmrAtoms+[i_m_1_NmrAtom])

def _isPeakWithinTollerances(referencePeak, targetPeak, tolerances):
    referencePeakPos = np.array(referencePeak.position)
    targetPeakPeakPos = np.array(targetPeak.position)
    tolerancesArray = np.array(list(tolerances.values()))
    diff = abs(targetPeakPeakPos-referencePeakPos)
    return all(diff<tolerancesArray)

def _getPeakForNmrAtom(peaks, queryNA):
    for peak in peaks:
        for na in makeIterableList(peak.assignedNmrAtoms):
            if na == queryNA:
                return peak

def _copyPeakFromOtherExpType(tobeCopiedPeak, targetPeakList, nmrAtomLabel = 'CA-1'):
    if tobeCopiedPeak:
        missingPeak = tobeCopiedPeak.copyTo(targetPeakList)
        missingPeak.comment = '%s Copied from %s. Inspect it' % (nmrAtomLabel,tobeCopiedPeak.peakList.id)
        return missingPeak

def getRegions(hsqcPosition, limits):
    dd = limits.copy()
    dd[H] = [hsqcPosition[0]-limits[H][0], hsqcPosition[0]+limits[H][1]]
    dd[N] =  [hsqcPosition[1]-limits[N][0], hsqcPosition[1]+limits[N][1]]
    return dd

def _pickAndAssign_HNCA(hnca,hsqcPosition, hsqc_nmrAtoms,nmrResidue, expectedPeakCount=2):
    regions = getRegions(hsqcPosition, HNCA_limits)
    hncaPeaks = hnca.peakLists[-1].pickPeaksRegion(regionToPick=regions, doPos=True, doNeg=False,
                                         minDropFactor=minDropFactor)
    _assignNmrAtomsToPeaks(hncaPeaks, hsqc_nmrAtoms)
    peaks = _orderPeaksByHeight(hncaPeaks)
    _assignByHeights(nmrResidue, peaks[:expectedPeakCount], label=CA)
    return hncaPeaks

def _pickAndAssign_HNCOCA(hncoca,hsqcPosition, hsqc_nmrAtoms, m1nmrResidue, expectedPeakCount=1):
    regions = getRegions(hsqcPosition, HNCOCA_limits)
    hncocaPeaks = hncoca.peakLists[-1].pickPeaksRegion(regionToPick=regions, doPos=True, doNeg=False,
                                                       minDropFactor=minDropFactor)
    peaks = _orderPeaksByHeight(hncocaPeaks)
    m1nmrAtomCA = m1nmrResidue.fetchNmrAtom(CA)
    _assignNmrAtomsToPeaks(peaks[:expectedPeakCount], hsqc_nmrAtoms + [m1nmrAtomCA])
    return hncocaPeaks

def _pickAndAssign_CBCACONH(cbcaconh, hsqcPosition, hsqc_nmrAtoms, m1nmrResidue, expectedPeakCount=2):
    regions = getRegions(hsqcPosition, CBCACONH_limits)
    cbcaconhPeaks = cbcaconh.peakLists[-1].pickPeaksRegion(regionToPick=regions, doPos=True, doNeg=False,
                                                       minDropFactor=minDropFactor)
    peaks = _orderPeaksByHeight(cbcaconhPeaks)
     # cannot guess yet which one is CA or CB  so give it a C !
    m1nmrAtomC = m1nmrResidue.fetchNmrAtom(C)
    _assignNmrAtomsToPeaks(peaks[:expectedPeakCount], hsqc_nmrAtoms + [m1nmrAtomC])  # assign first generic C
    return cbcaconhPeaks

def _pickAndAssign_HNCACB(hncacb, hsqcPosition, hsqc_nmrAtoms, nmrResidue , expectedPeakCount=4):
    regions = getRegions(hsqcPosition, HNCACB_limits)
    hncacbPeaks = hncacb.peakLists[-1].pickPeaksRegion(regionToPick=regions, doPos=True, doNeg=True, minDropFactor=minDropFactor)
    _assignNmrAtomsToPeaks(hncacbPeaks, hsqc_nmrAtoms)
    posPeaks = [p for p in hncacbPeaks if p.height > 0]
    negPeaks = [p for p in hncacbPeaks if p.height < 0]
    sortedPosPeaks = _orderPeaksByHeight(posPeaks)
    sortednegPeaks = _orderPeaksByHeight(negPeaks)
    if CA_in_HNCACB_isPositive:
        _assignByHeights(nmrResidue, sortedPosPeaks[:int(expectedPeakCount/2)], CA, hsqc_nmrAtoms)
        _assignByHeights(nmrResidue, sortednegPeaks[:int(expectedPeakCount/2)], CB, hsqc_nmrAtoms)
    else:
        _assignByHeights(nmrResidue, sortedPosPeaks[:int(expectedPeakCount / 2)], CB, hsqc_nmrAtoms)
        _assignByHeights(nmrResidue, sortednegPeaks[:int(expectedPeakCount / 2)], CA, hsqc_nmrAtoms)
    return hncacbPeaks

def pickRestrictedPeaksAndAddLabels():
    hsqcPeaks = hsqc.peakLists[-1].peaks
    allPeaks = []
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for peak in _stoppableProgressBar(hsqcPeaks, title='Labelling 3Ds...'):
                _CAm1Peak = None
                _CBm1Peak = None
                # hsqc nmrAtoms
                hsqcPosition = peak.position
                hsqc_nmrAtoms = makeIterableList(peak.assignedNmrAtoms)
                nmrResidue = hsqc_nmrAtoms[-1].nmrResidue
                m1nmrResidue = nmrChain.fetchNmrResidue(nmrResidue.sequenceCode + '-1')

                if hncacb:
                    hncacbPeaks = _pickAndAssign_HNCACB(hncacb, hsqcPosition, hsqc_nmrAtoms, nmrResidue)
                    allPeaks.extend(hncacbPeaks)

                if cbcaconh:
                    cbcaconhPeaks = _pickAndAssign_CBCACONH(cbcaconh, hsqcPosition, hsqc_nmrAtoms, m1nmrResidue)
                    allPeaks.extend(cbcaconhPeaks)

                if hnca:
                    hncaPeaks = _pickAndAssign_HNCA(hnca, hsqcPosition, hsqc_nmrAtoms,nmrResidue)
                    allPeaks.extend(hncaPeaks)

                if hncoca:
                    hncocaPeaks = _pickAndAssign_HNCOCA(hncoca,hsqcPosition, hsqc_nmrAtoms, m1nmrResidue)
                    allPeaks.extend(hncocaPeaks)


            toBeDeleted3DsPeaks = [p for p in allPeaks if not p.isFullyAssigned() if not p.isDeleted]
            project.deleteObjects(*toBeDeleted3DsPeaks)
    return allPeaks

def deleteDuplicatedCACBm1():
    """
    Removes weaker peaks which are assigned to the same nmrAtoms in the same peakList.
    """
    tobeDeletedPeaks = []
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for nmrResidue in _stoppableProgressBar(project.nmrResidues, title='Cleaning up...'):
                if nmrResidue.relativeOffset == -1:
                    for nmrAtom in nmrResidue.nmrAtoms:
                        if len(nmrAtom.assignedPeaks) > 0:
                            pls = [{peak.peakList: peak} for peak in nmrAtom.assignedPeaks]
                            dd = defaultdict(list)
                            for d in pls:
                                for pl, peak in d.items(): # make a dict with key the peakList and as value a list of all peak belonging to that peakList
                                    dd[pl].append(peak)
                            for pl, peaks in dd.items():
                                tobeDeletedPeaks.extend([peak for peak in peaks if abs(peak.height)!= max([abs(peak.height) for peak in peaks])])
            project.deleteObjects(*tobeDeletedPeaks)

def findPeaksAssignedOnlyToHSQC():
    peaks = []
    unAssignedNmrResidues = []
    print('NmrResidues which contain Peaks assigned only on the HSQC and unassigned on 3Ds. Might be noisy or sidechain peaks:')
    for nmrResidue in nmrChain.nmrResidues:
        l1 = [peak for na in nmrResidue.nmrAtoms for peak in na.assignedPeaks]
        if len(l1) == 0:
            unAssignedNmrResidues.append(nmrResidue)
        if len(set(l1)) == 1:
            peaks.extend(l1)
            print(nmrResidue.pid)
    print('If you want to delete these peaks run: \nproject.deleteObjects(*unAssigned)')
    # project.deleteObjects(*unAssignedNmrResidues) # not assigned to any peak. No point in keeping it for now
    return peaks


def _propagate_toOther(nmrAtomName = CA, originSpectrum=None, targetPeakLists=[]):
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for nr in _stoppableProgressBar(project.nmrResidues, title='Propagating NmrAtoms...'):
                if nr.relativeOffset == -1:
                    na = nr.getNmrAtom(nmrAtomName)
                    if na:
                        aaPeaks = makeIterableList(na.assignedPeaks)
                        if len(aaPeaks):
                            aaPeaksOrigin = [p for p in aaPeaks if p.peakList.spectrum == originSpectrum]

                            for aPeak in aaPeaksOrigin:
                                for peakList in targetPeakLists:
                                    for otherPeak in peakList.peaks:
                                        if _isPeakWithinTollerances(aPeak, otherPeak, tolerances):
                                            tbPropagated = makeIterableList(aPeak.assignedNmrAtoms)
                                            _assignNmrAtomsToPeaks([otherPeak], tbPropagated)






def _copyPeaksToOthePeakList(originPeakList, targetPeakList, nmrAtomLabel=CA):
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for peak in originPeakList.peaks:
                tobeCopied = []
                for targetPeak in targetPeakList.peaks:
                    if _isPeakWithinTollerances(peak, targetPeak, tolerances):
                        a1 = makeIterableList(peak.assignedNmrAtoms)
                        a2 = makeIterableList(targetPeak.assignedNmrAtoms)
                        # _assignNmrAtomsToPeaks([otherPeak], tbPropagated)
                        if a2 != a1:
                            tobeCopied.append(peak)
                newPeak =_copyPeakFromOtherExpType(peak, targetPeakList, nmrAtomLabel)

def copyExpectedPeaksFromOtherSpectra():
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for nr in _stoppableProgressBar(project.nmrResidues, title='Copying missing Peaks/NmrAtoms...'):
                if nr.relativeOffset == -1:
                    caIm1 = nr.getNmrAtom(CA)
                    cbIm1 = nr.getNmrAtom(CB)

                    if cbIm1:
                        cbIm1Peaks = makeIterableList(cbIm1.assignedPeaks)
                        cbIm1Dict = od()
                        for cbIm1Peak in cbIm1Peaks:
                            cbIm1Dict[cbIm1Peak.peakList.spectrum] = cbIm1Peak
                        if cbcaconh:
                            if not cbIm1Dict.get(cbcaconh):
                                while True:
                                    if cbIm1Dict.get(hncacb):  # only choice
                                        cbIm1Dict.get(hncacb).copyTo(cbcaconh.peakLists[-1])
                                        break
                                    break

                    if caIm1:
                        caPeaks = makeIterableList(caIm1.assignedPeaks)
                        caIm1Dict = od()
                        for p in caPeaks:
                            caIm1Dict[p.peakList.spectrum] = p
                        if not caIm1Dict.get(hncacb):
                            if caIm1Dict.get(hncoca): # copy from hncoca 1st choice
                                caIm1Dict.get(hncoca).copyTo(hncacb.peakLists[-1])
                            else:
                                if caIm1Dict.get(hnca):  # copy from hnca 2nd choice
                                    caIm1Dict.get(hnca).copyTo(hncacb.peakLists[-1])
                                    if hncoca: # if  you have on hnca but not on hncoca
                                        caIm1Dict.get(hnca).copyTo(hncoca.peakLists[-1])
                        if cbcaconh:
                            if not caIm1Dict.get(cbcaconh):
                                while True:
                                    if caIm1Dict.get(hncoca):  # copy from hncoca 1st choice
                                        caIm1Dict.get(hncoca).copyTo(cbcaconh.peakLists[-1])
                                        break
                                    if caIm1Dict.get(hnca):    # copy from hnca   2nd choice
                                        caIm1Dict.get(hnca).copyTo(cbcaconh.peakLists[-1])
                                        break
                                    if caIm1Dict.get(hncacb):  # copy from hncacb 3rd choice
                                        caIm1Dict.get(hncacb).copyTo(cbcaconh.peakLists[-1])
                                        break
                                    break
                        if hnca:
                            if not caIm1Dict.get(hnca):
                                while True:
                                    if caIm1Dict.get(hncoca):  # copy from hncoca 1st choice
                                        caIm1Dict.get(hncoca).copyTo(hnca.peakLists[-1])
                                        break
                                    if caIm1Dict.get(hncacb):  # copy from hncacb 3rd choice
                                        caIm1Dict.get(hncacb).copyTo(hnca.peakLists[-1])
                                        break
                                    break

def removeObsoletePeaks():
    tobedelpeaks =[]
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for peak in  _stoppableProgressBar(cbcaconh.peakLists[-1].peaks, title='removing  obsolete C NmrAtoms...'):
                nmrAtoms = makeIterableList(peak.assignedNmrAtoms)
                names = [na.name for na in nmrAtoms]
                if names == [C, CA, CB]: # C is Obsolete
                    for nmrAtom in nmrAtoms:
                        if nmrAtom.name == C:
                            tobedelpeaks.append(peak)
                if Correct_CBCACONH_assignments:
                    if C and CA and not CB in names: # missing CB, assume C is instead of CB, so swap it! this could just add mistake.
                        newNmrAtoms = []
                        for nmrAtom in nmrAtoms:
                            if nmrAtom.name == C:
                                bIm1 = nmrAtom.nmrResidue.fetchNmrAtom(CB)
                                newNmrAtoms.append(bIm1)
                            else:
                                newNmrAtoms.append(nmrAtom)
                        _assignNmrAtomsToPeaks([peak], newNmrAtoms)

                    if C and CB and not CA in names: # missing CA, assume C is instead of CA, so swap it! this could just add mistake.
                        newNmrAtoms = []
                        for nmrAtom in nmrAtoms:
                            if nmrAtom.name == C:
                                caIm1 = nmrAtom.nmrResidue.fetchNmrAtom(CA)
                                newNmrAtoms.append(caIm1)
                            else:
                                newNmrAtoms.append(nmrAtom)
                        _assignNmrAtomsToPeaks([peak], newNmrAtoms)
    project.deleteObjects(*tobedelpeaks)

def _propagate_HNCACB_to_CBCACONH():
    caPeaks= []
    cbPeaks = []
    cPeaks = []
    for nr in _stoppableProgressBar(project.nmrResidues, title='Propagating NmrAtoms from HNCACB to CBCACONH...'):
            if nr.relativeOffset == -1:
                caNa = nr.getNmrAtom(CA)
                cbNa = nr.getNmrAtom(CB)
                cNa = nr.getNmrAtom(C)
                if caNa:
                    caPeaks = makeIterableList(caNa.assignedPeaks)
                if cbNa:
                    cbPeaks = makeIterableList(cbNa.assignedPeaks)
                if cNa:
                    cPeaks = makeIterableList(cNa.assignedPeaks)
            with notificationEchoBlocking():
                with undoBlockWithoutSideBar():
                    for cPeak in cPeaks:
                        for caPeak in caPeaks:
                            if _isPeakWithinTollerances(cPeak, caPeak, tolerances):
                                tbPropagated = makeIterableList(caPeak.assignedNmrAtoms)
                                _assignNmrAtomsToPeaks([cPeak], tbPropagated)
                        for cbPeak in cbPeaks:
                            if _isPeakWithinTollerances(cPeak, cbPeak, tolerances):
                                tbPropagated = makeIterableList(cbPeak.assignedNmrAtoms)
                                _assignNmrAtomsToPeaks([cPeak], tbPropagated)

##################################################################################################
#####################################         Run Macro      #####################################
##################################################################################################

if not HSQC_alreadyAssigned:
    pickPeaksHSQC()
    addLabelsHSQC()
pickRestrictedPeaksAndAddLabels()
unAssigned = findPeaksAssignedOnlyToHSQC()
if Propagate_HNCACB_to_CBCACONH:
    _propagate_HNCACB_to_CBCACONH()
if CopyExpectedPeaksFromOtherSpectra:
    copyExpectedPeaksFromOtherSpectra()
removeObsoletePeaks()






