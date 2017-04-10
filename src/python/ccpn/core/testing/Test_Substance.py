"""Module Documentation here

"""
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
__dateModified__ = "$dateModified: 2017-04-10 12:56:47 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


class SubstanceTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_simple_create(self):
    substance1 = self.project.newSubstance('MolComp1', userCode='userCode',smiles=':-)')
    self.assertEqual(substance1.id, 'MolComp1.')
    self.assertEqual(substance1.smiles, ':-)')
    self.assertEqual(substance1.substanceType, 'Molecule')

    substance2 = self.project.newSubstance('Cell1', substanceType='Cell', labelling='moxy',
                                                 smiles=':-)')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(substance2.id, 'Cell1.moxy')
    self.assertEqual(substance2.smiles, None)
    self.assertEqual(substance2.substanceType, 'Cell')

  def test_substance_rename_1(self):

    chain1 = self.project.createChain(sequence='ACDC', compoundName='hardrock', shortName='X',
                                      molType='protein')
    substance1 = chain1.substances[0]
    chain2 = substance1.createChain(shortName='Y')
    self.assertEqual(len(substance1.chains), 2)
    self.assertEqual(substance1._id, 'hardrock.')
    self.assertEqual(chain2.compoundName, 'hardrock')
    self.assertEqual(substance1.chains, (chain1, chain2))

    sample1 = self.project.newSample(name='S1')
    sc1 = sample1.newSampleComponent(name='hardrock')
    sample1 = self.project.newSample(name='S2')
    sc2 = sample1.newSampleComponent(name='hardrock', labelling='adhesive')
    self.assertEqual(sc1._id, 'S1.hardrock.')
    self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
    self.assertEqual(substance1.sampleComponents, (sc1,))
    self.project.newUndoPoint()
    substance1.rename(name='electrical', labelling='cafe')
    self.assertEqual(substance1._id, 'electrical.cafe')
    self.assertEqual(sc1._id, 'S1.electrical.cafe')
    self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
    self.assertEqual(substance1.sampleComponents, (sc1,))
    self.project._undo.undo()
    self.assertEqual(substance1._id, 'hardrock.')
    self.assertEqual(sc1._id, 'S1.hardrock.')
    self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
    self.assertEqual(substance1.sampleComponents, (sc1,))
    self.project._undo.redo()
    self.assertEqual(substance1._id, 'electrical.cafe')
    self.assertEqual(sc1._id, 'S1.electrical.cafe')
    self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
    self.assertEqual(substance1.sampleComponents, (sc1,))
    substance1.rename(name='notmuch', labelling=None)
    self.assertEqual(sc1._id, 'S1.notmuch.')



