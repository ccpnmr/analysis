__author__ = 'simon1'


from ccpn.util import Io as ccpnIo

import unittest

import os

from ccpncore.util import Path
from ccpncore.lib.spectrum import Spectrum as libSpectrum

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
    self.assertEqual(a._apiResonance.isotopeCode, '15N')

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
    specLocation = Path.getDirectoryFromTop('data', 'testProjects', 'spectra', 'hsqc.spc')
    spectra = self.newProject.loadSpectrum(specLocation, subType='Azara')
    self.spectrum = spectra[0] if spectra else None

    c = self.newProject.newNmrChain()
    r = c.newNmrResidue()
    self.atom = r.newNmrAtom(isotopeCode='15N')
    # NBNB The first shiftList, called 'default' is created automatically
    self.shiftList = self.newProject.chemicalShiftLists[0]
    self.peakList = self.spectrum.newPeakList() if spectra else None

  def tearDown(self):
    self.newProject.delete()

  def test_assignDimension(self):
    peaks = self.peakList.findPeaksNd([[7.0, 111.75], [7.2, 112.2]], dataDims=self.spectrum._wrappedData.sortedDataDims())
    peaks[0].assignDimension(axisCode=libSpectrum.axisCodeMatch('N', self.spectrum.axisCodes),
                             value=self.atom)
    self.assertIsNotNone(self.shiftList.getChemicalShift(self.atom.id))

