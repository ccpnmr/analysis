__author__ = 'simon1'


from ccpn.util import Io as ccpnIo

import unittest

from unittest.mock import Mock, MagicMock

class Test_makeNmrAtom(unittest.TestCase):

  def setUp(self):
    # pass
    self.newProject = ccpnIo.newProject('testProject')
    self.assertEqual(self.newProject.name, 'testProject')

  def test_createNmrAtom_withIsotopeCode(self):
    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(isotopeCode='15N')
    self.assertEqual(a.apiResonance.isotopeCode, '15N')

  def _test_createNmrAtom_withIsotopeCode(self):
    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(isotopeCode='15N')
    self.assertEqual(a.isotopeCode, '15N')

  def test_createNmrAtom_withName(self):
    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(name='CA')
    self.assertEqual(a.name, 'CA')

  def test_fetchNmrAtom(self):
    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    a = r.fetchNmrAtom(name='CB')
    self.assertEqual(a.name, 'CB')



# class Test_nmrAtoms(unittest.TestCase):
#
#   def setUp(self):
#     self.newProject = ccpnIo.newProject('testProject')
#     c = self.newProject.newNmrChain()
#     r = c.newNmrResidue()
#     self.atom = r.newNmrAtom(isotopeCode='15N')
#     self.shiftList = self.newProject.newChemicalShiftList()
#
#   def tearDown(self):
#     self.newProject.delete()
#
#   def _test_getChemicalShift(self):
#
#     shift = self.shiftList.findChemicalShift(self.atom)
#     self.assertIsNotNone(shift)
#
#   def test_setChemicalShift(self):
#
#     shift = self.shiftList.newChemicalShift(value=55, nmrAtom=self.atom)
#     self.assertEqual(shift.value, 55)


class Test_chemicalShift(unittest.TestCase):

  def setUp(self):
    self.newProject = ccpnIo.newProject('testProject')
    self.spectrum = self.newProject.loadSpectrum('/Users/simon1/PycharmProjects/CCPN_V3/trunk/ccpnv3/data/testProjects/spectra/115.spc', subType='Azara')

    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    self.atom = r.newNmrAtom(isotopeCode='15N')
    self.shiftList = self.newProject.newChemicalShiftList()
    self.peakList = self.spectrum[0].newPeakList()

  def tearDown(self):
    self.newProject.delete()

  def test_assignDimension(self):
    peaks = self.peakList.findPeaksNd([[7.0, 111.75], [7.2, 112.2]], dataDims=self.spectrum[0]._wrappedData.sortedDataDims())
    peaks[0].assignDimension(axisCode='N', value=self.atom)
    self.assertIsNotNone(self.shiftList.findChemicalShift(self.atom))

