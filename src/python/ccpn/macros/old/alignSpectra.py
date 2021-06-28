"""This macro takes two HSQC spectra in current.strip, peak picks them, calculates the shift difference 
between them using a Gaussian KDE and uses the different to overlay the two spectra.""" 

# Get hold of current.strip
strip = current.strip

# Define the querySpectrum as the second spectrum in the 
# strip using the spectra attribute of the Strip class
querySpectrum = strip.spectra[0]

# Define the refSpectrum as the first spectrum in the 
# strip using the spectra attribute of the Strip class
refSpectrum = strip.spectra[1]

# Define the peak picking ranges for the two dimensions
hRange = [6.2, 14.0] # list for 1H picking range
nRange = [100.0, 133.0] # list for 15N picking range

# Put the lists into one combined list for the peak picker
regionToPick = [hRange, nRange]

# Get hold of the first peakLists in the two spectra
queryPeakList = querySpectrum.peakLists[0]
refPeakList = refSpectrum.peakLists[0]

# Peak pick both spectra using positive contours only
# queryPeakList.pickPeaksNd(regionToPick, doNeg=False)
# refPeakList.pickPeaksNd(regionToPick, doNeg=False)

queryAxisCodeDict = dict((code, regionToPick[ii]) for ii, code in enumerate(queryPeakList.spectrum.axisCodes))
# # queryPeakList.pickPeaksRegion(queryAxisCodeDict, doNeg=False)
# NOTE:ED - this should be the new call
querySpectrum.pickPeaks(queryPeakList,
                        querySpectrum.positiveContourBase,
                        None, **queryAxisCodeDict)

# refAxisCodeDict = dict((code,
#                           reorder(regionToPick, refSpectrum.axisCodes, axisOrder)[ii])
#                          for ii, code in enumerate(refPeakList.spectrum.axisCodes))
# # refPeakList.pickPeaksRegion(refAxisCodeDict, doNeg=False)

refAxisCodeDict = dict((code, regionToPick[ii]) for ii, code in enumerate(refPeakList.spectrum.axisCodes))
# # refPeakList.pickPeaksRegion(refAxisCodeDict, doNeg=False)
# NOTE:ED - this should be the new call
refSpectrum.pickPeaks(refPeakList,
                        refSpectrum.positiveContourBase,
                        None, **refAxisCodeDict)

# Create numpy arrays containing the peak positions of 
# each peakList
import numpy as np

refPeakPositions = np.array([peak.position for peak in 
                              refPeakList.peaks])

queryPeakPositions = np.array([peak.position for peak in queryPeakList.peaks])

# Align the two numpy arrays by centre of mass
refMean = np.mean(refPeakPositions, axis=0)
queryMean = np.mean(queryPeakPositions, axis=0)
roughShift = queryMean - refMean
shiftedQueryPeakPositions = queryPeakPositions - roughShift


# Define a log-likelihood target for fitting the query 
# peak positions
from scipy.optimize import leastsq
from scipy.stats import gaussian_kde

def negLogLikelihood(deltas, queryPeakPositions, kde):
  shifted = queryPeakPositions - deltas
  return -kde.logpdf(shifted.T)

# Create the Gaussian KDE
kde = gaussian_kde(refPeakPositions.T, bw_method=0.1)

# Get hold of the values to overlay the two spectra
shifts, status = leastsq(negLogLikelihood, roughShift,
                          args=(queryPeakPositions, kde))

# Get hold of the reference values of the querySpectrum 
queryRefValues = queryPeakList.spectrum.referenceValues

# Calculate the corrected reference values 
correctedValues = np.array(queryRefValues) - shifts

# Set the querySpectrum reference values to the corrected 
# reference values to overlay the spectra.
queryPeakList.spectrum.referenceValues = correctedValues
