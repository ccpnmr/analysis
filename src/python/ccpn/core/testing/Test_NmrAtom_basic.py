__author__ = 'TJ Ragan'

import unittest

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError


class TestNmrAtomCreation(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.nmrChain = self.project.newNmrChain()
      self.nmrResidue = self.nmrChain.newNmrResidue()

  def tearDown(self):
    super().tearDown()
    self.assertEqual(self.nmrChain._wrappedData.__class__._notifies,
                     {'': [], '__init__': [], 'delete': [], 'undelete': [],
                      'setImplCode': []})
    self.assertEqual(self.nmrResidue._wrappedData.__class__._notifies,
                     {'': [], '__init__': [], 'delete': [], 'undelete': [],
                      'setDirectNmrChain': [], 'addResonance': [],
                      'setResonances': [],'setResidueType': [],'setAssignedResidue': [], 'setSequenceCode': []})

  def test_deassign(self):
    nmrAtom = self.nmrResidue.fetchNmrAtom(name='churl')
    self.assertEquals(nmrAtom.pid, 'NA:@2.@1..churl')
    nmrAtom.deassign()
    self.assertEquals(nmrAtom.pid, 'NA:@2.@1..C@1')


  def test_CreateAnonymousNmrAtomWithHIsotopeCode(self):
    a = self.nmrResidue.newNmrAtom(isotopeCode='1H')
    self.assertEqual(a.pid, 'NA:@2.@1..H@1')


  def test_CreateAnonymousNmrAtomWithCIsotopeCode(self):
    a = self.nmrResidue.newNmrAtom(isotopeCode='13C')
    self.assertEqual(a.pid, 'NA:@2.@1..C@1')

  def test_CreateAnonymousNmrAtomWithNIsotopeCode(self):
    a = self.nmrResidue.newNmrAtom(isotopeCode='15N')
    self.assertEqual(a.pid, 'NA:@2.@1..N@1')

  def test_CreateNmrAtomWithHName(self):
    a = self.nmrResidue.newNmrAtom(name='H')
    self.assertEqual(a.pid, 'NA:@2.@1..H')
    self.assertEqual(a.isotopeCode, '1H')

  def test_CreateNmrAtomWithDeuteriumName(self):
    a = self.nmrResidue.newNmrAtom(name='D')
    self.assertEqual(a.pid, 'NA:@2.@1..D')
    self.assertEqual(a.isotopeCode, '2H')

  def test_CreateNmrAtomWithTritiumName(self):
    a = self.nmrResidue.newNmrAtom(name='T')
    self.assertEqual(a.pid, 'NA:@2.@1..T')
    self.assertEqual(a.isotopeCode, '3H')

  def test_CreateNmrAtomWithCarbonName(self):
    a = self.nmrResidue.newNmrAtom(name='C')
    self.assertEqual(a.pid, 'NA:@2.@1..C')
    self.assertEqual(a.isotopeCode, '13C')

  def test_CreateNmrAtomWithNName(self):
    a = self.nmrResidue.newNmrAtom(name='N')
    self.assertEqual(a.pid, 'NA:@2.@1..N')
    self.assertEqual(a.isotopeCode, '15N')

  def test_CreateNmrAtomWithOxygenName(self):
    a = self.nmrResidue.newNmrAtom(name='O')
    self.assertEqual(a.pid, 'NA:@2.@1..O')
    self.assertEqual(a.isotopeCode, '17O')

  def test_CreateNmrAtomWithFluorineName(self):
    a = self.nmrResidue.newNmrAtom(name='F')
    self.assertEqual(a.pid, 'NA:@2.@1..F')
    self.assertEqual(a.isotopeCode, '19F')

  def test_CreateNmrAtomWithSiliconName(self):
    a = self.nmrResidue.newNmrAtom(name='Si')
    self.assertEqual(a.pid, 'NA:@2.@1..Si')
    self.assertEqual(a.isotopeCode, '29Si')

  def test_CreateNmrAtomWithPhosphorusName(self):
    a = self.nmrResidue.newNmrAtom(name='P')
    self.assertEqual(a.pid, 'NA:@2.@1..P')
    self.assertEqual(a.isotopeCode, '31P')

  def test_CreateNmrAtomWithBromineName(self):
    a = self.nmrResidue.newNmrAtom(name='Br')
    self.assertEqual(a.pid, 'NA:@2.@1..Br')
    self.assertEqual(a.isotopeCode, '79Br')

  def test_CreateNmrAtomWithArbitraryHydrogenName(self):
    a = self.nmrResidue.newNmrAtom(name='H_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..H_arbitrary')
    self.assertEqual(a.isotopeCode, '1H')

  def test_CreateNmrAtomWithArbitraryDeuteriumName(self):
    a = self.nmrResidue.newNmrAtom(name='D_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..D_arbitrary')
    self.assertEqual(a.isotopeCode, '2H')

  def test_CreateNmrAtomWithArbitraryTritiumName(self):
    a = self.nmrResidue.newNmrAtom(name='T_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..T_arbitrary')
    self.assertEqual(a.isotopeCode, '3H')

  def test_CreateNmrAtomWithArbitraryCarbonName(self):
    a = self.nmrResidue.newNmrAtom(name='C_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..C_arbitrary')
    self.assertEqual(a.isotopeCode, '13C')

  def test_CreateNmrAtomWithArbitraryNitrogenName(self):
    a = self.nmrResidue.newNmrAtom(name='N_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..N_arbitrary')
    self.assertEqual(a.isotopeCode, '15N')

  def test_CreateNmrAtomWithArbitraryOxygenName(self):
    a = self.nmrResidue.newNmrAtom(name='O_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..O_arbitrary')
    self.assertEqual(a.isotopeCode, '17O')

  def test_CreateNmrAtomWithArbitraryFluorineName(self):
    a = self.nmrResidue.newNmrAtom(name='F_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..F_arbitrary')
    self.assertEqual(a.isotopeCode, '19F')

  def test_CreateNmrAtomWithArbitrarySiliconName(self):
    a = self.nmrResidue.newNmrAtom(name='Si_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..Si_arbitrary')
    self.assertEqual(a.isotopeCode, '29Si')

  def test_CreateNmrAtomWithArbitraryPhosphorusName(self):
    a = self.nmrResidue.newNmrAtom(name='P_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..P_arbitrary')
    self.assertEqual(a.isotopeCode, '31P')

  def test_CreateNmrAtomWithArbitraryBromineName(self):
    a = self.nmrResidue.newNmrAtom(name='Br_arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..Br_arbitrary')
    self.assertEqual(a.isotopeCode, '79Br')

  def test_CreateNmrAtomWithArbitraryNameAndXenonIsotopeCode(self):
    a = self.nmrResidue.newNmrAtom(name='Arbitrary', isotopeCode='129Xe')
    self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')

  def test_CreateNmrAtomWithArbitraryName(self):
    a = self.nmrResidue.newNmrAtom(name='Arbitrary')
    self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')
    self.assertEqual(a.isotopeCode, '?')

  def test_CreateNmrAtomWithArbitraryDottedName(self):
    a = self.nmrResidue.newNmrAtom(name='Arbitrary.Name')
    self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary^Name')
    self.assertEqual(a.isotopeCode, '?')

  # NBNB LOOK AT ME! This now fails - hatted names cannot be set or created
  # @unittest.expectedFailure
  def test_CreateNmrAtomWithArbitraryHattedName(self):
    with self.assertRaises(ValueError):
      a = self.nmrResidue.newNmrAtom(name='Arbitrary^Name')
    # self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary^Name')
    # self.assertEqual(a.isotopeCode, 'unknown')

  # NBNB now obsolete
  # @unittest.expectedFailure
  # def test_CreateNmrAtomWithArbitraryDottedAndHattedNamesCollide(self):
  #   self.nmrResidue.newNmrAtom(name='Arbitrary^Name')
  #   self.assertRaises(Exception, self.nmrResidue.newNmrAtom, name='Arbitrary.Name')

  def test_CreateNmrAtomWithArbitraryNameAndArbitraryIsotopeCode(self):
    a = self.nmrResidue.newNmrAtom(name='Arbitrary', isotopeCode='Arbitrary_Isotope')
    self.assertEqual(a.pid, 'NA:@2.@1..Arbitrary')

  def test_CreateNmrAtomWithArbitraryIsotopeWithSpace(self):
    self.assertRaises(ApiError, self.nmrResidue.newNmrAtom,
                      name='Arbitrary', isotopeCode='Arbitrary Isotope')

  def test_CreateTwoAnonymousNmrAtomsWithNIsotopeCode(self):
    a1 = self.nmrResidue.newNmrAtom(isotopeCode='15N')
    a2 = self.nmrResidue.newNmrAtom(isotopeCode='15N')
    self.assertEqual(a1.pid, 'NA:@2.@1..N@1')
    self.assertEqual(a2.pid, 'NA:@2.@1..N@2')

  def test_CreateTwoAnonymousNmrAtomsWithDifferentIsotopeCodes(self):
    a1 = self.nmrResidue.newNmrAtom(isotopeCode='15N')
    a2 = self.nmrResidue.newNmrAtom(isotopeCode='1H')
    self.assertEqual(a1.pid, 'NA:@2.@1..N@1')
    self.assertEqual(a2.pid, 'NA:@2.@1..H@2')

  def test_CreateTwoNmrAtomsWithSameName(self):
    self.nmrResidue.newNmrAtom(name='H')
    self.assertRaises(ApiError, self.nmrResidue.newNmrAtom, name='H')

  def test_CreateNmrAtomByFetchingFromResidue(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])
    newNmrAtom = self.nmrResidue.fetchNmrAtom(name='H')
    self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..H')
    self.assertEqual(self.nmrResidue.nmrAtoms, [newNmrAtom])


  def test_CreateNmrAtomByProducingFromProjectByPid(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])

    newNmrAtom1 = self.project.produceNmrAtom(name='HX')
    newNmrAtom2 = self.project.produceNmrAtom(name='HX')

    self.assertEqual(newNmrAtom1.pid, 'NA:@-.@2..HX')
    self.assertEqual(newNmrAtom2.pid, 'NA:@-.@3..HX')

    self.assertEqual(self.project.nmrAtoms, [newNmrAtom1, newNmrAtom2])


  def test_CreateNmrAtomByProducingFromProjectWithParametersMismatchedType(self):
    self.assertRaises(ValueError, self.project.produceNmrAtom, '@2.@1.ARG.NE')


  def test_CreateNmrAtomByProducingFromProjectByPidWithChain(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])

    newNmrAtom = self.project.produceNmrAtom('@2.@1..NE')

    self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..NE')
    self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
    self.assertIs(self.nmrResidue, newNmrAtom.nmrResidue)
    self.assertEqual(self.project.nmrResidues, [self.nmrResidue])

  def test_CreateNmrAtomByProducingFromProjectByPidMismatchedType(self):
    self.assertRaises(ValueError, self.project.produceNmrAtom, '@2.@1.ARG.NE')


  def test_CreateNmrAtomByProducingFromProjectWithParameters(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])

    newNmrAtom = self.project.produceNmrAtom(chainCode='@2',
                                             sequenceCode='@1',
                                             name='NE')

    self.assertEqual(newNmrAtom.pid, 'NA:@2.@1..NE')
    self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
    self.assertIs(self.nmrResidue, newNmrAtom.nmrResidue)
    self.assertEqual(self.project.nmrResidues, [self.nmrResidue])


  def test_CreateNmrAtomAndNmrResidueByProducingFromProjectWithParameters(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])
    self.assertEqual(len(self.project.nmrResidues), 1)


    newNmrAtom = self.project.produceNmrAtom(chainCode='A',
                                             sequenceCode='11',
                                             name='NE')

    self.assertEqual(newNmrAtom.pid, 'NA:A.11..NE')
    self.assertEqual(self.project.nmrAtoms, [newNmrAtom])
    self.assertEqual(len(self.project.nmrResidues), 2)
    self.assertIn(newNmrAtom.nmrResidue, self.project.nmrResidues)


  def test_CreateNmrAtomByProducingFromProjectWithPid(self):
    self.assertEqual(self.nmrResidue.nmrAtoms, [])

    newNmrAtom = self.project.produceNmrAtom('NA:A.11.ARG.NE')

    self.assertEqual(newNmrAtom.pid, 'NA:A.11.ARG.NE')
    self.assertEqual(self.project.nmrAtoms, [newNmrAtom])


