"""Tests for  package

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
__author__ = 'rhf22'

#
# Import the Implementation package - this is the root package
#

from ccpncore.util import Io as ioUtil
from ccpn.testing.Testing import Testing
from ccpncore.lib.molecule import MoleculeModify

class CreateMoleculeTest(Testing):

  def __init__(self, *args, **kwargs):
    # Testing.__init__( *args, **kwargs)
    Testing.__init__(self, 'CcpnCourse2c', *args, **kwargs)
    self.ccpnProject = self.project.wrappedData.root

  def test_create_protein_from_one_letter_string(self):
    seq1 = "QWERTYIPASDFGHKLCVNM"
    startNumber = 10
    molecule1 = MoleculeModify.makeMolecule(self.ccpnProject, seq1, startNumber=startNumber)
    assert molecule1.seqString == seq1, ("seqString %s does not match input %s"
                                         % (molecule1.seqString, seq1))
    residues = molecule1.sortedResidues()
    assert residues[0].seqCode == startNumber
    assert residues[-1].seqCode == startNumber + len (seq1)
    assert molecule1.molType == 'protein', ("Molecule %s has non-protein molType: %s"
                                            % (seq1, molecule1.molType))

  def test_create_DNA_from_one_letter_string(self):
    seq1 = "acgitu"
    molecule1 = MoleculeModify.makeMolecule(self.ccpnProject,  seq1, molType='DNA')
    assert molecule1.seqString == seq1.upper(), ("seqString %s does not match input %s"
                                         % (molecule1.seqString, seq1.upper()))
    assert molecule1.molType == 'DNA', ("Molecule %s has non-DNA molType: %s"
                                            % (seq1, molecule1.molType))

  def test_create_RNA_from_one_letter_string(self):
    seq1 = "acgitu"
    molecule1 = MoleculeModify.makeMolecule(self.ccpnProject,  seq1, molType='RNA')
    assert molecule1.seqString == seq1.upper(), ("seqString %s does not match input %s"
                                         % (molecule1.seqString, seq1.upper()))
    assert molecule1.molType == 'RNA', ("Molecule %s has non-RNA molType: %s"
                                            % (seq1, molecule1.molType))

  def test_create_cyclic_dna_rna(self):
    seq1 =  ['DA', 'DT', 'DC', 'DG', 'RT',
            '5MU', 'A', 'C', 'G', 'U', 'DU']
    molecule1 = MoleculeModify.makeMolecule(self.ccpnProject, seq1, isCyclic=True)
    assert molecule1.isCyclic, "Molecule is not cyclic as input."

  def test_create_mixed_molecule(self):
    seq1 = ['Ala', 'CYSS', 'DAL', 'D-Val', 'THR', 'HIS+', 'TRP', 'DA', 'DT', 'DC', 'DG', 'RT',
            '5MU', 'A', 'C', 'G', 'GLC', 'U', 'Ser']
    startNumber = -1
    molecule1 = MoleculeModify.makeMolecule(self.ccpnProject, seq1, startNumber=startNumber)