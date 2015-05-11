
spectrum = project.getById('SP:hsqc')
peakList = project.getById('PL:hsqc.1')

display = self.createSpectrumDisplay(spectrum)

display.strips[0].showPeaks(peakList)

self.removeBlankDisplay()
