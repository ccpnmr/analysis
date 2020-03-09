#Macro to create a CC peak list from an imported BRMB chemical shift list

# specify chemical shift list
csl = project.getByPid('CL:chemicalshiftlist_1')

# specify PDSD spectrum
targetSpectrum = project.getByPid('SP:PDSD')

# create new peaklist for specified PDSD spectrum
peakList = targetSpectrum.newPeakList(title=None, comment=None, isSimulated=True, symbolStyle=None, symbolColour=None, textColour=None)

# specify NmrChain associated with the imported chemical shifts
nmrCh = project.getByPid('NC:@2')

# Loop through each NmrResidue in the NmrChain
for nmrRes in nmrCh:
    # Loop through each NmrAtom
    atomlist = []
    for nmrAt in nmrRes:
        # Check that the NmrAtom is a carbon atom
        if nmrAt[0] == 'C':
            atomlist.append(nmrAt)
    # create all combinations of C-C peaks and assign them
    while len(atomlist) > 1:
        v = atomlist.pop()
        for w in atomlist:
            #get chemShifts of v and w NmrAtoms from csl

            #create peak with atoms v and w
            peak = peakList.newPeak((vChemShift,wChemShift))
            peak.assignDimension(axisCode='C', v)
            peak.assignDimension(axisCode='C1', w)
            #create second peak with shifts/atoms the other way round
            peak = peakList.newPeak((wChemShift, vChemshift))
            peak.assignDimension(axisCode='C', w)
            peak.assignDimension(axisCode='C1', v)

# Is there an issue if peaks are created outside the spectrum bounds??