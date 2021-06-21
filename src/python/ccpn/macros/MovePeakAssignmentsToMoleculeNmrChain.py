# This macro will change the NmrChain assignment of each peak to be an NmrChain called 'molecule'
# and then remove all NmrChains other than 'molecule' and '@-'.
#
# Context:
# When importing a Sparky project with several peak lists, the V3 project may end up having
# separate NmrChains for each peak list and if the Sparky project contained a chemical shift list,
# then there will also be an additional NmrChain called 'molecule'.
# The result is that the assignments across different spectra won't be linked.
# This macro will tidy up the project and move all the peak assignments to an NmrChain called 'molecule'.
# It will then remove all the other NmrChains which are no longer needed.
# The project will then contain a single NmrChain containing all assigned residues/atoms (as well as the default '@-'
# NmrChain.
# The user can then rename the 'molecule' NmrChain to a name of their choice.
#
# Note:
# If the residue types are specified using the 1-letter code (often the case in Sparky projects), we recommend running a
# macro to change these to the IUPAC/NEF three-letter code in uppercase.

##############################    Start of the code      #################################

def _reassignPeaks():
    for peak in project.peaks:
        for currentAssignmentsByDim, axCde in zip(peak.assignmentsByDimensions, peak.axisCodes):
            for currentAssignment in currentAssignmentsByDim:
                if currentAssignment.nmrResidue.nmrChain.name != 'molecule':
                    newNc = project.fetchNmrChain('molecule')
                    try:
                        newNr = newNc.fetchNmrResidue(currentAssignment.nmrResidue.sequenceCode,
                                                      currentAssignment.nmrResidue.residueType)
                    except ValueError:
                        currentAssignment.delete()
                        continue
                    newNa = newNr.fetchNmrAtom(currentAssignment.name)
                    peak.assignDimension(axCde, newNa)

def _deleteObsoleteNmrChains():
    for nmrChain in project.nmrChains:
        if nmrChain.name != '@-' and nmrChain.name != 'molecule':
               project.deleteObjects(nmrChain)

_reassignPeaks()
_deleteObsoleteNmrChains()