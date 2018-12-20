"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
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
        self.project.newUndoPoint()
        # Undo and redo all operations
        newList.rename('Chikka')
        self.undo.undo()
        self.assertEqual(newList.name, 'Boom')
        self.undo.undo()
        self.undo.redo()
        self.undo.redo()
        self.assertEqual(newList.name, 'Chikka')
