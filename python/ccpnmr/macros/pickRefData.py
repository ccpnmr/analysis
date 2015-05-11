__author__ = 'simon'

from ccpn.lib.mixtureUtil import setupMixtures

refData = window.leftWidget.spectrumReference

refCount = window.leftWidget.spectrumReference.childCount()

spectra = []

for i in range(refCount):
  item = refData.child(i)
  itemCount = item.childCount()
  for j in range(itemCount):
    spectrumPid = item.child(j).text(0)
    spectrum = project.getById(spectrumPid)
    spectra.append(spectrum)
    spectrum.peakLists[0].findPeaks1dFiltered()


mixtures = setupMixtures(spectra, 10, 'nMixtures')