__author__ = 'simon1'

from ccpn.core.testing.WrapperTesting import WrapperTesting

from ccpncore.lib.spectrum import Spectrum as libSpectrum


class Test_makeNmrAtom(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def test_createNmrAtom_withIsotopeCode(self):
    c = self.project.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(isotopeCode='15N')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(a._apiResonance.isotopeCode, '15N')

  def _test_createNmrAtom_withIsotopeCode(self):
    c = self.project.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(isotopeCode='15N')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(a.isotopeCode, '15N')

  def test_createNmrAtom_withName(self):
    c = self.project.newNmrChain()
    r = c.newNmrResidue()
    a = r.newNmrAtom(name='CA')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(a.name, 'CA')

  def test_fetchNmrAtom(self):
    c = self.project.newNmrChain()
    r = c.newNmrResidue()
    a = r.fetchNmrAtom(name='CB')
    # Undo and redo all operations
    self.undo.undo()
    self.undo.redo()
    self.assertEqual(a.name, 'CB')



# class Test_nmrAtoms(unittest.TestCase):
#
#   # Path of project to load (None for new project)
#   projectPath = None
#
#   def setUp(self):
#     WrapperTesting.setUp(self)
#     c = self.project.newNmrChain()
#     r = c.newNmrResidue()
#     self.atom = r.newNmrAtom(isotopeCode='15N')F
#     self.shiftList = self.project.newChemicalShiftList()
#
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


class Test_chemicalShift(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  def setUp(self):

    with self.initialSetup():
      spectra = self.loadData('spectra/hsqc.spc')
      self.spectrum = spectra[0] if spectra else None

      c = self.project.newNmrChain()
      r = c.newNmrResidue()
      self.atom = r.newNmrAtom(isotopeCode='15N')
      # NBNB The first shiftList, called 'default' is created automatically
      self.shiftList = self.project.chemicalShiftLists[0]
      self.peakList = self.spectrum.newPeakList() if spectra else None


  def test_assignDimension(self):
    peaks = self.peakList.pickPeaksNd([[7.0, 111.75], [7.2, 112.2]], dataDims=self.spectrum._wrappedData.sortedDataDims())
    peaks[0].assignDimension(axisCode=libSpectrum.axisCodeMatch('N', self.spectrum.axisCodes),
                             value=self.atom)
    # Undo and redo all operations
    self.assertIsNotNone(self.shiftList.getChemicalShift(self.atom.id))
    self.undo.undo()
    self.undo.redo()
    self.assertIsNotNone(self.shiftList.getChemicalShift(self.atom.id))

