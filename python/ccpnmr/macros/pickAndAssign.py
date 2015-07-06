from sklearn import svm
import numpy
from ccpn.lib.assignment import isInterOnlyExpt, getExptDict, assignAlphas, assignBetas



if len(project.nmrChains) == 0:
  c = project.newNmrChain()
else:
  c = project.nmrChains[0]

ssLabels = []
positions = []
atomDict = {}

hsqcPeakList = project.getById('PL:HSQC-115.1')

shiftList = project.chemicalShiftLists[0]

for peak in hsqcPeakList.peaks:
  r = c.newNmrResidue()
  a = r.newNmrAtom(name='N')
  a2 = r.newNmrAtom(name='H')
  shiftList.newChemicalShift(value=peak.position[0], nmrAtom=a2)
  shiftList.newChemicalShift(value=peak.position[1], nmrAtom=a)
  atoms = [[a2], [a]]
  peak.dimensionNmrAtoms = atoms
  ssLabels.append(r.pid)
  atomDict[r.pid] = atoms
  positions.append(numpy.array(peak.position))

clf=svm.SVC()
clf.fit(positions, ssLabels)

for peakList in project.peakLists[1:]:
  if isInterOnlyExpt(peakList.spectrum.experimentType):
    for peak in peakList.peaks:
      array = [peak.position[0], peak.position[2]]
      result = clf.predict(array)
      if peak.height > 0:
        name = 'CA-1'
      else:
        name = 'CB-1'
      r = project.getById(result[0])
      newNmrAtom = r.fetchNmrAtom(name=name)
      print(newNmrAtom)
      try:
        shiftList.newChemicalShift(value = peak.position[1], nmrAtom=newNmrAtom)
      except:
        pass
      dimNmrAtoms = [atomDict[result[0]][0], [newNmrAtom], atomDict[result[0]][1]]
      peak.dimensionNmrAtoms = dimNmrAtoms
  else:
    for peak in peakList.peaks:
      array = [peak.position[0], peak.position[2]]
      result = clf.predict(array)
      dimNmrAtoms = [atomDict[result[0]][0], [], atomDict[result[0]][1]]
      peak.dimensionNmrAtoms = dimNmrAtoms

for ssLabel in ssLabels:

  nmrResidue = project.getById(ssLabel)
  for peaks in nmrResidue.fetchNmrAtom(name='N').assignedPeaks:
    exptDict = getExptDict(project)
    for peak in peaks:
      if peak.peakList.spectrum.experimentType in exptDict:
        exptDict[peak.peakList.spectrum.experimentType].append(peak)
  for exptType in exptDict.keys():
    if isInterOnlyExpt(exptType):
      for peak in exptDict[exptType]:
        if peak.height > 0:
          peak.dimensionNmrAtoms[1][0] = nmrResidue.fetchNmrAtom(name='CA-1')
        if peak.height < 0:
          peak.dimensionNmrAtoms[1][0] = nmrResidue.fetchNmrAtom(name='CB-1')
    else:
      negativePeaks = [peak for peak in exptDict[exptType] if peak.height < 0]
      positivePeaks = [peak for peak in exptDict[exptType] if peak.height > 0]
      assignAlphas(nmrResidue=nmrResidue, peaks=positivePeaks)
      assignBetas(nmrResidue=nmrResidue, peaks=negativePeaks)
