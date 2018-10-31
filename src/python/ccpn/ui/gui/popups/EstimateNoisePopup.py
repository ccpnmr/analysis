"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util import Common as commonUtil


# These can be imported from Nmr/PeakList
def _cumulativeArray(array):
    """ get total size and strides array.
        NB assumes fastest moving index first """

    ndim = len(array)
    cumul = ndim * [0]
    n = 1
    for i, size in enumerate(array):
        cumul[i] = n
        n = n * size

    return (n, cumul)


def _arrayOfIndex(index, cumul):
    """ Get from 1D index to point address tuple
    NB assumes fastest moving index first
    """

    ndim = len(cumul)
    array = ndim * [0]
    for i in range(ndim - 1, -1, -1):
        c = cumul[i]
        array[i], index = divmod(index, c)

    return np.array(array)


class EstimateNoisePopup(CcpnDialog):
    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 400

    def __init__(self, parent=None, mainWindow=None, title='EstimateNoise',
                 strip=None, orderedSpectrumViews=None, **kw):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        # label the current strip
        self.strip = strip
        self.stripLabel = Label(self, "Current strip: %s" % strip.id, grid=(0, 0), gridSpan=(1, 4))

        # create a tab widget in the middle for the listed spectra
        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = OrderedSet([spec.spectrum for spec in self.orderedSpectrumViews])

        self.tabWidget = Tabs(self, setLayout=True, grid=(1, 0), gridSpan=(1, 4))
        self.tabWidget.setMinimumWidth(
                max(self.MINIMUM_WIDTH, self.MINIMUM_WIDTH_PER_TAB * len(self.orderedSpectra)))

        self._noiseTab = []
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            self._noiseTab.append(NoiseTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=strip))
            self.tabWidget.addTab(self._noiseTab[specNum], thisSpec.name)

        # estimate noise function here

        ButtonList(self, ['Close'], [self._accept], grid=(2, 3))

        self.setFixedSize(self.sizeHint())

    def _accept(self):
        """Close button pressed
        """
        self.accept()

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self.close()


