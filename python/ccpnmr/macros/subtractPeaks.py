__author__ = 'simon1'

peakList1 = project.getById('PL:HSQC-115.1')

peakList2 = project.getById('PL:HSQC-115.2')

peakList1.spectrum.assignmentTolerances = [0.05, 0.01]

peakList1.subtractPeakLists(peakList2)

peakList3 = project.getById('PL:HSQC-115.3')

print(peakList3.peaks)