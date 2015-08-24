c = project.newNmrChain()

r = c.newNmrResidue()

a = r.newNmrAtom(isotopeCode='15N')

a2 = r.newNmrAtom(isotopeCode='1H')

a3 = r.newNmrAtom(name='CA')

atoms2 = [[a2], [a]]

project.peakLists[0].peaks[0].dimensionNmrAtoms = atoms2

self.showPeakTable()
