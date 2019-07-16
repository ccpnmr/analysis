# Macro to change the tolerances of all (or a selection of?) spectra in one go

# What the macro ultimately needs to do:
# Check whether Spectrum display contains current.strip
# if yes, then
#    Remove all strips in spectrum display except for the current strip
# if no, then
#    Remove all strips in the spectrum display except for the first one

# Determine current number of strips is display
numberOfStrips = len(spectrumDisplay.strips)

# Check whether spectrumDisplay contains more than one strip
if numberOfStrips > 1:
    # Check whether Spectrum display contains current.strip
    if current.strip in spectrumDisplay:
        for ii in range(numberOfStrips):
          # Check whether that the last strip is not the current strip
            if last strip is not current.strip:
                spectrumDisplay.deleteStrip(spectrumDisplay.strips[-1])
            else
                spectrumDisplay.deleteStrip(spectrumDisplay.strips[1])
    else
       for ii in range(1, numberOfStrips):
           spectrumDisplay.deleteStrip(spectrumDisplay.strips[-1])
