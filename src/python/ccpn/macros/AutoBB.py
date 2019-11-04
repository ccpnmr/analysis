"""
This macro has been requested by Fred Musket.
Written by LucaM with AnalysisAssign 3.0.0 on the 31/10/2019

This macro doesn't want to be an automated Backbone assignment and is aimed only to add initial labels to a project containing:
 15N-HSQC,  HNCA,  HNCOCA,  HNCACB,  CBCACONH, which will be carefully inspected manually and amended as needed it.


The macro uses the picking peak routines present in 3.0.0 to pick the HSQC first and label with incremental numbered nmrResidues.
Then picks restricted peak for all the 3Ds.
It guesses the "i-1" and "i" by peak heights for HNCA and HNCACB
Cbcaconh CA i-1s are propagated from hncoca if peaks from the two spectra are within tollerances
Searches for "i-1"s which are present in same spectra but missing and expected in others and copies them. (note added for inspection)
Deletes weaker peaks which are assigned to same nmrAtoms CA and CB i-1.
Deletes unassigned peaks

Modify as you need and share it!

"""

##################################################################################################
#####################################    User's  Parameters  #####################################
##################################################################################################

# Replace with your spectra names
HSQC_spectrumName = 'hsqc'
HNCA_spectrumName = 'hnca'
HNCOCA_spectrumName = 'hncoca'
HNCACB_spectrumName = 'hncacb'
CBCACONH_spectrumName = 'cbcaconh'

# labels used to create nmrAtoms, NB on the current version 3.0.0 changing H to Hn and N to Nh
# might break the assignment prediction for sequential matches!
H  = 'H'
N  = 'N'
CA = 'CA'
CB = 'CB'
C  = 'C'
CH = 'CH'

# implemented only for -1 at the moment!
OFFSET = '-1'

nmrChainName = '@-' # use the default. Change this name to create a different one

# Picking parameters: HSQC
from collections import OrderedDict as od
HSQC_limits = od(((H, [6,11]), (N, [100,134]))) # ppm limits where to find the signal
minDropFactor = 0.01  # (1%) # pick more then less, unlabeled peaks will be deleted afterwards

# Restricted peaks Tolerances in ppm for each axis for each 3D spectrum. These seem to be crucial for the current picker algorithm,
# if picks to little or too much try to change this, especially  on H and N.
# The following values were optimised for Sec5part1 tutorial spectra!)
HNCA_tolerances     = od(((H, 0.1), (N, 1,), (CA, 0.3)))
HNCOCA_tolerances   = od(((H, 0.1), (N, 1,), (CA, 0.3)))
HNCACB_tolerances   = od(((H, 0.1), (N, 1,), (C, 0.3)))
CBCACONH_tolerances = od(((H, 0.1), (N, 1,), (CH, 0.3))) #also used to propagate assignments from HNCOCA peaks


# Contours, in case you don't want set it manually from display ...
setContours = True # set False if not needed
hsqcContours      =  (64194.19080018526, -64194.19080018526) # positive and negative Contours values
hncaContours      =  (5835252.217157302, -5835252.217157302)
hncocaContours    =  (15051295.29692141, -15051295.29692142)
hncacbContours    =  (13094258.00380035, -13094258.00380035)
cbcaconhContours  =  (8161392.113049264, -8161392.113049264)


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
msg = "%s has to be in the project for this macro. Amend the macro if you don't have this spectrum"
if not hnca:
    showWarning('Error', msg % 'hnca')
    raise ValueError
if not hncoca:
    showWarning('Error', msg % 'hncoca')
    raise ValueError
if not hncacb:
    showWarning('Error', msg % 'hncacb')
    raise ValueError
if not cbcaconh:
    showWarning('Error', msg % 'cbcaconh')
    raise ValueError

# get nmrChain object
nmrChain = project.fetchNmrChain(nmrChainName)
# add tolerances
hnca.assignmentTolerances = list(HNCA_tolerances.values())
hncoca.assignmentTolerances = list(HNCOCA_tolerances.values())
hncacb.assignmentTolerances = list(HNCACB_tolerances.values())
cbcaconh.assignmentTolerances = list(CBCACONH_tolerances.values())

