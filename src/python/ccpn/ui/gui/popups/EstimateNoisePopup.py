"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.Common import getAxisCodeMatchIndices
from collections import OrderedDict
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.core.lib.SpectrumLib import setContourLevelsFromNoise, DEFAULTLEVELS, DEFAULTMULTIPLIER, DEFAULTCONTOURBASE


COL_WIDTH = 140


class EstimateNoisePopup(CcpnDialog):
    MINIMUM_WIDTH_PER_TAB = 100
    MINIMUM_WIDTH = 400
    MAXIMUM_WIDTH = 700

    def __init__(self, parent=None, mainWindow=None, title='Estimate Noise',
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

        # add a tab for each spectrum in the spectrumDisplay
        self._noiseTab = []
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            if thisSpec.dimensionCount > 1:
                self._noiseTab.append(NoiseTabNd(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=strip))
            else:
                self._noiseTab.append(NoiseTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=strip))

            self.tabWidget.addTab(self._noiseTab[specNum], thisSpec.name)

        ButtonList(self, ['Close'], [self._accept], grid=(2, 3))

        # restrict the width of the tab widget
        self.tabWidget.adjustSize()
        self.tabWidget.setFixedHeight(self.tabWidget.sizeHint().height())
        self.tabWidget.setFixedWidth(min(max(self.MINIMUM_WIDTH, self.MINIMUM_WIDTH_PER_TAB * len(self.orderedSpectra)),
                                         self.MAXIMUM_WIDTH))

        # restrict popup size
        self.adjustSize()
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
    """Class to contain the information for a single pectrum in the spectrum display
    Holds the common values for 1d and Nd spectra
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None, **kwds):
        """Initialise the tab settings
        """
        super().__init__(parent, setLayout=True, **kwds)

        self._parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.strip = strip
        self.noiseLevel = None

        # set up the common widgets
        row = 0

        self.axisCodes = [i for i in range(len(spectrum.axisCodes))]
        for ii, axis in enumerate(spectrum.axisCodes):
            Label(self, text=axis, grid=(row, 0), vAlign='t', hAlign='l')
            self.axisCodes[ii] = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')
            row += 1

        Label(self, text='Mean', grid=(row, 0), vAlign='t', hAlign='l')
        self.meanLabel = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='SD', grid=(row, 0), vAlign='t', hAlign='l')
        self.SDLabel = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='Max', grid=(row, 0), vAlign='t', hAlign='l')
        self.maxLabel = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')

        row += 1
        Label(self, text='Min', grid=(row, 0), vAlign='t', hAlign='l')
        self.minLabel = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')

        # row += 1
        # HLine(parent, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        Label(self, text='Current Noise Level', grid=(row, 0), vAlign='t', hAlign='l')
        self.currentNoiseLabel = Label(self, text='<None>', grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l')
        self.currentNoiseLabel.setText(str(self.spectrum.noiseLevel))
        self.recalculateLevelsButton = Button(self, grid=(row, 2), callback=self._calculateLevels, text='Recalculate Noise')

        row += 1
        Label(self, text='Estimated Noise Level', grid=(row, 0), vAlign='t', hAlign='l')
        self.noiseLevelSpinBox = ScientificDoubleSpinBox(self, grid=(row, 1), vAlign='t')
        self.noiseLevelSpinBox.setMaximum(1e12)
        self.noiseLevelSpinBox.setMinimum(0.1)

        # self.noiseLevelButton = Button(self, grid=(row, 2), callback=self._setNoiseLevel, text='Set Noise')
        self.noiseLevelButtons = ButtonList(self, grid=(row, 2), callbacks=[self._setNoiseLevel],
                                            texts=['Set Noise'])

        # remember the row for subclassed Nd below
        self.row = row

        self._calculateLevels()

    def _calculateLevels(self):
        # calculate the region over which to estimate the noise
        selectedRegion = [[self.strip._CcpnGLWidget.axisL, self.strip._CcpnGLWidget.axisR],
                          [self.strip._CcpnGLWidget.axisB, self.strip._CcpnGLWidget.axisT]]
        for n in self.strip.orderedAxes[2:]:
            selectedRegion.append((n.region[0], n.region[1]))
        sortedSelectedRegion = [list(sorted(x)) for x in selectedRegion]

        # get indexing for spectrum onto strip.axisCodes
        indices = getAxisCodeMatchIndices(self.spectrum.axisCodes, self.strip.axisCodes)

        if None in indices:
            return

        # map the spectrum selectedRegions to the strip
        axisCodeDict = OrderedDict((code, sortedSelectedRegion[indices[ii]])
                                   for ii, code in enumerate(self.spectrum.axisCodes) if indices[ii] is not None)

        # add an exclusion buffer to ensure that getRegionData always returns a region,
        # otherwise region may be 1 plain thick which will contradict error trapping for peak fitting
        # (which requires at least 3 points in each dimension)
        # exclusionBuffer = [1] * self.spectrum.dimensionCount
        # however, this shouldn't be needed of the range is > valuePrePoint in each dimension

        foundRegions = self.spectrum.getRegionData(minimumDimensionSize=1, **axisCodeDict)

        if foundRegions:

            # just use the first region
            for region in foundRegions[:1]:
                dataArray, intRegion, *rest = region

                if dataArray.size:
                    # calculate the noise values
                    flatData = dataArray.flatten()

                    self.SD = np.std(flatData)
                    self.max = np.max(flatData)
                    self.min = np.min(flatData)
                    self.mean = np.mean(flatData)
                    self.noiseLevel = abs(self.mean) + 3.0 * self.SD

                    # populate the widgets
                    for ii, ind in enumerate(indices):
                        self.axisCodes[ii].setText('(' + ','.join(['%.3f' % rr for rr in sortedSelectedRegion[ind]]) + ')')

                    self.meanLabel.setText(str(self.mean))
                    self.SDLabel.setText(str(self.SD))
                    self.maxLabel.setText(str(self.max))
                    self.minLabel.setText(str(self.min))
                    self.noiseLevelSpinBox.setValue(self.noiseLevel)

        else:
            # no regions so just put the current noise level back into the spinBox
            self.noiseLevelSpinBox.setValue(self.spectrum.noiseLevel)

    def _setNoiseLevel(self):
        """Apply the current noiseLevel to the spectrum
        """
        self.spectrum.noiseLevel = float(self.noiseLevelSpinBox.value())


def _addContourNoiseButtons(self, row, buttonLabel='Set Contours'):
    row += 1
    HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[SOFTDIVIDER], height=15)

    row += 1
    Label(self, text='Estimate Contour Levels', grid=(row, 0), gridSpan=(1, 3), vAlign='t', hAlign='l')

    from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget

    row += 1
    self.setPositiveContours = CheckBoxCompoundWidget(self, grid=(row, 0), gridSpan=(1, 3),
                                                      vAlign='top', stretch=(0, 0), hAlign='left',
                                                      orientation='right', margins=(15, 0, 0, 0),
                                                      labelText='Set positive contour levels',
                                                      checked=True
                                                      )

    row += 1
    self.setNegativeContours = CheckBoxCompoundWidget(self, grid=(row, 0), gridSpan=(1, 3),
                                                      vAlign='top', stretch=(0, 0), hAlign='left',
                                                      orientation='right', margins=(15, 0, 0, 0),
                                                      labelText='Set negative contour levels',
                                                      checked=True
                                                      )

    row += 1
    self.setUseSameMultiplier = CheckBoxCompoundWidget(self, grid=(row, 0), gridSpan=(1, 3),
                                                       vAlign='top', stretch=(0, 0), hAlign='left',
                                                       orientation='right', margins=(15, 0, 0, 0),
                                                       labelText='Use same (positive) multiplier for negative contours',
                                                       checked=True
                                                       )

    row += 1
    self.setDefaults = CheckBoxCompoundWidget(self, grid=(row, 0), gridSpan=(1, 3),
                                              vAlign='top', stretch=(0, 0), hAlign='left',
                                              orientation='right', margins=(15, 0, 0, 0),
                                              labelText='Use default multiplier (%0.3f)\n and contour level count (%i)' % (
                                                  DEFAULTMULTIPLIER, DEFAULTLEVELS),
                                              checked=True
                                              )

    row += 1
    self.noiseLevelButton = Button(self, grid=(row, 2), callback=self._setContourLevels, text=buttonLabel)


class NoiseTabNd(NoiseTab):
    """Class to contain the information for a single spectrum in the spectrum display
    Holds the extra widgets for changing Nd contour settings
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None, **kwds):
        """Initialise the tab settings
        """
        super().__init__(parent=parent, mainWindow=mainWindow, spectrum=spectrum, strip=strip, **kwds)

        row = self.row
        _addContourNoiseButtons(self, self.row)

    def _setContourLevels(self):
        """Estimate the contour levels for the current spectrum
        """
        setContourLevelsFromNoise(self.spectrum, setNoiseLevel=False,
                                  setPositiveContours=self.setPositiveContours.isChecked(),
                                  setNegativeContours=self.setNegativeContours.isChecked(),
                                  useSameMultiplier=self.setUseSameMultiplier.isChecked(),
                                  useDefaultLevels=self.setDefaults.isChecked(),
                                  useDefaultMultiplier=self.setDefaults.isChecked())
