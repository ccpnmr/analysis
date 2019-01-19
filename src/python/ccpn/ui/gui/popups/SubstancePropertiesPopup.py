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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.CompoundView import CompoundView, Variant, importSmiles
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


OTHER_UNIT = ['µ', 'm', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg', 'kg', 'g', 'mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
SUBSTANCE_TYPE = ['Molecule', 'Cell', 'Material', 'Composite ', 'Other']

SEP = ', '


class SubstancePropertiesPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None,
                 substance=None, sampleComponent=None, newSubstance=False,
                 title='Substance Properties', **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        # self.setModal(True)         # ejb - WHY????

        self.mainWindow = mainWindow  # ejb - should always be done like this
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.preferences = self.application.preferences

        # self.sample = parent # GWV: this cannot be correct
        self.sampleComponent = sampleComponent
        self.substance = substance

        self.createNewSubstance = newSubstance

        self.contentsFrame = Frame(self, setLayout=True, grid=(1, 1), spacing=(5, 5))
        # self.moreWidgetsFrame = Frame(self, setLayout=True, grid=(1,1), gridSpan=(3,1), spacing=(5,5))

        self._setMainLayout()
        self._setWidgets()
        self._addWidgetsToLayout(self._allWidgets(), self.mainLayout)

        if self.createNewSubstance:
            self._checkCurrentSubstances()
        else:
            self._hideSubstanceCreator()

    def _setMainLayout(self):
        self.mainLayout = self.contentsFrame.layout()  # QtWidgets.QGridLayout()
        # self.contentsFrame.setLayout(self.mainLayout)

        # self.setWindowTitle("Substance Properties")
        # self.setFixedHeight(300)
        self.mainLayout.setContentsMargins(15, 20, 25, 10)  # L,T,R,B

    def _setWidgets(self):
        for setWidget in self._getWidgetsToSet():
            setWidget()

    def _addWidgetsToLayout(self, widgets, frame):
        count = int(len(widgets) / 2)
        self.positions = [[i + 1, j] for i in range(count) for j in range(2)]
        for position, widget in zip(self.positions, widgets):
            i, j = position
            frame.layout().addWidget(widget, i, j)

    def _getWidgetsToSet(self):
        widgetsToSet = (self._initialOptionWidgets, self._setCurrentSubstanceWidgets,
                        self._substanceNameWidget, self.labellingWidget,
                        self._chemicalNameWidget, self._referenceSpectrumWidget,
                        self._smilesWidget, self._empiricalFormulaWidget,
                        self._molecularMassWidget, self._commentWidget, self._labelUserCodeWidget,
                        self._casNumberWidget, self._atomWidget, self._bondCountWidget,
                        self._ringCountWidget, self._bondDonorCountWidget, self._bondAcceptorCountWidget,
                        self._polarSurfaceAreaWidget, self._logPWidget, self._showCompoundView,
                        self._setPerformButtonWidgets
                        # self._moreWidgetsFrame
                        )
        return widgetsToSet

    def _allWidgets(self):
        return (
            self.spacerLabel, self.selectInitialRadioButtons,
            self.currentSubstanceLabel, self.substancePulldownList,
            self.substanceLabel, self.nameSubstance,
            self._substanceLabellingLabel, self.labelling,
            self.chemicalNameLabel, self.chemicalName,
            self.referenceSpectraLabel, self.referenceSpectra,
            self.smilesLabel, self.smilesLineEdit,
            self.empiricalFormulaLabel, self.empiricalFormula,
            self.molecularMassLabel, self.molecularMass,
            self.labelUserCode, self.userCode,
            self.labelCasNumber, self.casNumber,
            self.labelAtomCount, self.atomCount,
            self.labelBondCount, self.bondCount,
            self.labelRingCount, self.ringCount,
            self.labelHBondDonorCount, self.hBondDonorCount,
            self.labelHBondAcceptorCount, self.hBondAcceptorCount,
            self.labelpolarSurfaceArea, self.polarSurfaceArea,
            self.labelLogP, self.logP,
            self.moleculeViewLabel, self.compoundView,
            self.labelcomment, self.comment,
            self.spacerLabel, self.buttonBox
            )

    def _initialOptionWidgets(self):
        self.spacerLabel = Label(self, text="")
        self.selectInitialRadioButtons = RadioButtons(self, texts=['New', 'From Existing'],
                                                      selectedInd=1,
                                                      callback=None,
                                                      direction='h',
                                                      tipTexts=None,
                                                      )

    def _setCurrentSubstanceWidgets(self):
        self.currentSubstanceLabel = Label(self, text="Current Substances")
        self.substancePulldownList = PulldownList(self)
        if self.createNewSubstance:
            self._fillsubstancePulldownList()
            self.substancePulldownList.activated[str].connect(self._fillInfoFromSubstance)

    def _substanceTypeWidget(self):
        self.typeLabel = Label(self, text="Type")
        self.type = Label(self, text="Molecule")

    def _substanceNameWidget(self):
        self.substanceLabel = Label(self, text="Substance Name")
        self.nameSubstance = LineEdit(self, 'New')
        if self.substance:
            self.nameSubstance.setText(self.substance.name)

    def labellingWidget(self):
        self._substanceLabellingLabel = Label(self, text="Labelling")
        self.labelling = LineEdit(self, 'None')
        if self.substance:
            self.labelling.setText(self.substance.labelling)

    def _referenceSpectrumWidget(self):
        self.referenceSpectraLabel = Label(self, text="Reference Spectrum")
        spectra = self.project.spectra
        spectraPids = [sp.pid for sp in self.project.spectra]
        self.referenceSpectra = PulldownList(self, objects=spectra, texts=spectraPids)

        if self.substance:
            if len(self.substance.referenceSpectra) > 0:
                referenceSpectrum = self.substance.referenceSpectra[0]
                if referenceSpectrum is not None:
                    self.referenceSpectra.select(referenceSpectrum.pid)

    def _chemicalNameWidget(self):
        self.chemicalNameLabel = Label(self, text="Chemical Names")
        self.chemicalName = LineEdit(self)
        if self.substance:
            self.chemicalName.setText(SEP.join(self.substance.synonyms))

    def _smilesWidget(self):
        self.smilesLabel = Label(self, text="Smiles")
        self.smilesLineEdit = LineEdit(self)
        if self.substance:
            self.smilesLineEdit.setText(self.substance.smiles)

    def _empiricalFormulaWidget(self):
        self.empiricalFormulaLabel = Label(self, text="Empirical Formula")
        self.empiricalFormula = LineEdit(self)
        if self.substance:
            self.empiricalFormula.setText(str(self.substance.empiricalFormula))

    def _molecularMassWidget(self):
        self.molecularMassLabel = Label(self, text="Molecular Mass")
        self.molecularMass = LineEdit(self)
        if self.substance:
            self.molecularMass.setText(str(self.substance.molecularMass))

    def _commentWidget(self):
        self.labelcomment = Label(self, text="Comment")
        self.comment = LineEdit(self)
        if self.substance:
            self.comment.setText(self.substance.comment)

    def _labelUserCodeWidget(self):
        self.labelUserCode = Label(self, text="User Code")
        self.userCode = LineEdit(self)
        if self.substance:
            self.userCode.setText(str(self.substance.userCode))

    def _casNumberWidget(self):
        self.labelCasNumber = Label(self, text="Cas Number")
        self.casNumber = LineEdit(self)
        if self.substance:
            self.casNumber.setText(str(self.substance.casNumber))

    def _atomWidget(self):
        self.labelAtomCount = Label(self, text="Atom Count")
        self.atomCount = LineEdit(self)
        if self.substance:
            self.atomCount.setText(str(self.substance.atomCount))

    def _bondCountWidget(self):
        self.labelBondCount = Label(self, text="Bond Count")
        self.bondCount = LineEdit(self)
        if self.substance:
            self.bondCount.setText(str(self.substance.bondCount))

    def _ringCountWidget(self):
        self.labelRingCount = Label(self, text="Ring Count")
        self.ringCount = LineEdit(self)
        if self.substance:
            self.ringCount.setText(str(self.substance.ringCount))

    def _bondDonorCountWidget(self):
        self.labelHBondDonorCount = Label(self, text="H Bond Donor Count")
        self.hBondDonorCount = LineEdit(self)
        if self.substance:
            self.hBondDonorCount.setText(str(self.substance.hBondDonorCount))

    def _bondAcceptorCountWidget(self):
        self.labelHBondAcceptorCount = Label(self, text="H Bond Acceptor Count")
        self.hBondAcceptorCount = LineEdit(self)
        if self.substance:
            self.hBondAcceptorCount.setText(str(self.substance.hBondAcceptorCount))

    def _polarSurfaceAreaWidget(self):
        self.labelpolarSurfaceArea = Label(self, text="Polar Surface Area")
        self.polarSurfaceArea = LineEdit(self)
        if self.substance:
            self.polarSurfaceArea.setText(str(self.substance.polarSurfaceArea))

    def _logPWidget(self):
        self.labelLogP = Label(self, text="LogP")
        self.logP = LineEdit(self)
        if self.substance:
            self.logP.setText(str(self.substance.logPartitionCoefficient))

    def _showCompoundView(self):
        self.moleculeViewLabel = Label(self, text="Compound View")
        if self.substance:
            smiles = self.substance.smiles
            if smiles is None:
                smiles = 'H'
            else:
                smiles = smiles
        else:
            smiles = ''
        self.compoundView = CompoundView(self, smiles=smiles, preferences=self.preferences)
        # self.compoundView.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
        #                                 QtWidgets.QSizePolicy.MinimumExpanding)
        # self.compoundView.scene.setSceneRect(self.compoundView.scene.itemsBoundingRect())  # resize to the new items

        self.compoundView.centerView()
        self.compoundView.updateAll()

    def _setPerformButtonWidgets(self):
        self.spacerLabel = Label(self, text="")
        callbacks = [self._hideExtraSettings, self._showMoreSettings, self.reject, self._applyChanges, self._okButton]
        texts = ['Less', 'More', 'Cancel', 'Apply', 'Ok']

        # if not self.createNewSubstance:
        # Apply doesn't really work when creating new substance
        # (So after the apply, does the next apply/ok affect the just created substance or is a new one created??)
        # Pulldown list is not updated
        # But more seriously you end up editing existing substance instead of creating new ones
        # callbacks.insert(-1, self._applyChanges)
        # texts.insert(-1, 'Apply')

        self.buttonBox = ButtonList(self, callbacks=callbacks, texts=texts)
        self._hideExtraSettings()

    def _moreWidgetsFrame(self):
        # create a new frame to the more/less stuff in
        self.moreWidgetsFrame = Frame(self, setLayout=True, spacing=(5, 5))

    # CallBacks

    def _getCallBacksDict(self):
        return {
            self._renameLabelSubstance     : str(self.nameSubstance.text()),  # ejb - swap for the next two
            # self._changeNameSubstance: str(self.nameSubstance.text()),
            # self._labellingChanged:str(self.labelling.text()),
            self._chemicalNameChanged      : [name.strip() for name in self.chemicalName.text().split(SEP.strip()) if name.strip()],
            self._smilesChanged            : str(self.smilesLineEdit.text()),
            self._empiricalFormulaChanged  : str(self.empiricalFormula.text()),
            self._molecularMassChanged     : self.molecularMass.text(),
            self._referenceSpectraChanged  : self.referenceSpectra.getObject(),
            self._userCodeChanged          : str(self.userCode.text()),
            self._casNumberChanged         : str(self.casNumber.text()),
            self._atomCountChanged         : self.atomCount.text(),
            self._ringCountChanged         : self.ringCount.text(),
            self._hBondDonorCountChanged   : self.hBondDonorCount.text(),
            self._hBondAcceptorCountChanged: self.hBondAcceptorCount.text(),
            self._polarSurfaceAreaChanged  : self.polarSurfaceArea.text(),
            self._logPChanged              : self.logP.text(),
            self._commentChanged           : str(self.comment.text()),

            }

    #
    # def _substanceType(self, value):
    #   if value:
    #     print(value)
    #     # self.substance.substanceType = str(value)

    def _fillsubstancePulldownList(self):
        if len(self.project.substances) > 0:
            substancePulldownData = ['Select an option']
            for substance in self.project.substances:
                substancePulldownData.append(str(substance.id))
            self.substancePulldownList.setData(substancePulldownData)

    def _fillInfoFromSubstance(self, selected):
        if selected != 'Select an option':
            substance = self.project.getByPid('SU:' + selected)
            self.nameSubstance.setText(str(substance.name) + '-Copy')
            self.labelling.setText(str(substance.labelling))

    # def _changeNameSubstance(self, value):
    #   if value:
    #     if self.substance.name != value:
    #       self.substance.rename(name=value)
    #
    # def _labellingChanged(self, value):
    #   if value:
    #     if self.substance.labelling != value:
    #       self.substance.rename(labelling=value)

    def _renameLabelSubstance(self, value):
        name = str(self.nameSubstance.text())
        label = str(self.labelling.text())
        if self.substance.name != name or self.substance.labelling != label:
            self.substance.rename(name=name, labelling=label)

    def _chemicalNameChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.synonyms = value

    def _smilesChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.smiles = value
                if self.compoundView is not None:
                    self.compoundView.setSmiles(value)

                    # resize to the new items
                    self.compoundView.scene.setSceneRect(self.compoundView.scene.itemsBoundingRect())

    def _empiricalFormulaChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.empiricalFormula = str(value)

    def _molecularMassChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.molecularMass = float(value)

    def _referenceSpectraChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.referenceSpectra = (value,)

    def _userCodeChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.userCode = value

    def _casNumberChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.casNumber = value

    def _atomCountChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.atomCount = int(value)

    def _boundCountChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.bondCount = int(value)

    def _ringCountChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.ringCount = int(value)

    def _hBondDonorCountChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.hBondDonorCount = int(value)

    def _hBondAcceptorCountChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.hBondAcceptorCount = int(value)

    def _polarSurfaceAreaChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.polarSurfaceArea = float(value)

    def _logPChanged(self, value):
        if value:
            if value == 'None':
                return
            else:
                self.substance.logPartitionCoefficient = float(value)

    def _commentChanged(self, value):
        if value:
            self.substance.comment = value

    def _getSubstance(self):
        if len(self.project.substances) > 0:
            substance = self.project.newSubstance(name='NewSubstance-' + str(len(self.project.substances)))
            return substance
        else:
            substance = self.project.newSubstance(name='NewSubstance-', )
            return substance

    def _hideExtraSettings(self):
        self.contentsFrame.hide()
        for w in self._allWidgets()[12:-1]:
            w.hide()
        self.buttonBox.setButtonVisible('Less', False)
        self.buttonBox.setButtonVisible('More', True)
        self.contentsFrame.show()
        self.setFixedHeight(250)

    def _showMoreSettings(self):
        self.contentsFrame.hide()
        for w in self._allWidgets()[12:-1]:
            w.show()
        self.buttonBox.setButtonVisible('More', False)
        self.buttonBox.setButtonVisible('Less', True)
        self.contentsFrame.show()
        self.setFixedHeight(800)

    def _checkCurrentSubstances(self):
        if len(self.project.substances) > 0:
            for w in self._allWidgets()[0:4]:
                w.show()
        else:
            for w in self._allWidgets()[2:4]:
                w.hide()
            self.selectInitialRadioButtons.radioButtons[0].setChecked(True)
            self.selectInitialRadioButtons.radioButtons[1].setEnabled(False)

    def _hideSubstanceCreator(self):
        if len(self.project.substances) > 0:
            for w in self._allWidgets()[0:4]:
                w.hide()

    def _createNewSubstance(self):
        name = str(self.nameSubstance.text())
        labelling = str(self.labelling.text())
        self.substance = self.project.newSubstance(name=name, labelling=labelling)
        self.createNewSubstance = False

    def _setValue(self):
        for property, value in self._getCallBacksDict().items():
            property(value)

    def _setCallBacksDict(self):
        return [
            (self.substance.name, str, self.nameSubstance.setText),
            (self.substance.labelling, str, self.labelling.setText),
            # (self.substance.synonyms, str, self.chemicalName.setText),
            (self.substance.smiles, str, self.smilesLineEdit.setText),
            (self.substance.empiricalFormula, str, self.empiricalFormula.setText),
            (self.substance.molecularMass, str, self.molecularMass.setText),
            # (self.QWERT, str, self.referenceSpectra.setText),
            (self.substance.userCode, str, self.userCode.setText),
            (self.substance.casNumber, str, self.casNumber.setText),
            (self.substance.atomCount, str, self.atomCount.setText),
            (self.substance.bondCount, str, self.bondCount.setText),
            (self.substance.ringCount, str, self.ringCount.setText),
            (self.substance.hBondDonorCount, str, self.hBondDonorCount.setText),
            (self.substance.hBondAcceptorCount, str, self.hBondAcceptorCount.setText),
            (self.substance.polarSurfaceArea, str, self.polarSurfaceArea.setText),
            (self.substance.logPartitionCoefficient, str, self.logP.setText),
            (self.substance.comment, str, self.comment.setText)
            ]

    def _repopulate(self):
        if self.substance:
            for attrib, attribType, widget in self._setCallBacksDict():
                try:
                    if attrib is not None:  # trap the setting of the widgets
                        widget(attribType(attrib))
                finally:
                    pass

            if len(self.substance.referenceSpectra) > 0:
                referenceSpectrum = self.substance.referenceSpectra[0]
                if referenceSpectrum is not None:
                    self.referenceSpectra.select(referenceSpectrum.pid)

            self.chemicalName.setText(SEP.join(self.substance.synonyms))  # don't know how to handle above

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        applyAccept = False
        oldUndo = self.project._undo.numItems()

        from ccpn.core.lib.ContextManagers import undoBlockManager

        with undoBlockManager():
            try:
                # dependent on whether the popup is called as createNew or editExisting
                if self.createNewSubstance:
                    self._createNewSubstance()

                self._setValue()

                applyAccept = True
            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            # repopulate popup
            self._repopulate()
            return False
        else:
            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
