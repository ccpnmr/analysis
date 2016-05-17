__author__ = 'simon1'

peakList1 = project.getByPid('PL:HSQC-115.1')

peakList2 = project.getByPid('PL:HSQC-115.2')

peakList1.spectrum.assignmentTolerances = [0.05, 0.01]

peakList1._subtractPeakLists(peakList2)

peakList3 = project.getByPid('PL:HSQC-115.3')

print(peakList3.peaks)