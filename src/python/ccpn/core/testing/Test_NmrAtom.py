"""Test code for NmrResidue

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

class NmrAtomTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse2c'

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

    atomCX.rename('CZ')
    self.assertEqual(atomCX.pid, 'NA:A.11.ARG.CZ')

    atomCX = atomCX.assignTo(chainCode='A', sequenceCode='888')
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

    atomCX = atomCX.assignTo()
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

    atomCX.rename()
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')


    with self.assertRaises(ValueError):
      atomCX = self.project.produceNmrAtom('NA:A.11.VAL.CX')

    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')

  def test_produce_reassign(self):
    at0 = self.project.produceNmrAtom(name='HX')
    self.assertEqual(at0.id,'@-.@89..HX')
    at1 = self.project.produceNmrAtom('X.101.VAL.N')
    self.assertEqual(at1.id,'X.101.VAL.N')
    at1 = at1.assignTo(name='NE')
    self.assertEqual(at1.id,'X.101.VAL.NE')
    at0 = at0.assignTo(sequenceCode=101)
    self.assertEqual(at0.id,'@-.101..HX')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(at0.id,'@-.101..HX')
    self.assertEqual(at1.id,'X.101.VAL.NE')
