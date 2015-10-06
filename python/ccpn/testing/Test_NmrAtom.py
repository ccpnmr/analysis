"""Test code for NmrResidue

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpn.testing.WrapperTesting import WrapperTesting

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

    atomCX = atomCX.reassigned(chainCode='A', sequenceCode='888')
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

    atomCX = atomCX.reassigned()
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.CZ')

    atomCX.rename()
    self.assertEqual(atomCX.pid, 'NA:A.888.ARG.C@198')


    with self.assertRaises(ValueError):
      atomCX = self.project.produceNmrAtom('NA:A.11.VAL.CX')

    nchain0 = self.project.getByPid('NC:@')
    nr1, nr2 = nchain.nmrResidues[:2]
    res1 = nr1.residue
    res2 = nr2.residue
    res3 = self.project.chains[0].residues[2]
    nr3 = res3.nmrResidue
    nr2.residue = None
    self.assertEqual(nr2.longPid, "NmrResidue:A.@2.ARG")
    target =  self.project.getByPid('NR:A.2.LYS')
    target.rename('.LYS')
    self.assertEqual(target.longPid, "NmrResidue:A.@11.LYS")
    nr2.rename('2.LYS')
    self.assertEqual(nr2.longPid, "NmrResidue:A.2.LYS")
    newNr = nchain0.newNmrResidue()
    self.assertEqual(newNr.longPid, "NmrResidue:@.@90.")
    nr3.nmrChain = nchain0
    self.assertEqual(nr3.longPid, "NmrResidue:@.3.GLU")
    newNr.residue = res3
    self.assertEqual(newNr.longPid, "NmrResidue:A.3.GLU")
    nchain.rename('X')
    self.assertEqual(nchain.longPid, "NmrChain:X")
    self.assertEqual(nr2.longPid, "NmrResidue:X.2.ARG")
    nr2.rename()
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(nr2.longPid, "NmrResidue:X.@2.")

  def test_produce_reassign(self):
    at0 = self.project.produceNmrAtom(name='HX')
    self.assertEqual(at0.id,'@-.@89..HX')
    at1 = self.project.produceNmrAtom('X.101.VAL.N')
    self.assertEqual(at1.id,'X.101.VAL.N')
    at1 = at1.reassigned(name='NE')
    self.assertEqual(at1.id,'X.101.VAL.NE')
    at0 = at0.reassigned(sequenceCode=101)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(at0.id,'@-.101..HX')

    
  def test_fetchNmrAtom(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
    res2 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs(res1, res2)

  def test_fetchEmptyNmrResidue(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode=None, residueType="ALA")
    sequenceCode = '@%s' % res1._wrappedData.serial
    self.assertEqual(res1.sequenceCode, sequenceCode)
    res2 = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs(res1, res2)

  def test_offsetNmrResidue(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
    res2 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", residueType="ALA")
    self.assertIs(res2._wrappedData.mainResonanceGroup, res1._wrappedData)
    res3 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", residueType="ALA")
    self.assertIs(res2, res3)
    res1.delete()
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertTrue( res2._wrappedData.isDeleted)

  def test_get_by_serialName(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode=None, residueType="ALA")
    serialName = '@%s' % res1._wrappedData.serial
    res2 = nmrChain.fetchNmrResidue(sequenceCode=serialName)
    self.assertIs(res1, res2)
    res3 = nmrChain.fetchNmrResidue(sequenceCode=serialName + '+0')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs(res3._wrappedData.mainResonanceGroup, res1._wrappedData)