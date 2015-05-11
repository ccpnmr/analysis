c = project.newNmrChain()

r = c.newNmrResidue()

a = r.newNmrAtom(isotopeCode='15N')

a2 = r.newNmrAtom(isotopeCode='1H')

atoms2 = [[a2], [a]]

project.peakLists[0].peaks[0].dimensionNmrAtoms = atoms2

self.showPeakTable()
