#Macro to create a (synthetic) peak list from a chemical shift list
#
# What this macro ultimately needs to do:
# User specifies a chemical shift list
# User specifies an existing spectrum
#   - macro identifies axis codes and asks for atom types for each axis
#     (ideally as drop-down based on atom types in CSL?)
#     (ideally include ability to have multiple atom types per axis (HNCACB!))
#     (at some stage use Experiment types? (i.e. if there is an experiment type, automatically set the atom types,
#     rather than asking the user))
#   - create a new peak list with peaks for all residues where the specified atom types exist in the CSL
#   - (Let user know if no peaks could be created)
# (Alternatively user specifies a new (type of) spectrum in which case create a dummy spectrum before
# creating and populating the peak list)


# Try first:
# get the default csl
# specify atom types as HN
# create a new HSQC peak list
# populate the peak list with peaks

# specify chemical shift list
csl = project.getByPid('CL:default')

# set Atom types wanted in peak list
atomTypes = [H, N]

# create new HSQC peaklist (based on axis codes)
get('SP:hsqc').newPeakList(title=None, comment=None, isSimulated=True, symbolStyle=None, symbolColour=None, textColour=None)

# Loop through each shift in the chemical shift list
for chemicalShift in csl.chemicalShifts:
    # check if a shift belongs to the first atom type required in the new list (H in this case)
    na[0] = chemicalShift.nmrAtom
    if na[0].name = atomTypes[0]:
        #try creating the peak
        try:
            na[1] = na[0]
            na[1].name = atomTypes[1]

            peak.assignDimension(chemicalShift.nmrAtom, chemicalShift.nmrAtom2)

    if cslNmrAtoms of residue include all atomTypes
    #  create an HN peak in the peak list using the ChemShifts and NmrAtoms in the csl
    peak = peakList.newPeak(cslHAtomShift, cslNAtomShift)
    peak.assignDimension(cslHNmrAtom, cslNNmrAtom)

# if no peaks created, give an error message
