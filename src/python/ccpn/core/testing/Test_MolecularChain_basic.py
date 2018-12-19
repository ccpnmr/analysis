#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:33 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
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
        c = self.project.createChain('acd', molType='protein')

        self.assertEqual(len(self.project.chains), 1)
        self.assertIs(self.project.chains[0], c)
        self.assertEqual(c.pid, 'MC:A')

    def test_createPhysicalChainFromPolymerSubstance(self):
        s = self.project.createPolymerSubstance('acd', name='test', molType='protein')
        c = s.createChain()

        self.assertIs(self.project.chains[0], c)
        self.assertEqual(c.pid, 'MC:A')
        self.assertIs(c.substances[0], s)
