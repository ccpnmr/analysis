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
          # shiftList.newChemicalShift(value = peak.position[1], nmrAtom=nmrResidue.fetchNmrAtom(name='CA-1'))
        if peak.height < 0:
          peak.dimensionNmrAtoms[1][0] = nmrResidue.fetchNmrAtom(name='CB-1')
          # shiftList.newChemicalShift(value = peak.position[1], nmrAtom=nmrResidue.fetchNmrAtom(name='CB-1'))
    else:
      negativePeaks = [peak for peak in exptDict[exptType] if peak.height < 0]
      positivePeaks = [peak for peak in exptDict[exptType] if peak.height > 0]
      assignAlphas(nmrResidue=nmrResidue, peaks=positivePeaks)
      assignBetas(nmrResidue=nmrResidue, peaks=negativePeaks)

# hsqc = project.getById('SP:HSQC-115')
#
# hsqc.positiveContourCount = 5
# hsqc.positiveContourFactor = 1.4
# hsqcSpectrumDisplay = window.createSpectrumDisplay(hsqc)
#
# window.removeBlankDisplay()
#
# hnca = project.getById('SP:HNCA-110')
# hncoca = project.getById('SP:HNCOCA-111')
# hncacb = project.getById('SP:HNCACB-112')
# hncocacb = project.getById('SP:HNCOCACB-113')
#
# hnca.positiveContourBase = 20000.0
# hnca.positiveContourCount = 9
# hnca.positiveContourColour = 'magenta'
#
# hncoca.positiveContourCount = 5
# hncoca.positiveContourColour = 'cyan'
# hncoca.positiveContourBase = 20000.0
#
# hncacb.positiveContourBase = 56568.54
# hncacb.positiveContourCount = 8
# hncacb.negativeContourCount = 8
# hncacb.displayNegativeContours = True
# hncacb.negativeContourBase = -56568.54
#
# hncocacb.positiveContourCount = 8
# hncocacb.positiveContourBase = 40000.00
# hncocacb.negativeContourBase = -40000.00
# hncocacb.positiveContourColour = 'blue'
# hncocacb.negativeContourColour = 'yellow'
# hncocacb.negativeContourCount = 8
# hncocacb.displayNegativeContours = True
#
#
# hncocacbSpectrumDisplay =  window.createSpectrumDisplay(hncocacb)
# hncocacbSpectrumDisplay.displaySpectrum(hncacb)
# # hncocacbOrthogSpectrumDisplay = window.createSpectrumDisplay(hncocacb, axisOrder=['N', 'C', 'H'])
#
# hncacbSpectrumDisplay =  window.createSpectrumDisplay(hncacb)
# hncacbSpectrumDisplay.displaySpectrum(hncocacb)
# # hncacbOrthogSpectrumDisplay = window.createSpectrumDisplay(hncacb, axisOrder=['N', 'C', 'H'])
#
# pickAndAssignModule = window.showPickAndAssignModule(position='bottom',
#                            relativeTo=hsqcSpectrumDisplay, hsqcDisplay=hsqcSpectrumDisplay)
#
