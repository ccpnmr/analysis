"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2021-01-08 11:49:57 +0000 (Fri, January 08, 2021) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.util import Common as commonUtil


class StringifierTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse2c.ccpn'

    def test_defaultFormatting(self):
        spectrum = self.project.getSpectrum('T2a-216')
        peak = spectrum.peaks[0]
        toString = commonUtil.stringifier('serial', 'peakList', 'height', 'volume', 'className',
                                          'axisCodes', 'position', 'positionError', 'assignedNmrAtoms',
                                          'dimensionNmrAtoms')
        self.assertEquals(toString(peak), "<PK:T2a-216.1.1062| serial=1062, peakList=<PL:T2a-216.1>, "
                                          "height=4.93752e+06, volume=4.12035e+07, className='Peak', "
                                          "axisCodes=('Hn', 'Nh', 'delay'), "
                                          "position=(7.90695, 122.516, 3), "
                                          "positionError=(None, None, None), "
                                          "assignedNmrAtoms=((<NA:A.56.ALA.H>, <NA:A.56.ALA.N>, None),),"
                                          " dimensionNmrAtoms=((<NA:A.56.ALA.H>,), (<NA:A.56.ALA.N>,), ())>")

    def test_userFormatting(self):
        spectrum = self.project.getSpectrum('HSQC-115')
        peak = spectrum.peaks[0]
        toString = commonUtil.stringifier('serial', 'peakList', 'height', 'volume', 'className',
                                          'axisCodes', 'position', 'positionError', 'assignedNmrAtoms',
                                          'dimensionNmrAtoms', floatFormat='.3f')
        self.assertEquals(toString(peak),
                          "<PK:HSQC-115.1.1| serial=1, peakList=<PL:HSQC-115.1>, height=142260384.000,"
                          " volume=1314892194.000, className='Peak', axisCodes=('Hn', 'Nh'), "
                          "position=(8.062, 124.933), positionError=(None, None), "
                          "assignedNmrAtoms=((<NA:A.93.SER.H>, <NA:A.93.SER.N>),), "
                          "dimensionNmrAtoms=((<NA:A.93.SER.H>,), (<NA:A.93.SER.N>,))>")
