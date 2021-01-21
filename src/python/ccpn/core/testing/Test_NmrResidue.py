"""
Test code for NmrResidue
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-21 15:55:18 +0000 (Thu, January 21, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from unittest import skip
from ccpn.core.testing.WrapperTesting import WrapperTesting


class ResidueAllNmrResiduesTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    def setUp(self):

        with self.initialSetup():
            self.chain = self.project.createChain(sequence='CDEFGHI', molType='protein',
                                                  shortName='A')

    def testAllNmrResidues(self):

        allResidues = [(),
                       ('NR:A.3-1.',),
                       ('NR:A.3.GLU', 'NR:A.3+0.', 'NR:A.4-1.'),
                       ('NR:A.4.PHE', 'NR:A.4+0.', 'NR:A.5-1.'),
                       ('NR:A.3+2.', 'NR:A.5.GLY', 'NR:A.5+0.'),
                       ('NR:A.4+2.',),
                       ('NR:A.5+2.',)]
        allAtoms = [(),
                    ('NA:A.3-1..N', 'NA:A.3-1..CA'),
                    ('NA:A.3.GLU.N', 'NA:A.3.GLU.CA', 'NA:A.3+0..N', 'NA:A.3+0..CA', 'NA:A.4-1..N',
                     'NA:A.4-1..CA'),
                    ('NA:A.4.PHE.N', 'NA:A.4.PHE.CA', 'NA:A.4+0..N', 'NA:A.4+0..CA', 'NA:A.5-1..N',
                     'NA:A.5-1..CA'),
                    ('NA:A.3+2..N', 'NA:A.3+2..CA', 'NA:A.5.GLY.N', 'NA:A.5.GLY.CA', 'NA:A.5+0..N',
                     'NA:A.5+0..CA'),
                    ('NA:A.4+2..N', 'NA:A.4+2..CA'),
                    ('NA:A.5+2..N', 'NA:A.5+2..CA'),
                    ]

        for res in self.chain.residues:
            self.assertEquals(res.allNmrResidues, ())

        nmrResidues = []
        nmrChain = self.project.newNmrChain(isConnected=True)

        for residueType in ['GLU', 'PHE', 'GLY']:
            nr = nmrChain.newNmrResidue(residueType=residueType)
            nmrResidues.append(nr)
            for suffix in ('-1', '+0', '+2'):
                nmrResidues.append(nmrChain.newNmrResidue(sequenceCode=nr.sequenceCode + suffix))

        for nr in nmrResidues:
            nr.newNmrAtom(name='N')
            nr.newNmrAtom(name='CA')

        nmrChain.assignConnectedResidues(self.chain.residues[2])

        self.assertEquals([x.pid for x in nmrResidues],
                          ['NR:A.3.GLU', 'NR:A.3-1.', 'NR:A.3+0.', 'NR:A.3+2.',
                           'NR:A.4.PHE', 'NR:A.4-1.', 'NR:A.4+0.', 'NR:A.4+2.',
                           'NR:A.5.GLY', 'NR:A.5-1.', 'NR:A.5+0.', 'NR:A.5+2.']
                          )
        for ii, residue in enumerate(self.chain.residues):
            self.assertEquals(tuple(x.pid for x in residue.allNmrResidues), allResidues[ii])

        self.assertIs(nmrResidues[4].previousNmrResidue, nmrResidues[0])
        self.assertIs(nmrResidues[8].previousNmrResidue, nmrResidues[4])
        self.assertIs(nmrResidues[0].nextNmrResidue, nmrResidues[4])
        self.assertIs(nmrResidues[4].nextNmrResidue, nmrResidues[8])
        self.assertFalse(nmrResidues[0].nmrChain.isConnected)


class NmrStretchTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    def setUp(self):

        with self.initialSetup():
            self.chain = self.project.createChain(sequence='QWERTYIPASD', molType='protein',
                                                  shortName='X')

    def test_connect_nmr_residues_0(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in nmrChain.nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN', ])

        nmrResidues[0].connectPrevious(nmrResidues[1])
        # self.undo.undo()
        # self.undo.redo()
        nmrResidues[1].connectPrevious(nmrResidues[2])
        nmrResidues[4].connectNext(nmrResidues[3])
        nmrResidues[4].connectPrevious(nmrResidues[0])
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#3.@3.GLY', '#3.@2.VAL', '#3.@1.ALA', '#3.@5.GLN', '#3.@4.CYS', ])

        self.undo.undo()
        self.undo.undo()  # ejb - error here on Nmr.py/setLabel(41524)
        self.undo.undo()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN', ])
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#3.@3.GLY', '#3.@2.VAL', '#3.@1.ALA', '#3.@5.GLN', '#3.@4.CYS', ])

    def test_connect_nmr_residues_1(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in nmrChain.nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN', ])

        nmrResidues[0].connectPrevious(nmrResidues[1])
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@2.VAL', '#2.@1.ALA', ])
        self.assertEqual(nmrResidues[0].nextNmrResidue, None)
        self.assertEqual(nmrResidues[0].previousNmrResidue, nmrResidues[1])

        nmrResidues[-1].connectNext(nmrResidues[-2])
        self.assertEqual([x.id for x in nmrResidues[-1].nmrChain.mainNmrResidues],
                         ['#3.@5.GLN', '#3.@4.CYS', ])
        self.assertEqual(nmrResidues[-1].nextNmrResidue, nmrResidues[-2])
        self.assertEqual(nmrResidues[-1].previousNmrResidue, None)

        nmrResidues[2].connectNext(nmrResidues[-1])
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[-1].nmrChain.mainNmrResidues],
                         ['#3.@5.GLN', '#3.@4.CYS', ])
        self.assertEqual(nmrResidues[-1].nextNmrResidue, nmrResidues[-2])
        self.assertEqual(nmrResidues[-1].previousNmrResidue, None)
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues[2].nmrChain.mainNmrResidues],
                         ['#3.@3.GLY', '#3.@5.GLN', '#3.@4.CYS', ])

        nmrResidues[2].connectPrevious(nmrResidues[0])

        stretch = nmrResidues[2].nmrChain.mainNmrResidues
        stretch[-2].deassign()
        self.assertEqual([x.id for x in stretch],
                         ['#3.@2.VAL', '#3.@1.ALA', '#3.@3.GLY', '#3.@5.', '#3.@4.CYS', ])

        self.assertRaises(ValueError, stretch[-1].connectNext, stretch[0])

        self.project._wrappedData.root.checkAllValid(complete=True)

    def test_connected_nmr_residues(self):
        nmrChain = self.project.newNmrChain()
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))

        with self.assertRaises(AttributeError):
            nmrChain.nmrResidues = nmrResidues
        self.assertRaises(ValueError, nmrResidues[2].connectNext, None)
        self.assertIs(nmrResidues[2].nextNmrResidue, None)
        self.assertIs(nmrResidues[2].previousNmrResidue, None)

    def test_disconnect_triplet_1(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[1].disconnectPrevious()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '#2.@2.VAL', '#2.@3.', ])

    def test_disconnect_triplet_2(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[2].disconnectPrevious()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.', ])

    def test_disconnect_triplet_3(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[0].disconnectNext()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '#2.@2.VAL', '#2.@3.', ])

    def test_disconnect_triplet_4(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[1].disconnectNext()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.', ])

    def test_disconnect_triplet_5(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[0].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '#2.@2.VAL', '#2.@3.', ])

    def test_disconnect_triplet_6(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[1].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.', ])
        self.assertEquals([x.id for x in self.project.nmrChains], ['@-'])

    def test_disconnect_triplet_7(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        nmrResidues[2].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.', ])

    def test_disconnect_double(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', ])
        nmrResidues[0].disconnectNext()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL'])

    def test_connect_chain_chain(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE', 'ALA'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues

        nmrChain2 = self.project.newNmrChain(isConnected=True)
        nmrResidues2 = []
        for residueType in ('VAL', 'SER', None, 'ILE'):
            nmrResidues2.append(nmrChain2.fetchNmrResidue(residueType=residueType))
        nmrChain2.mainNmrResidues = nmrResidues2

        nmrChain3 = self.project.newNmrChain(isConnected=False)
        nmrResidues3 = []
        for residueType in ('ILE',):
            nmrResidues3.append(nmrChain3.fetchNmrResidue(residueType=residueType))
        nmrChain3.mainNmrResidues = nmrResidues3

        nmrChain4 = self.project.newNmrChain(isConnected=False)
        nmrResidues4 = []
        for residueType in ('MET',):
            nmrResidues4.append(nmrChain4.fetchNmrResidue(residueType=residueType))
        nmrChain4.mainNmrResidues = nmrResidues4

        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])

        self.assertEqual([x.id for x in nmrChain2.mainNmrResidues],
                         ['#3.@7.VAL', '#3.@8.SER', '#3.@9.', '#3.@10.ILE'])

        self.assertEqual([x.id for x in nmrChain3.mainNmrResidues],
                         ['@4.@11.ILE', ])

        self.assertEqual([x.id for x in nmrChain4.mainNmrResidues],
                         ['@5.@12.MET', ])

        # add a connected stretch to the right
        nmrChain.nmrResidues[-1].connectNext(nmrChain2.nmrResidues[0])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA', '#2.@7.VAL', '#2.@8.SER', '#2.@9.', '#2.@10.ILE'])

        self.assertEqual(nmrChain2.isDeleted, True)
        self.assertEqual(self.project.getNmrChain('#3'), None)
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain2.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('#3').nmrResidues, nmrResidues2)

        # add an unconnected stretch to the right
        nmrChain.nmrResidues[-1].connectNext(nmrChain3.nmrResidues[0])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA', '#2.@11.ILE'])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)

        # add an unconnected-connected stretch to the right
        nmrChain3.nmrResidues[-1].connectNext(nmrChain.nmrResidues[0])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@11.ILE', '#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)

        # add an unconnected-unconnected stretch to the right
        nmrChain3.nmrResidues[-1].connectNext(nmrChain4.nmrResidues[0])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.assertEqual(nmrChain4.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@5').nmrResidues, [])
        self.assertEqual(self.project.getNmrChain('#6').nmrResidues, nmrResidues3 + nmrResidues4)

        self.undo.undo()
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)
        self.assertEqual(nmrChain4.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@5').nmrResidues, nmrResidues4)

        # add a connected stretch to the left
        nmrChain.nmrResidues[0].connectPrevious(nmrChain2.nmrResidues[-1])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@7.VAL', '#2.@8.SER', '#2.@9.', '#2.@10.ILE', '#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])

        self.assertEqual(nmrChain2.isDeleted, True)
        self.assertEqual(self.project.getNmrChain('#3'), None)
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain2.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('#3').nmrResidues, nmrResidues2)

        # add an unconnected stretch to the left
        nmrChain.nmrResidues[0].connectPrevious(nmrChain3.nmrResidues[-1])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@11.ILE', '#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)

        # add an connected-unconnected stretch to the left
        nmrChain3.nmrResidues[0].connectPrevious(nmrChain.nmrResidues[-1])
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA', '#2.@11.ILE'])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.undo.undo()
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE', '#2.@6.ALA'])
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)

        # add an unconnected-unconnected stretch to the left
        nmrChain4.nmrResidues[0].connectPrevious(nmrChain3.nmrResidues[-1])

        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, [])
        self.assertEqual(nmrChain4.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@5').nmrResidues, [])
        self.assertEqual(self.project.getNmrChain('#7').nmrResidues, nmrResidues3 + nmrResidues4)

        self.undo.undo()
        self.assertEqual(nmrChain3.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@4').nmrResidues, nmrResidues3)
        self.assertEqual(nmrChain4.isDeleted, False)
        self.assertEqual(self.project.getNmrChain('@5').nmrResidues, nmrResidues4)

        return

        nmrResidues[1].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])

    def test_disconnect_midchain_1(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        nmrResidues[1].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])

    def test_disconnect_midchain_2(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        nmrResidues[2].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.SER', '#3.@4.', '#3.@5.ILE'])

    def test_disconnect_midchain_3(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        nmrResidues[3].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '@-.@4.', '@-.@5.ILE'])

    def test_disconnect_midchain_4(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        nmrResidues[2].disconnectNext()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#3.@4.', '#3.@5.ILE'])

    def test_disconnect_midchain_5(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'SER', None, 'ILE'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        nmrResidues[2].disconnectPrevious()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#3.@1.ALA', '#3.@2.VAL', '#2.@3.SER', '#2.@4.', '#2.@5.ILE'])

    def test_disconnect_nmr_residues_2(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))

        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.GLY', '#2.@4.CYS', '#2.@5.GLN', ])

        nmrResidues[3].disconnectPrevious()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#3.@1.ALA', '#3.@2.VAL', '#3.@3.GLY', '#2.@4.CYS', '#2.@5.GLN', ])

    def test_disconnect_nmr_residues_3(self):
        nmrChain0 = self.project.fetchNmrChain(shortName='@-')
        nmrChain = self.project.newNmrChain(isConnected=True)
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain0.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN', ])

        nmrChain.mainNmrResidues = nmrResidues
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.GLY', '#2.@4.CYS', '#2.@5.GLN', ])

        nmrResidues[-1].disconnectNext()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.GLY', '#2.@4.CYS', '#2.@5.GLN', ])

        nmrResidues[-1].disconnectPrevious()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '#2.@3.GLY', '#2.@4.CYS', '@-.@5.GLN'])

        nmrResidues[2].disconnect()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN'])

        nmrResidues[1].disconnectPrevious()
        self.undo.undo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['#2.@1.ALA', '#2.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN'])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues],
                         ['@-.@1.ALA', '@-.@2.VAL', '@-.@3.GLY', '@-.@4.CYS', '@-.@5.GLN'])
        self.assertEqual([x.id for x in self.project.nmrChains], ['@-'])

    def test_disconnect_nmr_residue_triplet(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        nmrResidues = []
        for residueType in ('TRP', 'THR', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in sorted(nmrChain.mainNmrResidues)],
                         ['@-.@1.TRP', '@-.@2.THR', '@-.@3.', ])

        nmrChain2 = self.project.newNmrChain(isConnected=True)
        nmrChain2.mainNmrResidues = reversed(nmrResidues)
        self.assertEqual([x.id for x in sorted(nmrChain2.nmrResidues)],
                         ['#2.@3.', '#2.@2.THR', '#2.@1.TRP', ])

        nmrChain2.mainNmrResidues[1].disconnect()
        self.undo.undo()
        self.assertEqual([x.id for x in sorted(nmrChain2.nmrResidues)],
                         ['#2.@3.', '#2.@2.THR', '#2.@1.TRP', ])
        self.undo.redo()
        self.assertEqual([x.id for x in nmrChain.nmrResidues],
                         ['@-.@1.TRP', '@-.@2.THR', '@-.@3.', ])

    def test_disconnect_nmr_residue_triplet2(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        nmrResidues = []
        for residueType in ('TRP', 'THR', None):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in nmrChain.mainNmrResidues],
                         ['@-.@1.TRP', '@-.@2.THR', '@-.@3.', ])

        nmrChain2 = self.project.newNmrChain(isConnected=True)
        nmrChain2.mainNmrResidues = reversed(nmrResidues)
        self.assertEqual([x.id for x in sorted(nmrChain2.nmrResidues)],
                         ['#2.@3.', '#2.@2.THR', '#2.@1.TRP', ])

        nmrChain2.mainNmrResidues[1].moveToNmrChain(nmrChain)
        self.undo.undo()
        self.assertEqual([x.id for x in sorted(nmrChain2.nmrResidues)],
                         ['#2.@3.', '#2.@2.THR', '#2.@1.TRP', ])
        self.undo.redo()
        self.assertEqual([x.id for x in sorted(nmrChain.nmrResidues)],
                         ['@-.@1.TRP', '@-.@2.THR', '@-.@3.', ])

    def test_assigning_connected_stretch(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        residues = self.chain.residues
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        #
        # self.assertRaises(ValueError,  nmrResidues[1].assignTo, chainCode=nmrChain.shortName,
        #                   sequenceCode=nmrResidues[2])

        # nmrResidues[0].residue = residues[5]
        nmrChain.assignSingleResidue(nmrResidues[0], residues[5])

        self.assertRaises(ValueError, nmrChain.assignConnectedResidues, residues[3])

        self.assertRaises(ValueError, nmrChain.assignConnectedResidues, residues[-2])

        nmrChain.assignConnectedResidues(residues[1])
        assignedNmrChain = self.project.getByPid('NC:X')

        mergedResidue = nmrResidues[1].assignTo(chainCode=residues[2].chain.shortName,
                                                sequenceCode=residues[2].sequenceCode,
                                                mergeToExisting=True)
        self.assertIs(mergedResidue, nmrResidues[2])

        self.undo.undo()  # undo - assignTo

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.2.TRP', 'X.3.GLU', 'X.4.ARG', 'X.5.THR', 'X.6.TYR', ])

        self.undo.undo()  # undo - assignConnectedResidues

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.6.TYR', ])
        self.assertEqual([x.id for x in self.project.getByPid('NC:#2').nmrResidues],
                         ['#2.@2.VAL', '#2.@3.GLY', '#2.@4.CYS', '#2.@5.GLN', ])

        self.undo.redo()

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.2.TRP', 'X.3.GLU', 'X.4.ARG', 'X.5.THR', 'X.6.TYR', ])

    def test_assigning_unConnectedToAssigned(self):
        nmrChain = self.project.newNmrChain(isConnected=True)
        residues = self.chain.residues
        nmrResidues = []
        for residueType in ('ALA', 'VAL', 'GLY', 'CYS', 'GLN'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))

        nmrChain.assignConnectedResidues(residues[3])
        assignedNmrChain = self.project.getByPid('NC:X')

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO', ])

        self.undo.undo()  # undo - assignConnectedResidues
        self.undo.redo()

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO', ])

        # a new short chain
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        nmrResidues = []
        for residueType in ('ALA', 'VAL'):
            nmrResidues.append(nmrChain.fetchNmrResidue(residueType=residueType))
        self.assertEqual([x.id for x in nmrChain.nmrResidues],
                         ['@-.@6.ALA', '@-.@7.VAL'])

        nmrResidues[0].connectPrevious(nmrResidues[1])
        self.undo.undo()
        self.undo.redo()
        self.assertEqual([x.id for x in nmrResidues[0].nmrChain.mainNmrResidues],
                         ['#4.@7.VAL', '#4.@6.ALA'])

        singleNmrResidue = nmrChain.fetchNmrResidue(residueType='THR')

        # attach single to the end
        singleNmrResidue.nmrChain.assignSingleResidue(singleNmrResidue, residues[8])

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO', 'X.9.ALA'])

        self.undo.undo()
        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])

        # attach single to the start
        singleNmrResidue.nmrChain.assignSingleResidue(singleNmrResidue, residues[2])

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.3.GLU', 'X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])

        self.undo.undo()
        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])

        # attach nmrChain to the end
        nmrChain4 = self.project.getByPid('NC:#4')
        self.assertRaises(ValueError, singleNmrResidue.nmrChain.assignConnectedResidues, residues[8])

        nmrChain4.assignConnectedResidues(residues[8])

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO', 'X.9.ALA', 'X.10.SER'])

        self.undo.undo()
        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])

        nmrChain4.assignConnectedResidues(residues[1])

        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.2.TRP', 'X.3.GLU', 'X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])

        self.undo.undo()
        self.assertEqual([x.id for x in self.project.getByPid('NC:X').nmrResidues],
                         ['X.4.ARG', 'X.5.THR', 'X.6.TYR', 'X.7.ILE', 'X.8.PRO'])


class NmrResidueTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse2c'

    def test_reassign_attributes(self):
        nchain = self.project.getByPid('NC:A')
        nchain0 = self.project.getByPid('NC:@-')

        nr1, nr2 = sorted(nchain.nmrResidues)[8:10]
        res1 = nr1.residue
        res2 = nr2.residue
        res3 = sorted(self.project.chains[0].residues)[2]
        nr3 = res3.nmrResidue

        # nr2.residue = None
        nr2.deassign()

        # self.assertEqual(nr2.longPid, "NmrResidue:A.@2.ARG")
        self.assertEqual(nr2.longPid, "NmrResidue:A.@2.")

        target = self.project.getByPid('NR:A.2.LYS')
        target.rename('.LYS')
        self.assertEqual(target.longPid, "NmrResidue:A.@11.LYS")
        newNr = nchain0.newNmrResidue()
        self.assertEqual(newNr.longPid, "NmrResidue:@-.@89.")
        nr3.moveToNmrChain(nchain0)
        self.assertEqual(nr3.longPid, "NmrResidue:@-.3.GLU")

        # newNr.residue = res3
        nchain0.assignSingleResidue(newNr, res3)

        self.assertEqual(newNr.longPid, "NmrResidue:A.3.GLU")
        nchain.rename('X')
        self.assertEqual(nchain.longPid, "NmrChain:X")
        self.assertEqual(nr2.longPid, "NmrResidue:X.@2.")

        newNr.rename(None)
        self.assertEqual(newNr.longPid, "NmrResidue:X.@89.")
        self.undo.undo()
        self.assertEqual(newNr.longPid, "NmrResidue:X.3.GLU")
        self.undo.redo()
        self.assertEqual(newNr.longPid, "NmrResidue:X.@89.")

    def test_rename(self):
        nchain = self.project.getByPid('NC:A')
        nr1, nr2 = sorted(nchain.nmrResidues)[8:10]
        self.assertEqual(nr1.id, "A.10.TYR")
        nr1.deassign()
        self.assertEqual(nr1.id, "A.@1.")
        nr1.rename('999')
        self.assertEqual(nr1.id, "A.999.")
        nr1.rename('999.ALA')
        self.assertEqual(nr1.id, "A.999.ALA")
        nr1.rename('998.VAL')
        self.assertEqual(nr1.id, "A.998.VAL")
        nr1.rename('.TYR')
        self.assertEqual(nr1.id, "A.@1.TYR")
        nr1.rename('997')
        nr1.moveToNmrChain()
        # Undo and redo all operations
        self.undo.undo()
        self.undo.undo()
        self.assertEqual(nr1.id, "A.@1.TYR")
        self.undo.redo()
        self.undo.redo()
        self.assertEqual(nr1.id, "@-.997.")

    def test_reassign(self):
        nchain = self.project.getByPid('NC:A')
        nr1, nr2 = sorted(nchain.nmrResidues)[8:10]
        self.assertEqual(nr1.id, "A.10.TYR")
        nr1 = nr1.assignTo(chainCode='A', sequenceCode=999)
        self.assertEqual(nr1.id, "A.999.TYR")
        nr1 = nr1.assignTo()
        # This is a no-op
        self.assertEqual(nr1.id, "A.999.TYR")

        # TODO:ED this does not raise an error now!
        # with self.assertRaises(ValueError):
        #   nr2 = nr2.assignTo(sequenceCode=15)

        nr2 = nr2.assignTo(sequenceCode=515, residueType='XXX')
        self.assertEqual(nr2.id, 'A.515.XXX')
        obj = nchain.newNmrResidue(sequenceCode=777)
        self.assertEqual(obj.id, 'A.777.')

        self.assertTrue(len(nr1.nmrAtoms) == 2)

        # self.assertRaises(ValueError,  nr2.assignTo, chainCode=nr1.nmrChain.shortName,
        #                   sequenceCode=nr1.sequenceCode, residueType=nr1.residueType,)
        # with self.assertRaises(ValueError):
        # nr2 = nr2.assignTo(chainCode=nr1.nmrChain.shortName,
        #                   sequenceCode=nr1.sequenceCode, residueType=nr1.residueType)

        nrx = nr2.assignTo(chainCode=nr1.nmrChain.shortName, sequenceCode=nr1.sequenceCode,
                           residueType=nr1.residueType, mergeToExisting=True)
        # NB merging is not undoable
        # self.assertEqual(len(self.undo), 0)
        # self.assertEqual(len(self.undo.waypoints), 0)
        self.assertEqual(nr2.id, 'A.515.XXX-Deleted')
        self.assertIs(nrx, nr1)
        self.assertTrue(len(nr1.nmrAtoms) == 4)

    def test_fetchNmrResidue(self):
        nmrChain = self.project.fetchNmrChain()
        res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
        res2 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
        self.assertIs(res1, res2)
        obj = nmrChain.fetchNmrResidue(sequenceCode=515)
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertEqual(obj.pid, 'NR:@%s.515.' % nmrChain._wrappedData.serial)

    def test_fetchEmptyNmrResidue(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        res1 = nmrChain.fetchNmrResidue(sequenceCode=None, residueType="ALA")
        sequenceCode = '@%s' % res1._wrappedData.serial
        self.assertEqual(res1.sequenceCode, sequenceCode)
        res2 = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode)
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertIs(res1, res2)

    def test_offsetNmrResidue(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
        res1 = nmrChain.fetchNmrResidue(sequenceCode="127B", residueType="ALA")
        res2 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", residueType="ALA")
        self.assertIs(res2._wrappedData.mainResonanceGroup, res1._wrappedData)
        res3 = nmrChain.fetchNmrResidue(sequenceCode="127B-1", residueType="ALA")
        self.assertIs(res2, res3)

        self.assertIs(res2.mainNmrResidue, res1)
        self.assertEqual(res1.offsetNmrResidues, (res2,))
        self.assertIs(res1.getOffsetNmrResidue(-1), res2)
        self.assertIsNone(res2.getOffsetNmrResidue(1))

        res1.delete()

        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertIsNone(res2._wrappedData)

    def test_get_by_serialName(self):
        nmrChain = self.project.fetchNmrChain(shortName='@-')
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
