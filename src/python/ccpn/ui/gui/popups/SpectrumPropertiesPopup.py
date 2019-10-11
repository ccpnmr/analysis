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
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from PyQt5 import QtWidgets, QtCore
from itertools import permutations
from ccpn.core.lib import Util as ccpnUtil
from ccpn.core.Spectrum import MAXALIASINGRANGE
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ColourDialog import ColourDialog
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox, ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.popups.ExperimentTypePopup import _getExperimentTypes
from ccpn.util.Colour import spectrumColours, addNewColour, fillColourPulldown, addNewColourString, colourNameNoSpace
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.util.Logging import getLogger
from ccpn.util.Constants import DEFAULT_ISOTOPE_DICT
from ccpn.util.OrderedSet import OrderedSet
from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlock
from ccpn.ui.gui.popups.ValidateSpectraPopup import SpectrumValidator
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import PulldownListCompoundWidget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.popups.Dialog import CcpnDialog, handleDialogApply, CANCELBUTTONTEXT, APPLYBUTTONTEXT, OKBUTTONTEXT
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.ui.gui.popups.EstimateNoisePopup import _addContourNoiseButtons
from ccpn.core.lib.SpectrumLib import getContourLevelsFromNoise
from ccpn.core.lib.ContextManagers import queueStateChange


SPECTRA = ['1H', 'STD', 'Relaxation Filtered', 'Water LOGSY']


def _updateGl(self, spectrumList):
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

    # # spawn a redraw of the contours
    # for spec in spectrumList:
    #     for specViews in spec.spectrumViews:
    #         specViews.buildContours = True

    GLSignals = GLNotifier(parent=self)
    GLSignals.emitPaintEvent()


class SpectrumPropertiesPopup(CcpnDialog):
    # The values on the 'General' and 'Dimensions' tabs are queued as partial functions when set.
    # The apply button then steps through each tab, and calls each function in the _changes dictionary
    # in order to set the parameters.

    def __init__(self, parent=None, mainWindow=None, spectrum=None,
                 title='Spectrum Properties', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.spectrum = spectrum

        self.tabWidget = Tabs(self, setLayout=True, grid=(0, 0), gridSpan=(2, 4), focusPolicy='strong')

        if spectrum.dimensionCount == 1:
            self._generalTab = GeneralTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum)
            self._dimensionsTab = DimensionsTab(parent=self, mainWindow=self.mainWindow,
                                                spectrum=spectrum, dimensions=spectrum.dimensionCount)

            self.tabWidget.addTab(self._generalTab, "General")
            self.tabWidget.addTab(self._dimensionsTab, "Dimensions")
            self._contoursTab = None
        else:
            self._generalTab = GeneralTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum)
            self._dimensionsTab = DimensionsTab(parent=self, mainWindow=self.mainWindow,
                                                spectrum=spectrum, dimensions=spectrum.dimensionCount)
            self._contoursTab = ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=spectrum)

            self.tabWidget.addTab(self._generalTab, "General")
            self.tabWidget.addTab(self._dimensionsTab, "Dimensions")
            self.tabWidget.addTab(self._contoursTab, "Contours")

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(3, 1), gridSpan=(1, 1))

        self.applyButtons = ButtonList(self, texts=[CANCELBUTTONTEXT, APPLYBUTTONTEXT, OKBUTTONTEXT],
                                       callbacks=[self._rejectButton, self._applyButton, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(4, 1), gridSpan=(1, 4))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setFocus()

        self._fillPullDowns()
        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton(APPLYBUTTONTEXT))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)

    def _fillPullDowns(self):
        if self.spectrum.dimensionCount == 1:
            fillColourPulldown(self._generalTab.colourBox, allowAuto=False)
        else:
            fillColourPulldown(self._contoursTab.positiveColourBox, allowAuto=False)
            fillColourPulldown(self._contoursTab.negativeColourBox, allowAuto=False)

    def _keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            pass

    def _repopulate(self):
        if self._generalTab:
            self._generalTab._repopulate()
        if self._dimensionsTab:
            self._dimensionsTab._repopulate()
        if self._contoursTab:
            self._contoursTab._repopulate()

    def _applyAllChanges(self, changes):
        for v in changes.values():
            v()

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        tabs = (self._generalTab, self._dimensionsTab, self._contoursTab)
        allChanges = any(t._changes for t in tabs if t is not None)

        if not allChanges:
            return True

        with handleDialogApply(self) as error:

            spectrumList = []
            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateGl, self, spectrumList))

            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        self._applyAllChanges(changes)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateGl, self, spectrumList))

            for spec in spectrumList:
                for specViews in spec.spectrumViews:
                    specViews.buildContours = True
            _updateGl(self, spectrumList)

            self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)
            if error.errorValue:
                # repopulate popup on an error
                self._repopulate()
                return False

            return True

    def _rejectButton(self):
        self.reject()

    def _applyButton(self):
        self._applyChanges()

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()


def _verifyApply(tab, attributeName, value, postFix=None):
    """Change the state of the apply button based on the changes in the tabs
    """
    popup = tab._parent

    # if attributeName is defined use as key to dict to store change functions
    # append postFix if need to differentiate partial functions
    if attributeName:
        if postFix is not None:
            attributeName += str(postFix)
        if value:

            # store in dict
            tab._changes[attributeName] = value
        else:
            if attributeName in tab._changes:

                # delete from dict - empty dict implies no changes
                del tab._changes[attributeName]

    if popup:
        # set button state depending on number of changes
        # tabs = (popup._generalTab, popup._dimensionsTab, popup._contoursTab)
        tabs = tuple(popup.tabWidget.widget(ii) for ii in range(popup.tabWidget.count()))
        allChanges = any(t._changes for t in tabs if t is not None)
        popup.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(allChanges)


class GeneralTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, item=None, colourOnly=False):

        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        super().__init__(parent, setLayout=True, spacing=(5, 5))  # ejb
        self.setWindowTitle("Spectrum Properties")

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project

        self.item = item
        self.spectrum = spectrum
        self._changes = dict()
        self.atomCodes = ()

        self.experimentTypes = spectrum._project._experimentTypeMap

        self.layout().addItem(QtWidgets.QSpacerItem(0, 5), 0, 0)
        row = 1

        Label(self, text="PID ", vAlign='t', hAlign='l', grid=(row, 0))
        # self.layout().addItem(QtWidgets.QSpacerItem(0, 5), 0, 0)
        Label(self, text=spectrum.pid, vAlign='t', grid=(row, 1))
        row += 1

        Label(self, text="Name ", grid=(row, 0))
        self.nameData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1))
        self.nameData.setText(spectrum.name)
        self.nameData.textChanged.connect(partial(self._queueSpectrumNameChange, spectrum))  # ejb - was editingFinished
        row += 1

        Label(self, text="Path", vAlign='t', hAlign='l', grid=(row, 0))
        self.pathData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1))
        self.pathData.setValidator(SpectrumValidator(parent=self.pathData, spectrum=spectrum))
        self.pathButton = Button(self, grid=(row, 2), callback=partial(self._getSpectrumFile, spectrum), icon='icons/directory')
        row += 1

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()  # self.spectrum.project._logger

        self.spectrumData = {}
        self.spectrumData[spectrum] = (self.pathData, self.pathButton, Label)
        self._setPathData(spectrum)
        # apiDataStore = spectrum._apiDataSource.dataStore
        # if not apiDataStore:
        #     self.pathData.setText('<None>')
        # elif apiDataStore.dataLocationStore.name == 'standard':
        #     dataUrlName = apiDataStore.dataUrl.name
        #     if dataUrlName == 'insideData':
        #         self.pathData.setText('$INSIDE/%s' % apiDataStore.path)
        #     elif dataUrlName == 'alongsideData':
        #         self.pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
        #     elif dataUrlName == 'remoteData':
        #         self.pathData.setText('$DATA/%s' % apiDataStore.path)
        #     else:
        #         self.pathData.setText(apiDataStore.fullPath)
        # else:
        #     self.pathData.setText(apiDataStore.fullPath)
        self.pathData.textEdited.connect(partial(self._queueSetSpectrumPath, spectrum))

        try:
            index = spectrum.project.chemicalShiftLists.index(spectrum.chemicalShiftList)
        except:
            index = 0
        Label(self, text="ChemicalShiftList ", vAlign='t', hAlign='l', grid=(row, 0))
        self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', grid=(row, 1), index=index,
                                                      texts=[csList.pid for csList in spectrum.project.chemicalShiftLists] + ['<New>'],
                                                      callback=partial(self._queueChemicalShiftListChange, spectrum))
        row += 1

        Label(self, text="Sample", vAlign='t', hAlign='l', grid=(row, 0))
        self.samplesPulldownList = PulldownList(self, texts=['None'], objects=[None], vAlign='t', grid=(row, 1))
        for sample in spectrum.project.samples:
            self.samplesPulldownList.addItem(sample.name, sample)
        if spectrum.sample is not None:
            self.samplesPulldownList.select(spectrum.sample.name)
        self.samplesPulldownList.activated[str].connect(partial(self._queueSampleChange, spectrum))

        if spectrum.dimensionCount == 1:
            Label(self, text="Colour", vAlign='t', hAlign='l', grid=(7, 0))
            self.colourBox = PulldownList(self, vAlign='t', grid=(7, 1))

            # populate initial pulldown
            spectrumColourKeys = list(spectrumColours.keys())
            fillColourPulldown(self.colourBox, allowAuto=False)
            c = spectrum.sliceColour
            if c in spectrumColourKeys:
                self.colourBox.setCurrentText(spectrumColours[c])
            else:
                addNewColourString(c)
                fillColourPulldown(self.colourBox, allowAuto=False)
                spectrumColourKeys = list(spectrumColours.keys())
                self.colourBox.setCurrentText(spectrumColours[c])

            self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))
            colourButton = Button(self, vAlign='t', hAlign='l', grid=(7, 2), hPolicy='fixed',
                                  callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')

            Label(self, text="Experiment Type ", vAlign='t', hAlign='l', grid=(8, 0))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(8, 1))
            spButton = Button(self, grid=(8, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')

            experimentTypes = _getExperimentTypes(spectrum.project, spectrum)
            self.spectrumType.setData(texts=list(experimentTypes.keys()), objects=list(experimentTypes.values()))

            # Added to account for renaming of experiments
            self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))
            if spectrum.experimentType is not None:
                self.spectrumType.select(spectrum.experimentType)

            Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(9, 0))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(9, 1), min=0.1, max=100.0)
            self.spectrumScalingData.setValue(spectrum.scale)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))

            Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(11, 0))
            Label(self, text='n/a', vAlign='t', hAlign='l', grid=(11, 1))

            Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(12, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', hAlign='l', grid=(12, 1))

            if spectrum.noiseLevel is not None:
                self.noiseLevelData.setValue(spectrum.noiseLevel)
            else:
                self.noiseLevelData.setValue(0)
            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))

        else:
            Label(self, text="Experiment Type ", vAlign='t', hAlign='l', grid=(7, 0))
            self.spectrumType = FilteringPulldownList(self, vAlign='t', grid=(7, 1))
            spButton = Button(self, grid=(7, 2),
                              callback=partial(self._raiseExperimentFilterPopup, spectrum),
                              hPolicy='fixed', icon='icons/applications-system')
            experimentTypes = _getExperimentTypes(spectrum.project, spectrum)
            if experimentTypes:
                self.spectrumType.setData(texts=list(experimentTypes.keys()), objects=list(experimentTypes.values()))

            # axisCodes = []
            # for isotopeCode in spectrum.isotopeCodes:
            #   axisCodes.append(''.join([code for code in isotopeCode if not code.isdigit()]))
            #
            # self.atomCodes = tuple(sorted(axisCodes))
            # itemsList = list(self.experimentTypes[spectrum.dimensionCount].get(self.atomCodes).keys())
            # self.spectrumType.addItems(itemsList)
            # Get the text that was used in the pulldown from the refExperiment
            # NBNB This could possibly give unpredictable results
            # if there is an experiment with experimentName (user settable!)
            # that happens to match the synonym for a different experiment type.
            # But if people will ignore our defined vocabulary, on their head be it!
            # Anyway, tha alternative (discarded) is to look into the ExpPrototype
            # to compare RefExperiment names and synonyms
            # or (too ugly for words) to have a third attribute in parallel with
            # spectrum.experimentName and spectrum.experimentType
            text = spectrum.experimentName
            if experimentTypes and text not in experimentTypes:
                text = spectrum.experimentType
            # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
            # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
            # Added to account for renaming of experiments
            text = priorityNameRemapping.get(text, text)
            self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

            self.spectrumType.currentIndexChanged.connect(partial(self._queueSetSpectrumType, spectrum))
            self.spectrumType.setMinimumWidth(self.pathData.width() * 1.95)
            self.spectrumType.setFixedHeight(25)

            spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', grid=(9, 0))
            self.spectrumScalingData = ScientificDoubleSpinBox(self, vAlign='t', grid=(9, 1), min=0.1, max=100.0)
            self.spectrumScalingData.setValue(spectrum.scale)
            self.spectrumScalingData.valueChanged.connect(partial(self._queueSpectrumScaleChange, spectrum, self.spectrumScalingData.textFromValue))

            noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(10, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', grid=(10, 1))

            if spectrum.noiseLevel is None:
                self.noiseLevelData.setValue(spectrum.estimateNoise())
            else:
                self.noiseLevelData.setValue(spectrum.noiseLevel)
            self.noiseLevelData.valueChanged.connect(partial(self._queueNoiseLevelDataChange, spectrum, self.noiseLevelData.textFromValue))

            self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(12, 1), gridSpan=(1, 1))

    def _setPathDataFromUrl(self, spectrum, newFilePath):
        """Set the pathData widgets from the dataUrl.
        """
        # from ValidateSpectraPopup...
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]

            dataUrl = spectrum.project._wrappedData.root.fetchDataUrl(newFilePath)

            # apiDataStore = spectrum._apiDataSource.dataStore
            # # apiDataStore = dataUrl.dataStore
            #
            # standardStore = spectrum.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
            # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls()
            #           for url in store.sortedDataStores() if url == dataUrl.url]
            # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]

            apiDataStores = [store for store in dataUrl.sortedDataStores() if store.fullPath == newFilePath]
            if not apiDataStores:
                return

            apiDataStore = apiDataStores[0]

            if not apiDataStore:
                pathData.setText('<None>')
            elif apiDataStore.dataLocationStore.name == 'standard':

                # this fails on the first loading of V2 projects - ordering issue?
                dataUrlName = apiDataStore.dataUrl.name
                if dataUrlName == 'insideData':
                    pathData.setText('$INSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'alongsideData':
                    pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'remoteData':
                    pathData.setText('$DATA/%s' % apiDataStore.path)
            else:
                pathData.setText(apiDataStore.fullPath)

            pathData.validator().resetCheck()

    def _setPathData(self, spectrum):
        """Set the pathData widgets from the spectrum.
        """
        # from ValidateSpectraPopup...
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]

            apiDataStore = spectrum._apiDataSource.dataStore
            if not apiDataStore:
                pathData.setText('<None>')
            elif apiDataStore.dataLocationStore.name == 'standard':

                # this fails on the first loading of V2 projects - ordering issue?
                dataUrlName = apiDataStore.dataUrl.name
                if dataUrlName == 'insideData':
                    pathData.setText('$INSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'alongsideData':
                    pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'remoteData':
                    pathData.setText('$DATA/%s' % apiDataStore.path)
            else:
                pathData.setText(apiDataStore.fullPath)

            pathData.validator().resetCheck()

    def _repopulate(self):
        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        self.nameData.setText(self.spectrum.name)
        self.pathData.setValidator(SpectrumValidator(parent=self.pathData, spectrum=self.spectrum))

        try:
            index = self.spectrum.project.chemicalShiftLists.index(self.spectrum.chemicalShiftList)
        except:
            index = 0
        self.chemicalShiftListPulldown.setIndex(index)

        if self.spectrum.sample is not None:
            self.samplesPulldownList.select(self.spectrum.sample.name)

        if self.atomCodes:
            itemsList = list(self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).keys())
            self.spectrumType.addItems(itemsList)
            text = self.spectrum.experimentName
            if text not in itemsList:
                text = self.spectrum.experimentType
            text = priorityNameRemapping.get(text, text)
            self.spectrumType.setCurrentIndex(self.spectrumType.findText(text))

        if self.spectrum.scale is not None:
            self.spectrumScalingData.setText(str(self.spectrum.scale))

        if self.spectrum.noiseLevel is None:
            self.noiseLevelData.setValue(self.spectrum.estimateNoise())
        else:
            self.noiseLevelData.setValue(self.spectrum.noiseLevel)

        # if self.spectrum.noiseLevel is None:
        #     self.noiseLevelData.setText(str('%.3d' % self.spectrum.estimateNoise()))
        # else:
        #     self.noiseLevelData.setText('%.3d' % self.spectrum.noiseLevel)

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)







    @queueStateChange(_verifyApply)
    def _queueSpectrumNameChange(self, spectrum, value):
        if value != spectrum.name:
            return partial(self._changeSpectrumName, spectrum, value)

    def _changeSpectrumName(self, spectrum, name):
        spectrum.rename(name)
        self._writeLoggingMessage("spectrum.rename('%s')" % str(name))







    @queueStateChange(_verifyApply)
    def _queueSpectrumScaleChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.scale)
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setSpectrumScale, spectrum, value)

    def _setSpectrumScale(self, spectrum, scale):
        spectrum.scale = float(scale)
        self._writeLoggingMessage("spectrum.scale = %s" % str(scale))
        self.pythonConsole.writeConsoleCommand("spectrum.scale = %s" % scale, spectrum=spectrum)







    @queueStateChange(_verifyApply)
    def _queueNoiseLevelDataChange(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.noiseLevel) if spectrum.noiseLevel else None
        if value >= 0 and textFromValue(value) != specValue:
            return partial(self._setNoiseLevelData, spectrum, value)

    def _setNoiseLevelData(self, spectrum, noise):
        spectrum.noiseLevel = float(noise)
        self._writeLoggingMessage("spectrum.noiseLevel = %s" % str(noise))













    @queueStateChange(_verifyApply)
    def _queueChemicalShiftListChange(self, spectrum, item):
        if item == '<New>':
            listLen = len(self.chemicalShiftListPulldown.texts)
            return partial(self._setNewChemicalShiftList, spectrum, listLen)
        else:
            value = spectrum.project.getByPid(item)
            if value and value != spectrum.chemicalShiftList:
                return partial(self._setChemicalShiftList, spectrum, item)

    def _raiseExperimentFilterPopup(self, spectrum):
        from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        self.spectrumType.select(popup.expType)

    def _setNewChemicalShiftList(self, spectrum, listLen):
        newChemicalShiftList = spectrum.project.newChemicalShiftList()
        insertionIndex = listLen - 1
        self.chemicalShiftListPulldown.texts.insert(insertionIndex, newChemicalShiftList.pid)
        self.chemicalShiftListPulldown.setData(self.chemicalShiftListPulldown.texts)
        self.chemicalShiftListPulldown.setCurrentIndex(insertionIndex)
        self.spectrum.chemicalShiftList = newChemicalShiftList
        self._writeLoggingMessage("""newChemicalShiftList = project.newChemicalShiftList()
                                spectrum.chemicalShiftList = newChemicalShiftList""")
        self.pythonConsole.writeConsoleCommand('spectrum.chemicalShiftList = chemicalShiftList', chemicalShiftList=newChemicalShiftList, spectrum=spectrum)
        self.logger.info('spectrum.chemicalShiftList = chemicalShiftList')

    def _setChemicalShiftList(self, spectrum, item):
        self.spectrum.chemicalShiftList = spectrum.project.getByPid(item)
        self.pythonConsole.writeConsoleCommand('spectrum.newChemicalShiftList = chemicalShiftList', chemicalShiftList=spectrum.chemicalShiftList,
                                               spectrum=spectrum)
        self._writeLoggingMessage("""chemicalShiftList = project.getByPid('%s')
                                  spectrum.chemicalShiftList = chemicalShiftList""" % spectrum.chemicalShiftList.pid)







    @queueStateChange(_verifyApply)
    def _queueSampleChange(self, spectrum, value):
        return partial(self._changeSampleSpectrum, spectrum, self.samplesPulldownList.currentObject())

    def _changeSampleSpectrum(self, spectrum, sample):
        if sample is not None:
            sample.spectra += (spectrum,)
        else:
            if spectrum.sample is not None:
                spectrum.sample = None







    @queueStateChange(_verifyApply)
    def _queueSetSpectrumType(self, spectrum, value):
        if self.spectrumType.getObject():
            expType = self.spectrumType.objects[value]
            if expType != spectrum.experimentType:
                return partial(self._setSpectrumType, spectrum, expType)

    def _setSpectrumType(self, spectrum, expType):
        # expType = self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).get(self.spectrumType.currentText())
        # expType = self.spectrumType.getObject()
        spectrum.experimentType = expType
        self.pythonConsole.writeConsoleCommand('spectrum.experimentType = experimentType', experimentType=expType, spectrum=self.spectrum)
        self._writeLoggingMessage("spectrum.experimentType = '%s'" % expType)




    @queueStateChange(_verifyApply)
    def _getSpectrumFile(self, spectrum):
        """Get the path from the widget and call the open dialog.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]
            filePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            dialog = FileDialog(self, text='Select Spectrum File', directory=filePath,
                                fileMode=1, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if directory:
                newFilePath = directory[0]

                if spectrum.filePath != newFilePath:

                    from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                    dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                    if dataType == 'Spectrum':

                        # self._changes['spectrumFilePath'] = partial(self._setSpectrumFilePath, newFilePath)
                        with undoStackBlocking():
                            self._setPathDataFromUrl(spectrum, newFilePath)

                        return partial(self._setSpectrumFilePath, spectrum, newFilePath)

                    # else:
                    #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                    # set the widget text
                    # self._setPathData(spectrum)

    @queueStateChange(_verifyApply)
    def _queueSetSpectrumPath(self, spectrum):
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]
            newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':
                    return partial(self._setSpectrumFilePath, spectrum, newFilePath)
                # else:
                #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

    def _setSpectrumFilePath(self, spectrum, filePath):
        spectrum.filePath = filePath
        self._writeLoggingMessage("spectrum.filePath = '%s'" % filePath)
        self.pythonConsole.writeConsoleCommand("spectrum.filePath('%s')" % filePath,
                                               spectrum=spectrum)

        spectrum.filePath = filePath
        self._setPathData(spectrum)

        # # TODO: Find a way to convert to the shortened path without setting the value in the model,
        # #       then move this back to _setSpectrumPath
        # apiDataSource = self.spectrum._apiDataSource
        # apiDataStore = apiDataSource.dataStore
        #
        # if not apiDataStore or apiDataStore.dataLocationStore.name != 'standard':
        #     raise NotImplemented('Non-standard API data store locations are invalid.')
        #
        # dataUrlName = apiDataStore.dataUrl.name
        # apiPathName = apiDataStore.path
        # if dataUrlName == 'insideData':
        #     shortenedPath = '$INSIDE/{}'.format(apiPathName)
        # elif dataUrlName == 'alongsideData':
        #     shortenedPath = '$ALONGSIDE/{}'.format(apiPathName)
        # elif dataUrlName == 'remoteData':
        #     shortenedPath = '$DATA/{}'.format(apiPathName)
        # else:
        #     shortenedPath = apiDataStore.fullPath
        # self.pathData.setText(shortenedPath)





    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._parent._fillPullDowns()  #fillColourPulldown(self.colourBox, allowAuto=False)
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.sliceColour:
            return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=spectrum)



class DimensionsTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, dimensions=None):
        super().__init__(parent, setLayout=True)  # ejb

        self._parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum
        self.dimensions = dimensions
        self._changes = dict()

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()  # self.spectrum.project._logger

        Label(self, text="Dimension ", grid=(1, 0), hAlign='l', vAlign='t', )

        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)
        for i in range(dimensions):
            dimLabel = Label(self, text='%s' % str(i + 1), grid=(1, i + 1), vAlign='t', hAlign='l')

        self.axisCodeEdits = [i for i in range(dimensions)]
        self.isotopeCodePullDowns = [i for i in range(dimensions)]
        self.spectralReferencingData = [i for i in range(dimensions)]
        self.spectralReferencingDataPoints = [i for i in range(dimensions)]
        self.spectralAssignmentToleranceData = [i for i in range(dimensions)]
        self.spectralDoubleCursorOffset = [i for i in range(dimensions)]

        self.foldingModesCheckBox = [i for i in range(dimensions)]
        self.minAliasingPullDowns = [i for i in range(dimensions)]
        self.maxAliasingPullDowns = [i for i in range(dimensions)]

        row = 2
        Label(self, text="Axis Code ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Isotope Code ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Point Counts ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Dimension Type ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectrum Width (ppm) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectral Width (Hz) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Spectrometer Frequency (MHz) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Referencing (ppm) ", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Referencing (points)", grid=(row, 0), vAlign='t', hAlign='l')

        row += 1
        Label(self, text="Assignment Tolerance ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Second cursor offset (Hz) ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Show folded contours", grid=(row, 0), hAlign='l')

        row += 1
        label = Label(self, text="Dimension is inverted", grid=(row, 0), hAlign='l')
        label.setEnabled(False)

        row += 1
        Label(self, text="Maximum displayed aliasing ", grid=(row, 0), hAlign='l')

        row += 1
        Label(self, text="Minimum displayed aliasing ", grid=(row, 0), hAlign='l')

        for i in range(dimensions):
            row = 2
            # Label(self, text=str(spectrum.axisCodes[i]), grid=(row, i+1),  hAlign='l', vAlign='t',)

            value = spectrum.axisCodes[i]
            self.axisCodeEdits[i] = LineEdit(self,
                                             text='<None>' if value is None else str(value),
                                             grid=(row, i + 1), vAlign='t', hAlign='l')
            self.axisCodeEdits[i].textChanged.connect(partial(self._queueSetAxisCodes, spectrum,
                                                              self.axisCodeEdits[i].text, i))

            row += 1
            # Label(self, text=str(spectrum.isotopeCodes[i]), grid=(row, i + 1), hAlign='l', vAlign='t', )

            self.isotopeCodePullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t')
            isotopeList = [code for code in DEFAULT_ISOTOPE_DICT.values() if code]
            self.isotopeCodePullDowns[i].setData(isotopeList)
            # self.isotopeCodePullDowns[i].setMaxVisibleItems(10)

            if spectrum.isotopeCodes[i] in isotopeList:
                index = isotopeList.index(spectrum.isotopeCodes[i])
                self.isotopeCodePullDowns[i].setIndex(index)

            self.isotopeCodePullDowns[i].currentIndexChanged.connect(partial(self._queueSetIsotopeCodes, spectrum, self.isotopeCodePullDowns[i].getText, i))

            row += 1
            Label(self, text=str(spectrum.pointCounts[i]), grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            Label(self, text=spectrum.dimensionTypes[i], grid=(row, i + 1), vAlign='t', hAlign='l')

            row += 1
            Label(self, text=str("%.3f" % (spectrum.spectralWidths[i] or 0.0)), grid=(row, i + 1),
                  vAlign='t', hAlign='l')

            row += 1
            Label(self, text=str("%.3f" % (spectrum.spectralWidthsHz[i] or 0.0)), grid=(row, i + 1),
                  vAlign='t', hAlign='l')

            row += 1
            Label(self, text=str("%.3f" % (spectrum.spectrometerFrequencies[i] or 0.0)), grid=(row, i + 1),
                  vAlign='t', hAlign='l')

            row += 1
            value = spectrum.referenceValues[i]
            self.spectralReferencingData[i] = DoubleSpinbox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralReferencingData[i].setValue(value)
            self.spectralReferencingData[i].valueChanged.connect(partial(self._queueSetDimensionReferencing, spectrum, i,
                                                                         self.spectralReferencingData[i].textFromValue))

            row += 1
            # Label(self, text="Referencing (points)", grid=(8, 0), vAlign='t', hAlign='l')
            value = spectrum.referencePoints[i]
            self.spectralReferencingDataPoints[i] = DoubleSpinbox(self, grid=(row, i + 1), vAlign='t', hAlign='l', decimals=3, step=0.1)
            self.spectralReferencingDataPoints[i].setValue(value)
            self.spectralReferencingDataPoints[i].valueChanged.connect(partial(self._queueSetPointDimensionReferencing, spectrum, i,
                                                                               self.spectralReferencingDataPoints[i].textFromValue))
            # self.spectralReferencingDataPointsList.append(spectralReferencingDataPoints)

            row += 1
            # Label(self, text="Assignment Tolerance ", grid=(row, 0),  hAlign='l')
            value = spectrum.assignmentTolerances[i]
            self.spectralAssignmentToleranceData[i] = DoubleSpinbox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            self.spectralAssignmentToleranceData[i].setValue(value)
            self.spectralAssignmentToleranceData[i].valueChanged.connect(partial(self._queueSetAssignmentTolerances, spectrum, i,
                                                                                 self.spectralAssignmentToleranceData[i].textFromValue))

            row += 1
            # Label(self, text="Second cursor offset (Hz) ", grid=(10, 0), hAlign='l')
            value = spectrum.doubleCrosshairOffsets[i]
            self.spectralDoubleCursorOffset[i] = DoubleSpinbox(self, grid=(row, i + 1), hAlign='l', decimals=3, step=0.1)
            self.spectralDoubleCursorOffset[i].setValue(value)
            self.spectralDoubleCursorOffset[i].valueChanged.connect(partial(self._queueSetDoubleCursorOffset, spectrum, i,
                                                                            self.spectralDoubleCursorOffset[i].textFromValue))

            row += 1
            if i == 0:
                # only need 1 checkbox in the first column
                showFolded = spectrum.displayFoldedContours
                self.displayedFoldedContours = CheckBox(self, grid=(row, i + 1), vAlign='t',
                                                        checked=showFolded)
                self.displayedFoldedContours.clicked.connect(partial(self._queueSetDisplayFoldedContours, spectrum, self.displayedFoldedContours.isChecked))

            row += 1
            fModes = spectrum.foldingModes
            dd = {'circular': False, 'mirror': True, None: False}
            self.foldingModesCheckBox[i] = CheckBox(self, grid=(row, i + 1), vAlign='t')
            self.foldingModesCheckBox[i].setChecked(dd[fModes[i]])
            self.foldingModesCheckBox[i].clicked.connect(partial(self._queueSetFoldingModes, spectrum, self.foldingModesCheckBox[i].isChecked, i))
            # self.foldingModesCheckBox[i].setEnabled(False)

            # pullDown for min/max aliasing
            aliasLim = spectrum.visibleAliasingRange
            aliasMaxRange = list(range(MAXALIASINGRANGE, -1, -1))
            aliasMinRange = list(range(0, -MAXALIASINGRANGE - 1, -1))
            aliasMaxText = [str(aa) for aa in aliasMaxRange]
            aliasMinText = [str(aa) for aa in aliasMinRange]

            # max aliasing
            row += 1
            self.maxAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t',
                                                        texts=aliasMaxText)
            if aliasLim[i][1] in aliasMaxRange:
                index = aliasMaxRange.index(aliasLim[i][1])
                self.maxAliasingPullDowns[i].setIndex(index)

            self.maxAliasingPullDowns[i].currentIndexChanged.connect(partial(self._queueSetMaxAliasing, spectrum, self.maxAliasingPullDowns[i].getText, i))

            # min aliasing
            row += 1
            self.minAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t',
                                                        texts=aliasMinText)
            if aliasLim[i][0] in aliasMinRange:
                index = aliasMinRange.index(aliasLim[i][0])
                self.minAliasingPullDowns[i].setIndex(index)

            self.minAliasingPullDowns[i].currentIndexChanged.connect(partial(self._queueSetMinAliasing, spectrum, self.minAliasingPullDowns[i].getText, i))

        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText="Preferred Axis Order",
                                                                     grid=(row, 0), gridSpan=(1, dimensions + 1), vAlign='t')
        self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)
        self._fillPreferredWidget()
        self.preferredAxisOrderPulldown.pulldownList.setCallback(partial(self._queueSetSpectrumOrderingComboIndex, spectrum))

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, dimensions + 1), gridSpan=(1, 1))

    def _fillPreferredWidget(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum.preferredAxisOrdering) if self.spectrum.preferredAxisOrdering is not None else None

        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in self.spectrum.axisCodes])
            axisOrder = tuple(permutations(list(range(len(self.spectrum.axisCodes)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None and self.mainWindow:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)

    def _fillPreferredWidgetFromAxisTexts(self):
        """Fill the pullDown with the currently available permutations of the axis codes
        """
        specOrder = tuple(self.spectrum.preferredAxisOrdering) if self.spectrum.preferredAxisOrdering is not None else None

        axisCodeTexts = tuple([ss.text() for ss in self.axisCodeEdits])
        ll = ['<None>']
        axisPerms = []
        axisOrder = []
        if self.mainWindow:
            # add permutations for the axes
            axisPerms = permutations([axisCode for axisCode in axisCodeTexts])
            axisOrder = tuple(permutations(list(range(len(axisCodeTexts)))))
            ll += [" ".join(ax for ax in perm) for perm in axisPerms]

        self.preferredAxisOrderPulldown.pulldownList.setData(ll)

        if specOrder is not None and self.mainWindow:
            specIndex = axisOrder.index(specOrder) + 1
            self.preferredAxisOrderPulldown.setIndex(specIndex)

    @queueStateChange(_verifyApply)
    def _queueSetSpectrumOrderingComboIndex(self, spectrum, item):
        if item:
            index = self.preferredAxisOrderPulldown.getIndex()

            axisOrder = tuple(permutations(list(range(len(spectrum.axisCodes)))))
            value = tuple(axisOrder[index - 1])
            if value != spectrum.preferredAxisOrdering:
                return partial(self._setSpectrumOrdering, spectrum, value)

    def _setSpectrumOrdering(self, spectrum, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        spectrum.preferredAxisOrdering = value
        self.pythonConsole.writeConsoleCommand("spectrum.preferredAxisOrdering = {0}".format(str(value)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.preferredAxisOrdering = {0}".format(str(value)))

    def _repopulate(self):
        for i in range(self.dimensions):
            value = self.spectrum.referenceValues[i]
            self.spectralReferencingData[i].setText('<None>' if value is None else str("%.3f" % value))

            value = self.spectrum.referencePoints[i]
            self.spectralReferencingDataPoints[i].setText('<None>' if value is None else str("%.3f" % value))

            value = self.spectrum.assignmentTolerances[i]
            self.spectralAssignmentToleranceData[i].setText('<None>' if value is None else str("%.3f" % value))

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)







    @queueStateChange(_verifyApply)
    def _queueSetAssignmentTolerances(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.assignmentTolerances[dim])
        if textFromValue(value) != specValue:
            return partial(self._setAssignmentTolerances, spectrum, dim, value)

    def _setAssignmentTolerances(self, spectrum, dim, value):
        assignmentTolerances = list(spectrum.assignmentTolerances)
        assignmentTolerances[dim] = float(value)
        spectrum.assignmentTolerances = assignmentTolerances
        self.pythonConsole.writeConsoleCommand("spectrum.assignmentTolerances = {0}".format(assignmentTolerances), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.assignmentTolerances = {0}".format(assignmentTolerances))







    @queueStateChange(_verifyApply)
    def _queueSetDoubleCursorOffset(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.doubleCrosshairOffsets[dim])
        if textFromValue(value) != specValue:
            return partial(self._setDoubleCursorOffset, spectrum, dim, value)

    def _setDoubleCursorOffset(self, spectrum, dim, value):
        doubleCrosshairOffsets = list(spectrum.doubleCrosshairOffsets)
        doubleCrosshairOffsets[dim] = float(value)
        spectrum.doubleCrosshairOffsets = doubleCrosshairOffsets
        self.pythonConsole.writeConsoleCommand("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets))







    @queueStateChange(_verifyApply)
    def _queueSetAxisCodes(self, spectrum, valueGetter, dim):
        value = valueGetter()
        if value != spectrum.axisCodes[dim]:
            return partial(self._setAxisCodes, spectrum, dim, value)

        # repopulate the preferred axis order pulldown
        self._fillPreferredWidgetFromAxisTexts()

    def _setAxisCodes(self, spectrum, dim, value):
        axisCodes = list(spectrum.axisCodes)
        axisCodes[dim] = str(value)
        spectrum.axisCodes = axisCodes
        showWarning('Change Axis Code', 'Caution is advised when changing axis codes\n'
                                        'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')

        self.pythonConsole.writeConsoleCommand("spectrum.axisCodes = {0}".format(axisCodes), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(axisCodes))







    @queueStateChange(_verifyApply)
    def _queueSetIsotopeCodes(self, spectrum, valueGetter, dim):
        value = valueGetter()
        if value != spectrum.isotopeCodes[dim]:
            return partial(self._setIsotopeCodes, spectrum, dim, value)

    def _setIsotopeCodes(self, spectrum, dim, value):
        isotopeCodes = list(spectrum.isotopeCodes)
        isotopeCodes[dim] = str(value)
        spectrum.isotopeCodes = isotopeCodes
        showWarning('Change Isotope Code', 'Caution is advised when changing isotope codes\n'
                                           'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')

        self.pythonConsole.writeConsoleCommand("spectrum.isotopeCodes = {0}".format(isotopeCodes), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(isotopeCodes))







    @queueStateChange(_verifyApply)
    def _queueSetDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referenceValues[dim])
        if textFromValue(value) != specValue:
            return partial(self._setDimensionReferencing, spectrum, dim, value)

    def _setDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referenceValues)
        spectrumReferencing[dim] = float(value)
        spectrum.referenceValues = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referenceValues = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(spectrumReferencing))


    @queueStateChange(_verifyApply)
    def _queueSetPointDimensionReferencing(self, spectrum, dim, textFromValue, value):
        specValue = textFromValue(spectrum.referencePoints[dim])
        if textFromValue(value) != specValue:
            return partial(self._setPointDimensionReferencing, spectrum, dim, value)

    def _setPointDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referencePoints)
        spectrumReferencing[dim] = float(value)
        spectrum.referencePoints = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referencePoints = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referencePoints = {0}".format(spectrumReferencing))


    @queueStateChange(_verifyApply, 'minAliasing')
    def _queueSetMinAliasing(self, spectrum, valueGetter, dim):
        minValue = int(valueGetter())
        if minValue != spectrum.visibleAliasingRange[dim][1]:
            returnVal = partial(self._setMinAliasing, self.spectrum, dim, minValue)
            maxValue = int(self.maxAliasingPullDowns[dim].getText())
            if minValue > maxValue:
                self.maxAliasingPullDowns[dim].select(str(minValue))
            return returnVal

    def _setMinAliasing(self, spectrum, dim, value):
        alias = list(spectrum.visibleAliasingRange)
        value = int(value)

        alias[dim] = (value, max(alias[dim][1], value))
        spectrum.visibleAliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.visibleAliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.visibleAliasingRange = {0}".format(tuple(alias)))







    @queueStateChange(_verifyApply)
    def _queueSetMaxAliasing(self, spectrum, valueGetter, dim):
        maxValue = int(valueGetter())
        if maxValue != spectrum.visibleAliasingRange[dim][0]:
            returnVal = partial(self._setMaxAliasing, spectrum, dim, maxValue)
            minValue = int(self.minAliasingPullDowns[dim].getText())
            if maxValue < minValue:
                self.minAliasingPullDowns[dim].select(str(maxValue))
            return returnVal

    def _setMaxAliasing(self, spectrum, dim, value):
        alias = list(spectrum.visibleAliasingRange)
        value = int(value)
        alias[dim] = (min(alias[dim][0], value), value)
        spectrum.visibleAliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.visibleAliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.aliasingLimits = {0}".format(tuple(alias)))







    @queueStateChange(_verifyApply)
    def _queueSetFoldingModes(self, spectrum, valueGetter, dim):
        dd = {True: 'mirror', False: 'circular', None: None}
        value = dd[valueGetter()]
        if value != spectrum.foldingModes[dim]:
            return partial(self._setFoldingModes, spectrum, dim, value)

    def _setFoldingModes(self, spectrum, dim, value):
        folding = list(spectrum.foldingModes)
        folding[dim] = value
        spectrum.foldingModes = tuple(folding)

        self.pythonConsole.writeConsoleCommand("spectrum.foldingModes = {0}".format(tuple(folding)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.foldingModes = {0}".format(tuple(folding)))







    @queueStateChange(_verifyApply)
    def _queueSetDisplayFoldedContours(self, spectrum, valueGetter):
        value = valueGetter()
        if value != spectrum.displayFoldedContours:
            return partial(self._setDisplayFoldedContours, spectrum, value)

    def _setDisplayFoldedContours(self, spectrum, value):
        spectrum.displayFoldedContours = bool(value)

        self.pythonConsole.writeConsoleCommand("spectrum.displayFoldedContours = {0}".format(spectrum.displayFoldedContours), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.displayFoldedContours = {0}".format(spectrum.displayFoldedContours))


class ContoursTab(Widget):

    def __init__(self, parent=None, mainWindow=None, spectrum=None):

        super().__init__(parent, setLayout=True)  # ejb

        self._parent = parent
        self.mainWindow = mainWindow
        self.spectrum = spectrum

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()  # self.spectrum.project._logger

        # TODO self._changes looks unused, as do all the functions put in it
        # Check if the lot can be removed
        self._changes = dict()

        row = 0
        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), row, 0)

        row += 1
        linkContoursLabel = Label(self, text="Link Contours", grid=(row, 0), vAlign='t', hAlign='l')
        self.linkContoursCheckBox = CheckBox(self, grid=(row, 1), checked=True, vAlign='t', hAlign='l')

        row += 1
        positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(row, 0), vAlign='t', hAlign='l')
        positiveContoursCheckBox = CheckBox(self, grid=(row, 1), checked=True, vAlign='t', hAlign='l')
        # for spectrumView in self.spectrum.spectrumViews:
        #     if spectrumView.displayPositiveContours:
        #         positiveContoursCheckBox.setChecked(True)
        #     else:
        #         positiveContoursCheckBox.setChecked(False)
        positiveContoursCheckBox.setChecked(self.spectrum.includePositiveContours)

        # self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)
        positiveContoursCheckBox.stateChanged.connect(partial(self._queueChangePositiveContourDisplay, spectrum))

        row += 1
        positiveContourBaseLabel = Label(self, text="Positive Base Level", grid=(row, 0), vAlign='c', hAlign='l')
        self.positiveContourBaseData = ScientificDoubleSpinBox(self, grid=(row, 1), vAlign='t', min=0.1, max=1e12)
        self.positiveContourBaseData.setValue(self.spectrum.positiveContourBase)
        self.positiveContourBaseData.valueChanged.connect(partial(self._queueChangePositiveContourBase, spectrum, self.positiveContourBaseData.textFromValue))
        # self.positiveContourBaseData.setSingleStep(self.positiveContourBaseData.value()*(self.positiveMultiplierData.value()-1))
        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.positiveContourBaseData.setSingleStep(self.positiveContourBaseData.value() * 0.1)

        row += 1
        positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(row, 0), vAlign='c', hAlign='l')
        self.positiveMultiplierData = DoubleSpinbox(self, grid=(row, 1), vAlign='t', min=0.0, decimals=3, step=0.1)
        # self.positiveMultiplierData.setSingleStep(0.1)
        self.positiveMultiplierData.setValue(float(self.spectrum.positiveContourFactor))
        self.positiveMultiplierData.valueChanged.connect(partial(self._queueChangePositiveContourFactor, spectrum, self.positiveMultiplierData.textFromValue))

        row += 1
        positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(row, 0), vAlign='c', hAlign='l')
        self.positiveContourCountData = Spinbox(self, grid=(row, 1), vAlign='t')
        self.positiveContourCountData.setValue(int(self.spectrum._apiDataSource.positiveContourCount))
        self.positiveContourCountData.valueChanged.connect(partial(self._queueChangePositiveContourCount, spectrum))

        row += 1
        positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(row, 0), vAlign='c', hAlign='l')
        self.positiveColourBox = PulldownList(self, grid=(row, 1), vAlign='t')


        self.negativeColourBox = PulldownList(self, grid=(row, 1), vAlign='t')

        # populate initial pulldown
        spectrumColourKeys = list(spectrumColours.keys())
        fillColourPulldown(self.positiveColourBox, allowAuto=False)
        fillColourPulldown(self.negativeColourBox, allowAuto=False)

        c = self.spectrum.positiveContourColour
        if c in spectrumColourKeys:
            col = spectrumColours[c]
            self.positiveColourBox.setCurrentText(col)
        else:
            addNewColourString(c)
            fillColourPulldown(self.positiveColourBox, allowAuto=False)
            fillColourPulldown(self.negativeColourBox, allowAuto=False)
            spectrumColourKeys = list(spectrumColours.keys())
            col = spectrumColours[c]
            self.positiveColourBox.setCurrentText(col)

        # self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, self.spectrum))

        self.positiveColourButton = Button(self, grid=(row, 2), vAlign='t', hAlign='l',
                                           icon='icons/colours', hPolicy='fixed')
        self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, spectrum))

        row += 1
        negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(row, 0), vAlign='c', hAlign='l')
        negativeContoursCheckBox = CheckBox(self, grid=(row, 1), checked=True, vAlign='t', hAlign='l')
        # for spectrumView in self.spectrum.spectrumViews:
        #     if spectrumView.displayNegativeContours:
        #         negativeContoursCheckBox.setChecked(True)
        #     else:
        #         negativeContoursCheckBox.setChecked(False)
        negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)

        negativeContoursCheckBox.stateChanged.connect(partial(self._queueChangeNegativeContourDisplay, spectrum))

        row += 1
        negativeContourBaseLabel = Label(self, text="Negative Base Level", grid=(row, 0), vAlign='c', hAlign='l')
        self.negativeContourBaseData = ScientificDoubleSpinBox(self, grid=(row, 1), vAlign='t', min=-1e12, max=-0.1)
        # self.negativeContourBaseData.setMaximum(-0.1)
        # self.negativeContourBaseData.setMinimum(-1e12)
        self.negativeContourBaseData.setValue(-abs(self.spectrum.negativeContourBase))
        # self.negativeContourBaseData.setMaximum(1e12)
        # self.negativeContourBaseData.setMinimum(0.1)
        # self.negativeContourBaseData.setValue(abs(self.spectrum.negativeContourBase))

        self.negativeContourBaseData.valueChanged.connect(partial(self._queueChangeNegativeContourBase, spectrum, self.negativeContourBaseData.textFromValue))
        # self.negativeContourBaseData.setSingleStep((self.negativeContourBaseData.value()*-1)*self.negativeMultiplierData.value()-1)
        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.negativeContourBaseData.setSingleStep((self.negativeContourBaseData.value() * -1) * 0.1)

        row += 1
        negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(row, 0), vAlign='c', hAlign='l')
        self.negativeMultiplierData = DoubleSpinbox(self, grid=(row, 1), vAlign='t', min=0.0, decimals=3, step=0.1)
        self.negativeMultiplierData.setValue(self.spectrum.negativeContourFactor)
        # self.negativeMultiplierData.setSingleStep(0.1)
        self.negativeMultiplierData.valueChanged.connect(partial(self._queueChangeNegativeContourFactor, spectrum, self.negativeMultiplierData.textFromValue))

        row += 1
        negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(row, 0), vAlign='c', hAlign='l')
        self.negativeContourCountData = Spinbox(self, grid=(row, 1), vAlign='t')
        self.negativeContourCountData.setValue(self.spectrum.negativeContourCount)
        self.negativeContourCountData.valueChanged.connect(partial(self._queueChangeNegativeContourCount, spectrum))

        row += 1
        negativeContourColourLabel = Label(self, text="Negative Contour Colour", grid=(row, 0), vAlign='c', hAlign='l')

        # self.negativeColourBox = PulldownList(self, grid=(10, 1), vAlign='t')
        c = self.spectrum.negativeContourColour
        if c in spectrumColourKeys:
            self.negativeColourBox.setCurrentText(spectrumColours[c])
        else:
            addNewColourString(c)
            fillColourPulldown(self.positiveColourBox, allowAuto=False)
            fillColourPulldown(self.negativeColourBox, allowAuto=False)
            spectrumColourKeys = list(spectrumColours.keys())
            self.negativeColourBox.setCurrentText(spectrumColours[c])

        self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, spectrum))
        self.negativeColourBox.currentIndexChanged.connect(partial(self._queueChangeNegColourComboIndex, spectrum))

        self.negativeColourButton = Button(self, grid=(row, 2), icon='icons/colours', hPolicy='fixed',
                                           vAlign='t', hAlign='l')
        self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, spectrum))
        # move to the correct row
        self.getLayout().addWidget(self.negativeColourBox, row, 1)

        # self._contourOptionsFromNoise = _addContourNoiseButtons(self, 11, buttonLabel='Estimate Levels')

        row += 1
        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(row, 1), gridSpan=(1, 1))

    def _setContourLevels(self):
        """Estimate the contour levels for the current spectrum
        """
        posBase, negBase, posMult, negMult, posLevels, negLevels = getContourLevelsFromNoise(self.spectrum, setNoiseLevel=False,
                                                                                 setPositiveContours=self.setPositiveContours.isChecked(),
                                                                                 setNegativeContours=self.setNegativeContours.isChecked(),
                                                                                 useSameMultiplier=self.setUseSameMultiplier.isChecked(),
                                                                                 useDefaultLevels=self.setDefaults.isChecked(),
                                                                                 useDefaultMultiplier=self.setDefaults.isChecked())

        # put the new values into the widgets (will queue changes)
        if posBase:
            self.positiveContourBaseData.setValue(posBase)
        if negBase:
            self.negativeContourBaseData.setValue(negBase)
        if posMult:
            self.positiveMultiplierData.setValue(posMult)
        if negMult:
            self.negativeMultiplierData.setValue(negMult)
        if posLevels:
            self.positiveContourCountData.setValue(posLevels)
        if negLevels:
            self.negativeContourCountData.setValue(negLevels)

    def _repopulate(self):
        # don't need anything here as can't generate any errors
        pass

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)







    @queueStateChange(_verifyApply)
    def _queueChangePositiveContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includePositiveContours:
            return partial(self._changePositiveContourDisplay, spectrum, state)

    def _changePositiveContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includePositiveContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = True")
        else:
            self.spectrum.includePositiveContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayPositiveContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = False")

    @queueStateChange(_verifyApply)
    def _queueChangeNegativeContourDisplay(self, spectrum, state):
        if (state == QtCore.Qt.Checked) != spectrum.includeNegativeContours:
            return partial(self._changeNegativeContourDisplay, spectrum, state)

    def _changeNegativeContourDisplay(self, spectrum, state):
        if state == QtCore.Qt.Checked:
            spectrum.includeNegativeContours = True
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = True")
        else:
            spectrum.includeNegativeContours = False
            for spectrumView in spectrum.spectrumViews:
                spectrumView.displayNegativeContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = False")

    @queueStateChange(_verifyApply)
    def _queueChangePositiveContourBase(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.positiveContourBase)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changePositiveContourBase, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeContourBaseData.set(-value)
        return returnVal

    def _changePositiveContourBase(self, spectrum, value):
        spectrum.positiveContourBase = float(value)
        self._writeLoggingMessage("spectrum.positiveContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourBase = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyApply)
    def _queueChangePositiveContourFactor(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.positiveContourFactor)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changePositiveContourFactor, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeMultiplierData.set(value)
        return returnVal

    def _changePositiveContourFactor(self, spectrum, value):
        spectrum.positiveContourFactor = float(value)
        self._writeLoggingMessage("spectrum.positiveContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourFactor = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyApply)
    def _queueChangePositiveContourCount(self, spectrum, value):
        if value >= 0 and value != spectrum.positiveContourCount:
            returnVal = partial(self._changePositiveContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.negativeContourCountData.set(value)
        return returnVal

    def _changePositiveContourCount(self, spectrum, value):
        spectrum.positiveContourCount = int(value)
        self._writeLoggingMessage("spectrum.positiveContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourCount = %d" % int(value), spectrum=spectrum)

    @queueStateChange(_verifyApply)
    def _queueChangeNegativeContourBase(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.negativeContourBase)
        if value <= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changeNegativeContourBase, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveContourBaseData.set(-value)
        return returnVal
        
    def _changeNegativeContourBase(self, spectrum, value):
        # force to be negative
        value = -abs(value)
        spectrum.negativeContourBase = float(value)
        self._writeLoggingMessage("spectrum.negativeContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourBase = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyApply)
    def _queueChangeNegativeContourFactor(self, spectrum, textFromValue, value):
        specValue = textFromValue(spectrum.negativeContourFactor)
        if value >= 0 and textFromValue(value) != specValue:
            returnVal = partial(self._changeNegativeContourFactor, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveMultiplierData.set(value)
        return returnVal
        
    def _changeNegativeContourFactor(self, spectrum, value):
        spectrum.negativeContourFactor = float(value)
        self._writeLoggingMessage("spectrum.negativeContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourFactor = %f" % float(value), spectrum=spectrum)

    @queueStateChange(_verifyApply)
    def _queueChangeNegativeContourCount(self, spectrum, value):
        if value >= 0 and value != spectrum.negativeContourCount:
            returnVal = partial(self._changeNegativeContourCount, spectrum, value)
        else:
            returnVal = None

        # check linked attribute
        if self.linkContoursCheckBox.isChecked():
            self.positiveContourCountData.set(value)
        return returnVal
        
    def _changeNegativeContourCount(self, spectrum, value):
        spectrum.negativeContourCount = int(value)
        self._writeLoggingMessage("spectrum.negativeContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourCount = %d" % int(value), spectrum=spectrum)

    # spectrum negativeContourColour button and pulldown
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyApply)
    def _queueChangePosColourComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.positiveContourColour:
            return partial(self._changePosColourComboIndex, spectrum, value)

    def _changePosColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.positiveColourBox.currentText()))]
        if newColour:
            spectrum.positiveContourColour = newColour
            self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour, spectrum=spectrum)

    # spectrum negativeContourColour button and pulldown
    def _queueChangeNegSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.negativeColourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyApply)
    def _queueChangeNegColourComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.negativeContourColour:
            return partial(self._changeNegColourComboIndex, spectrum, value)

    def _changeNegColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.negativeColourBox.currentText()))]
        if newColour:
            spectrum.negativeContourColour = newColour
            self._writeLoggingMessage("spectrum.negativeContourColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.negativeContourColour = '%s'" % newColour, spectrum=spectrum)


class SpectrumDisplayPropertiesPopupNd(CcpnDialog):
    """All spectra in the current display are added as tabs
    The apply button then steps through each tab, and calls each function in the _changes dictionary
    in order to set the parameters.
    """
    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 400

    def __init__(self, parent=None, mainWindow=None, orderedSpectrumViews=None,
                 title='SpectrumDisplay Properties', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = OrderedSet([spec.spectrum for spec in self.orderedSpectrumViews])

        self.tabWidget = Tabs(self, setLayout=True, grid=(0, 0), gridSpan=(2, 4), focusPolicy='strong')
        self.tabWidget.setFixedWidth(self.MINIMUM_WIDTH)

        self._contoursTab = []
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            self._contoursTab.append(ContoursTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec))
            self.tabWidget.addTab(self._contoursTab[specNum], thisSpec.name)

        self.applyButtons = ButtonList(self, texts=[CANCELBUTTONTEXT, APPLYBUTTONTEXT, OKBUTTONTEXT],
                                       callbacks=[self.reject, self._applyChanges, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(2, 1), gridSpan=(1, 4))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setFocus()

        self._fillPullDowns()

        # clear the changes dict in each tab
        tabs = self._contoursTab
        for t in tabs:
            t._changes = dict()

        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton(APPLYBUTTONTEXT))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)

    def _fillPullDowns(self):
        for aTab in self._contoursTab:
            fillColourPulldown(aTab.positiveColourBox, allowAuto=False)
            fillColourPulldown(aTab.negativeColourBox, allowAuto=False)

    def _keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            pass

    def _repopulate(self):
        if self._contoursTab:
            self._contoursTab._repopulate()

    def _applyAllChanges(self, changes):
        for v in changes.values():
            v()

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        tabs = self._contoursTab
        allChanges = any(t._changes for t in tabs if t is not None)

        if not allChanges:
            return True

        with handleDialogApply(self) as error:

            spectrumList = []
            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateGl, self, spectrumList))

            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        self._applyAllChanges(changes)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateGl, self, spectrumList))

            for spec in spectrumList:
                for specViews in spec.spectrumViews:
                    specViews.buildContours = True
            _updateGl(self, spectrumList)

        self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)
        if error.errorValue:
            # repopulate popup
            self._repopulate()
            return False

        return True

    def _rejectButton(self):
        self.reject()

    def _applyButton(self):
        self._applyChanges()

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()


class SpectrumDisplayPropertiesPopup1d(CcpnDialog):
    """All spectra in the current display are added as tabs
    The apply button then steps through each tab, and calls each function in the _changes dictionary
    in order to set the parameters.
    """

    MINIMUM_WIDTH_PER_TAB = 120
    MINIMUM_WIDTH = 400

    def __init__(self, parent=None, mainWindow=None, orderedSpectrumViews=None,
                 title='SpectrumDisplay Properties', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.orderedSpectrumViews = orderedSpectrumViews
        self.orderedSpectra = [spec.spectrum for spec in self.orderedSpectrumViews]

        self.tabWidget = Tabs(self, setLayout=True, grid=(0, 0), gridSpan=(2, 4), focusPolicy='strong')
        self.tabWidget.setFixedWidth(self.MINIMUM_WIDTH)

        self._generalTab = []
        # for specNum, thisSpec in enumerate(self.orderedSpectra):
        for specNum, thisSpec in enumerate(self.orderedSpectra):
            self._generalTab.append(ColourTab(parent=self, mainWindow=self.mainWindow, spectrum=thisSpec))
            self.tabWidget.addTab(self._generalTab[specNum], thisSpec.name)

        self.applyButtons = ButtonList(self, texts=[CANCELBUTTONTEXT, APPLYBUTTONTEXT, OKBUTTONTEXT],
                                       callbacks=[self._rejectButton, self._applyButton, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(2, 1), gridSpan=(1, 4))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setFocus()

        self._fillPullDowns()

        # clear the changes dict in each tab
        tabs = self._generalTab
        for t in tabs:
            t._changes = dict()

        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton(APPLYBUTTONTEXT))
        self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)

    def _fillPullDowns(self):
        for aTab in self._generalTab:
            fillColourPulldown(aTab.colourBox, allowAuto=False)

    def _keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Enter:
            pass

    def _repopulate(self):
        pass
        # if self._generalTab:
        #   self._generalTab._repopulate()

    def _applyAllChanges(self, changes):
        for v in changes.values():
            v()

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        # tabs = self.tabWidget.findChildren(QtGui.QStackedWidget)[0].children()
        # tabs = [t for t in tabs if not isinstance(t, QtGui.QStackedLayout)]

        # ejb - error above, need to set the tabs explicitly
        tabs = self._generalTab
        allChanges = any(t._changes for t in tabs if t is not None)

        if not allChanges:
            return True

        with handleDialogApply(self) as error:

            spectrumList = []
            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        spectrumList.append(t.spectrum)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(_updateGl, self, spectrumList))

            for t in tabs:
                if t is not None:
                    changes = t._changes
                    if changes:
                        self._applyAllChanges(changes)

            with undoStackBlocking() as addUndoItem:
                addUndoItem(redo=partial(_updateGl, self, spectrumList))

            for spec in spectrumList:
                for specViews in spec.spectrumViews:
                    specViews.buildContours = True
            _updateGl(self, spectrumList)

        self.applyButtons.getButton(APPLYBUTTONTEXT).setEnabled(False)
        if error.errorValue:
            # repopulate popup
            self._repopulate()
            return False

        return True

    def _rejectButton(self):
        self.reject()

    def _applyButton(self):
        self._applyChanges()

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()


class ColourTab(Widget):
    def __init__(self, parent=None, mainWindow=None, spectrum=None, item=None, colourOnly=False):

        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        super().__init__(parent, setLayout=True)  # ejb

        self._parent = parent
        self.mainWindow = mainWindow
        self.application = self.mainWindow.application
        self.project = self.mainWindow.project

        self.item = item
        self.spectrum = spectrum
        self._changes = dict()
        self.atomCodes = ()

        self.pythonConsole = mainWindow.pythonConsole
        self.logger = getLogger()  # self.spectrum.project._logger

        Label(self, text="Colour", vAlign='t', hAlign='l', grid=(7, 0))
        self.colourBox = PulldownList(self, vAlign='t', grid=(7, 1))

        # populate initial pulldown
        spectrumColourKeys = list(spectrumColours.keys())
        fillColourPulldown(self.colourBox, allowAuto=False)
        c = self.spectrum.sliceColour
        if c in spectrumColourKeys:
            self.colourBox.setCurrentText(spectrumColours[c])
        else:
            addNewColourString(c)
            fillColourPulldown(self.colourBox, allowAuto=False)
            spectrumColourKeys = list(spectrumColours.keys())
            self.colourBox.setCurrentText(spectrumColours[c])

        self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, spectrum))
        colourButton = Button(self, vAlign='t', hAlign='l', grid=(7, 2), hPolicy='fixed',
                              callback=partial(self._queueSetSpectrumColour, spectrum), icon='icons/colours')

    def _repopulate(self):
        pass

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    # spectrum sliceColour button and pulldown
    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

    @queueStateChange(_verifyApply)
    def _queueChangeSliceComboIndex(self, spectrum, value):
        if value >= 0 and list(spectrumColours.keys())[value] != spectrum.sliceColour:
            return partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=spectrum)
