"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-01-05 14:27:54 +0000 (Thu, January 05, 2023) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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
        self.assertEqual(list(x._id for x in chain.residues), ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])
        self.assertEqual(list(x._id for x in sorted(chain.residues)),
                         ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])

        nmrChain = self.project.newNmrChain(shortName='A')
        for residue in reversed(chain.residues):
            nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)
        self.assertEqual(list(x._id for x in nmrChain.nmrResidues),
                         ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])

        self.assertIs(chain.residues[1].nextResidue, chain.residues[2])
        self.assertIs(chain.residues[1].previousResidue, chain.residues[0])
        self.assertIs(sorted(nmrChain.nmrResidues)[1].nextNmrResidue, sorted(nmrChain.nmrResidues)[2])
        self.assertIs(sorted(nmrChain.nmrResidues)[1].previousNmrResidue,
                      sorted(nmrChain.nmrResidues)[0])

        chain.renumberResidues(-4)
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.-1.ALA', 'A.0.CYS', 'A.1.LYS', 'A.2.TRP'])
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])

        self.assertIs(chain.residues[1].nextResidue, chain.residues[2])
        self.assertIs(chain.residues[1].previousResidue, chain.residues[0])
        self.assertIs(sorted(nmrChain.nmrResidues)[1].nextNmrResidue, None)
        self.assertIs(sorted(nmrChain.nmrResidues)[1].previousNmrResidue, None)

        nmrChain.renumberNmrResidues(-4)
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.-1.ALA', 'A.0.CYS', 'A.1.LYS', 'A.2.TRP'])
        self.assertEqual(list(x._id for x in nmrChain.nmrResidues),
                         ['A.-1.ALA', 'A.0.CYS', 'A.1.LYS', 'A.2.TRP'])
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.-1.ALA', 'A.0.CYS', 'A.1.LYS', 'A.2.TRP'])

        chain.renumberResidues(10, 1)
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.-1.ALA', 'A.0.CYS', 'A.11.LYS', 'A.12.TRP'])

        nmrChain.renumberNmrResidues(10, 1)
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.-1.ALA', 'A.0.CYS', 'A.11.LYS', 'A.12.TRP'])

        # NBNB this should *NOT* be done in practice, as it brings the residues out of sequence
        # Still this is how the function should work, as residues are in seqId order.
        chain.renumberResidues(-5, 0, 0)
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.-1.ALA', 'A.-5.CYS', 'A.11.LYS', 'A.12.TRP'])

        # NBNB this should *NOT* be done in practice, as it brings the residues out of sequence
        # Still this is how the function should work, as NmrResidues are sorted.
        nmrChain.renumberNmrResidues(-5, 0, 0)
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.-5.CYS', 'A.-1.ALA', 'A.11.LYS', 'A.12.TRP'])

        self.assertRaises(ValueError, nmrChain.renumberNmrResidues, 4, -5, -5)
        self.assertRaises(ValueError, chain.renumberResidues, 4, -5, -5)

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
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.1.VAL', 'A.2.LEU', 'A.3.PHE', 'A.3B.TYR', 'A.3C-1.GLY', 'A.3C.TRP',
                          'A.3C+0.CYS', 'A.4.ARG', 'A.4+1.ASP', 'A.5.SER', 'A.@1.', 'A.@2.PRO'])
        nmrChain.renumberNmrResidues(10, 2, 4)
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.1.VAL', 'A.5.SER', 'A.12.LEU', 'A.13.PHE', 'A.13B.TYR', 'A.13C-1.GLY',
                          'A.13C.TRP', 'A.13C+0.CYS', 'A.14.ARG', 'A.14+1.ASP', 'A.@1.', 'A.@2.PRO'])

    def test_broken_renumbering(self):

        chain = self.project.createChain(('ALA', 'CYS', 'LYS', 'TRP'), startNumber=3,
                                         shortName='A')
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.3.ALA', 'A.4.CYS', 'A.5.LYS', 'A.6.TRP'])

        nmrChain = self.project.newNmrChain(shortName='A')
        for residue in chain.residues:
            nmrChain.newNmrResidue(sequenceCode=residue.sequenceCode, residueType=residue.residueType)

        self.assertRaises(ValueError, chain.renumberResidues, -3, 5)
        self.assertEqual(list(x._id for x in chain.residues),
                         ['A.3.ALA', 'A.4.CYS', 'A.2.LYS', 'A.6.TRP'])

        self.assertRaises(ValueError, nmrChain.renumberNmrResidues, -3, 5)
        self.assertEqual(list(x._id for x in sorted(nmrChain.nmrResidues)),
                         ['A.2.LYS', 'A.3.ALA', 'A.4.CYS', 'A.6.TRP'])
        self.assertEqual(list(x._id for x in nmrChain.nmrResidues),
                         ['A.2.LYS', 'A.3.ALA', 'A.4.CYS', 'A.6.TRP'])
