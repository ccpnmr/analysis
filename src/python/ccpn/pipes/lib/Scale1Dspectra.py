import numpy as np


def resetSpectraScale(spectra, value = 1):
    for sp in spectra:
        sp.scale = value


def scaleSpectraByStd(spectra, pts = 200):
    '''
    Scale 1D spectra intensities by the mean of stds for the first selected pts
    so that all spectra have (roughly the same baseline noise)
    '''
    if len(spectra)<1: return
    stds = []
    resetSpectraScale(spectra,1)
    ys = [sp.intensities for sp in spectra]
    for y in ys:
        y0_m = np.std(y[:pts])
        stds.append(y0_m)

    targetValue = np.mean(stds)
    if targetValue == 0 : return
    scaleValues = targetValue/stds
    for sp, y, v in zip(spectra, ys, scaleValues):
        if v == 0:
            v = 1
            print('Not possible to scale %s' %sp.name)
        sp.scale = float(v)
        # sp.intensities = sp.intensities * v     #in case don't want use the scale property


def scaleSpectraByRegion(spectra, limits, engine = 'mean', resetScale=True):
    '''
    Scale 1D spectra intensities by a region of interest.
    eg a region between a peak, so that the spectra are scaled relative to that peak.
    engine =    'mean':  heights will be the median of the two
                'min' :  heights will be relative to the lower
                'max' :  heights will be relative to the highest

    resetScale: always start with a scale of 1 (original spectrum data)
    limits = list of 1d regions in ppm, eg [1,3]
    '''
    availableEngines = ['mean', 'min', 'max', 'std']
    if engine not in availableEngines:
        engine = availableEngines[0]
    if len(spectra)<1: return
    point1, point2 = np.max(limits), np.min(limits)
    ys = []
    for sp in spectra:
        # if resetScale: sp.scale = 1  # reset first
        xRef, yRef = sp.positions, sp.intensities
        x_filtered = np.where((xRef <= point1) & (xRef >= point2))
        y_filtered = yRef[x_filtered]
        ys.append(y_filtered)

    maxs = []
    for y in ys:
            y0_m = np.max(abs(y)) #so will work also for negative regions
            maxs.append(y0_m)

    targetValue = getattr(np, engine)(maxs)
    if targetValue == 0 : return
    scaleValues = targetValue/maxs
    for sp, y, v in zip(spectra, ys, scaleValues):
        sp.scale = float(v)
        # sp.intensities = sp.intensities * v     #in case don't want use the scale property

