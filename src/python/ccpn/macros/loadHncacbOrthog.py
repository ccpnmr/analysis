"""This macro will load an HNCACB spectrum into an empty project and 
create two spectrum display modules with this spectrum inside."""

# load in the HNCACB spectrum using the loadData() method
# of the project object
spectrumPath = '/Users/simon1/nmrdata/spectra/hncacb.spc'
project.loadData(spectrumPath)

# Use the getByPid() method of the project class to get
# hold of the spectrum object
hncacbSpectrum = project.getByPid('SP:hncacb')

# use the createSpectrumDisplay() method of ui.MainWindow
# with the axisOrder argument to display the spectrum with
# x = H, y = C and z = N
ui.mainWindow.createSpectrumDisplay(hncacbSpectrum, axisOrder=['H', 'C', 'N'])

# use the createSpectrumDisplay() method of ui.MainWindow
# with the axisOrder argument to display the spectrum with
# x = H, y = N and z = C
ui.mainWindow.createSpectrumDisplay(hncacbSpectrum, axisOrder=['H', 'N', 'C'])
