# Macro to copy the peak assignments from one peak to another
# It is primarily intended for copying assignments in spectrum series, e.g. a titration series
#
# Select one (fully or partially) assigned peak and one or more unassigned peaks. The assignments from the assigned
# peak will be copied to the unassigned peaks. This will work both within and between peak lists, spectra and
# spectrum displays.
#
# The macro works in a similar way to the V2 `Propagate Assignment` function. However, note that there is no checking
# of chemical shifts. This is deliberate, so that you can copy assignments in situations where the chemical shift has
# changed.
# It will only work for peaks belonging to spectra with the same number/type of axes (e.g. HN and HN, HNC and HNC etc.).
# Note that it will not work for copying peaks from an HNC to an HCN spectrum (check the Dimensions tab of the
# Spectrum Properties).
# Also, your dimensions will be swapped if you apply it to two peaks on opposite sides of the diagonal of a
# homonuclear spectrum. Probably not what you want!
###################################################################################################################

from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.ui.gui.widgets.MessageDialog import showWarning

with undoBlock():
    assignmentsToCopy = None
    dimensionIsotopesDiffer = False
    tooManyAssignedPeaks = False
    pk = current.peak
    # Check all peaks have the same dimension types
    for peak in current.peaks:
        if peak.spectrum.isotopeCodes != pk.spectrum.isotopeCodes:
            dimensionIsotopesDiffer = True
    # Check only one peak is fully or partially assigned and get the assignments to copy
    for peak in current.peaks:
        if len(peak.assignments) != 0 and assignmentsToCopy is None:
            assignmentsToCopy = peak.assignmentsByDimensions
        elif len(peak.assignments) != 0 and assignmentsToCopy is not None:
            tooManyAssignedPeaks = True

    if dimensionIsotopesDiffer:
        showWarning('Dimension Isotopes Differ', 'Please make sure the spectra containing your peaks all have the same '
                                               'number of dimensions with the same isotopes in the same order')
    elif tooManyAssignedPeaks:
        showWarning('Too many assigned peaks', 'Please make sure only one of your peaks is assigned')
    elif not assignmentsToCopy:
        showWarning('No assigned peaks', 'Please make sure one of your peaks has at least one assigned dimension')
    else:
        for peak in current.peaks:
            if len(peak.assignments) == 0:  # only copy assignments to unassigned peaks
                peak.dimensionNmrAtoms = assignmentsToCopy

