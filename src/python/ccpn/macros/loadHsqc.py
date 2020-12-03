"""This macro will load an HSQC spectrum into an empty project
   and create a spectrum display module with this spectrum inside."""

# load in the HSQC spectrum using the loadData() method of the project object
spectrumPath = '/Users/simon1/nmrdata/spectra/hsqc.spc' # specifies path to processed spectrum
project.loadData(spectrumPath)

# Use the getByPid() method of the project class to get hold of the spectrum object
hsqcSpectrum = get('SP:hsqc')

# use the createSpectrumDisplay() method of ui.mainWindow to display the spectrum
mainWindow.createSpectrumDisplay(hsqcSpectrum)