class NoiseTab(QtWidgets.QWidget, Base):

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None):
        super(NoiseTab, self).__init__(parent)
        Base.__init__(self, setLayout=True)

        self.parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.strip = strip

        # set up the widgets
        row = 0

        self.axisCodes = [i for i in range(len(spectrum.axisCodes))]
        for ii, axis in enumerate(spectrum.axisCodes):
            Label(self, text=axis, grid=(row, 0), vAlign='t', hAlign='l')
            self.axisCodes[ii] = Label(self, text='<None>', grid=(row, 1), vAlign='t', hAlign='l')
            row += 1

        Label(self, text='Mean', grid=(row, 0), vAlign='t', hAlign='l')
        self.meanLabel = Label(self, text='<None>', grid=(row, 1), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='SD', grid=(row, 0), vAlign='t', hAlign='l')
        self.SDLabel = Label(self, text='<None>', grid=(row, 1), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='Max', grid=(row, 0), vAlign='t', hAlign='l')
        self.maxLabel = Label(self, text='<None>', grid=(row, 1), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='Min', grid=(row, 0), vAlign='t', hAlign='l')
        self.minLabel = Label(self, text='<None>', grid=(row, 1), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='Noise Level', grid=(row, 0), vAlign='t', hAlign='l')
        self.noiseLevelSpinBox = ScientificDoubleSpinBox(self, grid=(row, 1), vAlign='t')
        self.noiseLevelSpinBox.setMaximum(1e12)
        self.noiseLevelSpinBox.setMinimum(0.1)
        self.noiseLevelButton = Button(self, grid=(row, 2), callback=self._setNoiseLevel, text='Apply')

        # calculate the noise levels
        self.noise = self.spectrum.estimateNoise()

        # This can be moved somewhjere more sensible

        # calculate the region over which to estimate the noise
        selectedRegion = [[self.strip._CcpnGLWidget.axisL, self.strip._CcpnGLWidget.axisR],
                          [self.strip._CcpnGLWidget.axisB, self.strip._CcpnGLWidget.axisT]]
        for n in self.strip.orderedAxes[2:]:
            selectedRegion.append((n.region[0], n.region[1]))

        if self.spectrum.dimensionCount > 1:
            sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]
            spectrumAxisCodes = self.spectrum.axisCodes
            stripAxisCodes = self.strip.axisCodes
            regionToPick = [0] * self.spectrum.dimensionCount

            remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
            if remapIndices:
                for n, axisCode in enumerate(spectrumAxisCodes):
                    # idx = stripAxisCodes.index(axisCode)
                    idx = remapIndices[n]
                    regionToPick[n] = sortedSelectedRegion[idx]
            else:
                regionToPick = sortedSelectedRegion

        startPoint = []
        endPoint = []
        spectrum = self.spectrum
        dataDims = spectrum._apiDataSource.sortedDataDims()
        aliasingLimits = spectrum.aliasingLimits
        apiPeaks = []
        # for ii, dataDim in enumerate(dataDims):
        spectrumReferences = spectrum.mainSpectrumReferences
        if None in spectrumReferences:
            raise ValueError("pickPeaksNd() only works for Frequency dimensions"
                             " with defined primary SpectrumReferences ")
        if regionToPick is None:
            regionToPick = self.spectrum.aliasingLimits
        for ii, spectrumReference in enumerate(spectrumReferences):
            aliasingLimit0, aliasingLimit1 = aliasingLimits[ii]
            value0 = regionToPick[ii][0]
            value1 = regionToPick[ii][1]
            value0, value1 = min(value0, value1), max(value0, value1)
            if value1 < aliasingLimit0 or value0 > aliasingLimit1:
                break  # completely outside aliasing region
            value0 = max(value0, aliasingLimit0)
            value1 = min(value1, aliasingLimit1)

            position0 = spectrumReference.valueToPoint(value0) - 1
            position1 = spectrumReference.valueToPoint(value1) - 1
            position0, position1 = min(position0, position1), max(position0, position1)

            position0 = int(position0 + 1)
            position1 = int(position1 + 1)

            startPoint.append((spectrumReference.dimension, position0))
            endPoint.append((spectrumReference.dimension, position1))
        else:
            startPoints = [point[1] for point in sorted(startPoint)]
            endPoints = [point[1] for point in sorted(endPoint)]

            # print('>>>', startPoint, startPoints, endPoint, endPoints)

        # originally from the PeakList datasource which should be the same as the spectrum _apiDataSource
        # dataSource = self.dataSource
        dataSource = self.spectrum._apiDataSource
        numDim = dataSource.numDim

        minLinewidth = [0.0] * numDim
        exclusionBuffer = [0] * numDim          # [1] * numDim
        nonAdj = 0
        excludedRegions = []
        excludedDiagonalDims = []
        excludedDiagonalTransform = []

        startPoint = np.array(startPoints)
        endPoint = np.array(endPoints)

        startPoint, endPoint = np.minimum(startPoint, endPoint), np.maximum(startPoint, endPoint)

        # extend region by exclusionBuffer
        bufferArray = np.array(exclusionBuffer)
        startPointBuffer = startPoint - bufferArray
        endPointBuffer = endPoint + bufferArray

        regions = numDim * [0]
        npts = numDim * [0]
        for n in range(numDim):
            start = startPointBuffer[n]
            end = endPointBuffer[n]
            npts[n] = dataSource.findFirstDataDim(dim=n + 1).numPointsOrig
            tile0 = start // npts[n]
            tile1 = (end - 1) // npts[n]
            region = regions[n] = []
            if tile0 == tile1:
                region.append((start, end, tile0))
            else:
                region.append((start, (tile0 + 1) * npts[n], tile0))
                region.append((tile1 * npts[n], end, tile1))
            for tile in range(tile0 + 1, tile1):
                region.append((tile * npts[n], (tile + 1) * npts[n], tile))

        peaks = []
        objectsCreated = []

        nregions = [len(region) for region in regions]
        nregionsTotal, cumulRegions = _cumulativeArray(nregions)
        for n in range(nregionsTotal):
            array = _arrayOfIndex(n, cumulRegions)
            chosenRegion = [regions[i][array[i]] for i in range(numDim)]
            startPointBufferActual = np.array([cr[0] for cr in chosenRegion])
            endPointBufferActual = np.array([cr[1] for cr in chosenRegion])
            tile = np.array([cr[2] for cr in chosenRegion])
            startPointBuffer = np.array([startPointBufferActual[i] - tile[i] * npts[i] for i in range(numDim)])
            endPointBuffer = np.array([endPointBufferActual[i] - tile[i] * npts[i] for i in range(numDim)])

            dataArray, intRegion = dataSource.getRegionData(startPointBuffer, endPointBuffer)
            pass

        # populate the widgets
        self.noiseLevelSpinBox.setValue(self.noise)

        self.meanLabel.setText(str(regionToPick))

    def _setNoiseLevel(self):
        """Apply the current noiseLevel to the spectrum
        """
        pass
