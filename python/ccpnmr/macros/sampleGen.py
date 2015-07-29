
filePath = '/Users/luca/Desktop/patrick/lookup/lookupPatrick.csv'

window.leftWidget.parseLookupFile(filePath)


for i, spectrum in enumerate(project.spectra):
  print(i+2, spectrum)
  newSample = project.newSample(name=str(i+2))
  spectrum.sample = newSample

print('Done')