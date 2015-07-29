"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from ccpnmrcore import Current

# NBNB This should obviously use teh proper objects.as
#  But since the code does tno type check or go into te objects, this will do
#

def test_current_spectra():
  current = Current.Current(project='dummy')
  assert (not current.spectra)
  assert (current.spectrum is None)

  ll = [1,2,3]
  current.spectra = ll
  assert (current.spectra == ll)
  assert (current.spectrum == 3)

  def notifier(curr, spectra):
    curr.notifiedSpectra = spectra

  Current.Current.notifySpectra = notifier
  current.registerNotify(current.notifySpectra, 'spectra')


  current.addSpectrum(4)
  print("@~@~", dir(Current.Current))
  print("@~@~2", dir(current))
  assert (current.spectrum == 4)
  assert (current.spectra == ll + [4])
  assert (current.notifiedSpectra == ll + [4])
  current.unRegisterNotify(current.notifySpectra, 'spectra')

  current.spectrum = 7
  assert (current.spectrum == 7)
  assert (current.spectra == [7])
  assert (current.notifiedSpectra == ll + [4])

  current.clearSpectra()
  assert (not current.spectra)
  assert (current.spectrum is None)

def test_current_peaks():
  current = Current.Current(project='dummy')
  assert (not current.peaks)
  assert (current.peak is None)

  ll = [9,8,5]
  current.peaks = ll
  assert (current.peaks == ll)
  assert (current.peak == 5)

  def notifier(curr, peaks):
    curr.notifiedPeaks = peaks

  Current.Current.notifyPeaks = notifier
  current.registerNotify(current.notifyPeaks, 'peaks')

  current.addPeak(11)
  print("@~@~", dir(Current.Current))
  print("@~@~2", dir(current))
  assert (current.peak == 11)
  assert (current.peaks == ll + [11])
  assert (current.notifiedPeaks == ll+ [11])
  current.unRegisterNotify(current.notifyPeaks, 'peaks')

  current.peak = 27
  assert (current.peak == 27)
  assert (current.peaks == [27])
  assert (current.notifiedPeaks == ll+ [11])

  current.clearPeaks()
  assert (not current.peaks)
  assert (current.peak is None)




