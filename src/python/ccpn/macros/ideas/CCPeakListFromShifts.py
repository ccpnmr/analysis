# Macro to create a CC peak list from a chemical shift list

from ccpn.core.lib.ContextManagers import undoBlock

# specify NmrChain associated with the imported chemical shifts
nmrChain = project.getByPid('NC:@2')

# specify CC spectrum
targetSpectrum = project.getByPid('SP:sh3_uni_pdsd100')
# find carbon dimensions
carbonAxes = [axis for axis in targetSpectrum.axisCodes if axis.startswith('C')]


def makePairs(theList):
    "make pairs from the elements of theList (excluding same-item pairs); return a list of tuples"
    result = []
    for idx, item1 in enumerate(theList):
        for item2 in theList[idx + 1:]:
            result.append((item1, item2))
            result.append((item2, item1))
    return result


with undoBlock():
    # create new peaklist for specified  spectrum
    peakList = targetSpectrum.newPeakList(isSimulated=True)
    print('created:', peakList)

    # Loop through each NmrResidue in the NmrChain
    for nmrRes in nmrChain.nmrResidues:
        # Loop through each NmrAtom, selecting each carbon
        atomList = [nmrAtom for nmrAtom in nmrRes.nmrAtoms if nmrAtom.name.startswith('C')]

        # create C-C peaks according to makePairs routine
        pairs = makePairs(atomList)
        for atm1, atm2 in pairs:
            peak = peakList.newPeak(ppmPositions=(atm1.chemShifts[0].value, atm2.chemShifts[0].value))
            peak.assignDimension(carbonAxes[0], atm1)
            peak.assignDimension(carbonAxes[1], atm2)

