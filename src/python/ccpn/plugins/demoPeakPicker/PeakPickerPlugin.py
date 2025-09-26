
from ccpn.api import PeakPickerABC, SimplePeak, getLogger
from nmrglue.analysis.peakpick import pick as nmrgluePeakPick


class MyPeakPicker(PeakPickerABC):
    peakPickerType = "MyPluginPeakPicker"

    def findPeaks(self, data) -> list:
        """Detect peaks in nD numpy data and return them as SimplePeak instances.(points are z,y,x for nD)."""
        locations, cluster_ids, scales, amps = nmrgluePeakPick(data=data,  pthres=self.positiveThreshold, nthres=self.negativeThreshold, cluster=True, table=False)
        return [SimplePeak( points=loc, height=None, lineWidths=[float(lw) for lw in sc], volume=float(amp), clusterId=cid,) for loc, cid, sc, amp in zip(locations, cluster_ids, scales, amps)]

MyPeakPicker._registerPeakPicker()