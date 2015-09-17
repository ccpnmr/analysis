from ccpn.lib.Assignment import copyAssignments, isInterOnlyExpt

# NBNB TBD FIXME. Looks broken. Clean up or removce? RHF


def getExptDict(project):
  exptDict = {}
  for peakList in project.peakLists[1:]:
    exptDict[peakList.spectrum.experimentType] = []
  return exptDict

if len(project.nmrChains) == 0:
  c = project.newNmrChain()
else:
  c = project.nmrChains[0]

hsqcPeakList = project.getByPid('PL:15N-HSQC-115^spc^par.1')

shiftList = project.chemicalShiftLists[0]

for peak in hsqcPeakList.peaks:
  r = c.newNmrResidue()
  a = r.fetchNmrAtom(name='N')
  a2 = r.fetchNmrAtom(name='H')
  atoms = [[a2], [a]]
  # peak.dimensionNmrAtoms = atoms
  peak.assignDimension(axisCode='Nh', value=a)
  peak.assignDimension(axisCode='Hn', value=a2)
  dim1 = peak.peakList.spectrum.axisCodes.index('Nh')
  dim2 = peak.peakList.spectrum.axisCodes.index('Hn')
  shiftList.newChemicalShift(nmrAtom=a, value=peak.position[hsqcPeakList.spectrum.axisCodes.index('Nh')])
  shiftList.newChemicalShift(nmrAtom=a2, value=peak.position[hsqcPeakList.spectrum.axisCodes.index('Hn')])


hncocacb = project.getByPid('PL:CBCA(CO)NH-125^spc^par.1')
hncoca = project.getByPid('PL:HN(CO)CA-117^spc^par.1')
hncacb = project.getByPid('PL:126.1')
hnca =  project.getByPid('PL:HNCA-120^spc^par.1')
#
# copyAssignments(hsqcPeakList, hncocacb)
# copyAssignments(hncocacb, hncacb)
# copyAssignments(hncacb, hnca)
# copyAssignments(hnca, hncoca)


peaklists2 = [hncocacb, hncacb]


# copyAssignments(peakLists2[0], project.getByPid('PL:126.1'))




# copyAssignments(peakLists2[0], project.getByPid('PL:126.1'))
for peakList in peaklists2:
  if isInterOnlyExpt(peakList.spectrum.experimentType):
    for peak in peakList.peaks:

      # array = [peak.position[dim2], peak.position[dim1]]
      # result = peak.dimensionNmrAtoms[0]
      # print(result)
      if 'CA' in peakList.spectrum.axisCodes:
        cdim = peakList.spectrum.axisCodes.index('CA')
      elif 'C' in peakList.spectrum.axisCodes:
        cdim = peakList.spectrum.axisCodes.index('C')
      elif 'Ch' in peakList.spectrum.axisCodes:
        cdim = peakList.spectrum.axisCodes.index('Ch')
      if not peak.height:
        peak.height = peak._apiPeak.findFirstPeakIntensity().value
      if peak.height > 0 and 45 < peak.position[cdim] < 66:
        name = 'CA'
      elif peak.height > 0 and 10 < peak.position[cdim] < 45:
        name = 'CB'
      else:
        name = 'CB'
      try:
        r = peak.dimensionNmrAtoms[0][0].nmrResidue
      except IndexError:
         continue
      seqCode =  r.sequenceCode
      # print(seqCode)
      newNmrResidue = c.fetchNmrResidue(sequenceCode=seqCode)
      newNmrAtom = r.fetchNmrAtom(name=name)
      try:
        peak.assignDimension(axisCode='CA', value=newNmrAtom)
        if shiftList.getChemicalShift(newNmrAtom.id) is None:
          shiftList.newChemicalShift(value=peak.position[cdim], nmrAtom=newNmrAtom)
      except ValueError:
        # print(peak.peakList.spectrum.axisCodes)
        try:
          peak.assignDimension(axisCode='C', value=newNmrAtom)
          if shiftList.getChemicalShift(newNmrAtom.id) is None:
            shiftList.newChemicalShift(value=peak.position[cdim], nmrAtom=newNmrAtom)
        except ValueError:
            peak.assignDimension(axisCode='Ch', value=newNmrAtom)
            if shiftList.getChemicalShift(newNmrAtom.id) is None:
              shiftList.newChemicalShift(value=peak.position[cdim], nmrAtom=newNmrAtom)
            # shiftList.newChemicalShift(value=peak.position[cdim], nmrAtom=newNmrAtom)




copyAssignments(hncocacb, hncacb)
copyAssignments(hncocacb, hncoca)

# from sklearn import svm
# import numpy
# nmrResidueLabels = []
# nmrAtoms = []
# for nmrResidue in project.nmrResidues:
#   atoms = [shiftList.getChemicalShift(atom.id).value for atom in nmrResidue.atoms if atom._apiResonance.isotopeCode == '13C' and atom.name=='CA' or atom.name=='CB']
#   for atom in atoms:
#     if atom is None:
#       atoms.pop(atoms.index(atom))
#   if len(atoms) > 1:
#     nmrAtoms.append(numpy.array(atoms))
#     nmrResidueLabels.append(nmrResidue.pid)

#
# # copyAssignments(peakLists2[0], project.getByPid('PL:126.1'))
# #
# pl = project.getByPid('PL:126.1')
# clf = svm.SVC()
# clf.fit(nmrAtoms, nmrResidueLabels)
# hncacbPeaks = {}
# for r in project.nmrResidues:
#   atomSet = set()
#   for a in r.atoms:
#     for aPeak in a.assignedPeaks[0]:
#       if aPeak.peakList.pid == pl.pid:
#        atomSet.add(aPeak)
#   if len(atomSet) > 0:
#     hncacbPeaks[r.pid] = atomSet
# # keys = []
# for k, v in hncacbPeaks.items():
#   print(k, len(v))
# #


#
#
# print(hncacbPeaks)
# # copyAssignments(project.getByPid('PL:HNCOCACB-113.1'), project.getByPid('PL:HNCACB-112.1'))
# # copyAssignments(project.getByPid('PL:HSQC-115.1'), project.getByPid('PL:HNCACB-112.1'))
# # copyAssignments(project.getByPid('PL:HNCOCA-111.1'), project.getByPid('PL:HNCA-110.1'))
# # copyAssignments(project.getByPid('PL:HSQC-115.1'), project.getByPid('PL:HNCA-110.1'))


# nmrResidues2 = peakLists3.peaks



for nmrResidue in project.nmrResidues:

  # nmrResidue = project.getByPid(ssLabel)
  for peaks in nmrResidue.fetchNmrAtom(name='N').assignedPeaks:
    exptDict = getExptDict(project)
    for peak in peaks:
      if peak.peakList.spectrum.experimentType in exptDict:
        if not peak.height:
          peak.height = peak._apiPeak.findFirstPeakIntensity().value
        exptDict[peak.peakList.spectrum.experimentType].append(peak)
  for exptType in exptDict.keys():
    if not isInterOnlyExpt(exptType):
      for peak in exptDict[exptType]:
        if peak.height > 0:
          peak.assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CA')])
        if peak.height < 0:
          peak.assignDimension(axisCode='C', value=[nmrResidue.fetchNmrAtom(name='CB')])
    else:
      negativePeaks = [peak for peak in exptDict[exptType] if peak.height < 0]
      positivePeaks = [peak for peak in exptDict[exptType] if peak.height > 0]
      assignAlphas(nmrResidue=nmrResidue, peaks=positivePeaks)
      assignBetas(nmrResidue=nmrResidue, peaks=negativePeaks)

print('DONE')

