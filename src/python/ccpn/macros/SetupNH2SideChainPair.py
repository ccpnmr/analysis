# A macro which will automatically group two NH2 peaks in an HSQC into the same NmrResidue,
# change the NmrAtom names to side chain names and change the NmrResidue type.
# It assumes that the peaks have previously been assigned using Assign / Setup NmrResidues (SN)
#
# To run:
# Select two NH peaks that belong to one NH2 group in an HSQC spectrum and run the macro.
#
# Options:
# If you wish, you can change the new Residue type or Atom names in the top part of the macro.

import sys
from ccpn.ui.gui.widgets.MessageDialog import showWarning

if len(current.peaks) < 2:
    showWarning('Too few Peaks selected', 'Please make sure you have selected exactly two peaks.')
    sys.exit()
elif len(current.peaks) > 2:
    showWarning('Too many Peaks selected', 'Please make sure you have selected exactly two peaks.')
    sys.exit()


HDim = 0
NDim = 1
peak1 = current.peaks[0]
peak2 = current.peaks[1]
resType = 'ASN/GLN'
NAtom = 'ND/E1'
H1Atom = 'HD/E21'
H2Atom = 'HD/E22'

with undoBlock():
    peak1NNmrAtom = peak1.assignmentsByDimensions[NDim][0]
    peak1HNmrAtom = peak1.assignmentsByDimensions[HDim][0]
    peak1NmrRes = peak1NNmrAtom.nmrResidue
    peak2NmrRes = peak2.assignmentsByDimensions[NDim][0].nmrResidue

    peak1NNmrAtom.rename(value = NAtom)
    peak1HNmrAtom.rename(value = H1Atom)
    peak1NmrRes.residueType = resType

    peak2NmrRes.delete()

    peak2HNmrAtom = peak1NmrRes.fetchNmrAtom(name=H2Atom)
    peak2.assignDimension(axisCode='H', value = peak2HNmrAtom)
    peak2.assignDimension(axisCode='N', value = peak1NNmrAtom)