class TestNmrAtomProperties(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.nmrChain = self.project.newNmrChain()
      self.nmrResidue = self.nmrChain.newNmrResidue()
      self.nmrAtom = self.nmrResidue.newNmrAtom(isotopeCode='1H')

  def test_AnonoymousNmrAtom_id(self):
    self.assertEqual(self.nmrAtom.id,    '@2.@1..H@1')

  def test_AnonoymousNmrAtom_pid(self):
    self.assertEqual(self.nmrAtom.pid,    'NA:@2.@1..H@1')

  def test_AnonoymousNmrAtom_longPid(self):
    self.assertEqual(self.nmrAtom.longPid,    'NmrAtom:@2.@1..H@1')

  def test_AnonoymousNmrAtom_project(self):
    self.assertTrue(self.project is self.nmrAtom.project)

  def test_AnonoymousNmrAtom_nmrResidue(self):
    self.assertTrue(self.nmrResidue is self.nmrAtom.nmrResidue)

  @unittest.expectedFailure
  def test_AnonoymousNmrAtom_name(self):
    self.assertTrue('name' not in self.nmrAtom.keys())

  def _test_AnonoymousNmrAtom_apiResonance(self):
    print(self.nmrAtom.apiResonance)

  def _test_AnonoymousNmrAtom_atom(self):
    print(self.nmrAtom.atom)

  def _test_AnonoymousNmrAtom_assignedPeaks(self):
    self.assertEqual(self.nmrAtom.assignedPeaks, [[]])



class TestNmrAtomMethods(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.nmrChain = self.project.newNmrChain()
      self.nmrResidue = self.nmrChain.newNmrResidue()
      self.nmrAtom = self.nmrResidue.newNmrAtom(name='H')


  def test_NmrAtom_Get(self):
    self.assertEqual(self.nmrAtom.id, self.nmrAtom.id)

  def test_NmrAtom_GetByPid(self):
    atomPid = self.nmrAtom.pid
    self.assertTrue(self.nmrAtom is self.nmrAtom.getByPid(atomPid))
    self.assertTrue(self.nmrAtom is self.nmrResidue.getByPid(atomPid))
    self.assertTrue(self.nmrAtom is self.nmrChain.getByPid(atomPid))
    self.assertTrue(self.nmrAtom is self.project.getByPid(atomPid))


  def test_ReassignNmrAtomSequenceCode(self):
    self.assertEqual(len(self.project.nmrResidues), 1)

    atom1 = self.project.produceNmrAtom(name='HX')
    res1 = atom1.nmrResidue
    self.assertEqual(atom1.pid,'NA:@-.@2..HX')
    self.assertEqual(res1.pid, 'NR:@-.@2.')

    self.assertEqual(len(res1.nmrAtoms), 1)
    self.assertEqual(len(self.project.nmrResidues), 2)

    atom1 = atom1.assignTo(sequenceCode=101)

    self.assertEqual(atom1.pid,'NA:@-.101..HX')
    self.assertEqual(res1.pid, 'NR:@-.@2.')
    self.assertEqual(len(res1.nmrAtoms), 0)
    self.assertEqual(len(self.project.nmrResidues), 3)


  def test_ReassignNmrAtomName(self):
    self.assertEqual(len(self.project.nmrResidues), 1)

    atom1 = self.project.produceNmrAtom('X.101.VAL.N')
    res1 = atom1.nmrResidue
    self.assertEqual(atom1.pid,'NA:X.101.VAL.N')
    self.assertEqual(res1.pid, 'NR:X.101.VAL')

    self.assertEqual(len(res1.nmrAtoms), 1)
    self.assertEqual(len(self.project.nmrResidues), 2)

    atom1 = atom1.assignTo(name='NE')

    self.assertEqual(atom1.pid,'NA:X.101.VAL.NE')
    self.assertEqual(res1.pid, 'NR:X.101.VAL')
    self.assertEqual(len(res1.nmrAtoms), 1)
    self.assertEqual(len(self.project.nmrResidues), 2)


  @unittest.skip
  def test_RenameAtom(self):
    print(self.nmrAtom.id)
    self.nmrAtom.rename('N')
    print(self.nmrAtom.id)

  @unittest.skip
  def test_UpdateAtom(self):
    print(self.nmrAtom.update)

  @unittest.skip
  def test_PopAtom(self):
    print(self.nmrAtom.pop('id'))

  @unittest.skip
  def test_PopItemFromAtom(self):
    print(self.nmrAtom.popitem())

  @unittest.skip
  def test_SetDefault(self):
    print(self.nmrAtom.setdefault())

  @unittest.skip
  def test_ClearAtom(self):
    print(self.nmrAtom.clear())

  @unittest.skip
  def test_DeleteAtom(self):
    print(self.nmrAtom.delete())

  @unittest.skip
  def test_AtomItems(self):
    print(self.nmrAtom.items())

  @unittest.skip
  def test_AtomItems(self):
    print(self.nmrAtom.values())


class TestNmrAtomReceivedProperties(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.nmrChain = self.project.newNmrChain()
      self.nmrResidue = self.nmrChain.newNmrResidue()
      self.nmrAtom = self.nmrResidue.newNmrAtom(name='H')


  def test_ProjectName(self):
    self.assertEqual(self.nmrAtom.project.name, 'default')

  def test_NmrResiduePid(self):
    self.assertEqual(self.nmrAtom.nmrResidue.pid, 'NR:@2.@1.')

  def test_NmrResidueName(self):
    self.assertEqual(self.nmrAtom.nmrResidue.residueType, '')

  # @unittest.skip('ISSUE: Is there any way to pair Atom with NmrAtom other than by residue?')
  # sort-of, move to new residue and link that
  def test_AtomAtom(self):
    self.assertIsNone(self.nmrAtom.atom)
    ch = self.project.createChain(sequence = 'ag', molType='protein')
    self.nmrResidue.residue = ch.residues[1]
    self.assertEqual(self.nmrAtom.atom.pid, 'MA:A.2.GLY.H')

  def test_className(self):
    self.assertEqual(self.nmrAtom.className, 'NmrAtom')

  def test_ShortClassName(self):
    self.assertEqual(self.nmrAtom.shortClassName, 'NA')

  def test_AssignedPeaks(self):
    self.assertEqual(self.nmrAtom.assignedPeaks, [])


class TestAtomShifts(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.nmrChain = self.project.newNmrChain()
      self.nmrResidue = self.nmrChain.newNmrResidue()

  @unittest.skip('ISSUE: Must be able to create an empty spectrum to create peaks.')
  def test_GetShiftsFromNmrAtom(self):
    a = self.nmrResidue.newNmrAtom()
    print(a.shifts)

