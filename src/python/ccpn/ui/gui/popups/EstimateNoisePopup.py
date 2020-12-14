"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-12-03 10:01:42 +0000 (Thu, December 03, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.Common import getAxisCodeMatchIndices
from collections import OrderedDict
from ccpn.ui.gui.guiSettings import getColours, SOFTDIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.core.lib.SpectrumLib import setContourLevelsFromNoise, DEFAULTLEVELS, DEFAULTMULTIPLIER, DEFAULTCONTOURBASE
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget, ScientificSpinBoxCompoundWidget, \
    RadioButtonsCompoundWidget, PulldownListCompoundWidget, SpinBoxCompoundWidget, TextEditorCompoundWidget
from ccpn.core.lib.SpectrumLib import getNoiseEstimate


COL_WIDTH = 140
NONE_TEXT = '-'
MINIMUM_WIDTH_PER_TAB = 100
MINIMUM_WIDTH = 400
MAXIMUM_WIDTH = 700
ESTIMATEMETHOD = 'estimateMethod'
ESTIMATECONTOURS = 'estimateContours'
ESTIMATEPOSITIVE = 'estimatePositive'
ESTIMATENEGATIVE = 'estimateNegative'
ESTIMATEMULTIPLIER = 'estimateMultiplier'
ESTIMATEDEFAULT = 'estimateDefault'
ESTIMATEAUTO = 'estimateAuto'


