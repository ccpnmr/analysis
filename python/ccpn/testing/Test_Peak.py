"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.testing.Testing import Testing
from ccpncore.lib.spectrum import Spectrum as libSpectrum

class PeakTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, 'CcpnCourse1b', *args, **kw)
    self.spectrumName = 'HSQC-115'
    
  def test_assignPeak(self):
    spectrum = self.getSpectrum()
    shiftList = self.project.newChemicalShiftList()
    spectrum.chemicalShiftList = shiftList
    nmrResidue = self.project.nmrChains[0].fetchNmrResidue()
    nmrAtom = nmrResidue.fetchNmrAtom(name='N')
    peak = spectrum.peakLists[0].peaks[0]

    peak.assignDimension(axisCode=libSpectrum.axisCodeMatch('N', spectrum.axisCodes),
                         value=nmrAtom)
    # shift = shiftList.findChemicalShift(nmrAtom)
    shift = shiftList.getChemicalShift(nmrAtom.id)
    print("NewChemicalShift", shift, shift and shift.value)
    assert shift is not None, "New shift must be created"
    assert shift.value is not None, "New shift must have value"

