
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

class PeakListTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = 'CcpnCourse2b'

  def test_newDistanceRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newDistanceRestraintlist = restraintSet.newRestraintList('Distance')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newDihedralRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newDihedralRestraintList = restraintSet.newRestraintList('Dihedral')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newCsaRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newCsaRestraintList = restraintSet.newRestraintList('Csa')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newRdcRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newRdcRestraintList = restraintSet.newRestraintList('Rdc')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newChemicalShiftRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newChemicalShiftRestraintList = restraintSet.newRestraintList('ChemicalShift')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()

  def test_newJCouplingRestraintList(self):
    restraintSet = self.project.getByPid('RS:20')
    newJCouplingRestraintList = restraintSet.newRestraintList('JCoupling')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