class EstimateNoisePopup(CcpnDialogMainWidget):
    """
    Class to implement a ppopup for estimating noise in a set of spectra
    """

    def __init__(self, parent=None, mainWindow=None, title='Estimate Noise',
                 strip=None, orderedSpectrumViews=None, **kwds):
        """
        Initialise the widget
        """
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

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
        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = OrderedSet([spec.spectrum for spec in self.orderedSpectrumViews])

        # create the list of widgets and set the callbacks for each
        self._setWidgets()

        # set up the required buttons for the dialog
        self.setCloseButton(callback=self.accept, enabled=True)
        self.setHelpButton(callback=self.reject, enabled=False)
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

        # populate the widgets
        self._populate()

        # set the links to the buttons
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)
        self._helpButton = self.dialogButtons.button(self.HELPBUTTON)

        # make automatic estimates
        self._autoEstimate()

    def _accept(self):
        """Close button pressed
        """
        self.accept()

    def _cleanupWidget(self):
        """Cleanup the notifiers that are left behind after the widget is closed
        """
        self.close()

    def _setWidgets(self):
        self.stripLabel = Label(self.mainWidget, grid=(0, 0), gridSpan=(1, 4))

        # this will need to change in the future to a better method of listing spectra
        self.tabWidget = Tabs(self.mainWidget, setLayout=True, grid=(1, 0), gridSpan=(1, 4))
        self.infoFrame = Frame(self.mainWidget, setLayout=True, grid=(2, 0), gridSpan=(1, 4))
        self.commonFrame = Frame(self.mainWidget, setLayout=True, grid=(3, 0), gridSpan=(1, 4))

        # add a tab for each spectrum in the spectrumDisplay
        self._noiseTab = []
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            if thisSpec.dimensionCount > 1:
                self._noiseTab.append(NoiseTabNd(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=self.strip))
            else:
                self._noiseTab.append(NoiseTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec, strip=self.strip))

            self.tabWidget.addTab(self._noiseTab[specNum], thisSpec.name)

        self._setInfoWidgets()
        self._setCommonWidgets()

    def _setInfoWidgets(self):
        row = 0
        # NOTE:ED - this is not very good or generic, needs possibly a plugin type methods

        texts = ['Visible Area', 'Random Sampling']
        tipTexts = ['Estimate the noise from the visible plane',
                    'Estimate the noise from a random sampling of the whole spectrum']

        self.estimateOption = RadioButtonsCompoundWidget(self.infoFrame, labelText='Estimation method',
                                                         # callback=self._selectionButtonCallback,
                                                         # direction='h',
                                                         # tipTexts=None,
                                                         grid=(row, 0), gridSpan=(1, 2),
                                                         compoundKwds={'direction': 'h',
                                                                       # 'selectedInd': 0,
                                                                       'texts'    : texts,
                                                                       'tipTexts' : tipTexts})

    def _setCommonWidgets(self):
        row = 0
        # checkbox to recalculate on first popup - False to start
        self.autoCalculate = CheckBoxCompoundWidget(self.commonFrame,
                                                    grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                    #minimumWidths=(colwidth, 0),
                                                    # fixedWidths=(30, None),
                                                    orientation='right',
                                                    labelText='Automatically estimate noise on popup',
                                                    checked=False)

        # row += 1
        # tipText = 'Maximum number of random samples taken from spectrum'
        # self.randomSamples = SpinBoxCompoundWidget(self.infoFrame, labelText='Maximum Random Samples',
        #                                            grid=(row, 0), gridSpan=(1, 2),
        #                                            compoundKwds={'min': 1,
        #                                                          'max': 10000,
        #                                                          'step': 1,
        #                                                          'tipText': tipText})

        self._infoRow = row
        if not self.strip.spectrumDisplay.is1D:
            self._addContourNoiseButtons(self._infoRow, self.infoFrame)

    def _addContourNoiseButtons(self, row, frame, buttonLabel='Set Contours'):
        # add a series of buttons to the infoFrame
        row += 1
        HLine(frame, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[SOFTDIVIDER], height=15)

        row += 1
        Label(frame, text='Contour Options', grid=(row, 0), gridSpan=(1, 3), vAlign='t', hAlign='l')

        from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget

        row += 1
        self.setPositiveContours = CheckBoxCompoundWidget(frame, grid=(row, 0), gridSpan=(1, 3),
                                                          vAlign='top', stretch=(0, 0), hAlign='left',
                                                          orientation='right', margins=(15, 0, 0, 0),
                                                          labelText='Set positive contour levels',
                                                          checked=True
                                                          )

        row += 1
        self.setNegativeContours = CheckBoxCompoundWidget(frame, grid=(row, 0), gridSpan=(1, 3),
                                                          vAlign='top', stretch=(0, 0), hAlign='left',
                                                          orientation='right', margins=(15, 0, 0, 0),
                                                          labelText='Set negative contour levels',
                                                          checked=True
                                                          )

        row += 1
        self.setUseSameMultiplier = CheckBoxCompoundWidget(frame, grid=(row, 0), gridSpan=(1, 3),
                                                           vAlign='top', stretch=(0, 0), hAlign='left',
                                                           orientation='right', margins=(15, 0, 0, 0),
                                                           labelText='Use same (positive) multiplier for negative contours',
                                                           checked=True
                                                           )

        row += 1
        self.setDefaults = CheckBoxCompoundWidget(frame, grid=(row, 0), gridSpan=(1, 3),
                                                  vAlign='top', stretch=(0, 0), hAlign='left',
                                                  orientation='right', margins=(15, 0, 0, 0),
                                                  labelText='Use default multiplier (%0.3f)\n and contour level count (%i)' % (
                                                      DEFAULTMULTIPLIER, DEFAULTLEVELS),
                                                  checked=True
                                                  )

        # row += 1
        # self.noiseLevelButton = Button(frame, grid=(row, 2), callback=self._setContourLevels, text=buttonLabel)

    def _populate(self):
        # populate any settings in the popup and the tabs
        self.stripLabel.setText(f'Current strip: {self.strip.id}')
        for tab in self._noiseTab:
            tab._populate()

    def _autoEstimate(self):
        # calculate an estimate for each of the tabs
        if self.autoCalculate.isChecked():
            for tab in self._noiseTab:
                tab._estimateNoise()

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        for tab in self._noiseTab:
            # may not be necessary
            tab._storeWidgetState()

        if ESTIMATECONTOURS not in EstimateNoisePopup._storedState:
            EstimateNoisePopup._storedState[ESTIMATECONTOURS] = {ESTIMATEMETHOD: self.estimateOption.getIndex(),
                                                                 ESTIMATEAUTO  : self.autoCalculate.isChecked()
                                                                 }
        else:
            EstimateNoisePopup._storedState[ESTIMATECONTOURS].update({ESTIMATEMETHOD: self.estimateOption.getIndex(),
                                                                 ESTIMATEAUTO  : self.autoCalculate.isChecked()
                                                                 })

        if not self.strip.spectrumDisplay.is1D:
            EstimateNoisePopup._storedState[ESTIMATECONTOURS].update({ESTIMATEPOSITIVE  : self.setPositiveContours.isChecked(),
                                                                      ESTIMATENEGATIVE  : self.setNegativeContours.isChecked(),
                                                                      ESTIMATEMULTIPLIER: self.setUseSameMultiplier.isChecked(),
                                                                      ESTIMATEDEFAULT   : self.setDefaults.isChecked(),
                                                                      })

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        for tab in self._noiseTab:
            # may not be necessary
            tab._restoreWidgetState()

        states = EstimateNoisePopup._storedState.get(ESTIMATECONTOURS)
        if states:
            self.estimateOption.setIndex(states.get(ESTIMATEMETHOD))
            self.autoCalculate.set(states.get(ESTIMATEAUTO))
            if not self.strip.spectrumDisplay.is1D:
                self.setPositiveContours.set(states.get(ESTIMATEPOSITIVE, False))
                self.setNegativeContours.set(states.get(ESTIMATENEGATIVE, False))
                self.setUseSameMultiplier.set(states.get(ESTIMATEMULTIPLIER, False))
                self.setDefaults.set(states.get(ESTIMATEDEFAULT, False))


