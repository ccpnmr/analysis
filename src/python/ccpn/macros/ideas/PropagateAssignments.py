#Header

def checkSingleAssignedPeakAndGetAssignments(peak):
        assignmentsToCopy = None
        if peak.isPartlyAssgined is True and assignmentsToCopy is None:
            assignmentsToCopy = peak.assginments
        elif peak.isPartlyAssigned is True and assignmentsToCopy is True:
            print("Please only select one assigned peak")
            return
        return(assignmentsToCopy)

def copyAssignment(peak, assignmentsToCopy):
    for assignment in assignmentsToCopy:
        temp = str(assignment)
        assignmentLabels = temp.split(',')
        assignmentLabels = assignmentLabels[0:-1]
        assignmentLabels[0] = assignmentLabels[0][1:]
        assignmentLabels[-1] = assignmentLabels[-1][0:-1]
        for label in assignmentLabels:
            temp = str(label)
            assignmentComponents = temp.split(':')
            assignmentComponents[0] = 'NA'
            assignmentComponents[1] = assignmentComponents[1][0:-1]
            temps = assignmentComponents[1].split('.')
            axCde = temps[-1][0]
            newAssignment = ':'.join(assignmentComponents)
            peak.assignDimension(axCde, newAssignment)



for peak in current.peaks:
    checkSingleAssignedPeakAndGetAssignments(peak)

for peak in current.peaks:
    if peak.isPartlyAssgined is False:
        copyAssignment(peak, assignmentsToCopy)
