
import numpy


def isInterOnlyExpt(peakList):
  expList = ['HNCO', 'CONH', 'H[N[CO', 'H[N[co', 'seq.', 'HCA_NCO.Jmultibond']
  if(any(expType in peakList.spectrum.experimentType for expType in expList)):
    # interExpts.append(peakList.spectrum)
    return True

c = project.newNmrChain()
ssLabels = []
positions = []

hsqcPeakList = project.getByPid('PL:hsqc.1')

atomDict = {}

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

for peakList in project.peakLists[1:]:
  if isInterOnlyExpt(peakList):

    for peak in peakList.peaks:
      array = [peak.position[0], peak.position[2]]
      result = clf.predict(array)
      if peak._apiPeak.findFirstPeakIntensity().value > 0:
        name = 'CA-1'
      else:
        name = 'CB-1'
        print(peak, name)
      r = project.getByPid(result[0])
      newNmrAtom = r.fetchNmrAtom(name=name)
      dimNmrAtoms = [atomDict[result[0]][0], [newNmrAtom], atomDict[result[0]][1]]
      peak.dimensionNmrAtoms = dimNmrAtoms
  else:
    for peak in peakList.peaks:
    # if peakList.spectrum.experimentType == 'H[N[CA]]':
    #   noPeaks = 2
    # elif peakList.spectrum.experimentType == 'H[N[{CA|ca[Cali]}]]':
    #   noPeaks = 4
      array = [peak.position[0], peak.position[2]]
      result = clf.predict(array)
      dimNmrAtoms = [atomDict[result[0]][0], [], atomDict[result[0]][1]]
      peak.dimensionNmrAtoms = dimNmrAtoms








