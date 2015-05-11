__author__ = 'simon'

interShifts = {}
intraShifts = {}

shiftList = project.chemicalShiftLists[0]

for nmrResidue in self.project.nmrResidues:
  # intraShifts[nmrResidue] = []
  # interShifts[nmrResidue] = []
  for atom in nmrResidue.atoms:
    if atom.name == 'CA':
      # intraShifts[nmrResidue].append(shiftList.findChemicalShift(atom))
      print(atom, shiftList.findChemicalShift(atom).value)
#     if atom.name == 'CB':
#       intraShifts[nmrResidue].append(shiftList.findChemicalShift(atom))
#     if atom.name == 'CA-1':
#       intraShifts[nmrResidue].append(shiftList.findChemicalShift(atom))
#     if atom.name == 'CB-1':
#       intraShifts[nmrResidue].append(shiftList.findChemicalShift(atom))
#
# print(interShifts)
# print(intraShifts)
