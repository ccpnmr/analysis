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
__dateModified__ = "$dateModified: 2021-08-22 11:23:28 +0100 (Sun, August 22, 2021) $"
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
from ccpn.core.lib.Undo import Undo


class ComplexUndoTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'V3ProjectForTests.ccpn'

    def test_loaded_project(self):
        project = self.project._wrappedData.root
        project.checkAllValid()

    def test_delete_nmrAtoms_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        nc = self.project.getByPid('NC:A')
        for na in nc.nmrResidues[1].nmrAtoms:
            na.delete()
        project._undo.undo()
        project.checkAllValid()

    def test_delete_resonances_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        nc = self.project.getByPid('NC:A')
        for na in nc.nmrResidues[1].nmrAtoms:
            na.delete()
        project._undo.undo()
        project._undo.redo()
        project.checkAllValid()

    def test_make_chain_undo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        self.project.blankNotification()
        try:
            chainB = self.project.createChain(sequence='VICKYHIGMAN', compoundName='MyProtein', molType='protein')
            project._undo.undo()
        finally:
            self.project.unblankNotification()
        project.checkAllValid()

    def test_make_chain_undo_redo(self):
        project = self.project._wrappedData.root
        project._undo = Undo()
        self.project.newUndoPoint()
        self.project.blankNotification()
        try:
            chainB = self.project.createChain(sequence='VICKYHIGMAN', compoundName='MyProtein', molType='protein')
            project._undo.undo()
            project._undo.redo()
        finally:
            self.project.unblankNotification()
        project.checkAllValid()


    def test_copy_chain_undo(self):
        apiProject = self.project._wrappedData.root
        apiProject._undo = Undo()
        self.project.newUndoPoint()
        chainA = self.project.chains[0]
        chainB = chainA.clone()
        apiProject._undo.undo()
        apiProject.checkAllValid()

    def test_copy_chain_undo_redo(self):
        # NOTE:ED - this will fail until
        #   getBFactors, getOccupancies and getCoordinates are removed from api (or return [])
        #   not required for current structureEnsembles
        apiProject = self.project._wrappedData.root
        apiProject._undo = Undo()
        self.project.newUndoPoint()
        chainA = self.project.chains[0]
        chainB = chainA.clone()
        apiProject._undo.undo()
        apiProject._undo.redo()
        apiProject.checkAllValid(complete=True)

