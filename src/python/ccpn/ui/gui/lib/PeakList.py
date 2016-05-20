"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpnmodel.ccpncore.lib.spectrum import Spectrum as spectrumLib

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
    nmrResidueShifts = [shiftList.getChemicalShift(nmrAtom.id).value for nmrAtom in nmrResidue.nmrAtoms]
    shiftDict = dict(zip(nmrResidueIsotopeCodes, nmrResidueShifts))
    shiftIsotopeCodes = [spectrumLib.name2IsotopeCode(code) for code in axisCodes]
    positionCodeDict = {axisCodes[ii]: shiftDict[shiftIsotopeCode] for ii, shiftIsotopeCode in enumerate(shiftIsotopeCodes)}

  peaks = peakList.restrictedPick(positionCodeDict, doPos, doNeg)

  return peakList, peaks