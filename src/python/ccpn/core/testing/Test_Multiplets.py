"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:34 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from unittest import expectedFailure
from ccpn.framework import Framework
from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.memops.ApiError import ApiError
from ccpn.core.Peak import Peak
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Common import makeIterableList

#=========================================================================================
# MultipletTest_SetUp
#=========================================================================================

class MultipletTest_setUp(WrapperTesting):

  # Path of project to load (None for new project)
  projectPath = None

  #=========================================================================================
  # setUp       initialise a new project
  #=========================================================================================

  def setUp(self):
    """
    Create a valid spectrum and multipletList
    """
    with self.initialSetup():
      axisCodes = ('CO', 'Hn', 'Nh')
      self.spectrum = self.project.createDummySpectrum(axisCodes)
      self.multipletList = self.spectrum.newMultipletList()

      self.spectrum2 = self.project.createDummySpectrum(axisCodes)
      self.multipletList2 = self.spectrum.newMultipletList()

      self._multipletNotifier = Notifier(self.project,
                                        [Notifier.CREATE, Notifier.CHANGE, Notifier.DELETE],
                                        'Multiplet',
                                        self._multipletChange,
                                         onceOnly=True)

      # self._peakNotifier = Notifier(self.project,
      #                                   [Notifier.CREATE, Notifier.CHANGE, Notifier.DELETE],
      #                                   'Peak',
      #                                   self._peakChange)


  def test_newMultiplet(self):
    self.assertEqual(len(self.project.multiplets), 0)
    self.multipletList.newMultiplet()
    self.assertEqual(len(self.project.multipletLists), 2)
    self.assertEqual(len(self.project.multiplets), 1)

  def test_newMultiplet_goodPeaks(self):
    self.peakList = self.spectrum.newPeakList()
    pks = self.peakList.newPeak()

    self.assertEqual(len(self.project.multiplets), 0)
    mt = self.multipletList.newMultiplet(peaks=pks)
    self.assertEqual(len(self.project.multipletLists), 2)
    self.assertEqual(len(self.project.multiplets), 1)
    self.assertEqual(len(mt.peaks), 1)

    outPks = mt.peaks
    self.assertEqual(len(outPks), 1)
    self.assertEqual(pks, outPks[0])

  def test_newMultiplet_badPeaks(self):
    self.peakList = self.spectrum.newPeakList()
    pks = self.peakList.newPeak()

    self.assertEqual(len(self.project.multiplets), 0)
    with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
      mt = self.multipletList.newMultiplet(peaks=12)

  def test_newMultiplet_position(self):
    self.peakList = self.spectrum.newPeakList()
    pks = self.peakList.newPeak()
    pks.position = (0.1, 0.2, 0.5)
    pks = self.peakList.newPeak()
    pks.position = (0.3, 0.25, 1.0)
    pks = self.peakList.newPeak()
    pks.position = (0.05, 0.5, 0.1)

    allPks = self.peakList.peaks

    self.assertEqual(len(self.project.multiplets), 0)
    mt = self.multipletList.newMultiplet(peaks=allPks)

    # check that there are 2 lists from the setup
    self.assertEqual(len(self.project.multipletLists), 2)
    self.assertEqual(len(self.project.multiplets), 1)
    self.assertEqual(len(mt.peaks), 3)

    pks2 = self.peakList.newPeak()
    pks2.position = (0.1, 0.2, 0.5)
    pks2 = self.peakList.newPeak()
    pks2.position = (0.3, 0.25, 1.0)
    pks2 = self.peakList.newPeak()
    pks2.position = (0.05, 0.5, 0.1)

    pos = (0.45, 0.95, 1.6)
    mtPos = mt.position
    for ii in range(len(pos)):
      self.assertAlmostEqual(pos[ii], mtPos[ii])

    with self.assertRaisesRegex(TypeError, 'is not of type Peak'):
      mt.removePeaks('notPeak')
    with self.assertRaisesRegex(ValueError, 'does not belong to multiplet'):
      mt.removePeaks(pks2)

    print ('>>>preAddPeaks')
    morePeaks = self.peakList.peaks[3:]
    mt.addPeaks(morePeaks)
    self.assertEqual(len(mt.peaks), 6)
    self.undo.undo()
    self.assertEqual(len(mt.peaks), 3)
    self.undo.redo()
    self.assertEqual(len(mt.peaks), 6)

    # create another spectrum with a new peak
    self.peakList2 = self.spectrum2.newPeakList()
    pks3 = self.peakList2.newPeak()

    # check the new peak cannot be added to the first multiplet
    with self.assertRaisesRegex(ValueError, 'does not belong to spectrum'):
      mt.addPeaks(pks3)

    # check that changing the position of a peak notifies the multiplet
    print ('>>>prePositionChange')
    morePeaks[0].position = (0.0, 0.0, 0.0)
    print('>>>postPositionChange')
    morePeaks[0].lineWidths = (0.0, 0.0, 0.0)
    print('>>>postLineWidthChange')

  def _multipletChange(self, data):
    print ('>>>multipletNotifier', data[Notifier.OBJECT], data[Notifier.TRIGGER])

  def _peakChange(self, data):
    print ('>>>peakNotifier', data[Notifier.OBJECT], data[Notifier.TRIGGER])

#=========================================================================================
# MultipletTest_No_setUp
#=========================================================================================

class MultipletTest_No_setUp(WrapperTesting):

  #=========================================================================================
  # test_newMultipelt            functions to create new Multiplets
  #=========================================================================================

  def test_newMultiplet(self):
    """
    Test that creating a new Multiplet with no parameter creates a valid Multiplet.
    """
    axisCodes = ('CO', 'Hn', 'Nh')
    self.spectrum = self.project.createDummySpectrum(axisCodes)
    self.multipletList = self.spectrum.newMultipletList()

