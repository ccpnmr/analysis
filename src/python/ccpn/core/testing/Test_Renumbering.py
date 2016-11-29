"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
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

from ccpn.framework import Framework
from ccpn.core.testing.WrapperTesting import WrapperTesting


class RenumberingTest(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_renumbering(self):

    chain = self.project.createChain(('ALA', 'CYS', 'LYS', 'TRP'), startNumber=3,
                                     shortName='A')
    self.assertEquals(list(x._key for x in chain.residues), ['3.ALA','4.CYS','5.LYS','6.TRP'])

    nmrChain = self.project.newNmrChain(shortName='A')
    for residue in chain.residues:
      nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues), ['3.ALA','4.CYS','5.LYS','6.TRP'])

    chain.incrementResidueAssignments(-4)
    self.assertEquals(list(x._key for x in chain.residues), ['-1.ALA','0.CYS','1.LYS','2.TRP'])
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['3.ALA', '4.CYS', '5.LYS', '6.TRP'])

    nmrChain.incrementNmrResidueAssignments(-4)
    self.assertEquals(list(x._key for x in chain.residues), ['-1.ALA','0.CYS','1.LYS','2.TRP'])
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['-1.ALA', '0.CYS', '1.LYS', '2.TRP'])

    chain.incrementResidueAssignments(10, 1)
    self.assertEquals(list(x._key for x in chain.residues),
                      ['-1.ALA', '0.CYS', '11.LYS', '12.TRP'])

    nmrChain.incrementNmrResidueAssignments(10, 1)
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['-1.ALA', '0.CYS', '11.LYS', '12.TRP'])

    # NBNB this should *NOT* be done in practice, as it brings the residues out of sequence
    # Still this is how the function should work, as residues are in seqId order.
    chain.incrementResidueAssignments(-5, 0, 0)
    self.assertEquals(list(x._key for x in chain.residues),
                      ['-1.ALA', '-5.CYS', '11.LYS', '12.TRP'])

    # NBNB this should *NOT* be done in practice, as it brings the residues out of sequence
    # Still this is how the function should work, as NmrResidues are sorted.
    nmrChain.incrementNmrResidueAssignments(-5, 0, 0)
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['-5.CYS', '-1.ALA', '11.LYS', '12.TRP'])

    self.assertRaises(ValueError, nmrChain.incrementNmrResidueAssignments, 4, -5, -5)
    self.assertRaises(ValueError, chain.incrementResidueAssignments, 4, -5, -5)

  def test_renumbering_complex_cases(self):
    nmrChain = self.project.newNmrChain(shortName='A')
    nmrChain.newNmrResidue()
    nmrChain.newNmrResidue(residueType='PRO')
    nmrChain.newNmrResidue(sequenceCode='1', residueType='VAL')
    nmrChain.newNmrResidue(sequenceCode='2', residueType='LEU')
    nmrChain.newNmrResidue(sequenceCode='3', residueType='PHE')
    nmrChain.newNmrResidue(sequenceCode='3B', residueType='TYR')
    nmrChain.newNmrResidue(sequenceCode='3C', residueType='TRP')
    nmrChain.newNmrResidue(sequenceCode='3C+0', residueType='CYS')
    nmrChain.newNmrResidue(sequenceCode='3C-1', residueType='GLY')
    nmrChain.newNmrResidue(sequenceCode='4', residueType='ARG')
    nmrChain.newNmrResidue(sequenceCode='4+1', residueType='ASP')
    nmrChain.newNmrResidue(sequenceCode='5', residueType='SER')
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['1.VAL', '2.LEU', '3.PHE', '3B.TYR', '3C-1.GLY', '3C.TRP',
                       '3C+0.CYS', '4.ARG', '4+1.ASP','5.SER', '@1.', '@2.PRO'])
    nmrChain.incrementNmrResidueAssignments(10, 2, 4)
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['1.VAL', '5.SER', '12.LEU', '13.PHE', '13B.TYR', '13C-1.GLY',
                       '13C.TRP', '13C+0.CYS', '14.ARG', '14+1.ASP', '@1.', '@2.PRO'])


  def test_broken_renumbering(self):

    chain = self.project.createChain(('ALA', 'CYS', 'LYS', 'TRP'), startNumber=3,
                                     shortName='A')
    self.assertEquals(list(x._key for x in chain.residues), ['3.ALA','4.CYS','5.LYS','6.TRP'])

    nmrChain = self.project.newNmrChain(shortName='A')
    for residue in chain.residues:
      nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)

    self.assertRaises(ValueError, chain.incrementResidueAssignments, -3, 5)
    self.assertEquals(list(x._key for x in chain.residues),
                      ['3.ALA', '4.CYS', '2.LYS', '6.TRP'])

    self.assertRaises(ValueError, nmrChain.incrementNmrResidueAssignments, -3, 5)
    self.assertEquals(list(x._key for x in nmrChain.nmrResidues),
                      ['2.LYS', '3.ALA', '4.CYS', '6.TRP'])