for peak in current.peaks:
    peakPeakList = peak.peakList.pid
    for peakList in peak.spectrum.peakLists:
        if peakPeakList != peakList.pid:
            peak.copyTo(peakList)
            peak.delete()
