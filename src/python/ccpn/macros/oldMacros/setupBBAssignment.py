hsqc = project.getByPid('SP:hsqc')

hsqc.positiveContourCount = 5
hsqc.positiveContourFactor = 1.4
hsqcSpectrumDisplay = self.createSpectrumDisplay(hsqc)

self.deleteBlankDisplay()

hsqcPeakList = project.getByPid('PL:hsqc.1')

hnca = project.getByPid('SP:hnca')
hncoca = project.getByPid('SP:hncoca')
hncacb = project.getByPid('SP:hncacb')
hncocacb = project.getByPid('SP:hncocacb')

hnca.positiveContourCount = 5
hnca.positiveContourFactor = 1.4
hncoca.positiveContourCount = 5
hnca.positiveContourColour = 'magenta'
hncoca.positiveContourColour = 'cyan'
hncoca.positiveContourFactor = 1.4
hncacb.positiveContourCount = 5
hncacb.positiveContourFactor = 1.4
hncacb.negativeContourCount = 5
hncacb.negativeContourFactor = 1.4
hncocacb.positiveContourCount = 5
hncocacb.positiveContourColour = 'blue'
hncocacb.positiveContourFactor = 1.4
hncocacb.negativeContourColour = 'yellow'
hncocacb.negativeContourCount = 5
hncocacb.negativeContourFactor = 1.4

hncaSpectrumDisplay = self.createSpectrumDisplay(hncacb)
hncaSpectrumDisplay.strips[0].showPeaks(hncacb.peakLists[0])
hncaSpectrumDisplay.displaySpectrum(hncocacb)
hncaSpectrumDisplay.strips[0].showPeaks(hncocacb.peakLists[0])

hncocaSpectrumDisplay = self.createSpectrumDisplay(project.getByPid('SP:hncacb'), axisOrder=['N', 'C', 'H'])
hncocaSpectrumDisplay.strips[0].showPeaks(hncacb.peakLists[0])
hncocaSpectrumDisplay.displaySpectrum(hncocacb)
hncocaSpectrumDisplay.strips[0].showPeaks(hncocacb.peakLists[0])

# hncocaSpectrumDisplay.strips[0].showPeaks(hncacb.peakLists[0])

backboneAssignmentModule = self.showBackboneAssignmentModule(position='bottom',
                           relativeTo=hsqcSpectrumDisplay, hsqcDisplay=hsqcSpectrumDisplay)
# assigner = self.showAssigner('bottom')
# backboneAssignmentModule.setAssigner(assigner)

import numpy
import csv
ssLabels = []
positions = []
import re
hsqcPeakList = project.getByPid('PL:hsqc.1')

assignmentFile = open('/Users/simon1/FedirsData/CaM10hsqc.csv', 'r')

reader = csv.reader(assignmentFile)

for row in reader:
  peakPosition = [row[1], row[2]]
  positions.append(numpy.array(peakPosition))
  match = re.match(r"([a-z]+)([0-9]+)", row[0], re.I)
  residuePid = 'MR:A.%s.%s'.format(match[0], match[1])
  residue = project.getByPid(residuePid)
for peak in hsqcPeakList.peaks:
  r = c.newNmrResidue()
  a = r.newNmrAtom(isotopeCode='15N')
  a2 = r.newNmrAtom(isotopeCode='1H')
  atoms = [[a2], [a]]
  peak.dimensionNmrAtoms = atoms
  ssLabels.append(r.pid)
  atomDict[r.pid] = atoms
  positions.append(numpy.array(peak.position))

from sklearn import svm

clf=svm.SVC()
clf.fit(positions, ssLabels)

hncaPeaks = []

for peakList in project.peakLists[1:]:

  for peak in peakList.peaks:
    array = [peak.position[0], peak.position[2]]
    result = clf.predict(array)
    dimNmrAtoms = [atomDict[result[0]][0], [], atomDict[result[0]][1]]
    peak.dimensionNmrAtoms = dimNmrAtoms



