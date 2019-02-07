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


    res = 45
    span = ((-(res // 2), res // 2), (-(res // 2), res // 2))
    plotRange = ((-5, 15), (-5, 15))

    testPeaks = ((1.0, 2.0, 0.0, 0.0, 1.0),
                 (1.0, 2.4, 2.0, 10.0, 1.7),
                 (1.0, 1.4, 10.0, 1.0, 1.7),
                 (4.2, 1.8, 7.0, 7.0, 1.1)
                 )

    # h = 1.0
    # x0 = 2.245
    # y0 = -1.2357
    # sigmax = 1.0
    # sigmay = 1.0

    haveLow = 0
    haveHigh = 1
    low = 0  # arbitrary
    high = 0.001
    buffer = [1, 1]
    nonadjacent = 1
    dropFactor = 0.01
    minLinewidth = [0.0, 0.0]


    def sigma2fwhm(sigma):
        return sigma * np.sqrt(8 * np.log(2))


    def fwhm2sigma(fwhm):
        return fwhm / np.sqrt(8 * np.log(2))


    def _gauss(ii, jj, sigmax=1.0, sigmay=1.0, mx=0.0, my=0.0, h=1.0):
        fwhmx = sigma2fwhm(sigmax)
        fwhmy = sigma2fwhm(sigmay)

        pos = [ii - mx, jj - my]
        # for dim in range(2):
        #     ss = 1 / (span[dim][1] - span[dim][0])
        #     rr = plotRange[dim][1] - plotRange[dim][0]
        #
        #     val = plotRange[dim][0] + (rr * ss * (pos[dim] - span[dim][0]))
        #
        #     pos[dim] = val
        #
        # xx = (ii - mx)      #(((ii - mx) - plotRange[0][0]) / (plotRange[0][1] - plotRange[0][0])) + plotRange[0][0]
        # yy = (jj - my)      #(((jj - my) - plotRange[1][0]) / (plotRange[1][1] - plotRange[1][0])) + plotRange[1][0]
        # return h * np.exp(-4*np.log(2) * ((ii-mx)**2 / fwhmx**2 + (jj-my)**2 / fwhmy**2))
        return h * np.sqrt(4 * np.pi ** 2 * (sigmax * sigmay)) * np.exp(-(pos[0] ** 2 / sigmax ** 2) - (pos[1] ** 2 / sigmay ** 2))


    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    # print('SHOULD BE:', res, h, x0, y0, sigma2fwhm(sigmax), sigma2fwhm(sigmay))

    # xx = np.linspace(*span[0], res)
    # yy = np.linspace(*span[1], res)
    xx = np.linspace(*plotRange[0], res)
    yy = np.linspace(*plotRange[1], res)
    xm, ym = np.meshgrid(xx, yy)

    dataArray = np.zeros(shape=(res, res), dtype=np.float32)
    for thisPeak in testPeaks:

        sigmax, sigmay, mx, my, h = thisPeak

        peakArray = np.array(_gauss(xm, ym, sigmax=sigmax, sigmay=sigmay, mx=mx, my=my, h=h), dtype=np.float32)
        dataArray = np.add(dataArray, peakArray)

    peakPoints = Peak.findPeaks(dataArray, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth, [], [], [])

    print('number of peaks found = %d' % len(peakPoints))
    peakPoints.sort(key=itemgetter(1), reverse=True)
    for peak in peakPoints:
        position, height = peak
        print('position of peak = %s, height = %s' % (position, height))

    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax = fig.gca(projection='3d')

    ax.plot_wireframe(xm, ym, dataArray)

    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax2 = fig.gca(projection='3d')

    ax2.plot_wireframe(xm, ym, dataArray)

    peakPoints = [(np.array(position), height) for position, height in peakPoints]

    allPeaksArray = None
    regionArray = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # fit all peaks in single operation

    for position, height in peakPoints:

        numDim = len(position)
        numPointInt = np.array([dataArray.shape[1], dataArray.shape[0]])
        firstArray = np.maximum(position - 3, 0)
        lastArray = np.minimum(position + 4, numPointInt)

        if regionArray is not None:
            firstArray = np.minimum(firstArray, regionArray[0])
            lastArray = np.maximum(lastArray, regionArray[1])

        peakArray = position.reshape((1, numDim))
        peakArray = peakArray.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')

        regionArray = np.array((firstArray, lastArray))

        if allPeaksArray is None:
            allPeaksArray = peakArray
        else:
            allPeaksArray = np.append(allPeaksArray, peakArray, axis=0)

    result = Peak.fitPeaks(dataArray, regionArray, allPeaksArray, 0)

    for dim in range(len(result)):
        height, centerGuess, linewidth = result[dim]

        actualPos = []

        for dim in range(len(dataArray.shape)):
            mi, ma = plotRange[dim]
            ww = ma - mi

            actualPos.append(mi + (centerGuess[dim] / (dataArray.shape[dim] - 1)) * ww)

        ax.scatter(*actualPos, height, c='g', marker='^', s=20)
        x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax.get_proj())

        ax.text(*actualPos, height, '%.4f, %.4f, %.4f' % (actualPos[0], actualPos[1], height), fontsize=20)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # fit all peaks in individual operations (not correct)

    for position, height in peakPoints:

        numDim = len(position)
        numPointInt = np.array([dataArray.shape[1], dataArray.shape[0]])
        firstArray = np.maximum(position - 3, 0)
        lastArray = np.minimum(position + 4, numPointInt)

        peakArray = position.reshape((1, numDim))
        peakArray = peakArray.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')

        regionArray = np.array((firstArray, lastArray))

        result = Peak.fitPeaks(dataArray, regionArray, peakArray, 0)

        height, centerGuess, linewidth = result[0]

        actualPos = []

        for dim in range(len(dataArray.shape)):
            mi, ma = plotRange[dim]
            ww = ma - mi

            actualPos.append(mi + (centerGuess[dim] / (dataArray.shape[dim] - 1)) * ww)

        ax2.scatter(*actualPos, height, c='r', marker='^', s=20)
        x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax2.get_proj())

        ax2.text(*actualPos, height, '%.4f, %.4f, %.4f' % (actualPos[0], actualPos[1], height), fontsize=20)

    plt.show()
