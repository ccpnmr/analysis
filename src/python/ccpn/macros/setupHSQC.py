__author__ = 'simon1'
from ccpn.lib.Assignment import propagateAssignments
from ccpn.ui.gui.lib.Window import navigateToNmrResidue
from ccpn.macros.restrictedPick import restrictedPick

if len(project.nmrChains) == 0:
  c = project.newNmrChain()
else:
  c = project.nmrChains[0]

hsqcPeakListName = 'PL:hsqc.1'

hsqcPeakList = project.getByPid(hsqcPeakListName)


for peak in hsqcPeakList.peaks:
  r = c.newNmrResidue()
  a = r.fetchNmrAtom(name='N')
  a2 = r.fetchNmrAtom(name='H')
  atoms = [[a2], [a]]
  peak.assignDimension(axisCode='Nh', value=a)
  peak.assignDimension(axisCode='Hn', value=a2)
#   newPeaks = restrictedPick(project=project, nmrResidue=r)
#   newPeaks.append(peak)
#   propagateAssignments(newPeaks)
#
# for nmrResidue in project.nmrResidues:
#   for display in project.spectrumDisplays:
#     if len(display.orderedAxes) > 2:
#       strip = display.addStrip()
#       navigateToNmrResidue(project, nmrResidue, strip=strip)
#       strip.planeToolbar.spinSystemLabel.setText(nmrResidue.sequenceCode)



