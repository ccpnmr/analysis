"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9315 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.core.testing.WrapperTesting import WrapperTesting

from ccpn.core.lib import Summary

spectrumName = 'N-NOESY-182'

class SummaryTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse3e'

  def test_assignedPeakCount(self):
    #import time; t0 = time.time()
    spectrum = self.project.getSpectrum(spectrumName)
    peakList = spectrum.peakLists[0]
    assert len(peakList.peaks) == 1148
    assert Summary.partlyAssignedPeakCount(peakList) == 1029
    assert Summary.fullyAssignedPeakCount(peakList) == 262
    t1 = time.time();
    #print('time elapsed = %.1f' % (t1 - t0))

  def test_assignedAtomCount(self):
    #import time; t0 = time.time()
    chain = self.project.chains[0]
    assert len(chain.atoms) == 2493
    assert Summary.assignableAtomCount(chain) == 1405
    assert Summary.assignedAtomCount(chain) == 890
    #t1 = time.time(); print('time elapsed = %.1f' % (t1-t0))

