# Macro to change the tolerances of all (or a selection of?) spectra in one go

# What the macro ultimately needs to do:
# (User specifies which spectra to apply change to)
# User specifies new tolerances for H, N and C dims
# For each spectrum
#    find isotope codes
#    For each dimension match new tolerance according to isotope code
# Apply new tolerances

# Specify the new tolerances (interactively later on)
newTolerances = {'new1HTol': 0.05, 'new15NTol': 0.6, 'new13CTol': 0.6}

"""
# Loop through all spectra (later on the spectra chosen by the user)
for each spectrum:
    newValues=[]
    # Loop through each dimension of that spectrum and get the isotope Code
    for each dimension:
        get isotopeCode
        # Match the tolerance isotope to the dimension isotope and add the relevant new value to a list
        for i in newTolerances:
            if isotopeCode in i:
                newValues.append(newTolerances[i])
    # Assign new tolerances to spectrum
    spectrum.assignmentTolerances = [newValues]

"""