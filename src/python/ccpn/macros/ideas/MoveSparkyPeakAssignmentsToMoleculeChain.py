#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
#=========================================================================================
__title__ = "Move Sparky peak assignments to 'molecule' chain"
#=========================================================================================


"""
This macro will change the NmrChain assignment of each peak to be the default '@-' NmrChain 
and then remove all NmrChains other than '@-'.

Context:
When importing a Sparky project with several peak lists, the V3 project will end up having
separate NmrChains for each peak list and if the Sparky project contained a chemical shift list, 
then there will also be an addition NmrChain called 'molecule'.
The result is that the assigments across different spectra won't be linked.
This macro will tidy up the project and move all the peak assignments to the default NmrChain called '@-'.
It will then remove all the other NmrChains which are no longer needed.
The project will then contain a single NmrChain containing all assigned residues/atoms.
The user can then create a new NmrChain, cloned from the '@-' NmrChain in order to give it a name of their choice.

Note:
If the residue types are specified using the 1-letter code (often the case in Sparky projects), we recommend running the
ConvertResiduesOneToThreeLetterCode.py macro in order to change these to the IUPAC/NEF three-letter code in uppercase.

"""

# Do this on every peak in the project
for peak in project.peaks:
    # Get the assignments in all dimensions for a peak
    for assignOptions in peak.assignedNmrAtoms:
        for assignment in assignOptions:
            # Create the new assignment string with 'NA:molecule' as the NmrChain and identify the AxisCode
            temp = str(assignment)
            assignmentComponents = temp.split('.')
            assignmentComponents[0] = 'NA:@-'
            assignmentComponents[3] =  assignmentComponents[3][0:-1]
            chainPid = 'NC:@-'
            resPid = 'NR:@-.' + '.'.join(assignmentComponents[1:-1])
            print(resPid)
            seqCode = assignmentComponents[1]
            resType = assignmentComponents[2]
            atomName = assignmentComponents[3]
            axCde = assignmentComponents[3][0]
            newAssignment = '.'.join(assignmentComponents)
            get(chainPid).fetchNmrResidue(seqCode, resType)
            get(resPid).fetchNmrAtom(atomName)
            # Change the peak assignment to the new one
            get(peak.pid).assignDimension(axCde, newAssignment)

# Remove all the (now obsolete) NmrChains that are not NC:molecule and the default NC:@-
for nmrChain in project.nmrChains:
     if nmrChain.id != '@-':
            project.deleteObjects(nmrChain)
