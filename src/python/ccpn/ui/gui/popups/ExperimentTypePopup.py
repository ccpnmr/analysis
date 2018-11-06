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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialog

from functools import partial
from ccpn.ui.gui.widgets.Spacer import Spacer


def _getExperimentTypes(project, spectrum):
    ''' CCPN internal. Used in Spectrum Popup. Gets all the experiment type names to set the pulldown widgets'''
    axisCodes = []
    for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()]))
    atomCodes = tuple(sorted(axisCodes))
    return project._experimentTypeMap[spectrum.dimensionCount].get(atomCodes)
    # return list(project._experimentTypeMap[spectrum.dimensionCount].get(atomCodes).keys())


class ExperimentTypePopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, title: str = 'Experiment Type Selection', **kwds):

        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current

        self._parent = parent
        spectra = self.project.spectra
        self.experimentTypes = self.project._experimentTypeMap
        self.spPulldowns = []
        self.scrollArea = ScrollArea(self, setLayout=True, grid=(0, 0))
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.scrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.scrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")

        for spectrumIndex, spectrum in enumerate(spectra):
            axisCodes = []
            for isotopeCode in spectrum.isotopeCodes:
                axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()]))

            atomCodes = tuple(sorted(axisCodes))
            self.pulldownItems = list(self.experimentTypes[spectrum.dimensionCount].get(atomCodes).keys())
            spLabel = Label(self.scrollAreaWidgetContents, text=spectrum.pid, grid=(spectrumIndex, 0))
            self.spPulldown = FilteringPulldownList(self.scrollAreaWidgetContents, grid=(spectrumIndex, 1),
                                                    callback=partial(self._setExperimentType, spectrum, atomCodes),
                                                    texts=self.pulldownItems)
            self.spPulldown.lineEdit().editingFinished.connect(partial(self.editedExpTypeChecker, self.spPulldown, self.pulldownItems))
            # self.spPulldown._completer.setCompletionMode(QtGui.QCompleter.InlineCompletion &~  QtGui.QCompleter.UnfilteredPopupCompletion)
            self.spPulldowns.append(self.spPulldown)
            spButton = Button(self.scrollAreaWidgetContents, grid=(spectrumIndex, 2),
                              callback=partial(self.raiseExperimentFilterPopup,
                                               spectrum, spectrumIndex, atomCodes),
                              hPolicy='fixed', icon='icons/applications-system')

            # Get the text that was used in the pulldown from the refExperiment
            # NBNB This could possibly give unpredictable results
            # if there is an experiment with experimentName (user settable!)
            # that happens to match the synonym for a different experiment type.
            # But if people will ignore our defined vocabulary, on their head be it!
            # Anyway, the alternative (discarded) is to look into the ExpPrototype
            # to compare RefExperiment names and synonyms
            # or (too ugly for words) to have a third attribute in parallel with
            # spectrum.experimentName and spectrum.experimentType

            text = spectrum.experimentName
            text = priorityNameRemapping.get(text, text)
            if text not in self.pulldownItems:
                text = spectrum.experimentType
            # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
            # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
            text = priorityNameRemapping.get(text, text)
            self.spPulldown.setCurrentIndex(self.spPulldown.findText(text))

        Spacer(self.scrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(len(spectra), 2), gridSpan=(1, 1))

        self.buttonBox = Button(self, grid=(1, 0), text='Close',
                                callback=self.accept, hAlign='r', vAlign='b')

        self.setWindowTitle(title)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setMinimumHeight(200)
        self.setFixedWidth(self.sizeHint().width()+24)

    def _setExperimentType(self, spectrum, atomCodes, item):
        expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(item)
        spectrum.experimentType = expType

    def raiseExperimentFilterPopup(self, spectrum, spectrumIndex, atomCodes):

        popup = ExperimentFilterPopup(parent=self.mainWindow, mainWindow=self.mainWindow, spectrum=spectrum)
        popup.exec_()
        if popup.expType:
            self.spPulldowns[spectrumIndex].select(popup.expType)
            expType = self.experimentTypes[spectrum.dimensionCount].get(atomCodes).get(popup.expType)

            if expType is not None:
                spectrum.experimentType = expType

    def editedExpTypeChecker(self, pulldown, items):
        if not pulldown.currentText() in items:
            if pulldown.currentText():
                msg = ' (ExpTypeNotFound!)'
                if not msg in pulldown.currentText():
                    pulldown.lineEdit().setText(pulldown.currentText() + msg)
                    pulldown.lineEdit().selectAll()

    def keyPressEvent(self, KeyEvent):
        if KeyEvent.key() == QtCore.Qt.Key_Return:
            return
