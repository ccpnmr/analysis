acceptedNOEpeakList =''
rejectedNOEpeakList = ''

def getRejectedPeakList(pkLists, accepted = True):
    for peakList in pkLists:
        if "accept" in peakList.comment.lower():
            if accepted == True:
                return peakList
        if 'reject' in peakList.comment.lower():
            if accepted == False:
                return peakList

for peak in current.peaks:
    if "reject" in peak.peakList.comment.lower():
        # print('rejected:', peak)
        #copy to accepted
        destinationNOEpeakList = getRejectedPeakList(peak.spectrum.peakLists, accepted = True)
        if destinationNOEpeakList == '':
            print(peak, 'has no associated peaklist with "rejected" comment')
            continue


    if 'accept' in peak.peakList.comment.lower():
        # print('reject:' , peak)
        #copy to rejected
        destinationNOEpeakList = getRejectedPeakList(peak.spectrum.peakLists, accepted = False)
        if destinationNOEpeakList == '':
            print(peak, 'has no associated peaklist with "accepted" comment')
            continue

    # peak.commenet = 'moved'
    peak.copyTo(destinationNOEpeakList)
    peak.delete()
    continue

        