# set Contours
if setContours:
    hnca.positiveContourBase, hnca.negativeContourBase = hncaContours[0],  hncaContours[1]
    hncoca.positiveContourBase, hncoca.negativeContourBase = hncocaContours[0],  hncocaContours[1]
    hncacb.positiveContourBase, hncacb.negativeContourBase = hncacbContours[0],  hncacbContours[1]
    cbcaconh.positiveContourBase, cbcaconh.negativeContourBase = cbcaconhContours[0],  cbcaconhContours[1]

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
            for peak in _stoppableProgressBar(hsqcPeaks, title='Labelling HSQC... (1/3)'):
                nmrResidue = nmrChain.fetchNmrResidue()
                hNmrAtom = nmrResidue.fetchNmrAtom(name=H)
                nNmrAtom = nmrResidue.fetchNmrAtom(name=N)
                _assignNmrAtomsToPeaks([peak], [hNmrAtom, nNmrAtom])

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
    missingPeak = tobeCopiedPeak.copyTo(targetPeakList)
    missingPeak.comment = '%s Copied from %s. Inspect it' % (nmrAtomLabel,tobeCopiedPeak.peakList.id)
    return missingPeak

def _pickAndAssign_HNCA(hsqc_nmrAtoms,nmrResidue,m1nmrAtomCA,positionCodeDict):
    hncaPeaks = hnca.peakLists[-1].restrictedPick(positionCodeDict, doPos=True, doNeg=False)
    _assignNmrAtomsToPeaks(hncaPeaks, hsqc_nmrAtoms)
    _assignByHeights(nmrResidue, hncaPeaks, label=CA)
    hncaCAm1Peak = _getPeakForNmrAtom(hncaPeaks, m1nmrAtomCA)
    _CAm1Peak = hncaCAm1Peak
    return hncaPeaks, _CAm1Peak

def _pickAndAssign_HNCOCA(hsqc_nmrAtoms,nmrResidue,m1nmrAtomCA,positionCodeDict, _CAm1Peak=None):
    hncocaPeaks = hncoca.peakLists[-1].restrictedPick(positionCodeDict, doPos=True, doNeg=False)
    _assignNmrAtomsToPeaks(hncocaPeaks, hsqc_nmrAtoms + [m1nmrAtomCA])
    hncocaCAm1Peak = _getPeakForNmrAtom(hncocaPeaks, m1nmrAtomCA)
    if _CAm1Peak is None and hncocaCAm1Peak:
        _CAm1Peak = _copyPeakFromOtherExpType(hncocaCAm1Peak, hnca.peakLists[-1])
    if hncocaCAm1Peak is None and _CAm1Peak:
        _CAm1Peak = _copyPeakFromOtherExpType(_CAm1Peak, hncoca.peakLists[-1])
    return hncocaPeaks, _CAm1Peak

def _pickAndAssign_CBCACONH(hsqc_nmrAtoms,nmrResidue, m1nmrAtomCB,positionCodeDict, hncocaPeaks):
    cbcaconhPeaks = cbcaconh.peakLists[-1].restrictedPick(positionCodeDict, doPos=True, doNeg=False)
    _assignNmrAtomsToPeaks(cbcaconhPeaks, hsqc_nmrAtoms + [m1nmrAtomCB])  # assign first CB
    for hncocaPeak in hncocaPeaks:  # assign CA from hncoca Peak
        for cbcaconhPeak in cbcaconhPeaks:
            isWT = _isPeakWithinTollerances(hncocaPeak, cbcaconhPeak, CBCACONH_tolerances)
            if isWT:
                tbPropagated = makeIterableList(hncocaPeak.assignedNmrAtoms)
                _assignNmrAtomsToPeaks([cbcaconhPeak], tbPropagated)
    cbcaconhCBm1Peak = _getPeakForNmrAtom(cbcaconhPeaks, m1nmrAtomCB)
    _CBm1Peak = cbcaconhCBm1Peak
    return cbcaconhPeaks, _CBm1Peak

