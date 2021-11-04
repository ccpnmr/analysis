"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-04 20:12:05 +0000 (Thu, November 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting


class RestraintTableTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_newDistanceRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('Distance')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'Distance')

    def test_newDihedralRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('Dihedral')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'Dihedral')

    def test_newCsaRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('Csa')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'Csa')

    def test_newRdcRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('Rdc')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'Rdc')

    def test_newChemicalShiftRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('ChemicalShift')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'ChemicalShift')

    def test_newJCouplingRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('JCoupling')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEquals(dataSet.restraintTables[0].restraintType, 'JCoupling')

    def test_renameDistanceRestraintTable(self):
        dataSet = self.project.newStructureData()
        newList = dataSet.newRestraintTable('Distance', name='Boom', comment='blah', unit='A',
                                            potentialType='logNormal', tensorMagnitude=1.0,
                                            tensorRhombicity=1.0, tensorIsotropicValue=0.0,
                                            tensorChainCode='A', tensorSequenceCode='11',
                                            tensorResidueType='TENSOR', origin='NOE')
        self.project.newUndoPoint()
        # Undo and redo all operations
        newList.rename('Chikka')
        self.undo.undo()
        self.assertEqual(newList.name, 'Boom')
        self.undo.undo()
        self.assertEquals(len(dataSet.restraintTables), 0)
        self.undo.redo()
        self.assertEquals(len(dataSet.restraintTables), 1)
        self.assertEqual(newList.name, 'Boom')
        self.undo.redo()
        self.assertEqual(newList.name, 'Chikka')
