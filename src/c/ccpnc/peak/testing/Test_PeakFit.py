"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:20 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from operator import itemgetter
import numpy as np
# from ccpnmodel.ccpncore.testing.CoreTesting import CoreTesting
# from ccpnmodel.ccpncore.lib.ccp.nmr.Nmr import DataSource
from ccpnc.peak import Peak


class PeakFitTest():
    # Path of project to load (None for new project
    projectPath = 'CcpnCourse1a'

    def Test_PeakFit(self, *args, **kwds):
        spectrum = self.nmrProject.findFirstExperiment(name='HSQC').findFirstDataSource()
        data = spectrum.getPlaneData()
        print('data.shape = %s' % (data.shape,))

        haveLow = 0
        haveHigh = 1
        low = 0  # arbitrary
        high = 1.0e8
        buffer = [1, 1]
        nonadjacent = 0
        dropFactor = 0.0
        minLinewidth = [0.0, 0.0]

        peakPoints = Peak.findPeaks(data, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth, [], [], [])
        print('number of peaks found = %d' % len(peakPoints))

        peakPoints.sort(key=itemgetter(1), reverse=True)

        position, height = peakPoints[0]
        print('position of highest peak = %s, height = %s' % (position, height))

        numDim = len(position)
        peakArray = np.array(position, dtype='float32')
        firstArray = peakArray - 2
        lastArray = peakArray + 3
        peakArray = peakArray.reshape((1, numDim))
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')
        regionArray = np.array((firstArray, lastArray))

        method = 0  # Gaussian
        result = Peak.fitPeaks(data, regionArray, peakArray, method)
        intensity, center, linewidth = result[0]
        print('Gaussian fit: intensity = %s, center = %s, linewidth = %s' % (intensity, center, linewidth))

        method = 1  # Lorentzian
        result = Peak.fitPeaks(data, regionArray, peakArray, method)
        intensity, center, linewidth = result[0]
        print('Lorentzian fit: intensity = %s, center = %s, linewidth = %s' % (intensity, center, linewidth))


if __name__ == '__main__':

    # Ed testing the gauss function

    import matplotlib


    matplotlib.use('Qt5Agg')
    from mpl_toolkits import mplot3d
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm


    res = 9
    span = ((-4, 4), (-4, 4))
    h = 1.0
    x0 = 2.245
    y0 = -1.2357
    sigmax = 1.0
    sigmay = 1.0

    haveLow = 0
    haveHigh = 1
    low = 0  # arbitrary
    high = 0.000
    buffer = [1, 1]
    nonadjacent = 1
    dropFactor = 0.1
    minLinewidth = [0.0, 0.0]

    def sigma2fwhm(sigma):
        return sigma * np.sqrt(8 * np.log(2))


    def fwhm2sigma(fwhm):
        return fwhm / np.sqrt(8 * np.log(2))


    def _gauss(ii, jj):
        fwhmx = sigma2fwhm(sigmax)
        fwhmy = sigma2fwhm(sigmay)

        # return h * np.exp(-4*np.log(2) * ((ii-x0)**2 / fwhmx**2 + (jj-y0)**2 / fwhmy**2))
        return h / np.sqrt(4 * np.pi ** 2 * (sigmax * sigmay)) * np.exp(-((ii - x0) ** 2 / sigmax ** 2) - (((jj - y0) ** 2 / sigmay ** 2)))


    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('SHOULD BE:', res, h, x0, y0, sigma2fwhm(sigmax), sigma2fwhm(sigmay))


    xx = np.linspace(*span[0], res)
    yy = np.linspace(*span[1], res)
    xm, ym = np.meshgrid(xx, yy)

    dataArray = np.array(_gauss(xm, ym), dtype=np.float32)

    peakPoints = Peak.findPeaks(dataArray, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth, [], [], [])
    if peakPoints:
        print('number of peaks found = %d' % len(peakPoints))

        peakPoints.sort(key=itemgetter(1), reverse=True)

        position, height = peakPoints[0]
    else:
        position, height = (0.0, 0.0), 0.0

    print('position of highest peak = %s, height = %s' % (position, height))

    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax = fig.gca(projection='3d')

    ax.plot_surface(xm, ym, dataArray)

    peakPoints = [(np.array(position), height) for position, height in peakPoints]

    for position, height in peakPoints:

        numDim = len(position)
        firstArray = np.maximum(position - 2, 0)
        numPointInt = np.array([dataArray.shape[1], dataArray.shape[0]])
        lastArray = np.minimum(position + 3, numPointInt)
        peakArray = position.reshape((1, numDim))
        peakArray = peakArray.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')
        regionArray = np.array((firstArray, lastArray))

        result = Peak.fitPeaks(dataArray, regionArray, peakArray, 0)
        height, centerGuess, linewidth = result[0]

        actualPos = []

        for dim in range(len(dataArray.shape)):
            mi, ma = span[dim]
            ww = ma-mi

            actualPos.append(mi + (centerGuess[dim] / (dataArray.shape[dim]-1)) * ww)

        ax.scatter(*actualPos, height, c='r', marker='^')
        x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax.get_proj())

        ax.text(*actualPos, height, '%.4f, %.4f, %.4f' % (actualPos[0], actualPos[1],height), fontsize=20)

    plt.show()