class NoiseTab(Widget):
    """Class to contain the information for a single pectrum in the spectrum display
    Holds the common values for 1d and Nd spectra
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None, **kwds):
        """Initialise the tab settings
        """
        super().__init__(parent, setLayout=True, **kwds)
        self.setContentsMargins(5, 5, 5, 5)

        self._parent = parent
        self.mainWindow = mainWindow
        self.current = self.mainWindow.current
        self.spectrum = spectrum
        self.strip = strip
        self.noiseLevel = None

        # create the list of widgets and set the callbacks for each
        self._setWidgets()
        self._setFromCurrentCursor()

    def _setWidgets(self):
        # set up the common widgets
        row = 0

        self.axisCodeLabels = []
        for ii, axis in enumerate(self.spectrum.axisCodes):
            Label(self, text=axis, grid=(row, 0), vAlign='t', hAlign='l')
            self.axisCodeLabels.append(Label(self, text=NONE_TEXT, grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l'))
            row += 1

        for label, text in zip(['meanLabel', 'SDLabel', 'maxLabel', 'minLabel'], ['Mean', 'SD', 'Max', 'Min']):
            Label(self, text=text, grid=(row, 0), vAlign='t', hAlign='l')
            setattr(self, label, Label(self, text=NONE_TEXT, grid=(row, 1), gridSpan=(1, 2), vAlign='t', hAlign='l'))
            row += 1

        Label(self, text='Estimated Noise Level', grid=(row, 0), vAlign='c', hAlign='l')
        self.noiseLevelSpinBox = ScientificDoubleSpinBox(self, grid=(row, 1), vAlign='t')
        self.noiseLevelSpinBox.setMaximum(1e12)
        self.noiseLevelSpinBox.setMinimum(0.1)
        self.noiseLevelSpinBox.setMinimumCharacters(15)
        self.recalculateLevelsButton = Button(self, grid=(row, 2), callback=self._estimateNoise, text='Estimate Noise')

        row += 1
        Label(self, text='Current Noise Level', grid=(row, 0), vAlign='c', hAlign='l')
        self.currentNoiseLabel = Label(self, text=NONE_TEXT, grid=(row, 1), gridSpan=(1, 2), vAlign='c', hAlign='l')

        row += 1
        self.noiseLevelButtons = ButtonList(self, grid=(row, 2), callbacks=[self._setNoiseLevel],
                                            texts=['Set noiseLevel'])

        # remember the row for subclassed Nd below
        self.row = row

    def _populate(self):
        # populate the widgets, but don't perform any calculations
        if self.spectrum.noiseLevel is not None:
            self.currentNoiseLabel.setText(f'{self.spectrum.noiseLevel:.3f}')

    def _setFromCurrentCursor(self):
        "Add the initial spinbox value  from  the current cursor position. Implemented only for 1D."
        if self.mainWindow.current is not None:
            if self.spectrum.dimensionCount == 1:
                if self.current.cursorPosition:
                    self.noiseLevelSpinBox.set(float(self.current.cursorPosition[-1]))

    def _estimateNoise(self):
        # get the current mode and call the relevant estimate routine
        ind = self._parent.estimateOption.getIndex()
        if ind == 0:
            self._estimateFromRegion()
        elif ind == 1:
            self._estimateFromRandomSamples()

    def _estimateFromRegion(self):
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
                        self.axisCodeLabels[ii].setText('(' + ','.join(['%.3f' % rr for rr in sortedSelectedRegion[ind]]) + ')')

                    self._setLabels(self.mean, self.SD, self.min, self.max, self.noiseLevel)

        else:
            # no regions so just put the current noise level back into the spinBox
            self.noiseLevelSpinBox.setValue(self.spectrum.noiseLevel)

    def _estimateFromRandomSamples(self):
        # populate the widgets
        noise = getNoiseEstimate(self.spectrum)

        # clear the range labels (full range is implied)
        for lbl in self.axisCodeLabels:
            lbl.setText('-')

        self._setLabels(noise.mean, noise.std, noise.min, noise.max, noise.noiseLevel)

    def _setLabels(self, mean, std, min, max, noiseLevel):
        # fill the labels with the new values
        self.meanLabel.setText(f'{mean:.3f}')
        self.SDLabel.setText(f'{std:.3f}')
        self.maxLabel.setText(f'{max:.3f}')
        self.minLabel.setText(f'{min:.3f}')
        self.noiseLevelSpinBox.setValue(noiseLevel)

    def _setNoiseLevel(self):
        """Apply the current noiseLevel to the spectrum
        """
        value =  float(self.noiseLevelSpinBox.value())
        self.spectrum.noiseLevel = value
        self.spectrum.negativeNoiseLevel = -value if value > 0 else value*2
        self._populate()

    def _storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        pass

    def _restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        pass


class NoiseTabNd(NoiseTab):
    """Class to contain the information for a single spectrum in the spectrum display
    Holds the extra widgets for changing Nd contour settings
    """

    def __init__(self, parent=None, mainWindow=None, spectrum=None, strip=None, **kwds):
        """Initialise the tab settings
        """
        super().__init__(parent=parent, mainWindow=mainWindow, spectrum=spectrum, strip=strip, **kwds)
        self._parent = parent

    def _setWidgets(self):
        self.row = 0
        super()._setWidgets()

        # add the extra button
        self._addContourNoiseButtons(self.row, self)

    def _setContourLevels(self):
        """Estimate the contour levels for the current spectrum
        """
        # get the settings from the parent checkboxes
        setContourLevelsFromNoise(self.spectrum, setNoiseLevel=False,
                                  setPositiveContours=self._parent.setPositiveContours.isChecked(),
                                  setNegativeContours=self._parent.setNegativeContours.isChecked(),
                                  useSameMultiplier=self._parent.setUseSameMultiplier.isChecked(),
                                  useDefaultLevels=self._parent.setDefaults.isChecked(),
                                  useDefaultMultiplier=self._parent.setDefaults.isChecked())

    def _addContourNoiseButtons(self, row, frame, buttonLabel='Generate Contours'):
        row += 1
        self.noiseLevelButton = Button(frame, grid=(row, 2), callback=self._setContourLevels, text=buttonLabel)
