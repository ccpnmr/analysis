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
__version__ = "$Revision: 3.0.b3 $"
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

  def test_newMultiplet(self):
    self.assertEqual(len(self.project.multiplets), 0)
    self.multipletList.newMultiplet()
    self.assertEqual(len(self.project.multipletLists), 1)
    self.assertEqual(len(self.project.multiplets), 1)

  def test_newMultiplet_goodPeaks(self):
    self.peakList = self.spectrum.newPeakList()
    pks = self.peakList.newPeak()

    self.assertEqual(len(self.project.multiplets), 0)
    mt = self.multipletList.newMultiplet(peaks=pks)
    self.assertEqual(len(self.project.multipletLists), 1)
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
    self.assertEqual(len(self.project.multipletLists), 1)
    self.assertEqual(len(self.project.multiplets), 1)
    self.assertEqual(len(mt.peaks), 3)

    pos = (0.45, 0.95, 1.6)
    mtPos = mt.position
    for ii in range(len(pos)):
      self.assertAlmostEqual(pos[ii], mtPos[ii])

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

