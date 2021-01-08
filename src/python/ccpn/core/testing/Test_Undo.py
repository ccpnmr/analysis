"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2021-01-08 11:49:58 +0000 (Fri, January 08, 2021) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpn.core.lib.Undo import Undo


class ComplexUndoTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse2c.ccpn'

    def test_loaded_project(self):
        project = self.project._wrappedData.root
        project.checkAllValid()

    def test_make_chain_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        chainA = molSystem.findFirstChain(code='A')
        self.project.blankNotification()
        try:
            chainB = molSystem.newChain(code='X', molecule=chainA.molecule)
            project._undo.undo()
        finally:
            self.project.unblankNotification()
        project.checkAllValid()

    def test_make_chain_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        chainA = molSystem.findFirstChain(code='A')
        self.project.blankNotification()
        try:
            chainB = molSystem.newChain(code='X', molecule=chainA.molecule)
            project._undo.undo()
            project._undo.redo()
        finally:
            self.project.unblankNotification()
        project.checkAllValid()

    def test_copy_chain_undo(self):
        apiProject = self.project._wrappedData.root
        apiProject._undo = Undo()
        self.project.newUndoPoint()
        molSystem = apiProject.findFirstMolSystem(code='MS1')
        apiChainA = molSystem.findFirstChain(code='A')
        chainA = self.project._data2Obj.get(apiChainA)
        chainB = chainA.clone()
        apiProject._undo.undo()
        apiProject.checkAllValid()

    def test_copy_chain_undo_redo(self):
        apiProject = self.project._wrappedData.root
        apiProject._undo = Undo()
        self.project.newUndoPoint()
        molSystem = apiProject.findFirstMolSystem(code='MS1')
        apiChainA = molSystem.findFirstChain(code='A')
        chainA = self.project._data2Obj.get(apiChainA)
        chainB = chainA.clone()
        apiProject._undo.undo()
        apiProject._undo.redo()
        apiProject.checkAllValid(complete=True)

    def test_delete_residues_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        residues = molSystem.findFirstChain(code='A').sortedResidues()
        residues[22].delete()
        residues[45].delete()
        residues[21].delete()
        residues[20].delete()
        project._undo.undo()
        project.checkAllValid()

    def test_delete_residues_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        residues = molSystem.findFirstChain(code='A').sortedResidues()
        residues[22].delete()
        residues[45].delete()
        residues[21].delete()
        residues[20].delete()
        project._undo.undo()
        project._undo.redo()
        project.checkAllValid()

    def test_delete_chain_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        chain = molSystem.findFirstChain(code='A')
        chain.delete()
        project._undo.undo()
        project.checkAllValid()

    def test_delete_chain_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        chain = molSystem.findFirstChain(code='A')
        chain.delete()
        project._undo.undo()
        project._undo.redo()
        project.checkAllValid()

    def test_delete_molSystem_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        molSystem.delete()
        project._undo.undo()
        project.checkAllValid()

    def test_delete_molSystem_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        molSystem = project.findFirstMolSystem(code='MS1')
        molSystem.delete()
        project._undo.undo()
        project._undo.redo()
        project.checkAllValid()

    def test_delete_resonances_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        resonances = project.findFirstNmrProject().sortedResonances()
        for ii in range(1, 10):
            resonances[ii].delete()
            resonances[-ii].delete()
        project._undo.undo()
        project.checkAllValid()

    def test_delete_resonances_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        resonances = project.findFirstNmrProject().sortedResonances()
        for ii in range(1, 10):
            resonances[ii].delete()
            resonances[-ii].delete()
        project._undo.undo()
        project._undo.redo()
        project.checkAllValid()
