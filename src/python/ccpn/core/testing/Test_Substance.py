"""Module Documentation here

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
__version__ = "$Revision$"

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

    substance2 = self.project.newSubstance('Cell1', substanceType='Cell', labeling='moxy',
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
    substance1 = chain1.substance
    chain2 = substance1.createChain(shortName='Y')
    self.assertEqual(len(substance1.chains), 2)
    self.assertEqual(substance1._id, 'hardrock.')
    self.assertEqual(chain2.compoundName, 'hardrock')
    self.assertEqual(substance1.chains, (chain1, chain2))

    sample1 = self.project.newSample(name='S1')
    sc1 = sample1.newSampleComponent(name='hardrock')
    sample1 = self.project.newSample(name='S2')
    sc2 = sample1.newSampleComponent(name='hardrock', labeling='adhesive')
    self.assertEqual(sc1._id, 'S1.hardrock.')
    self.assertEqual(sc2._id, 'S2.hardrock.adhesive')
    self.assertEqual(substance1.sampleComponents, (sc1,))
    self.project.newUndoPoint()
    substance1.rename(name='electrical', labeling='cafe')
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
    substance1.rename(name='notmuch', labeling=None)
    self.assertEqual(sc1._id, 'S1.notmuch.')



