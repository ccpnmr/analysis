"""Test code for NmrChain

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Daniel Thompson $"
__dateModified__ = "$dateModified: 2023-11-23 14:46:22 +0000 (Thu, November 23, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting, getProperties
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
        undo_id = nc3.pid
        self.undo.undo()
        self.assertNotEqual(undo_id, nc3.pid)
        self.undo.redo()
        self.assertEqual(nc3.shortName, '@7')
        self.assertEqual(undo_id, nc3.pid)
        self.assertRaises(ApiError, nc3.rename, '#7')

        # cannot create chain beginning with @- for safety/clarity
        self.assertRaises(ValueError, self.project.newNmrChain, shortName='@-_new')

    def test_NmrChain_Chain(self):
        chain = self.project.createChain(sequence='AACKC', shortName='x', molType='protein')
        nmrChain = self.project.newNmrChain(shortName='x')

        undo_id = nmrChain.pid
        self.undo.undo()
        self.assertNotEqual(undo_id, nmrChain.pid)
        self.undo.redo()
        self.assertEqual(undo_id, nmrChain.pid)
        self.assertIs(nmrChain.chain, chain)
        self.assertIs(chain.nmrChain, nmrChain)

    def test_deassign(self):
        ncx = self.project.getNmrChain('@-')
        self.assertRaises(ApiError, ncx.deassign)
        self.assertEqual(ncx.pid, 'NC:@-')

        ncx = self.project.fetchNmrChain('AA')
        self.assertEqual(ncx.pid, 'NC:AA')
        ncx.deassign()
        self.assertEqual(ncx.pid, 'NC:@2')

        ncx = self.project.newNmrChain(isConnected=True)
        self.assertEqual(ncx.pid, 'NC:#3')
        ncx.deassign()

        self.undo.undo()
        self.undo.redo()

        self.assertEqual(ncx.pid, 'NC:#3')

