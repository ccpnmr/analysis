hsqc = project.getById('SP:HSQC-115')

hsqcSpectrumDisplay = window.createSpectrumDisplay(hsqc)

window.removeBlankDisplay()

hsqcPeakList = project.getById('PL:HSQC-115.1')

hnca = project.getById('SP:HNCA-110')
hncoca = project.getById('SP:HNCOCA-111')
hncacb = project.getById('SP:HNCACB-112')
hncocacb = project.getById('SP:HNCOCACB-113')

hncocacbSpectrumDisplay =  window.createSpectrumDisplay(hncocacb)
hncocacbSpectrumDisplay.displaySpectrum(hncacb)
# hncocacbOrthogSpectrumDisplay = window.createSpectrumDisplay(hncocacb, axisOrder=['N', 'C', 'H'])

hncacbSpectrumDisplay =  window.createSpectrumDisplay(hncacb)
hncacbSpectrumDisplay.displaySpectrum(hncocacb)
# hncacbOrthogSpectrumDisplay = window.createSpectrumDisplay(hncacb, axisOrder=['N', 'C', 'H'])

backboneAssignmentModule = window.showBackboneAssignmentModule(position='bottom',
                           relativeTo=hsqcSpectrumDisplay, hsqcDisplay=hsqcSpectrumDisplay)

assigner = window.showAssigner('bottom')
backboneAssignmentModule.setAssigner(assigner)

