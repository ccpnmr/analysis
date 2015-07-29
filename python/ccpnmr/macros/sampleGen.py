
filePath = '/Users/simon1/patrick/lookup.xlsx'

window.leftWidget.parseLookupFile(filePath)


for i, spectrum in enumerate(project.spectra):
  print(i+2, spectrum)
  newSample = project.newSample(name=str(i+2))
  spectrum.sample = newSample

print('Done')