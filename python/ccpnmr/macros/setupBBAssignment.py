hsqc = project.getById('SP:HSQC-115')

hsqc.positiveContourCount = 5
hsqc.positiveContourFactor = 1.4
hsqcSpectrumDisplay = window.createSpectrumDisplay(hsqc)

window.removeBlankDisplay()

hsqcPeakList = project.getById('PL:HSQC-115.1')

hnca = project.getById('SP:HNCA-110')
hncoca = project.getById('SP:HNCOCA-111')
hncacb = project.getById('SP:HNCACB-112')
hncocacb = project.getById('SP:HNCOCACB-113')

hnca.positiveContourBase = 20000.0
hnca.positiveContourCount = 9
hnca.positiveContourColour = 'magenta'

hncoca.positiveContourCount = 5
hncoca.positiveContourColour = 'cyan'
hncoca.positiveContourBase = 20000.0

hncacb.positiveContourBase = 56568.54
hncacb.positiveContourCount = 8
hncacb.negativeContourCount = 8
hncacb.displayNegativeContours = True
hncacb.negativeContourBase = -56568.54

hncocacb.positiveContourCount = 8
hncocacb.positiveContourBase = 40000.00
hncocacb.negativeContourBase = -40000.00
hncocacb.positiveContourColour = 'blue'
hncocacb.negativeContourColour = 'yellow'
hncocacb.negativeContourCount = 8
hncocacb.displayNegativeContours = True


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

project.getById('NA:@.@195..CB').delete()