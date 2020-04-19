import numpy as np




def scaleSpectraByStd(spectra, pts = 200):
    '''
    Scale 1D spectra intensities by the mean of stds for the first selected pts
    so that all spectra have (roughly the same baseline noise)
    '''
    if len(spectra)<1: return
    stds = []
    ys = [sp.intensities for sp in spectra ]
    for y in ys:
        y0_m = np.std(y[:pts])
        stds.append(y0_m)

    targetValue = np.mean(stds)
    if targetValue == 0 : return
    scaleValues = stds/targetValue
    for sp, y, v in zip(spectra, ys, scaleValues):
        if v == 0:
            v = 1
            print('Not possible to scale %s' %sp.name)
        sp.intensities = y/v


