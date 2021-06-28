"""This macro takes an HSQC spectrum and peak picks it within a specified range."""

# Use the getByPid() method of the project class to get
# hold of the spectrum object
hsqcSpectrum = project.getByPid('SP:hsqc')

# Get hold of the first peaklist in the HSQC spectrum
peakList = hsqcSpectrum.peakLists[0]

# Define the peak picking ranges for the two dimensions
hRange = [5.5, 10.0] # list for 1H picking range
nRange = [100.0, 133.0] # list for 15N picking range

# Put the lists into one combined list for the peak picker
regionToPick = [hRange, nRange]

# Pick the peaks using only positive contours
# peaks = peakList.pickPeaksNd(regionToPick, doPos=True, doNeg=False)

axisCodeDict = dict((code, regionToPick[ii]) for ii, code in enumerate(peakList.spectrum.axisCodes))

posThreshold = hsqcSpectrum.positiveContourBase
peaks = hsqcSpectrum.pickPeaks(peakList, posThreshold, None, **axisCodeDict)
