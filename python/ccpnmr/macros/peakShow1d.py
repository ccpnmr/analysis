
spectrum = project.getById('SP:1')
peakList = project.getById('PL:1.1')

display = self.createSpectrumDisplay(spectrum)

display.strips[0].showPeaks(peakList)

self.removeBlankDisplay()
