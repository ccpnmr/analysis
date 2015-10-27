__author__ = 'simon1'


if len(project.nmrChains) == 0:
  c = project.newNmrChain()
else:
  c = project.nmrChains[0]

hsqcPeakListName = 'PL:test.1'

hsqcPeakList = project.getByPid(hsqcPeakListName)


for peak in hsqcPeakList.peaks:
  r = c.newNmrResidue()
  a = r.fetchNmrAtom(name='N')
  a2 = r.fetchNmrAtom(name='H')
  atoms = [[a2], [a]]
  peak.assignDimension(axisCode='Nh', value=a)
  peak.assignDimension(axisCode='Hn', value=a2)
