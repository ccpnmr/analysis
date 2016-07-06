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

# class PeakListTest(WrapperTesting):
#
#   # Path of project to load (None for new project)
#   projectPath = 'CcpnCourse1b'
#
#   def test_newPeakList(self):
#     spectrum = self.project.getSpectrum('HSQC-115')
#     peakList = spectrum.newPeakList()
#     # Undo and redo all operations
#     self.undo.undo()
#     self.undo.redo()


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

