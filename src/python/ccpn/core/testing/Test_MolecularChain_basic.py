#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-05-29 16:04:28 +0100 (Wed, May 29, 2024) $"
__version__ = "$Revision: 3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


class TestPhysicalChainCreation(WrapperTesting):

    def test_createPhysicalChain(self):
        # now case-sensitive :|
        c = self.project.createChain('ACD', molType='protein')

        self.assertEqual(len(self.project.chains), 1)
        self.assertIs(self.project.chains[0], c)
        self.assertEqual(c.pid, 'MC:A')

    def test_createPhysicalChainLowercase(self):
        # now case-sensitive :|
        with self.assertRaises(ValueError):
            c = self.project.createChain('acd', molType='protein')

    def test_createPhysicalChainFromPolymerSubstance(self):
        # but this isn't case-sensitive :|
        s = self.project.createPolymerSubstance('acd', name='test', molType='protein')
        c = s.createChain()

        self.assertIs(self.project.chains[0], c)
        self.assertEqual(c.pid, 'MC:A')
        self.assertIs(c.substances[0], s)
