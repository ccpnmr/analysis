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

class NmrResidueTest(WrapperTesting):

  # Path of project to load (None for new project
  projectPath = 'CcpnCourse2c'

  def test_reassign_attributes(self):
    nchain = self.project.getByPid('NC:A')
    nchain0 = self.project.getByPid('NC:@-')

    nr1, nr2 = nchain.nmrResidues[9:11]
    res1 = nr1.residue
    res2 = nr2.residue
    res3 = self.project.chains[0].residues[2]
    nr3 = res3.nmrResidue
    nr2.residue = None
    self.assertEqual(nr2.longPid, "NmrResidue:A.@2.ARG")
    target =  self.project.getByPid('NR:A.2.LYS')
    target.rename('.LYS')
    self.assertEqual(target.longPid, "NmrResidue:A.@11.LYS")
    newNr = nchain0.newNmrResidue()
    self.assertEqual(newNr.longPid, "NmrResidue:@-.@89.")
    nr3.nmrChain = nchain0
    self.assertEqual(nr3.longPid, "NmrResidue:@-.3.GLU")
    newNr.residue = res3
    self.assertEqual(newNr.longPid, "NmrResidue:A.3.GLU")
    nchain.rename('X')
    self.assertEqual(nchain.longPid, "NmrChain:X")
    self.assertEqual(nr2.longPid, "NmrResidue:X.@2.ARG")
    newNr.rename(None)
    self.assertEqual(newNr.longPid, "NmrResidue:X.@89.")
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(newNr.longPid, "NmrResidue:X.@89.")

  def test_rename(self):
    nchain = self.project.getByPid('NC:A')
    nr1, nr2 = nchain.nmrResidues[9:11]
    self.assertEqual(nr1.id, "A.10.TYR")
    nr1.deassign()
    self.assertEqual(nr1.id, "@-.@1.")
    nr1.rename('999')
    self.assertEqual(nr1.id, "@-.999.")
    nr1.rename('999.ALA')
    self.assertEqual(nr1.id, "@-.999.ALA")
    nr1.rename('998.VAL')
    self.assertEqual(nr1.id, "@-.998.VAL")
    nr1.rename('.TYR')
    self.assertEqual(nr1.id, "@-.@1.TYR")
    nr1.rename('997')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(nr1.id, "@-.997.")

  def test_reassign(self):
    nchain = self.project.getByPid('NC:A')
    nr1, nr2 = nchain.nmrResidues[9:11]
    self.assertEqual(nr1.id, "A.10.TYR")
    nr1 = nr1.assignTo('A.999')
    self.assertEqual(nr1.id, "A.999.")
    nr1 = nr1.assignTo()
    # This is a no-op
    self.assertEqual(nr1.id, "A.999.")

    with self.assertRaises(ValueError):
      nr2 = nr2.assignTo(sequenceCode=15)

    nr2 = nr2.assignTo(sequenceCode=515, residueType='XXX')
    self.assertEqual(nr2.id, 'A.515.XXX')
    obj = nchain.newNmrResidue(sequenceCode=777)
    self.assertEqual(obj.id, 'A.777.')

    self.assertTrue(len(nr1.nmrAtoms) == 2)
    nrx = nr2.assignTo(nr1.id)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs(nrx, nr1)
    self.assertIsNone(nr2._apiResonanceGroup)
    self.assertTrue(len(nr1.nmrAtoms) == 4)


  def test_fetchNmrResidue(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
    res2 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
    self.assertIs(res1, res2)
    obj = nmrChain.fetchNmrResidue(sequenceCode=515)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(obj.pid, 'NR:@1.515.')

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
    self.assertIsNone( res2._wrappedData)

  def test_get_by_serialName(self):
    nmrChain = self.project.fetchNmrChain(shortName='@1')
    res1 = nmrChain.fetchNmrResidue(sequenceCode=None, residueType="ALA")
    serialName = '@%s' % res1._wrappedData.serial
    res2 = nmrChain.fetchNmrResidue(sequenceCode=serialName)
    self.assertIs(res1, res2)
    res3 = nmrChain.fetchNmrResidue(sequenceCode=serialName + '+0')
    self.assertIs(res3._wrappedData.mainResonanceGroup, res1._wrappedData)
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertIs(res3._wrappedData.mainResonanceGroup, res1._wrappedData)