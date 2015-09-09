
spectrum = project.getByPid('SP:hsqc')
peakList = project.getByPid('PL:hsqc.1')

display = self.createSpectrumDisplay(spectrum)

display.strips[0].showPeaks(peakList)

self.removeBlankDisplay()
