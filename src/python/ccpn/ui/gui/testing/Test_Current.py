"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from ccpn.framework import Current

# NBNB This should obviously use the proper objects.as
#  But since the code does not type check or go into the objects, this will do
#

def test_current_spectra():
  current = Current.Current(project='dummy')
  assert (not current.spectra)
  assert (current.spectrum is None)

  tt = (1,2,3)
  current.spectra = tt
  assert (current.spectra == tt)
  assert (current.spectrum == 3)

  def notifier(value, current=current):
    current.notifiedSpectra = tuple(value)
  current.registerNotify(notifier, 'spectra')

  try:
    current.addSpectrum(4)
    assert (current.spectrum == 4)
    assert (current.spectra == tt + (4,))
    assert (current.notifiedSpectra == tt + (4,))
  finally:
    current.unRegisterNotify(notifier, 'spectra')

  current.spectrum = 7
  assert (current.spectrum == 7)
  assert (current.spectra == (7,))
  assert (current.notifiedSpectra == tt + (4,))

  current.clearSpectra()
  assert (not current.spectra)
  assert (current.spectrum is None)

def test_current_peaks():
  current = Current.Current(project='dummy')
  assert (not current.peaks)
  assert (current.peak is None)

  tt = (9,8,5)
  current.peaks = tt
  assert (current.peaks == tt)
  assert (current.peak == 5)

  # def notifier(curr):
  #   curr.notifiedPeaks = curr.peaks
  # current.registerNotify(notifier, 'peaks')
  #
  # try:
  #   current.addPeak(47)
  #   assert (current.peak == 47)
  #   assert (current.peaks == tt + (47,))
  #   assert (current.notifiedPeaks == tt+ (47,))
  # finally:
  #   current.unRegisterNotify(notifier, 'peaks')

  current.peak = 27
  assert (current.peak == 27)
  assert (current.peaks == (27,))
  # assert (current.notifiedPeaks == tt + (11,))

  current.clearPeaks()
  assert (not current.peaks)
  assert (current.peak is None)




