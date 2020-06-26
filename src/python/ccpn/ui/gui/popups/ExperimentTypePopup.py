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
__dateModified__ = "$dateModified: 2020-06-26 12:13:45 +0100 (Fri, June 26, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore
from functools import partial
from ccpn.ui.gui.popups.ExperimentFilterPopup import ExperimentFilterPopup
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget


def _getAtomCodes(spectrum):
    """CCPN internal. Used in Spectrum Popup. Gets all the experiment type names to set the pulldown widgets
    """
    axisCodes = []
    for isotopeCode in spectrum.isotopeCodes:
        axisCodes.append(''.join([char for char in isotopeCode if not char.isdigit()] if isotopeCode else '*'))
    atomCodes = tuple(sorted(axisCodes))
    return atomCodes


def _getExperimentTypes(project, spectrum):
    """ CCPN internal. Used in Spectrum Popup. Gets all the experiment type names to set the pulldown widgets
    """
    atomCodes = _getAtomCodes(spectrum)
    return project._experimentTypeMap[spectrum.dimensionCount].get(atomCodes)


class ExperimentTypePopup(CcpnDialogMainWidget):

    USESCROLLWIDGET = True
    FIXEDWIDTH = True

    def __init__(self, parent=None, mainWindow=None, title: str = 'Experiment Type Selection', **kwds):

        from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import priorityNameRemapping

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current

        self._parent = parent
        spectra = self.project.spectra
        self.experimentTypes = self.project._experimentTypeMap
        self.spPulldowns = []

        for spectrumIndex, spectrum in enumerate(spectra):
            atomCodes = _getAtomCodes(spectrum)
            itemFilter = _getExperimentTypes(spectrum.project, spectrum)

            # add the widgets
            spLabel = Label(self.mainWidget, text=spectrum.pid, grid=(spectrumIndex, 0))
            spPulldown = FilteringPulldownList(self.mainWidget, grid=(spectrumIndex, 1),
                                                    callback=partial(self._setExperimentType, spectrum, atomCodes),)

            if itemFilter:
                # populate pullDown with filtered experimentTypes
                pulldownItems = list(itemFilter.keys())
                spPulldown.setData(texts=pulldownItems)

            else:
                # populate pullDown with all experimentTypes
                pulldownItems = list(vv for vals in self.experimentTypes[spectrum.dimensionCount].values() for vv in vals.keys())
                spPulldown.setData(texts=pulldownItems)

            spPulldown.lineEdit().editingFinished.connect(partial(self.editedExpTypeChecker, spPulldown, pulldownItems))
            self.spPulldowns.append(spPulldown)

            spButton = Button(self.mainWidget, grid=(spectrumIndex, 2),
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
            if text not in pulldownItems:
                text = spectrum.experimentType
            # apiRefExperiment = spectrum._wrappedData.experiment.refExperiment
            # text = apiRefExperiment and (apiRefExperiment.synonym or apiRefExperiment.name)
            text = priorityNameRemapping.get(text, text)
            spPulldown.setCurrentIndex(spPulldown.findText(text))

        self.setCloseButton(callback=self.accept)
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()

        # self.setWindowTitle(title)
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
