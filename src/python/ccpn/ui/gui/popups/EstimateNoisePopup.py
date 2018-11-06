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
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util import Common as commonUtil


class EstimateNoisePopup(CcpnDialog):
    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 400

    def __init__(self, parent=None, mainWindow=None, title='EstimateNoise',
                 strip=None, orderedSpectrumViews=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

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

        # add a tab for each spectrum in the spectrumDisplay
        self._noiseTab = []
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            self._noiseTab.append(NoiseTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=strip))
            self.tabWidget.addTab(self._noiseTab[specNum], thisSpec.name)

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


class NoiseTab(Widget):

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)

        self._parent = parent
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

        # This can be moved somewhere more sensible

        # calculate the region over which to estimate the noise
        selectedRegion = [[self.strip._CcpnGLWidget.axisL, self.strip._CcpnGLWidget.axisR],
                          [self.strip._CcpnGLWidget.axisB, self.strip._CcpnGLWidget.axisT]]
        for n in self.strip.orderedAxes[2:]:
            selectedRegion.append((n.region[0], n.region[1]))

        sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]

        # map the limits to the correct axisCodes
        axisCodeDict = {}
        if self.spectrum.dimensionCount > 1:
            spectrumAxisCodes = self.spectrum.axisCodes
            stripAxisCodes = self.strip.axisCodes

            # get the ordering of the strip axisCodes in the spectrum
            try:
                indices = self.spectrum.getByAxisCodes('indices', stripAxisCodes)
            except Exception as es:

                # spectrum possibly no compatible here, may be 2d overlaid onto Nd
                indices = self.spectrum.getByAxisCodes('indices', stripAxisCodes[0:2])

            # sort the axis limits by spectrum axis order
            for ii, ind in enumerate(indices):
                axisCodeDict[spectrumAxisCodes[ind]] = sortedSelectedRegion[ii]

            # # sort the axis limits by spectrum axis order
            # for n, axisCode in enumerate(spectrumAxisCodes):
            #     if indices and n <len(indices):
            #         axisCodeDict[axisCode] = sortedSelectedRegion[indices[n]]

            # regionToPick = [0] * self.spectrum.dimensionCount
            #
            # remapIndices = commonUtil._axisCodeMapIndices(stripAxisCodes, spectrumAxisCodes)
            # if remapIndices:
            #     for n, axisCode in enumerate(spectrumAxisCodes):
            #         # idx = stripAxisCodes.index(axisCode)
            #         idx = remapIndices[n]
            #         regionToPick[n] = sortedSelectedRegion[idx]
            #
            #         axisCodeDict[axisCode] = sortedSelectedRegion[idx]
            # else:
            #     regionToPick = sortedSelectedRegion
            #
            #     for n, axisCode in enumerate(spectrumAxisCodes):
            #         axisCodeDict[axisCode] = sortedSelectedRegion[n]

        else:
            spectrumAxisCodes = self.spectrum.axisCodes
            stripAxisCodes = self.strip.axisCodes

            # get the ordering of the strip axisCodes in the spectrum
            indices = self.spectrum.getByAxisCodes('indices', stripAxisCodes)

            # sort the axis limits by spectrum axis order
            for n, axisCode in enumerate(spectrumAxisCodes):
                axisCodeDict[axisCode] = sortedSelectedRegion[indices[n]]

        dataArray, intRegion = self.spectrum.getRegionData(**axisCodeDict)

        if dataArray.size:
            # calculate the noise values
            flatData = dataArray.flatten()

            self.SD = np.std(flatData)
            self.max = np.max(flatData)
            self.min = np.min(flatData)
            self.mean = np.mean(flatData)
            self.noiseLevel = self.mean + 3.0 * self.SD

            # populate the widgets
            # for axis, region in enumerate(sortedSelectedRegion):

            for ii, ind in enumerate(indices):
                self.axisCodes[ii].setText('(' + ','.join(['%.3f' % rr for rr in sortedSelectedRegion[ind]]) + ')')
            self.meanLabel.setText(str(self.mean))
            self.SDLabel.setText(str(self.SD))
            self.maxLabel.setText(str(self.max))
            self.minLabel.setText(str(self.min))
            self.noiseLevelSpinBox.setValue(self.noiseLevel)

    def _setNoiseLevel(self):
        """Apply the current noiseLevel to the spectrum
        """
        self.spectrum.noiseLevel = self.noiseLevel
