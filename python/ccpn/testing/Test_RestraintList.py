
"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.testing.WrapperTesting import WrapperTesting

class RestraintListTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_newDistanceRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('Distance')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newDihedralRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('Dihedral')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newCsaRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('Csa')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newRdcRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('Rdc')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newChemicalShiftRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('ChemicalShift')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newJCouplingRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('JCoupling')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_renameDistanceRestraintList(self):
    dataSet = self.project.newDataSet()
    newList = dataSet.newRestraintList('Distance', name='Boom', comment='blah', unit='A',
                                            potentialType='logNormal', tensorMagnitude=1.0,
                                            tensorRhombicity=1.0, tensorIsotropicValue=0.0,
                                            tensorChainCode='A', tensorSequenceCode='11',
                                            tensorResidueType='TENSOR', origin='NOE')
    self.undo.newWaypoint()
    # Undo and redo all operations
    newList.rename('Chikka')
    self.undo.undo()
    self.assertEqual(newList.name, 'Boom')
    self.undo.undo()
    self.undo.redo()
    self.undo.redo()
    self.assertEqual(newList.name, 'Chikka')
