"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-09-13 19:25:08 +0100 (Mon, September 13, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.testing.WrapperTesting import WrapperTesting


class StringifierTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'V3ProjectForTests.ccpn'

    def test_defaultFormatting(self):
        from ccpn.util import Common as commonUtil

        spectrum = self.project.getSpectrum('15NNoesy_182')
        peak = spectrum.peaks[2]
        toString = commonUtil.stringifier('serial', 'peakList', 'height', 'volume', 'className',
                                          'axisCodes', 'position', 'positionError', 'assignedNmrAtoms',
                                          'dimensionNmrAtoms')
        self.assertEquals(toString(peak), "<PK:15NNoesy_182.1.3| serial=3, peakList=<PL:15NNoesy_182.1>, "
                                          "height=3.35816e+06, volume=2.50861e+11, className='Peak', "
                                          "axisCodes=['H', 'H1', 'N'], "
                                          "position=(9.36823, 3.82816, 118.269), "
                                          "positionError=(None, None, None), "
                                          "assignedNmrAtoms=((<NA:A.4.THR.H>, None, <NA:A.4.THR.N>),),"
                                          " dimensionNmrAtoms=((<NA:A.4.THR.H>,), (), (<NA:A.4.THR.N>,))>")


    def test_userFormatting(self):
        from ccpn.util import Common as commonUtil

        spectrum = self.project.getSpectrum('hsqc_115')
        peak = spectrum.peaks[0]
        toString = commonUtil.stringifier('serial', 'peakList', 'height', 'volume', 'className',
                                          'axisCodes', 'position', 'positionError', 'assignedNmrAtoms',
                                          'dimensionNmrAtoms', floatFormat='.3f')
        self.assertEquals(toString(peak),
                          "<PK:hsqc_115.1.1| serial=1, peakList=<PL:hsqc_115.1>, height=16455916.000,"
                          " volume=4620582801.830, className='Peak', axisCodes=['H', 'N'], "
                          "position=(9.437, 121.039), positionError=(None, None), "
                          "assignedNmrAtoms=((<NA:A.2.GLU.H>, <NA:A.2.GLU.N>),), "
                          "dimensionNmrAtoms=((<NA:A.2.GLU.H>,), (<NA:A.2.GLU.N>,))>")

