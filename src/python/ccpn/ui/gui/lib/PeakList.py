"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-10 10:02:29 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util import Common as commonUtil

def restrictedPick(peakListView, axisCodes, peak=None, nmrResidue=None):
  """
  Takes a Peak or an NmrResidue, not both, a set of axisCodes, and a PeakListView.
  Derives positions for picking and feeds them into a PeakList wrapper function that
  performs the picking.
  """

  spectrum = peakListView.spectrumView.spectrum
  peakList = spectrum.peakLists[0]
  doPos = peakListView.spectrumView.displayPositiveContours
  doNeg = peakListView.spectrumView.displayNegativeContours
  # orderedDataDims = peakListView.spectrumView._wrappedData.spectrumView.orderedDataDims

  if peak and nmrResidue:
    return

  if not peak and not nmrResidue:
    return

  if peak:
    positionCodeDict = {peak.peakList.axisCodes[ii]: peak.position[ii] for ii in len(peak.position)}

  if nmrResidue:

    nmrResidueIsotopeCodes = [atom.isotopeCode for atom in nmrResidue.nmrAtoms]
    shiftList = spectrum.chemicalShiftList
    nmrResidueShifts = [shiftList.getChemicalShift(nmrAtom.id).value
                        for nmrAtom in nmrResidue.nmrAtoms]
    shiftDict = dict(zip(nmrResidueIsotopeCodes, nmrResidueShifts))
    shiftIsotopeCodes = [commonUtil.name2IsotopeCode(code) for code in axisCodes]
    positionCodeDict = {axisCodes[ii]: shiftDict[shiftIsotopeCode]
                        for ii, shiftIsotopeCode in enumerate(shiftIsotopeCodes)}

  peaks = peakList.restrictedPick(positionCodeDict, doPos, doNeg)

  return peakList, peaks
