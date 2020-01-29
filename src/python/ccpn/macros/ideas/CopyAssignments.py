#Header
#
# A macro to copy the assignment from one peak to another.
#
# Select one (fully or partially) assigned peak and one or more unassigned peaks.
# The assignments from the assigned peak will be copied to the unassigned peaks.
# This will work both within and between peak lists, spectra and spectrum displays.
#
# NOTE: The peak dimensions are matched by their Axis Codes. There is no checking of
# chemical shifts. This is deliberate, so that you can copy assignments in situations
# where the chemical shift has changed (e.g. due to the presence of a ligand). But this
# does mean that you might encounter incorrect behaviour for spectra with two dimensions
# belonging to the same isotope, e.g. when copying assignments across the diagonal of
# a homonuclear spectrum, or between two spectra where the peaks' Axis Codes and
# Assignments don't line up. But this should hopefully only be a minority of cases.


def copyAssignment(peak, assignmentsToCopy, axisCodesToUse):
    assignDone = 0
    count = 0
    for assignment in assignmentsToCopy:
        temp = str(assignment)
        assignmentLabels = temp.split(',')
        assignmentLabels[0] = assignmentLabels[0][1:]
        assignmentLabels[-1] = assignmentLabels[-1][0:-1]
        axCodes = dict(zip(assignmentLabels, axisCodesToUse))
        for label in assignmentLabels:
            count = count+1
            if 'None' not in label:
                temp = str(label)
                assignmentComponents = temp.split(':')
                assignmentComponents[0] = 'NA'
                assignmentComponents[1] = assignmentComponents[1][0:-1]
                axCde = axCodes[label]
                newAssignment = ':'.join(assignmentComponents)
                if axCde in peak.axisCodes:
                    peak.assignDimension(axCde, newAssignment)
                    assignDone = 1
    if assignDone == 0:
        print('Your peaks have to have matching Axis Codes in at least one assigned dimension in order to copy an assignment.')


assignmentsToCopy = None
axisCodesToUse = None
# Check only one peak is fully or partially assigned and get the assignments and Axis Codes to copy
for peak in current.peaks:
    if len(peak.assignments) != 0 and assignmentsToCopy is None:
        assignmentsToCopy = peak.assignments
        axisCodesToUse = peak.axisCodes
    elif len(peak.assignments) != 0 and assignmentsToCopy is not None:
        print("You have more than one assigned peak.")
        assignmentsToCopy = None


if assignmentsToCopy is not None:
    for peak in current.peaks:
        if len(peak.assignments) == 0:  # only copy assignments to unassigned peaks
            copyAssignment(peak, assignmentsToCopy, axisCodesToUse)
else:
    print("Please make sure you have one assigned peak.")

