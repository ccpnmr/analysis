

def nmrAtomsForPeaks(peaks, nmrAtoms, intraResidual=False, doubleTolerance=False):
    '''Get a set of nmrAtoms that fit to the dimensions of the
       peaks.

    '''

    selected = matchingNmrAtomsForPeaks(peaks, nmrAtoms, doubleTolerance=doubleTolerance)
    if intraResidual:
        selected = filterIntraResidual(selected)
    return selected


def filterIntraResidual(nmrAtomsForDimenions):
    '''Takes a N-list of lists of nmrAtoms, where N
       is the number of peak dimensions and only returns
       those which belong to residues that show up in
       at least to of the dimensions (This is the behaviour
       in v2, if I am correct).

    '''

    nmrResiduesForDimensions = []
    allNmrResidues = set()
    for nmrAtoms in nmrAtomsForDimenions:
        nmrResidues = set([nmrAtom.nmrResidue for nmrAtom in nmrAtoms if nmrAtom.nmrResidue])
        nmrResiduesForDimensions.append(nmrResidues)
        allNmrResidues.update(nmrResidues)
    #nmrResidues = intersectionOfAll(nmrResidues_for_dimensions)

    selectedNmrResidues = set()
    for nmrResidue in allNmrResidues:
        frequency = 0
        for nmrResidues in nmrResiduesForDimensions:
            if nmrResidue in nmrResidues:
                frequency += 1
        if frequency > 1:
            selectedNmrResidues.add(nmrResidue)

    nmrAtomsForDimenionsFiltered = []
    for nmrAtoms in nmrAtomsForDimenions:
        nmrAtoms_filtered = set()
        for nmrAtom in nmrAtoms:
            if nmrAtom.nmrResidue in selectedNmrResidues:
                nmrAtoms_filtered.add(nmrAtom)
        nmrAtomsForDimenionsFiltered.append(nmrAtoms_filtered)

    return nmrAtomsForDimenionsFiltered


def matchingNmrAtomsForPeaks(peaks, nmrAtoms, doubleTolerance=False):
    '''Get a set of nmrAtoms that fit to the dimensions of the
       peaks. This function does the actual calculation and does
       not involve filtering like in nmrAtoms_for_peaks, where
       more filters can be specified in the future.

    '''

    dimensionCount = [len(peak.position) for peak in peaks]
    #All peaks should have the same number of dimensions.
    if not len(set(dimensionCount)) == 1:
        return []
    N_dims = dimensionCount[0]
    dim_nmrAtoms = []

    for dim in range(N_dims):
        matching = matchingNmrAtomsForDimensionOfPeaks(peaks,
                                                            dim,
                                                            nmrAtoms,
                                                            doubleTolerance=doubleTolerance)
        dim_nmrAtoms.append(matching)

    return dim_nmrAtoms


def matchingNmrAtomsForDimensionOfPeaks(peaks, dim, nmrAtoms,
                                             doubleTolerance=False):
    '''Finds out which nmrAtom can be assigned to a specific
       dimension of all the peaks, the N dimension for instance.
       Only returns those nmrAtoms that can be assigned to this
       dimension of all the selected peaks.

    '''

    if not sameAxisCodes(peaks, dim):
        return set()
    fittingSets = []
    for peak in peaks:
        matchingNmrAtoms = matchingNmrAtomsForPeakDimension(peak, dim,
                                                                 nmrAtoms,
                                                                 doubleTolerance=doubleTolerance)
        fittingSets.append(set(matchingNmrAtoms))
    common = intersectionOfAll(fittingSets)

    return common


def matchingNmrAtomsForPeakDimension(peak, dim, nmrAtoms,
                                         doubleTolerance=False):
    '''Just finds the nmrAtoms that fit a dimension of one peak.

    '''

    fitting_nmrAtoms = set()
    shiftList = getShiftlistForPeak(peak)
    position = peak.position[dim]
    isotopeCode = getIsotopeCodeForPeakDimension(peak, dim)
    tolerance = getAssignmentToleranceForPeakDimension(peak, dim)
    if not position or not isotopeCode or not shiftList:
        return fitting_nmrAtoms
    if not tolerance:
        tolerance = 0.5
    if doubleTolerance:
        tolerance *= 2

    for nmrAtom in nmrAtoms:
        if not getIsotopeCode(nmrAtom) == isotopeCode:
            continue
        if not withinTolerance(nmrAtom, position, shiftList, tolerance):
            continue
        fitting_nmrAtoms.add(nmrAtom)

    return fitting_nmrAtoms


def withinTolerance(nmrAtom, position, shiftList, tolerance):
    '''Decides whether the shift of the nmrAtom is
       whithin the tolerance to be assigned to the
       peak dimension.

    '''
    shift = shiftList.findChemicalShift(nmrAtom)
    #delta = delta_shift(nmrAtom, position, shiftList)
    if shift and abs(position - shift.value) < tolerance:
        return True
    return False


#def delta_shift(nmrAtom, position, shiftList):

#    shift = shiftList.findChemicalShift(nmrAtom)
#    if shift:
#        return position - shift.value
#    return None


def peaksAreOnLine(peaks, dim):
    '''Returns True when multiple peaks are located
       on a line in the given dimensions.

    '''

    if not sameAxisCodes(peaks, dim):
        return False
    # Take the two furthest peaks (in this dimension) of the selection.
    positions = sorted([peak.position[dim] for peak in peaks])
    max_difference = abs(positions[0] - positions[-1])
    #Use the smallest tolerance of all peaks.
    tolerance = min([getAssignmentToleranceForPeakDimension(peak, dim) for peak in peaks])
    if max_difference < tolerance:
        return True
    return False


def sameAxisCodes(peaks, dim):
    '''Checks whether all peaks have the same axisCode
       for in the given dimension.

    '''

    if len(peaks) > 1:
        axisCode = getAxisCodeForPeakDimension(peaks[0], dim)
        for peak in peaks[1:]:
            if not getAxisCodeForPeakDimension(peak, dim) == axisCode:
                return False
    return True


# Here come some functions that should probably live somewhere else.
# They all involve api lookups that would otherwise make the
# code less readable.

def getAllNmrAtoms(project, isotope=None):
    nmrAtoms = [nmrAtom for nmrResidue in project.nmrResidues for nmrAtom in nmrResidue.nmrAtoms]
    if isotope:
        selected = [a for a in nmrAtoms if a.isotope == isotope]
        nmrAtoms = selected
    return nmrAtoms


def getIsotopeCodeForPeakDimension(peak, dim):
    return peak.peakList.spectrum.isotopeCodes[dim]


def getAssignmentToleranceForPeakDimension(peak, dim):
    spectrum = peak.peakList.spectrum
    if spectrum.assignmentTolerances[dim] is not None:
      return spectrum.assignmentTolerances[dim]
    else:
      assignmentTolerances = list(spectrum.assignmentTolerances)
      assignmentTolerances[dim] = 0.01
      spectrum.assignmentTolerances = assignmentTolerances
      return spectrum.assignmentTolerances[dim]

def getIsotopeCode(nmrAtom):
    return nmrAtom.apiResonance.isotopeCode


def getAxisCodeForPeakDimension(peak, dim):
    return peak.peakList.spectrum.axisCodes[dim]


def getShiftlistForPeak(peak):
    return peak.peakList.spectrum.chemicalShiftList


# Just Math

def intersectionOfAll(sets):

    if not sets:
        return set()
    if len(sets) == 1:
        return sets[0]
    intersection = sets[0]
    for s in sets[1:]:
        intersection = intersection.intersection(s)
    return intersection
