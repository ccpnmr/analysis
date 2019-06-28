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
__version__ = "$Revision: 3.0.b5 $"
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
                 (2.5, 1.7, 10.0, 1.0, 1.7),
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


    def _gaussFWHM(ii, jj, sigmax=1.0, sigmay=1.0, mx=0.0, my=0.0, h=1.0):
        """Calculate the normal(gaussian) distribution in Full-width-Half-Maximum.

        (https://arthursonzogni.com/Diagon/)
        """
        pos = [ii - mx, jj - my]

        fwhmx = sigma2fwhm(sigmax)
        fwhmy = sigma2fwhm(sigmay)

        return h * np.exp(-4*np.log(2) * ((pos[0] / fwhmx)**2 + (pos[1] / fwhmy)**2))

    def _gaussSigma(ii, jj, sigmax=1.0, sigmay=1.0, mx=0.0, my=0.0, h=1.0):
        """Calculate the normal(gaussian) distribution.
        """
        pos = [ii - mx, jj - my]

        ex = np.exp(-(pos[0] ** 2 / sigmax ** 2) - (pos[1] ** 2 / sigmay ** 2))
        return (h / np.sqrt(4 * (np.pi ** 2) * (sigmax * sigmay))) * ex


    def make_gauss(N, sigma, mu, height):
        k = height     # / (sigma * np.sqrt(2 * np.pi))
        s = -1.0 / (2 * sigma * sigma)

        return k * np.exp(s * (N - mu) * (N - mu))

    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    # print('SHOULD BE:', res, h, x0, y0, sigma2fwhm(sigmax), sigma2fwhm(sigmay))

    # xx = np.linspace(*span[0], res)
    # yy = np.linspace(*span[1], res)
    xx = np.linspace(*plotRange[0], res)
    yy = np.linspace(*plotRange[1], res)
    xm, ym = np.meshgrid(xx, yy)

    dataArray = np.zeros(shape=(res, res), dtype=np.float32)
    dataArrayCheck = np.zeros(shape=(res, res), dtype=np.float32)
    for thisPeak in testPeaks:

        sigmax, sigmay, mx, my, h = thisPeak

        print('>>>testPeak', sigmax, sigmay, mx, my, h)

        peakArrayFWHM = np.array(_gaussFWHM(xm, ym, sigmax=sigmax, sigmay=sigmay, mx=mx, my=my, h=h), dtype=np.float32)
        dataArray = np.add(dataArray, peakArrayFWHM)

        peakArraySigma = np.array(_gaussSigma(xm, ym, sigmax=sigmax, sigmay=sigmay, mx=mx, my=my, h=h), dtype=np.float32)
        dataArraySigma = np.add(dataArray, peakArraySigma)

    peakPoints = Peak.findPeaks(dataArray, haveLow, haveHigh, low, high, buffer, nonadjacent, dropFactor, minLinewidth, [], [], [])

    print('number of peaks found = %d' % len(peakPoints))
    peakPoints.sort(key=itemgetter(1), reverse=True)
    for peak in peakPoints:
        position, height = peak
        print('position of peak = %s, height = %s' % (position, height))

    # make a plot
    # okay, make  2d plot of xxSig, the gauss curve between +-3 sigma

    # testing the calculation of the area under a gaussian curve
    # convert the sigma into a FWHM and plot between volumeIntegralLimits * FWHM
    sigmax = 1.0
    mx = 0.0
    height = 1.0
    integralLimit = 4.0
    numPoints=45
    lx = numPoints-1
    ly = numPoints-1
    lxx = numPoints-1

    thisFWHM = sigma2fwhm(sigmax)
    lim = integralLimit * thisFWHM / 2.0

    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax0 = fig.gca(projection='3d')
    plotSigmaRange = ((0, lim), (0, lim))
    xxS = np.linspace(*plotSigmaRange[0], numPoints)
    yyS = np.linspace(*plotSigmaRange[1], numPoints)
    xmS, ymS = np.meshgrid(xxS, yyS)
    peakArrayFWHM = np.array(_gaussFWHM(xmS, ymS, sigmax=sigmax, sigmay=sigmax, mx=mx, my=mx, h=height), dtype=np.float32)
    ax0.plot_wireframe(xmS, ymS, peakArrayFWHM)

    # only need to use quadrant
    area2d = 4.0*np.trapz(np.trapz(peakArrayFWHM, xxS), yyS)/height        # why does this work?
    print('>>>area3D', area2d)

    xxSig = np.linspace(0, lim, numPoints)
    vals = list(make_gauss(xxSig, sigmax, mx, height))
    fig = plt.figure(figsize=(10, 8), dpi=100)
    axS = fig.gca()
    axS.plot(xxSig, vals)
    axS.grid()

    # only need to use half
    area = 2.0*np.trapz(vals, xxSig)/height     # THIS WORKS! - uses the correct x points for the trapz area
    print('>>>', vals, list(xxSig))
    print('>>>area', area, np.power(area, 2), np.power(area, 2)/area2d)

    # actually area will be area * FWHM * height / thisFWHM

    # make a plot
    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax = fig.gca(projection='3d')

    ax.plot_wireframe(xm, ym, dataArray)

    # make a plot
    fig = plt.figure(figsize=(10, 8), dpi=100)
    ax2 = fig.gca(projection='3d')

    ax2.plot_wireframe(xm, ym, dataArraySigma)

    peakPoints = [(np.array(position), height) for position, height in peakPoints]

    allPeaksArray = None
    regionArray = None






    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # fit all peaks in single operation

    for peakNum, (position, height) in enumerate(peakPoints):

        numDim = len(position)
        numPointInt = np.array([dataArray.shape[1], dataArray.shape[0]])
        firstArray = np.maximum(position - 3, 0)
        lastArray = np.minimum(position + 4, numPointInt)

        if regionArray is not None:
            firstArray = np.minimum(firstArray, regionArray[0])
            lastArray = np.maximum(lastArray, regionArray[1])

        peakArrayFWHM = position.reshape((1, numDim))
        peakArrayFWHM = peakArrayFWHM.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')

        regionArray = np.array((firstArray, lastArray))

        if allPeaksArray is None:
            allPeaksArray = peakArrayFWHM
        else:
            allPeaksArray = np.append(allPeaksArray, peakArrayFWHM, axis=0)

    result = Peak.fitPeaks(dataArray, regionArray, allPeaksArray, 0)

    for peakNum in range(len(result)):
        height, centerGuess, linewidth = result[peakNum]

        actualPos = []

        for dim in range(len(dataArray.shape)):
            mi, ma = plotRange[dim]
            ww = ma - mi

            actualPos.append(mi + (centerGuess[dim] / (dataArray.shape[dim] - 1)) * ww)

        ax.scatter(*actualPos, height, c='g', marker='^', s=50)
        x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax.get_proj())

        ax.text(*actualPos, height, '%i: %.4f, %.4f, %.4f' % (peakNum, actualPos[0], actualPos[1], height), fontsize=20)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # fit all peaks in individual operations (not correct)

    for peakNum, (position, _) in enumerate(peakPoints):

        numDim = len(position)
        numPointInt = np.array([dataArray.shape[1], dataArray.shape[0]])
        firstArray = np.maximum(position - 3, 0)
        lastArray = np.minimum(position + 4, numPointInt)

        peakArrayFWHM = position.reshape((1, numDim))
        peakArrayFWHM = peakArrayFWHM.astype('float32')
        firstArray = firstArray.astype('int32')
        lastArray = lastArray.astype('int32')

        regionArray = np.array((firstArray, lastArray))

        result = Peak.fitPeaks(dataArray, regionArray, peakArrayFWHM, 0)

        height, centerGuess, linewidth = result[0]

        actualPos = []

        for dim in range(len(dataArray.shape)):
            mi, ma = plotRange[dim]
            ww = ma - mi

            actualPos.append(mi + (centerGuess[dim] / (dataArray.shape[dim] - 1)) * ww)

        ax2.scatter(*actualPos, height, c='r', marker='^', s=50)
        x2, y2, _ = mplot3d.proj3d.proj_transform(1, 1, 1, ax2.get_proj())

        ax2.text(*actualPos, height, '%i: %.4f, %.4f, %.4f' % (peakNum, actualPos[0], actualPos[1], height), fontsize=20)

    plt.show()
