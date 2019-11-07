
from ccpn.core.lib.AssignmentLib import findClosePeaks, copyPeakAssignments, getNmrAtomPrediction, isInterOnlyExpt

from ccpnmodel.ccpncore.lib.Constants import dict1

hsqcPeakListPid = 'PL:15N-HSQC.1'
tocsyPeakListPid = 'PL:hbhaconhCaM10-hbhaconh.1'

hsqcPeakList = project.getByPid(hsqcPeakListPid)
tocsyPeakList = project.getByPid(tocsyPeakListPid)

refAxisCodes = hsqcPeakList.spectrum.axisCodes
matchAxisCodes = tocsyPeakList.spectrum.axisCodes

mappingArray = [refAxisCodes.index(axisCode) for axisCode in refAxisCodes if axisCode in matchAxisCodes]
mappingArray2 = [matchAxisCodes.index(axisCode) for axisCode in refAxisCodes if axisCode in matchAxisCodes]

for peak in hsqcPeakList.peaks:
  closePeaks = findClosePeaks(peak, tocsyPeakList)
  if closePeaks:
    copyPeakAssignments(peak, closePeaks)

tocsyDim = [x for x in [0, 1, 2] if x not in mappingArray2][0]

threshold = 25
for peak in tocsyPeakList.peaks:
  assignedDim = peak.dimensionNmrAtoms[mappingArray[0]]
  if assignedDim:
    if isInterOnlyExpt(peak.peakList.spectrum.experimentType):
      nmrResidue = assignedDim[0].nmrResidue.previousNmrResidue
    else:
      nmrResidue = assignedDim[0].nmrResidue
    residueCode = dict1[nmrResidue.residue.shortName]
    isotopeCode = peak.peakList.spectrum.isotopeCodes[tocsyDim]
    prediction = getNmrAtomPrediction(residueCode, peak.position[tocsyDim], isotopeCode)[0]
    predProb = float(prediction[1])
    if predProb > threshold:
      newNmrAtom = nmrResidue.fetchNmrAtom(prediction[0][1])
      axisCode = peak.peakList.spectrum.axisCodes[tocsyDim]
      peak.assignDimension(axisCode=axisCode, value=newNmrAtom)