def _pickAndAssign_HNCACB(hsqc_nmrAtoms,nmrResidue, m1nmrAtomCB,m1nmrAtomCA,hncocaCAm1Peak,cbcaconhCBm1Peak,positionCodeDict):
    hncacbPeaks = hncacb.peakLists[-1].restrictedPick(positionCodeDict, doPos=True, doNeg=True)
    _assignNmrAtomsToPeaks(hncacbPeaks, hsqc_nmrAtoms)
    _assignByHeights(nmrResidue, [p for p in hncacbPeaks if p.height > 0], CA, hsqc_nmrAtoms)
    _assignByHeights(nmrResidue, [p for p in hncacbPeaks if p.height < 0], CB, hsqc_nmrAtoms)
    hncacbCAm1Peak = _getPeakForNmrAtom(hncacbPeaks, m1nmrAtomCA)
    hncacbCBm1Peak = _getPeakForNmrAtom(hncacbPeaks, m1nmrAtomCB)
    if hncacbCAm1Peak is None and hncocaCAm1Peak:
        _CAm1Peak = _copyPeakFromOtherExpType(hncocaCAm1Peak, hncacb.peakLists[-1])
    if hncacbCBm1Peak is None and cbcaconhCBm1Peak:
        _CBm1Peak = _copyPeakFromOtherExpType(cbcaconhCBm1Peak, hncacb.peakLists[-1],'CB-1')
    if cbcaconhCBm1Peak is None and hncacbCBm1Peak:
        _CBm1Peak = _copyPeakFromOtherExpType(hncacbCBm1Peak, cbcaconh.peakLists[-1], 'CB-1')
    return hncacbPeaks

def pickRestrictedPeaksAndAddLabels():
    hsqcPeaks = hsqc.peakLists[-1].peaks
    allPeaks = []
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for peak in _stoppableProgressBar(hsqcPeaks, title='Labelling 3Ds...(2/3)'):
                _CAm1Peak = None
                _CBm1Peak = None
                # hsqc nmrAtoms
                hsqc_nmrAtoms = makeIterableList(peak.assignedNmrAtoms)
                nmrResidue = hsqc_nmrAtoms[-1].nmrResidue
                m1nmrResidue = nmrChain.fetchNmrResidue(nmrResidue.sequenceCode + OFFSET)
                m1nmrAtomCA = m1nmrResidue.fetchNmrAtom(CA)
                m1nmrAtomCB = m1nmrResidue.fetchNmrAtom(CB)
                positionCodeDict = {H:peak.position[0], N:peak.position[1]}
                hncaPeaks, _CAm1Peak = _pickAndAssign_HNCA(hsqc_nmrAtoms, nmrResidue, m1nmrAtomCA, positionCodeDict)
                allPeaks.extend(hncaPeaks)
                hncocaPeaks, _CAm1Peak =_pickAndAssign_HNCOCA(hsqc_nmrAtoms, nmrResidue, m1nmrAtomCA, positionCodeDict, _CAm1Peak)
                cbcaconhPeaks, _CBm1Peak = _pickAndAssign_CBCACONH(hsqc_nmrAtoms, nmrResidue, m1nmrAtomCB, positionCodeDict, hncocaPeaks)
                allPeaks.extend(cbcaconhPeaks)
                hncacbPeaks = _pickAndAssign_HNCACB(hsqc_nmrAtoms, nmrResidue, m1nmrAtomCB, m1nmrAtomCA, _CAm1Peak,
                                      _CBm1Peak, positionCodeDict)
                allPeaks.extend(hncacbPeaks)
            toBeDeleted3DsPeaks = [p for p in allPeaks if not p.isFullyAssigned()]
            project.deleteObjects(*toBeDeleted3DsPeaks)
    return allPeaks

def findPeaksAssignedOnlyToHSQC():
    peaks = []
    unAssignedNmrResidues = []
    for nmrResidue in nmrChain.nmrResidues:
        l1 = [peak for na in nmrResidue.nmrAtoms for peak in na.assignedPeaks]
        if len(l1) == 0:
            unAssignedNmrResidues.append(nmrResidue)
        if len(set(l1)) == 1:
            peaks.extend(l1)
            print('NmrResidue  %s contains Peaks assigned only on the HSQC and unassigned on 3Ds. Might be noisy or sidechain peaks' %nmrResidue)
    print('If you want to delete these peaks run: \nproject.deleteObjects(*unAssigned)')
    project.deleteObjects(*unAssignedNmrResidues) # not assigned to any peak. No point in keeping it for now
    return peaks

def deleteDuplicatedCACBm1():
    """
    Removes weaker peaks which are assigned to the same nmrAtoms in the same peakList.
    """
    tobeDeletedPeaks = []
    with notificationEchoBlocking():
        with undoBlockWithoutSideBar():
            for nmrResidue in _stoppableProgressBar(project.nmrResidues, title='Cleaning up...(3/3)'):
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

# run it
pickPeaksHSQC()
addLabelsHSQC()
pickRestrictedPeaksAndAddLabels()
unAssigned = findPeaksAssignedOnlyToHSQC()
# project.deleteObjects(*unAssigned)
deleteDuplicatedCACBm1()
