"""This macro takes an NmrResidue, creates a axisCode:shift value dictionary
using the NmrAtoms of the NmrResidue and performs a restricted peak pick
at the relevant position in spectrum called hncacb."""

#Get hold the spectrum
spectrum = project.getByPid('SP:hncacb')

#Get hold of the peakList for the spectrum
peakList = spectrum.peakLists[0]

# Get hold of the NmrResidue
nmrResidue = project.nmrResidues[0]

# Set the chemical shift list
shiftList = project.chemicalShiftLists[0]

# Define the axis codes
axisCodes = ['H', 'N']

# Define the corresponding isotopeCodes
shiftIsotopeCodes = ['15N', '1H']

# Get a list of the isotopeCodes of the NmrAtoms in the
# NmrResidue
nmrResidueIsotopeCodes = []
for nmrAtom in nmrResidue.nmrAtoms:
  nmrResidueIsotopeCodes.append(nmrAtom.isotopeCode)

# Get hold of the chemical shifts for the NmrAtoms in the
# NmrResidue and append them to a list
nmrResidueShifts = []
for nmrAtom in nmrResidue.nmrAtoms:
  shift = shiftList.getChemicalShift(nmrAtom.id).value
  nmrResidueShifts.append(shift)

# Create a dictionary of NmrAtomIsotopeCodes: shifts using
# the dict and zip Python methods
shiftDict = dict(zip(nmrResidueIsotopeCodes,
nmrResidueShifts))

# Create a position-axisCode dictionary called posDict
# Loop over the shiftIsotopeCode list, pull out the
# axisCode with the same index, use that axisCode as a key
# and assign its value as the chemical shifts with the
# corresponding isotope code in the posDict
positionCodeDict = {}
for ii, shiftIsotopeCode in enumerate(shiftIsotopeCodes):
  positionCodeDict[axisCodes[ii]] = shiftDict[shiftIsotopeCode]

# Use the created posDict as input for the
# restrictedPick() method of the PeakList class.

newPeaks = peakList.restrictedPick(positionCodeDict, doPos=True,
    doNeg=False)


assignmentDict = {}
for ii, axisCode in enumerate(spectrum.axisCodes):
  for nmrAtom in nmrResidue.nmrAtoms:
    if nmrAtom.isotopeCode == spectrum.isotopeCodes[ii]:
      assignmentDict[axisCode] = nmrAtom

for peak in newPeaks:
  for axisCode in peak.axisCodes:
    if axisCode in assignmentDict.keys():
      peak.assignDimension(axisCode, value=assignmentDict[axisCode])
