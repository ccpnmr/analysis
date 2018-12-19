"""Test code for NmrChain

"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:34 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class NmrChainTest(WrapperTesting):
    projectPath = None

    def test_NmrChain_naming(self):
        nchain0 = self.project.getByPid('NC:@-')
        self.assertEqual(nchain0._wrappedData.serial, 1)

        ncx = self.project.getNmrChain('@-')
        self.assertIs(nchain0, ncx)
        nchain1 = self.project.newNmrChain()
        self.assertEqual(nchain1.shortName, '@2')
        nchain2 = self.project.newNmrChain(isConnected=True)
        self.assertEqual(nchain2.shortName, '#3')
        nchain3 = self.project.newNmrChain('#5')
        self.assertEqual(nchain3.shortName, '#5')
        nchain4 = self.project.newNmrChain('@4')
        self.assertEqual(nchain4.shortName, '@4')

        self.assertRaises(ValueError, nchain0.rename, 'something')
        self.assertRaises(ValueError, self.project.newNmrChain, shortName='@-')
        self.assertRaises(ValueError, self.project.newNmrChain, shortName='@2')
        self.assertRaises(ValueError, self.project.newNmrChain, shortName='#2')
        nchain4.delete()
        nchain4 = self.project.newNmrChain(shortName='#4')
        self.assertEqual(nchain4.shortName, '#4')

        nc2 = self.project.newNmrChain(isConnected=True)
        self.assertEqual(nc2.shortName, '#6')
        self.assertRaises(ValueError, nc2.rename, '@6')

        nc3 = self.project.newNmrChain()
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(nc3.shortName, '@7')
        self.assertRaises(ApiError, nc3.rename, '#7')

    def test_NmrChain_Chain(self):
        chain = self.project.createChain(sequence='AACKC', shortName='x', molType='protein')
        nmrChain = self.project.newNmrChain(shortName='x')
        self.undo.undo()
        self.undo.redo()
        self.assertIs(nmrChain.chain, chain)
        self.assertIs(chain.nmrChain, nmrChain)

    def test_deassign(self):
        ncx = self.project.getNmrChain('@-')
        self.assertRaises(ApiError, ncx.deassign)
        self.assertEquals(ncx.pid, 'NC:@-')

        ncx = self.project.fetchNmrChain('AA')
        self.assertEquals(ncx.pid, 'NC:AA')
        ncx.deassign()
        self.assertEquals(ncx.pid, 'NC:@2')

        ncx = self.project.newNmrChain(isConnected=True)
        self.assertEquals(ncx.pid, 'NC:#3')
        ncx.deassign()
        self.undo.undo()
        self.undo.redo()
        self.assertEquals(ncx.pid, 'NC:#3')
