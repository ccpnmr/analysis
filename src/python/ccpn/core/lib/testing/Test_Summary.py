"""Module Documentation here

"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 06:41:02 +0100 (Mon, 16 May 2016) $"
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
        # t1 = time.time();
        #print('time elapsed = %.1f' % (t1 - t0))

    def test_assignedAtomCount(self):
        #import time; t0 = time.time()
        chain = self.project.chains[0]
        assert len(chain.atoms) == 2493
        # print ('@~@~ assignable', Summary.assignableAtomCount(chain))
        # print ('@~@~ assigned', Summary.assignedAtomCount(chain))
        # print ('@~@~ assignments', [(x.chain, len([y for y in x.nmrAtoms if y.atom]))
        #                             for x in self.project.nmrChains])
        # assert Summary.assignableAtomCount(chain) == 1405
        # assert Summary.assignedAtomCount(chain) == 890
        # NB The new numbers reflect the program as working on 17/10/2016, without deep analysis.
        # Since there are 864 assigned NmrAtoms, the new numbers are clearly better.
        assert Summary.assignableAtomCount(chain) == 1293
        assert Summary.assignedAtomCount(chain) == 864
        #t1 = time.time(); print('time elapsed = %.1f' % (t1-t0))
