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
__version__ = "$Revision: 3.0.b5 $"
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
from ccpn.ui.gui.popups.Dialog import CcpnDialog, handleDialogApply
from ccpn.core.lib.ContextManagers import undoStackBlocking
from ccpn.ui.gui.popups.EstimateNoisePopup import _addContourNoiseButtons
from ccpn.core.lib.SpectrumLib import getContourLevelsFromNoise


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

        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply', 'Ok'],
                                       callbacks=[self.reject, self._applyChanges, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(4, 1), gridSpan=(1, 4))
        self.applyButtons.getButton('Apply').setFocus()

        self._fillPullDowns()
        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton('Apply'))

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

        if error.errorValue:
            # repopulate popup on an error
            self._repopulate()
            return False

        return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()


# class SpectrumValidator(QtGui.QValidator):
#
#     def __init__(self, spectrum, parent=None, validationType='exists'):
#         QtGui.QValidator.__init__(self, parent=parent)
#         self.spectrum = spectrum
#         self.validationType = validationType
#         self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
#
#     def validate(self, p_str, p_int):
#         if self.validationType != 'exists':
#             raise NotImplemented('FilePathValidation only checks that the path exists')
#         filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, p_str.strip())
#
#         palette = self.parent().palette()
#
#         if os.path.exists(filePath):
#             if filePath == self.spectrum.filePath:
#                 palette.setColor(QtGui.QPalette.Base, self.baseColour)
#             else:
#                 from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
#
#                 dataType, subType, usePath = ioFormats.analyseUrl(filePath)
#                 if dataType == 'Spectrum':
#                     palette.setColor(QtGui.QPalette.Base, QtGui.QColor('palegreen'))
#                 else:
#                     palette.setColor(QtGui.QPalette.Base, QtGui.QColor('orange'))
#
#             state = QtGui.QValidator.Acceptable
#         else:
#             palette.setColor(QtGui.QPalette.Base, QtGui.QColor('lightpink'))
#             state = QtGui.QValidator.Intermediate
#         self.parent().setPalette(palette)
#
#         return state, p_str, p_int
#
#     def clearValidCheck(self):
#         palette = self.parent().palette()
#         palette.setColor(QtGui.QPalette.Base, self.baseColour)
#         self.parent().setPalette(palette)
#
#     def resetCheck(self):
#         self.validate(self.parent().text(), 0)

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
        self.nameData.textChanged.connect(self._queueSpectrumNameChange)  # ejb - was editingFinished
        row += 1

        Label(self, text="Path", vAlign='t', hAlign='l', grid=(row, 0))
        self.pathData = LineEdit(self, textAlignment='left', vAlign='t', grid=(row, 1))
        self.pathData.setValidator(SpectrumValidator(parent=self.pathData, spectrum=self.spectrum))
        self.pathButton = Button(self, grid=(row, 2), callback=partial(self._getSpectrumFile, self.spectrum), icon='icons/directory')
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
        self.pathData.editingFinished.connect(partial(self._queueSetSpectrumPath, self.spectrum))

        try:
            index = spectrum.project.chemicalShiftLists.index(spectrum.chemicalShiftList)
        except:
            index = 0
        Label(self, text="ChemicalShiftList ", vAlign='t', hAlign='l', grid=(row, 0))
        self.chemicalShiftListPulldown = PulldownList(self, vAlign='t', grid=(row, 1), index=index,
                                                      texts=[csList.pid for csList in spectrum.project.chemicalShiftLists] + ['<New>'],
                                                      callback=self._queueChemicalShiftListChange)
        row += 1

        Label(self, text="Sample", vAlign='t', hAlign='l', grid=(row, 0))
        self.samplesPulldownList = PulldownList(self, texts=['None'], objects=[None], vAlign='t', grid=(row, 1))
        for sample in spectrum.project.samples:
            self.samplesPulldownList.addItem(sample.name, sample)
        if spectrum.sample is not None:
            self.samplesPulldownList.select(spectrum.sample.name)
        self.samplesPulldownList.activated[str].connect(self._queueSampleChange)

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
            self.spectrumType.currentIndexChanged.connect(self._queueSetSpectrumType)
            if spectrum.experimentType is not None:
                self.spectrumType.select(spectrum.experimentType)

            Label(self, text='Spectrum Scaling', vAlign='t', hAlign='l', grid=(9, 0))
            self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', hAlign='l', grid=(9, 1))

            self.spectrumScalingData.textChanged.connect(self._queueSpectrumScaleChange)

            Label(self, text="Date Recorded ", vAlign='t', hAlign='l', grid=(11, 0))
            Label(self, text='n/a', vAlign='t', hAlign='l', grid=(11, 1))

            Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(12, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', hAlign='l', grid=(12, 1))

            self.noiseLevelData.valueChanged.connect(self._queueNoiseLevelDataChange)
            if spectrum.noiseLevel is not None:
                self.noiseLevelData.setValue(spectrum.noiseLevel)
            else:
                self.noiseLevelData.setValue(0)

            # self.noiseLevelData.textChanged.connect(self._queueNoiseLevelDataChange)
            # if spectrum.noiseLevel is not None:
            #     self.noiseLevelData.setText(str('%.3d' % spectrum.noiseLevel))
            # else:
            #     self.noiseLevelData.setText('None')

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

            self.spectrumType.currentIndexChanged.connect(self._queueSetSpectrumType)
            self.spectrumType.setMinimumWidth(self.pathData.width() * 1.95)
            self.spectrumType.setFixedHeight(25)

            spectrumScalingLabel = Label(self, text='Spectrum Scaling', vAlign='t', grid=(9, 0))
            self.spectrumScalingData = LineEdit(self, text=str(self.spectrum.scale), vAlign='t', grid=(9, 1))
            self.spectrumScalingData.textChanged.connect(self._queueSpectrumScaleChange)

            noiseLevelLabel = Label(self, text="Noise Level ", vAlign='t', hAlign='l', grid=(10, 0))
            self.noiseLevelData = ScientificDoubleSpinBox(self, vAlign='t', grid=(10, 1))
            self.noiseLevelData.valueChanged.connect(self._queueNoiseLevelDataChange)

            if spectrum.noiseLevel is None:
                self.noiseLevelData.setValue(spectrum.estimateNoise())
            else:
                self.noiseLevelData.setValue(spectrum.noiseLevel)

            # if spectrum.noiseLevel is None:
            #     self.noiseLevelData.setText(str('%.3d' % spectrum.estimateNoise()))
            # else:
            #     self.noiseLevelData.setText('%.3d' % spectrum.noiseLevel)

            # doubleCrosshairLabel = Label(self, text="Show Second Cursor", grid=(11, 0), vAlign='t', hAlign='l')
            # doubleCrosshairCheckBox = CheckBox(self, grid=(11, 1), checked=True, vAlign='t', hAlign='l')
            # doubleCrosshairCheckBox.setChecked(spectrum.showDoubleCrosshair)
            # doubleCrosshairCheckBox.stateChanged.connect(self._queueChangeDoubleCrosshair)

            self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(12, 1), gridSpan=(1, 1))

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

    def _queueSpectrumNameChange(self):
        if self.nameData.isModified():
            self._changes['spectrumName'] = partial(self._changeSpectrumName, self.nameData.text())

    def _changeSpectrumName(self, name):
        self.spectrum.rename(name)
        self._writeLoggingMessage("spectrum.rename('%s')" % self.nameData.text())

    def _queueSpectrumScaleChange(self):
        self._changes['spectrumScale'] = partial(self._setSpectrumScale, self.spectrumScalingData.text())

    def _setSpectrumScale(self, scale):
        self.spectrum.scale = float(scale)
        self._writeLoggingMessage("spectrum.scale = %s" % self.spectrumScalingData.text())
        self.pythonConsole.writeConsoleCommand("spectrum.scale = %s" % self.spectrumScalingData.text(), spectrum=self.spectrum)

    def _queueNoiseLevelDataChange(self):
        self._changes['spectrumNoiseLevel'] = partial(self._setNoiseLevelData, self.noiseLevelData.value())

    def _setNoiseLevelData(self, noise):
        self.spectrum.noiseLevel = float(noise)
        self._writeLoggingMessage("spectrum.noiseLevel = %s" % self.noiseLevelData.value())

    def _queueChangePositiveContourDisplay(self, state):
        self._changes['positiveContourDisplay'] = partial(self._changePositiveContourDisplay, state)

    def _queueChangeDoubleCrosshair(self, state):
        flag = (state == QtCore.Qt.Checked)
        self.spectrum.showDoubleCrosshair = flag
        self.logger.info("spectrum = ui.getByGid('%s')" % self.spectrum.pid)
        self.logger.info("spectrum.showDoubleCrosshair = %s" % flag)

    def _queueChemicalShiftListChange(self, item):
        if item == '<New>':
            listLen = len(self.chemicalShiftListPulldown.texts)
            self._changes['chemicalShiftList'] = partial(self._setNewChemicalShiftList, listLen)
        else:
            self._changes['chemicalShiftList'] = partial(self._setChemicalShiftList, item)

    def _raiseExperimentFilterPopup(self, spectrum):
        from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        self.spectrumType.select(popup.expType)

    def _setNewChemicalShiftList(self, listLen):
        newChemicalShiftList = self.spectrum.project.newChemicalShiftList()
        insertionIndex = listLen - 1
        self.chemicalShiftListPulldown.texts.insert(insertionIndex, newChemicalShiftList.pid)
        self.chemicalShiftListPulldown.setData(self.chemicalShiftListPulldown.texts)
        self.chemicalShiftListPulldown.setCurrentIndex(insertionIndex)
        self.spectrum.chemicalShiftList = newChemicalShiftList
        self._writeLoggingMessage("""newChemicalShiftList = project.newChemicalShiftList()
                                spectrum.chemicalShiftList = newChemicalShiftList""")
        self.pythonConsole.writeConsoleCommand('spectrum.chemicalShiftList = chemicalShiftList', chemicalShiftList=newChemicalShiftList, spectrum=self.spectrum)
        self.logger.info('spectrum.chemicalShiftList = chemicalShiftList')

    def _setChemicalShiftList(self, item):
        self.spectrum.chemicalShiftList = self.spectrum.project.getByPid(item)
        self.pythonConsole.writeConsoleCommand('spectrum.newChemicalShiftList = chemicalShiftList', chemicalShiftList=self.spectrum.chemicalShiftList,
                                               spectrum=self.spectrum)
        self._writeLoggingMessage("""chemicalShiftList = project.getByPid('%s')
                                  spectrum.chemicalShiftList = chemicalShiftList""" % self.spectrum.chemicalShiftList.pid)

    def _queueSampleChange(self):
        self._changes['sampleSpectrum'] = partial(self._changeSampleSpectrum, self.samplesPulldownList.currentObject())

    def _changeSampleSpectrum(self, sample):
        if sample is not None:
            sample.spectra += (self.spectrum,)
        else:
            if self.spectrum.sample is not None:
                self.spectrum.sample = None

    def _queueSetSpectrumType(self, value):
        self._changes['spectrumType'] = partial(self._setSpectrumType, value)

    def _setSpectrumType(self, value):

        # expType = self.experimentTypes[self.spectrum.dimensionCount].get(self.atomCodes).get(self.spectrumType.currentText())
        expType = self.spectrumType.getObject()
        print(expType)
        self.spectrum.experimentType = expType
        self.pythonConsole.writeConsoleCommand('spectrum.experimentType = experimentType', experimentType=expType, spectrum=self.spectrum)
        self._writeLoggingMessage("spectrum.experimentType = '%s'" % expType)

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
            if len(directory) > 0:
                newFilePath = directory[0]

                if spectrum.filePath != newFilePath:

                    from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                    dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                    if dataType == 'Spectrum':
                        self._changes['spectrumFilePath'] = partial(self._setSpectrumFilePath, newFilePath)

                    else:
                        getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                    # set the widget text
                    self._setPathData(spectrum)

    def _queueSetSpectrumPath(self, spectrum):
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]
            newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':
                    # spectrum.filePath = newFilePath
                    self._changes['spectrumFilePath'] = partial(self._setSpectrumFilePath, newFilePath)
                else:
                    getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

        # if self.pathData.isModified():
        #     filePath = self.pathData.text()
        #
        #     # Convert from custom repository names to full names
        #     filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, filePath)
        #
        #     if os.path.exists(filePath):
        #         self._changes['spectrumFilePath'] = partial(self._setSpectrumFilePath, filePath)
        #     else:
        #         self.logger.error('Cannot set spectrum path to %s. Path does not exist' % self.pathData.text())

    def _setSpectrumFilePath(self, filePath):
        self.spectrum.filePath = filePath
        self._writeLoggingMessage("spectrum.filePath = '%s'" % filePath)
        self.pythonConsole.writeConsoleCommand("spectrum.filePath('%s')" % filePath,
                                               spectrum=self.spectrum)

        self.spectrum.filePath = filePath
        self._setPathData(self.spectrum)

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

    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            addNewColour(newColour)
            self._parent._fillPullDowns()  #fillColourPulldown(self.colourBox, allowAuto=False)
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

            self._changes['spectrumColour'] = partial(self._setSpectrumColour, spectrum, newColour)

    def _setSpectrumColour(self, spectrum, newColour):
        spectrum._apiDataSource.setSliceColour(newColour.name())
        self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour.name())
        self.pythonConsole.writeConsoleCommand("spectrum.sliceColour = '%s'" % newColour.name(), spectrum=self.spectrum)

    def _queueChangeSliceComboIndex(self, spectrum, value):
        self._changes['sliceComboIndex'] = partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=self.spectrum)


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
        Label(self, text="Spectrometer Frequency (Hz) ", grid=(row, 0), vAlign='t', hAlign='l')

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
            self.axisCodeEdits[i].textChanged.connect(partial(self._queueSetAxisCodes,
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

            self.isotopeCodePullDowns[i].currentIndexChanged.connect(partial(self._queueSetIsotopeCodes, self.isotopeCodePullDowns[i].getText, i))

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
            self.spectralReferencingData[i] = LineEdit(self,
                                                       text='<None>' if value is None else str("%.3f" % value),
                                                       grid=(row, i + 1), vAlign='t', hAlign='l')
            self.spectralReferencingData[i].textChanged.connect(partial(self._queueSetDimensionReferencing,
                                                                        self.spectralReferencingData[i].text, i))
            # self.spectralReferencingDataList.append(spectralReferencingData)

            row += 1
            # Label(self, text="Referencing (points)", grid=(8, 0), vAlign='t', hAlign='l')
            value = spectrum.referencePoints[i]
            self.spectralReferencingDataPoints[i] = LineEdit(self,
                                                             text='<None>' if value is None else str("%.3f" % value),
                                                             # text=str("%.3f" % (spectrum.referencePoints[i] or 0.0)),
                                                             grid=(row, i + 1), vAlign='t', hAlign='l')
            self.spectralReferencingDataPoints[i].textChanged.connect(partial(self._queueSetPointDimensionReferencing,
                                                                              self.spectralReferencingDataPoints[i].text, i))
            # self.spectralReferencingDataPointsList.append(spectralReferencingDataPoints)

            row += 1
            # Label(self, text="Assignment Tolerance ", grid=(row, 0),  hAlign='l')
            value = spectrum.assignmentTolerances[i]
            self.spectralAssignmentToleranceData[i] = LineEdit(self,
                                                               text='<None>' if value is None else str("%.3f" % value),
                                                               grid=(row, i + 1), hAlign='l')
            self.spectralAssignmentToleranceData[i].textChanged.connect(partial(self._queueSetAssignmentTolerances,
                                                                                self.spectralAssignmentToleranceData[i].text, i))

            row += 1
            # Label(self, text="Second cursor offset (Hz) ", grid=(10, 0), hAlign='l')
            value = spectrum.doubleCrosshairOffsets[i]
            self.spectralDoubleCursorOffset[i] = LineEdit(self,
                                                          text='0' if value is None else str("%.3f" % value),
                                                          grid=(row, i + 1), hAlign='l')
            self.spectralDoubleCursorOffset[i].textChanged.connect(partial(self._queueSetDoubleCursorOffset,
                                                                           self.spectralDoubleCursorOffset[i].text, i))

            row += 1
            if i == 0:
                # only need 1 checkbox in the first column
                showFolded = spectrum.displayFoldedContours
                self.displayedFoldedContours = CheckBox(self, grid=(row, i + 1), vAlign='t',
                                                        checked=showFolded)
                self.displayedFoldedContours.clicked.connect(partial(self._queueSetDisplayFoldedContours, self.displayedFoldedContours.isChecked))

            row += 1
            fModes = spectrum.foldingModes
            dd = {'circular': False, 'mirror': True, None: False}
            self.foldingModesCheckBox[i] = CheckBox(self, grid=(row, i + 1), vAlign='t')
            self.foldingModesCheckBox[i].setChecked(dd[fModes[i]])
            self.foldingModesCheckBox[i].clicked.connect(partial(self._queueSetFoldingModes, self.foldingModesCheckBox[i].isChecked, i))
            # self.foldingModesCheckBox[i].setEnabled(False)

            # pullDown for min/max aliasing
            aliasLim = spectrum.aliasingRange
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

            self.maxAliasingPullDowns[i].currentIndexChanged.connect(partial(self._queueSetMaxAliasing, self.maxAliasingPullDowns[i].getText, i))

            # min aliasing
            row += 1
            self.minAliasingPullDowns[i] = PulldownList(self, grid=(row, i + 1), vAlign='t',
                                                        texts=aliasMinText)
            if aliasLim[i][0] in aliasMinRange:
                index = aliasMinRange.index(aliasLim[i][0])
                self.minAliasingPullDowns[i].setIndex(index)

            self.minAliasingPullDowns[i].currentIndexChanged.connect(partial(self._queueSetMinAliasing, self.minAliasingPullDowns[i].getText, i))

        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, dimensions + 1), colour=getColours()[DIVIDER], height=15)

        row += 1
        self.preferredAxisOrderPulldown = PulldownListCompoundWidget(self, labelText="Preferred Axis Order",
                                                                     grid=(row, 0), gridSpan=(1, dimensions + 1), vAlign='t',
                                                                     callback=self._setSpectrumOrdering)
        self.preferredAxisOrderPulldown.setPreSelect(self._fillPreferredWidgetFromAxisTexts)
        self._fillPreferredWidget()

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

    def _setSpectrumOrdering(self, value):
        """Set the preferred axis ordering from the pullDown selection
        """
        index = self.preferredAxisOrderPulldown.getIndex()

        axisOrder = tuple(permutations(list(range(len(self.spectrum.axisCodes)))))
        if index > 0:
            self.spectrum.preferredAxisOrdering = tuple(axisOrder[index - 1])
        else:
            self.spectrum.preferredAxisOrdering = None

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

    def _queueSetAssignmentTolerances(self, valueGetter, dim):
        self._changes['assignmentTolerances{}'.format(dim)] = partial(self._setAssignmentTolerances,
                                                                      self.spectrum, dim, valueGetter())

    def _setAssignmentTolerances(self, spectrum, dim, value):
        assignmentTolerances = list(spectrum.assignmentTolerances)
        assignmentTolerances[dim] = float(value)
        spectrum.assignmentTolerances = assignmentTolerances
        self.pythonConsole.writeConsoleCommand("spectrum.assignmentTolerances = {0}".format(assignmentTolerances), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.assignmentTolerances = {0}".format(assignmentTolerances))

    def _queueSetDoubleCursorOffset(self, valueGetter, dim):
        self._changes['doubleCursorOffset{}'.format(dim)] = partial(self._setDoubleCursorOffset,
                                                                    self.spectrum, dim, valueGetter())

    def _setDoubleCursorOffset(self, spectrum, dim, value):
        doubleCrosshairOffsets = list(spectrum.doubleCrosshairOffsets)
        doubleCrosshairOffsets[dim] = float(value)
        spectrum.doubleCrosshairOffsets = doubleCrosshairOffsets
        self.pythonConsole.writeConsoleCommand("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.doubleCrosshairOffsets = {0}".format(doubleCrosshairOffsets))

    def _queueSetAxisCodes(self, valueGetter, dim):
        self._changes['AxisCodes{}'.format(dim)] = partial(self._setAxisCodes,
                                                           self.spectrum, dim, valueGetter())

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

    def _queueSetIsotopeCodes(self, valueGetter, dim):
        self._changes['IsotopeCodes{}'.format(dim)] = partial(self._setIsotopeCodes,
                                                              self.spectrum, dim, valueGetter())

    def _setIsotopeCodes(self, spectrum, dim, value):
        isotopeCodes = list(spectrum.isotopeCodes)
        isotopeCodes[dim] = str(value)
        spectrum.isotopeCodes = isotopeCodes
        showWarning('Change Isotope Code', 'Caution is advised when changing isotope codes\n'
                                           'It can adversely affect spectrumDisplays and peak/integral/multiplet lists.')

        self.pythonConsole.writeConsoleCommand("spectrum.isotopeCodes = {0}".format(isotopeCodes), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(isotopeCodes))

    def _queueSetDimensionReferencing(self, valueGetter, dim):
        self._changes['dimensionReferencing{}'.format(dim)] = partial(self._setDimensionReferencing,
                                                                      self.spectrum, dim, valueGetter())

    def _setDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referenceValues)
        spectrumReferencing[dim] = float(value)
        spectrum.referenceValues = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referenceValues = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referenceValues = {0}".format(spectrumReferencing))

    def _queueSetPointDimensionReferencing(self, valueGetter, dim):
        self._changes['dimensionReferencingPoint{}'.format(dim)] = partial(self._setPointDimensionReferencing,
                                                                           self.spectrum, dim, valueGetter())

    def _setPointDimensionReferencing(self, spectrum, dim, value):
        spectrumReferencing = list(spectrum.referencePoints)
        spectrumReferencing[dim] = float(value)
        spectrum.referencePoints = spectrumReferencing
        self.pythonConsole.writeConsoleCommand("spectrum.referencePoints = {0}".format(spectrumReferencing), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.referencePoints = {0}".format(spectrumReferencing))

    def _queueSetMinAliasing(self, valueGetter, dim):
        self._changes['minAliasing{}'.format(dim)] = partial(self._setMinAliasing,
                                                             self.spectrum, dim, valueGetter())
        minValue = int(valueGetter())
        maxValue = int(self.maxAliasingPullDowns[dim].getText())
        if minValue > maxValue:
            self.maxAliasingPullDowns[dim].select(str(minValue))

    def _setMinAliasing(self, spectrum, dim, value):
        alias = list(spectrum.aliasingRange)
        value = int(value)

        alias[dim] = (value, max(alias[dim][1], value))
        spectrum.aliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.aliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.aliasingRange = {0}".format(tuple(alias)))

    def _queueSetMaxAliasing(self, valueGetter, dim):
        self._changes['maxAliasing{}'.format(dim)] = partial(self._setMaxAliasing,
                                                             self.spectrum, dim, valueGetter())
        maxValue = int(valueGetter())
        minValue = int(self.minAliasingPullDowns[dim].getText())
        if maxValue < minValue:
            self.minAliasingPullDowns[dim].select(str(maxValue))

    def _setMaxAliasing(self, spectrum, dim, value):
        alias = list(spectrum.aliasingRange)
        value = int(value)
        alias[dim] = (min(alias[dim][0], value), value)
        spectrum.aliasingRange = tuple(alias)

        self.pythonConsole.writeConsoleCommand("spectrum.aliasingRange = {0}".format(tuple(alias)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.aliasingLimits = {0}".format(tuple(alias)))

    def _queueSetFoldingModes(self, valueGetter, dim):
        self._changes['foldingModes{}'.format(dim)] = partial(self._setFoldingModes,
                                                              self.spectrum, dim, valueGetter())

    def _setFoldingModes(self, spectrum, dim, value):
        dd = {True: 'mirror', False: 'circular', None: None}

        folding = list(spectrum.foldingModes)
        folding[dim] = dd[bool(value)]
        spectrum.foldingModes = tuple(folding)

        self.pythonConsole.writeConsoleCommand("spectrum.foldingModes = {0}".format(tuple(folding)), spectrum=spectrum)
        self._writeLoggingMessage("spectrum.foldingModes = {0}".format(tuple(folding)))

    def _queueSetDisplayFoldedContours(self, valueGetter):
        self._changes['displayFoldedContours'] = partial(self._setDisplayFoldedContours,
                                                         self.spectrum, valueGetter())

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

        positiveContoursLabel = Label(self, text="Show Positive Contours", grid=(1, 0), vAlign='t', hAlign='l')
        positiveContoursCheckBox = CheckBox(self, grid=(1, 1), checked=True, vAlign='t', hAlign='l')
        # for spectrumView in self.spectrum.spectrumViews:
        #     if spectrumView.displayPositiveContours:
        #         positiveContoursCheckBox.setChecked(True)
        #     else:
        #         positiveContoursCheckBox.setChecked(False)
        positiveContoursCheckBox.setChecked(self.spectrum.includePositiveContours)

        self.layout().addItem(QtWidgets.QSpacerItem(0, 10), 0, 0)
        positiveContoursCheckBox.stateChanged.connect(self._queueChangePositiveContourDisplay)

        positiveBaseLevelLabel = Label(self, text="Positive Base Level", grid=(2, 0), vAlign='c', hAlign='l')
        self.positiveBaseLevelData = ScientificDoubleSpinBox(self, grid=(2, 1), vAlign='t')
        self.positiveBaseLevelData.setMaximum(1e12)
        self.positiveBaseLevelData.setMinimum(0.1)
        self.positiveBaseLevelData.setValue(self.spectrum.positiveContourBase)
        self.positiveBaseLevelData.valueChanged.connect(partial(self._queueChangePositiveBaseLevel, self.spectrum))
        # self.positiveBaseLevelData.setSingleStep(self.positiveBaseLevelData.value()*(self.positiveMultiplierData.value()-1))
        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.positiveBaseLevelData.setSingleStep(self.positiveBaseLevelData.value() * 0.1)

        positiveMultiplierLabel = Label(self, text="Positive Multiplier", grid=(3, 0), vAlign='c', hAlign='l')
        self.positiveMultiplierData = DoubleSpinbox(self, grid=(3, 1), vAlign='t')
        self.positiveMultiplierData.setSingleStep(0.1)
        self.positiveMultiplierData.setValue(float(self.spectrum.positiveContourFactor))
        self.positiveMultiplierData.valueChanged.connect(partial(self._queueChangePositiveContourMultiplier, self.spectrum))

        positiveContourCountLabel = Label(self, text="Number of positive contours", grid=(4, 0), vAlign='c', hAlign='l')
        self.positiveContourCountData = Spinbox(self, grid=(4, 1), vAlign='t')
        self.positiveContourCountData.setValue(int(self.spectrum._apiDataSource.positiveContourCount))
        self.positiveContourCountData.valueChanged.connect(partial(self._queueChangePositiveContourCount, self.spectrum))
        positiveContourColourLabel = Label(self, text="Positive Contour Colour", grid=(5, 0), vAlign='c', hAlign='l')

        self.positiveColourBox = PulldownList(self, grid=(5, 1), vAlign='t')
        self.negativeColourBox = PulldownList(self, grid=(10, 1), vAlign='t')

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

        self.positiveColourBox.currentIndexChanged.connect(partial(self._queueChangePosColourComboIndex, self.spectrum))

        self.positiveColourButton = Button(self, grid=(5, 2), vAlign='t', hAlign='l',
                                           icon='icons/colours', hPolicy='fixed')
        self.positiveColourButton.clicked.connect(partial(self._queueChangePosSpectrumColour, self.spectrum))

        negativeContoursLabel = Label(self, text="Show Negative Contours", grid=(6, 0), vAlign='c', hAlign='l')
        negativeContoursCheckBox = CheckBox(self, grid=(6, 1), checked=True, vAlign='t', hAlign='l')
        # for spectrumView in self.spectrum.spectrumViews:
        #     if spectrumView.displayNegativeContours:
        #         negativeContoursCheckBox.setChecked(True)
        #     else:
        #         negativeContoursCheckBox.setChecked(False)
        negativeContoursCheckBox.setChecked(self.spectrum.includeNegativeContours)

        negativeContoursCheckBox.stateChanged.connect(self._queueChangeNegativeContourDisplay)

        negativeBaseLevelLabel = Label(self, text="Negative Base Level", grid=(7, 0), vAlign='c', hAlign='l')
        self.negativeBaseLevelData = ScientificDoubleSpinBox(self, grid=(7, 1), vAlign='t')
        self.negativeBaseLevelData.setMaximum(-0.1)
        self.negativeBaseLevelData.setMinimum(-1e12)
        self.negativeBaseLevelData.setValue(self.spectrum.negativeContourBase)
        self.negativeBaseLevelData.valueChanged.connect(partial(self._queueChangeNegativeBaseLevel, self.spectrum))
        # self.negativeBaseLevelData.setSingleStep((self.negativeBaseLevelData.value()*-1)*self.negativeMultiplierData.value()-1)
        # Changed to get less quickly to zero - but DoubleSpinBox is NOT right for this
        self.negativeBaseLevelData.setSingleStep((self.negativeBaseLevelData.value() * -1) * 0.1)

        negativeMultiplierLabel = Label(self, text="Negative Multiplier", grid=(8, 0), vAlign='c', hAlign='l')
        self.negativeMultiplierData = DoubleSpinbox(self, grid=(8, 1), vAlign='t')
        self.negativeMultiplierData.setValue(self.spectrum.negativeContourFactor)
        self.negativeMultiplierData.setSingleStep(0.1)
        self.negativeMultiplierData.valueChanged.connect(partial(self._queueChangeNegativeContourMultiplier, self.spectrum))

        negativeContourCountLabel = Label(self, text="Number of negative contours", grid=(9, 0), vAlign='c', hAlign='l')
        self.negativeContourCountData = Spinbox(self, grid=(9, 1), vAlign='t')
        self.negativeContourCountData.setValue(self.spectrum.negativeContourCount)
        self.negativeContourCountData.valueChanged.connect(partial(self._queueChangeNegativeContourCount, self.spectrum))
        negativeContourColourLabel = Label(self, text="Negative Contour Colour", grid=(10, 0), vAlign='c', hAlign='l')

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

        self.negativeColourBox.currentIndexChanged.connect(
                partial(self._queueChangeNegColourComboIndex, self.spectrum)
                )
        self.negativeColourButton = Button(self, grid=(10, 2), icon='icons/colours', hPolicy='fixed',
                                           vAlign='t', hAlign='l')
        self.negativeColourButton.clicked.connect(partial(self._queueChangeNegSpectrumColour, self.spectrum))

        self._contourOptionsFromNoise = _addContourNoiseButtons(self, 11, buttonLabel='Estimate Levels')

        Spacer(self, 5, 5, QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(12, 1), gridSpan=(1, 1))

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
            self.positiveBaseLevelData.setValue(posBase)
        if negBase:
            self.negativeBaseLevelData.setValue(negBase)
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

    def _queueChangePositiveContourDisplay(self, state):
        self._changes['positiveContourDisplay'] = partial(self._changePositiveContourDisplay, state)

    def _changePositiveContourDisplay(self, state):
        if state == QtCore.Qt.Checked:
            self.spectrum.includePositiveContours = True
            for spectrumView in self.spectrum.spectrumViews:
                spectrumView.displayPositiveContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = True")
        else:
            self.spectrum.includePositiveContours = False
            for spectrumView in self.spectrum.spectrumViews:
                spectrumView.displayPositiveContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayPositiveContours = False")

    def _queueChangeNegativeContourDisplay(self, state):
        self._changes['negativeContourDisplay'] = partial(self._changeNegativeContourDisplay, state)

    def _changeNegativeContourDisplay(self, state):
        if state == QtCore.Qt.Checked:
            self.spectrum.includeNegativeContours = True
            for spectrumView in self.spectrum.spectrumViews:
                spectrumView.displayNegativeContours = True
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = True")
        else:
            self.spectrum.includeNegativeContours = False
            for spectrumView in self.spectrum.spectrumViews:
                spectrumView.displayNegativeContours = False
                self.logger.info("spectrumView = ui.getByGid('%s')" % spectrumView.pid)
                self.logger.info("spectrumView.displayNegativeContours = False")

    def _queueChangePositiveBaseLevel(self, spectrum, value):
        self._changes['positiveContourBaseLevel'] = partial(self._changePositiveBaseLevel, spectrum, value)

    def _changePositiveBaseLevel(self, spectrum, value):
        spectrum.positiveContourBase = float(value)
        self._writeLoggingMessage("spectrum.positiveContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourBase = %f" % float(value), spectrum=spectrum)

    def _queueChangePositiveContourMultiplier(self, spectrum, value):
        self._changes['positiveContourMultiplier'] = partial(self._changePositiveContourMultiplier, spectrum, value)

    def _changePositiveContourMultiplier(self, spectrum, value):
        spectrum.positiveContourFactor = float(value)
        self._writeLoggingMessage("spectrum.positiveContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourFactor = %f" % float(value), spectrum=spectrum)

    def _queueChangePositiveContourCount(self, spectrum, value):
        self._changes['positiveContourCount'] = partial(self._changePositiveContourCount, spectrum, value)

    def _changePositiveContourCount(self, spectrum, value):
        spectrum.positiveContourCount = int(value)
        self._writeLoggingMessage("spectrum.positiveContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.positiveContourCount = %d" % int(value), spectrum=spectrum)

    def _queueChangeNegativeBaseLevel(self, spectrum, value):
        self._changes['negativeContourBaseLevel'] = partial(self._changeNegativeBaseLevel, spectrum, value)

    def _changeNegativeBaseLevel(self, spectrum, value):
        spectrum.negativeContourBase = float(value)
        self._writeLoggingMessage("spectrum.negativeContourBase = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourBase = %f" % float(value), spectrum=spectrum)

    def _queueChangeNegativeContourMultiplier(self, spectrum, value):
        self._changes['negativeContourMultiplier'] = partial(self._changeNegativeContourMultiplier, spectrum, value)

    def _changeNegativeContourMultiplier(self, spectrum, value):
        spectrum.negativeContourFactor = float(value)
        self._writeLoggingMessage("spectrum.negativeContourFactor = %f" % float(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourFactor = %f" % float(value), spectrum=spectrum)

    def _queueChangeNegativeContourCount(self, spectrum, value):
        self._changes['negativeContourCount'] = partial(self._changeNegativeContourCount, spectrum, value)

    def _changeNegativeContourCount(self, spectrum, value):
        spectrum.negativeContourCount = int(value)
        self._writeLoggingMessage("spectrum.negativeContourCount = %d" % int(value))
        self.pythonConsole.writeConsoleCommand("spectrum.negativeContourCount = %d" % int(value), spectrum=spectrum)

    # change colours using comboboxes and colour buttons
    def _queueChangePosSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()  #fillColourPulldown(self.positiveColourBox, allowAuto=False)
            self.positiveColourBox.setCurrentText(spectrumColours[newColour.name()])

    def _queueChangeNegSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)
        newColour = dialog.getColor()
        if newColour is not None:
            addNewColour(newColour)
            self._parent._fillPullDowns()  #fillColourPulldown(self.positiveColourBox, allowAuto=False)
            # fillColourPulldown(self.negativeColourBox, allowAuto=False)
            self.negativeColourBox.setCurrentText(spectrumColours[newColour.name()])

    def _queueChangePosColourComboIndex(self, spectrum, value):
        self._changes['positiveColourComboIndex'] = partial(self._changePosColourComboIndex, spectrum, value)

    def _changePosColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.positiveColourBox.currentText()))]
        if newColour:
            spectrum.positiveContourColour = newColour
            self._writeLoggingMessage("spectrum.positiveContourColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.positiveContourColour = '%s'" % newColour, spectrum=spectrum)

    def _queueChangeNegColourComboIndex(self, spectrum, value):
        self._changes['negativeColourComboIndex'] = partial(self._changeNegColourComboIndex, spectrum, value)

    def _changeNegColourComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.negativeColourBox.currentText()))]
        if newColour:
            spectrum._apiDataSource.negativeContourColour = newColour
            self._writeLoggingMessage("spectrum.negativeContourColour = %s" % newColour)
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

        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply', 'Ok'],
                                       callbacks=[self.reject, self._applyChanges, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(2, 1), gridSpan=(1, 4))
        self.applyButtons.getButton('Apply').setFocus()

        self._fillPullDowns()

        # clear the changes dict in each tab
        tabs = self._contoursTab
        for t in tabs:
            t._changes = dict()

        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton('Apply'))

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

        if error.errorValue:
            # repopulate popup
            self._repopulate()
            return False

        return True

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

        self.applyButtons = ButtonList(self, texts=['Cancel', 'Apply', 'Ok'],
                                       callbacks=[self.reject, self._applyChanges, self._okButton],
                                       tipTexts=['', '', '', None], direction='h',
                                       hAlign='r', grid=(2, 1), gridSpan=(1, 4))
        self.applyButtons.getButton('Apply').setFocus()

        self._fillPullDowns()

        # clear the changes dict in each tab
        tabs = self._generalTab
        for t in tabs:
            t._changes = dict()

        self.setFixedSize(self.sizeHint())

        # as this is a dialog, need to set one of the buttons as the default button when other widgets have focus
        self.setDefaultButton(self.applyButtons.getButton('Apply'))

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

        if error.errorValue:
            # repopulate popup
            self._repopulate()
            return False

        return True

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

        self.colourBox.currentIndexChanged.connect(partial(self._queueChangeSliceComboIndex, self.spectrum))
        colourButton = Button(self, vAlign='t', hAlign='l', grid=(7, 2), hPolicy='fixed',
                              callback=partial(self._queueSetSpectrumColour, self.spectrum), icon='icons/colours')

    def _repopulate(self):
        pass

    def _writeLoggingMessage(self, command):
        self.logger.info("spectrum = project.getByPid('%s')" % self.spectrum.pid)
        self.logger.info(command)

    def _queueSetSpectrumColour(self, spectrum):
        dialog = ColourDialog(self)

        newColour = dialog.getColor()
        if newColour:
            # pix = QtGui.QPixmap(QtCore.QSize(20, 20))
            # pix.fill(QtGui.QColor(newColour))
            # newIndex = str(len(spectrumColours.items())+1)
            # self.colourBox.addItem(icon=QtGui.QIcon(pix), text='Colour %s' % newIndex)
            # # spectrumColours[newColour.name()] = 'Colour %s' % newIndex
            # addNewColour(newColour)
            #
            # self.colourBox.setCurrentIndex(int(newIndex)-1)

            addNewColour(newColour)
            self._parent._fillPullDowns()  #fillColourPulldown(self.colourBox, allowAuto=False)
            self.colourBox.setCurrentText(spectrumColours[newColour.name()])

            self._changes['spectrumColour'] = partial(self._setSpectrumColour, spectrum, newColour)

    def _setSpectrumColour(self, spectrum, newColour):
        spectrum._apiDataSource.setSliceColour(newColour.name())
        self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour.name())
        self.pythonConsole.writeConsoleCommand("spectrum.sliceColour = '%s'" % newColour.name(), spectrum=self.spectrum)

    def _queueChangeSliceComboIndex(self, spectrum, value):
        self._changes['sliceComboIndex'] = partial(self._changedSliceComboIndex, spectrum, value)

    def _changedSliceComboIndex(self, spectrum, value):
        # newColour = list(spectrumColours.keys())[value]
        newColour = list(spectrumColours.keys())[list(spectrumColours.values()).index(colourNameNoSpace(self.colourBox.currentText()))]
        if newColour:
            spectrum.sliceColour = newColour
            self._writeLoggingMessage("spectrum.sliceColour = '%s'" % newColour)
            self.pythonConsole.writeConsoleCommand("spectrum.sliceColour '%s'" % newColour, spectrum=self.spectrum)
