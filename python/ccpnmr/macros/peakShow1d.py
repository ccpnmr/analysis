
spectrum = project.getByPid('SP:1')
peakList = project.getByPid('PL:1.1')

display = self.createSpectrumDisplay(spectrum)

display.strips[0].showPeaks(peakList)

self.removeBlankDisplay()
