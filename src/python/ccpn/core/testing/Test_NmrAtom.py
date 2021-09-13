"""Test code for NmrResidue

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
__dateModified__ = "$dateModified: 2021-09-13 19:25:08 +0100 (Mon, September 13, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.core.testing.WrapperTesting import WrapperTesting, fixCheckAllValid


class NmrAtomTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'V3ProjectForTests.ccpn'

    def test_fetchNmrAtomReassign(self):
        nchain = self.project.getByPid('NC:A')

        ile5 = self.project.getByPid('NR:A.5.ILE')
        atomN = ile5.fetchNmrAtom('N')
        self.assertEqual(atomN.pid, 'NA:A.5.ILE.N')

        atomNE = ile5.fetchNmrAtom('NE')
        atomNE2 = ile5.fetchNmrAtom('NE')
        self.assertIs(atomNE, atomNE2)

        atomCX = ile5.fetchNmrAtom('CX')
        atomNX = ile5.newNmrAtom(name='NX')
        # with self.assertRaises(ValueError):
        #     atomCX.rename('NX')
        with self.assertRaises(ValueError):
            atomCX.rename(42)
        with self.assertRaises(ValueError):
            atomCX.rename(12.34)

        atomCX.rename('CZ')
        self.assertEqual(atomCX.pid, 'NA:A.5.ILE.CZ')

        atomCX = atomCX.assignTo(chainCode='A', sequenceCode='888')
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')

        atomCX = atomCX.assignTo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')

        atomCX.rename('Co')
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')

        # fix the bad structure for the test
        # new pdb loader does not load the into the data model so there are no atoms defined
        # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
        fixCheckAllValid(self.project)

        self.project._wrappedData.root.checkAllValid(complete=True)


        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.CZ')
        self.undo.redo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ILE.Co')

    def test_newNmrAtomReassign(self):
        nc = self.project.newNmrChain(shortName='X')
        self.assertEqual(nc.pid, 'NC:X')

        nr = nc.newNmrResidue(sequenceCode='101', residueType='VAL')
        self.assertEqual(nr.pid, 'NR:X.101.VAL')

        at1 = nr.newNmrAtom(name='N')
        self.assertEqual(at1.pid, 'NA:X.101.VAL.N')
        at1 = at1.assignTo(name='NE')
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        at1 = at1.assignTo(sequenceCode='777')
        self.assertEqual(at1.pid, 'NA:X.777.VAL.NE')
        self.undo.undo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        self.undo.undo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.N')
        self.undo.redo()
        self.assertEqual(at1.pid, 'NA:X.101.VAL.NE')
        self.undo.redo()
        self.assertEqual(at1.pid, 'NA:X.777.VAL.NE')

