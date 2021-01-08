"""Test code for NmrResidue

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
__dateModified__ = "$dateModified: 2021-01-08 11:49:57 +0000 (Fri, January 08, 2021) $"
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


class NmrAtomTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse2c.ccpn'

    def test_reassign1(self):
        nchain = self.project.getByPid('NC:A')

        arg11 = self.project.getByPid('NR:A.11.ARG')
        atomN = arg11.fetchNmrAtom('N')
        self.assertEqual(atomN.pid, 'NA:A.11.ARG.N')

        atomNE = self.project.produceNmrAtom('NA:A.11.ARG.NE')
        atomNE2 = self.project.produceNmrAtom(chainCode='A', sequenceCode='11', name='NE')
        self.assertIs(atomNE, atomNE2)

        atomCX = self.project.produceNmrAtom('NA:A.11.ARG.CX')
        atomNX = arg11.newNmrAtom(name='NX')
        with self.assertRaises(ValueError):
            atomCX.rename('NX')
        with self.assertRaises(TypeError):
            atomCX.rename(42)
        with self.assertRaises(TypeError):
            atomCX.rename(12.34)

        atomCX.rename('CZ')
        self.assertEqual(atomCX.pid, 'NA:A.11.ARG.CZ')

        atomCX = atomCX.assignTo(chainCode='A', sequenceCode='888')
        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

        atomCX = atomCX.assignTo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

        atomCX.rename()
        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')

        self.project._wrappedData.root.checkAllValid(complete=True)

        with self.assertRaises(ValueError):
            atomCX = self.project.produceNmrAtom('NA:A.11.VAL.CX')

        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')
        self.undo.redo()
        self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')

    def test_produce_reassign(self):
        at0 = self.project.produceNmrAtom(name='HX')
        self.assertEqual(at0.id, '@-.@89..HX')
        at1 = self.project.produceNmrAtom('X.101.VAL.N')
        self.assertEqual(at1.id, 'X.101.VAL.N')
        at1 = at1.assignTo(name='NE')
        self.assertEqual(at1.id, 'X.101.VAL.NE')
        at0 = at0.assignTo(sequenceCode=101)
        self.assertEqual(at0.id, '@-.101..HX')
        # Undo and redo all operations
        self.undo.undo()
        self.assertEqual(at0.id, '@-.@89..HX')
        self.undo.redo()
        self.assertEqual(at0.id, '@-.101..HX')
        self.assertEqual(at1.id, 'X.101.VAL.NE')
