"""Test code for NmrChain

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revisgion: 8885 $"

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

    self.assertRaises(ValueError, nchain0.rename, 'something')
    self.assertRaises(ApiError, self.project.newNmrChain, shortName='@-')
    self.assertRaises(ApiError, self.project.newNmrChain, shortName='@2')
    self.assertRaises(ApiError, self.project.newNmrChain, shortName='#2')
    self.assertRaises(ApiError, self.project.newNmrChain, shortName='@1')

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