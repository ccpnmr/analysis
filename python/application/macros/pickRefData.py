__author__ = 'simon'



from ccpn.lib.Sample import setupSamples


refData = window.leftWidget.spectrumReference

refCount = window.leftWidget.spectrumReference.childCount()


spectra = []

for i in range(refCount):
  item = refData.child(i)
  itemCount = item.childCount()
  for j in range(itemCount):
    spectrumPid = item.child(j).text(0)
    spectrum = project.getByPid(spectrumPid)
    spectra.append(spectrum)
    spectrum.peakLists[0].pickPeaks1dFiltered()

sampleTab = window.leftWidget.spectrumSamples

samples = setupSamples(spectra, 4, 'nSamples')


for sample in samples:
  print(sample.pid)
  newItem = window.leftWidget.addItem(sampleTab, sample)
  for peakCollection in sample.peakCollections[1:]:
    spectrum = project.getByPid('SP:'+peakCollection.name)
    window.leftWidget.addItem(newItem, spectrum)




