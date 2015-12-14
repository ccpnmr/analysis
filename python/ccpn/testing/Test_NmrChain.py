"""Test code for NmrChain

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
__version__ = "$Revisgion: 8885 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.testing.WrapperTesting import WrapperTesting
from ccpncore.memops.ApiError import ApiError

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
    self.assertEqual(nc3.shortName, '@7')
    self.assertRaises(ApiError, nc3.rename, '#7')

  def test_NmrChain_Chain(self):
    chain = self.project.createChain(sequence='AACKC', shortName='x', molType='protein')
    nmrChain = self.project.newNmrChain(shortName='x')
    self.assertIs(nmrChain.chain, chain)
    self.assertIs(chain.nmrChain, nmrChain)