"""This macro takes the first peakList of an HSQC spectrum called hsqc, 
creates an NmrResidue object in the default NmrChain, @- and 
then assigns child NmrAtom objects called H and N to the correct dimensions. """

# Get hold of the peakList using the getByPid() method of 
# the project class
peakList = project.getByPid('PL:hsqc.1')

# Get the default NmrChain
nmrChain = project.getNmrChain('@-')

# Use a for loop to iterate over the peaks in the peakList
for peak in peakList.peaks:
  # create an empty NmrResidue using the
  # fetchNmrResidue method of the NmrChain without any
  # arguments
  nmrResidue = nmrChain.fetchNmrResidue()
  # use the created NmrResidue to create two NmrAtoms
  # with names H and N, respectively.
  hNmrAtom = nmrResidue.fetchNmrAtom(name='H')
  nNmrAtom = nmrResidue.fetchNmrAtom(name='N')

# use the assignDimension method of the Peak class to
# assign the corresponding NmrAtoms to the correct
# dimensions
peak.assignDimension(axisCode='H', value=[hNmrAtom])
peak.assignDimension(axisCode='N', value=[nNmrAtom])
