"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
from ccpn.core.testing.WrapperTesting import WrapperTesting


# Properly done version of above
class PeakListCreationTest(WrapperTesting):
  def setUp(self):
    with self.initialSetup():
      self.spectrum = self.project.createDummySpectrum('H')


  def test_newPeakList(self):
    self.assertEqual(len(self.spectrum.peakLists), 1)

    peakList = self.spectrum.newPeakList()

    self.assertEqual(len(self.spectrum.peakLists), 2)
    self.assertEqual(peakList.className, 'PeakList')
    self.assertIs(self.spectrum.peakLists[1], peakList)


  def test_newPeakList_UndoRedo(self):
    peakList = self.spectrum.newPeakList()

    self.assertEqual(len(self.spectrum.peakLists), 2)
    self.undo.undo()
    self.assertEqual(len(self.spectrum.peakLists), 1)

    self.undo.redo()
    self.assertEqual(len(self.spectrum.peakLists), 2)
    self.assertIs(self.spectrum.peakLists[1], peakList)


class PeakListTest2(WrapperTesting):
  # Path of project to load (None for new project
  projectPath = 'CCPN_H1GI_clean_extended.nef'

  singleValueTags = ['isSimulated', 'symbolColour', 'symbolStyle', 'textColour', 'textColour',
                     'title']

  def test_PeakList_copy(self):
    peakList = self.project.getPeakList('3dNOESY-182.3')
    spectrum = peakList.spectrum
    peakList2 = peakList.copyTo(spectrum)

    self.assertEquals(peakList2.serial, 4)
    self.assertEquals(peakList2.comment,
"""Copy of PeakList:3dNOESY-182.3
ARIA2_NOE_Peaks_run1_it8_auto1195328348.86|6|1|2"""
                      )

    for tag in self.singleValueTags:
      self.assertEquals((tag, getattr(peakList, tag)), (tag, getattr(peakList2, tag)))

  def test_PeakList_copy_keyparameters(self):
    peakList = self.project.getPeakList('3dNOESY-182.3')
    spectrum = peakList.spectrum

    params = {
      'title':'ATITLE',
      'comment':'ACOMMENT',
      'symbolStyle':'+',
      'symbolColour':'RED',
      'textColour':'dish',
      'isSimulated':True,
    }
    peakList2 = peakList.copyTo(spectrum, **params)

    self.assertEquals(peakList2.serial, 4)
    self.assertEquals(peakList2.comment, 'ACOMMENT')

    for tag, val in params.items():
      self.assertEquals(val, getattr(peakList2, tag))

  def test_PeakList_copy_exo(self):
    peakList = self.project.getPeakList('3dNOESY-182.3')
    spectrum = self.project.getSpectrum('3dTOCSY-181')
    peakList2 = peakList.copyTo(spectrum)

    self.assertIs(peakList2._parent, spectrum)

    self.assertEquals(peakList2.serial, 2)
    self.assertEquals(peakList2.comment,
"""Copy of PeakList:3dNOESY-182.3
ARIA2_NOE_Peaks_run1_it8_auto1195328348.86|6|1|2"""
                      )

    for tag in self.singleValueTags:
      self.assertEquals((tag, getattr(peakList, tag)), (tag, getattr(peakList2, tag)))




