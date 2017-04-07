#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:35 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError

class TestSampleComponentCreation(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.sample = self.project.newSample('test sample')

  def _test_newSampleComponentWithoutName(self):
    self.assertRaises(TypeError, self.sample.newSampleComponent)
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponentEmptyName(self):
    self.assertRaises(ApiError, self.sample.newSampleComponent, '')
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponent(self):
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

    sc = self.sample.newSampleComponent('test sample component')

    self.assertEqual(sc.pid, 'SC:test sample.test sample component.')
    self.assertEqual(len(self.project.sampleComponents), 1)
    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.sampleComponents[0], sc)

class TestSampleComponentLinks(WrapperTesting):
  """Tests SampleComponent, Substance, Chain, and the links between them"""
  def setUp(self):
    with self.initialSetup():
      self.sample = self.project.newSample('test sample')

  def test_crosslinks(self):
    chain1 = self.project.createChain(sequence='QWERTYIPASDF', molType='protein',
                                      compoundName='typewriter')
    dna = self.project.createPolymerSubstance(sequence='ATTACGCAT', name='attackcat',
                                              molType='DNA',)
  def _test_newSampleComponentWithoutName(self):
    self.assertRaises(TypeError, self.sample.newSampleComponent)
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponentEmptyName(self):
    self.assertRaises(ApiError, self.sample.newSampleComponent, '')
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

  def test_newSampleComponent(self):
    self.assertEqual(len(self.project.sampleComponents), 0)
    self.assertEqual(len(self.project.substances), 0)

    sc = self.sample.newSampleComponent('test sample component')

    self.assertEqual(sc.pid, 'SC:test sample.test sample component.')
    self.assertEqual(len(self.project.sampleComponents), 1)
    self.assertEqual(len(self.project.substances), 1)
    self.assertIs(self.project.sampleComponents[0], sc)
