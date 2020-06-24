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
__dateModified__ = "$dateModified: 2020-06-24 14:48:32 +0100 (Wed, June 24, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.MoreLessFrame import MoreLessFrame
from ccpn.ui.gui.popups.AttributeEditorPopupABC import ComplexAttributeEditorPopupABC, VList, MoreLess, _blankContainer
from ccpn.ui.gui.widgets.CompoundWidgets import CompoundViewCompoundWidget
from ccpn.core.Substance import Substance


OTHER_UNIT = ['µ', 'm', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg', 'kg', 'g', 'mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
SUBSTANCE_TYPE = ['Molecule', 'Cell', 'Material', 'Composite ', 'Other']

SEP = ', '

SELECT = '> Select <'

LESS_BUTTON = 'Show less'
MORE_BUTTON = 'Show more'

TYPENEW = 'Type_New'
LABELLING = ['None', TYPENEW, '15N', '15N,13C', '15N,13C,2H', 'ILV', 'ILVA', 'ILVAT', 'SAIL', '1,3-13C- and 2-13C-Glycerol']
BUTTONSTATES = ['New', 'From Existing']

from ccpn.util.AttrDict import AttrDict
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, ScientificSpinBoxCompoundWidget, \
    RadioButtonsCompoundWidget, PulldownListCompoundWidget, SpinBoxCompoundWidget


class SubstancePropertiesPopup(ComplexAttributeEditorPopupABC):
    """
    Substance attributes editor popup
    """

    def _getLabelling(self, obj):
        """Populate the labelling pulldown
        """
        labels = LABELLING.copy()
        newLabel = str(self.obj.labelling)
        if newLabel not in labels:
            labels.append(newLabel)
        self.labelling.modifyTexts(labels)
        self.labelling.select(newLabel or 'None')

    def _getCurrentSubstances(self, obj):
        """Populate the current substances pulldown
        """
        substancePulldownData = [SELECT]
        for substance in self.project.substances:
            substancePulldownData.append(str(substance.id))
        self.Currentsubstances.pulldownList.setData(substancePulldownData)

    def _getSpectrum(self, attr, default):
        """change the value from the substance object into a pid for the pulldown
        """
        value = getattr(self, attr, default)
        if value and len(value) > 0:
            return value[0].pid

    def _setSpectrum(self, attr, value):
        """change the pid for the pulldown into the tuple for the substance object
        """
        spectrum = self.project.getByPid(value)
        if spectrum:
            setattr(self, attr, (spectrum,))
        else:
            setattr(self, attr, [])

    def _getCurrentSpectra(self, obj):
        """Populate the spectrum pulldown
        """
        spectrumPulldownData = [SELECT]
        for spectrum in self.project.spectra:
            spectrumPulldownData.append(str(spectrum.pid))
        self.referenceSpectra.pulldownList.setData(spectrumPulldownData)

    def _getSynonym(self, attr, default):
        """change the value from the substance object into a str for the synonym
        """
        value = getattr(self, attr, default)
        if value and len(value) > 0:
            return str(value[0])

    def _setSynonym(self, attr, value):
        """change the str for the synonym into the tuple for the substance object
        """
        if value:
            setattr(self, attr, (str(value),))
        else:
            setattr(self, attr, [])

    klass = Substance
    HWIDTH = 150
    attributes = VList([VList([('Select source', RadioButtonsCompoundWidget, None, None, None, None, {'texts'      : BUTTONSTATES,
                                                                                                      'selectedInd': 1,
                                                                                                      'direction'  : 'h',
                                                                                                      'hAlign'     : 'l'}),
                               ('Current substances', PulldownListCompoundWidget, None, None, _getCurrentSubstances, None, {'editable': False}),
                               ('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                               ('labelling', PulldownListCompoundWidget, getattr, setattr, _getLabelling, None, {'editable': True}),
                               ],
                              queueStates=False,
                              hWidth=HWIDTH,
                              ),
                        VList([('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}), ],
                              hWidth=HWIDTH,
                              ),
                        MoreLess([('synonyms', EntryCompoundWidget, _getSynonym, _setSynonym, None, None, {'backgroundText': ''}),
                                  ('referenceSpectra', PulldownListCompoundWidget, _getSpectrum, _setSpectrum, _getCurrentSpectra, None, {'editable': False}),
                                  ('empiricalFormula', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                                  ('molecularMass', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('userCode', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                                  ('casNumber', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                                  ('atomCount', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('bondCount', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('ringCount', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('hBondDonorCount', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('hBondAcceptorCount', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('polarSurfaceArea', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ('logPartitionCoefficient', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                                  ],
                                 hWidth=HWIDTH,
                                 name='Advanced',
                                 ),
                        MoreLess([VList([('smiles', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''})],
                                        hWidth=HWIDTH,
                                        ),
                                  VList([('Compound view', CompoundViewCompoundWidget, None, None, None, None, {})],
                                        queueStates=False,
                                        hWidth=HWIDTH,
                                        ),
                                  ],
                                 name='Compound',
                                 ),
                        ],
                       hWidth=HWIDTH,
                       )

    USESCROLLWIDGET = True
    FIXEDWIDTH = False
    FIXEDHEIGHT = False

    LABELEDITING = True

    def __init__(self, parent=None, mainWindow=None,
                 substance=None, sampleComponent=None, newSubstance=False, **kwds):
        """
        Initialise the widget
        """
        self.EDITMODE = not newSubstance
        self.WINDOWPREFIX = 'New ' if newSubstance else 'Edit '

        if newSubstance:
            obj = _blankContainer(self)
        else:
            obj = substance

        self.sampleComponent = sampleComponent
        self.substance = substance

        # initialise the widgets in the popup
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, size=(500, 100), **kwds)

        # attach callbacks to the new/fromSubstances radioButton
        if self.EDITMODE:
            self.Selectsource.setEnabled(False)
            self.Currentsubstances.setEnabled(False)
            self.Selectsource.setVisible(False)
            self.Currentsubstances.setVisible(False)
            self.name.setEnabled(True)  # False
            self.labelling.setEnabled(True)  # False
        else:
            self.Selectsource.radioButtons.buttonGroup.buttonClicked.connect(self._changeSource)
            self.Currentsubstances.pulldownList.activated.connect(self._fillInfoFromSubstance)

        self.labelling.pulldownList.activated.connect(self._labellingSpecialCases)
        self.smiles.entry.textEdited.connect(self._smilesChanged)
        self._initialiseCompoundView()

        self._firstSize = self.sizeHint()
        self._size = self.sizeHint()
        self.mainWidget.getLayout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        self._setDialogSize()

        self._moreLessFrames = []
        for item in self.findChildren(MoreLessFrame):
            item.setCallback(self._moreLessCallback)
            # assume all are initially closed
            self._moreLessFrames.append(item)

        self._baseSize = self.sizeHint()
        for item in self._moreLessFrames:
            self._baseSize -= item.sizeHint()

    def _setEnabledState(self, fromSubstances):
        if fromSubstances:
            self.Currentsubstances.setEnabled(True)
        else:
            self.Currentsubstances.setEnabled(False)
            self.labelling.setEnabled(True)

    def _changeSource(self, button):
        self._setEnabledState(True if button.get() == BUTTONSTATES[1] else False)

    def _fillInfoFromSubstance(self, index):
        selected = self.Currentsubstances.getText()
        if selected != SELECT:
            substance = self.project.getByPid('SU:' + selected)
            if substance:
                self.name.setText(str(substance.name))
                newLabel = str(substance.labelling)
                if newLabel not in self.labelling.getTexts():
                    self.labelling.pulldownList.addItem(text=newLabel)
                self.labelling.pulldownList.set(newLabel or 'None')
                self.labelling.setEnabled(True)  # False
        else:
            self.name.setText('')
            self.labelling.pulldownList.setIndex(0)
            self.labelling.setEnabled(True)

        if hasattr(self.name, '_queueCallback'):
            self.name._queueCallback()
        if hasattr(self.labelling, '_queueCallback'):
            self.labelling._queueCallback()

    def _labellingSpecialCases(self, index):
        selected = self.labelling.pulldownList.currentText()
        if selected == TYPENEW:
            self.labelling.pulldownList.setEditable(True)
        else:
            self.labelling.pulldownList.setEditable(self.LABELEDITING)

    def _populate(self):
        super()._populate()
        self.labelling.setEnabled(True)
        self.labelling.pulldownList.setEditable(self.LABELEDITING)
        # populate the compoundView on a revert
        self._smilesChanged(self.obj.smiles)

    def _applyAllChanges(self, changes):

        if self.EDITMODE:
            super()._applyAllChanges(changes)
            name = self.name.getText()
            labelling = self.labelling.getText()
            if name != self.obj.name or labelling != self.obj.labelling:
                self.obj.rename(name=name, labelling=labelling)
        else:
            # if new substance then call the new method - self.obj is container of new attributes
            name = self.name.getText()
            labelling = self.labelling.getText()
            self.obj = self.project.newSubstance(name=name, labelling=labelling)

            # only apply items that are not in the _VALIDATTRS list - defined by queueStates=True in attributes
            super()._applyAllChanges(changes)

    def _initialiseCompoundView(self):
        view = self.Compoundview.compoundView
        if self.obj:
            smiles = self.obj.smiles
            if smiles is None:
                smiles = 'H'
            else:
                smiles = smiles
        else:
            smiles = ''
        view.setSmiles(smiles)
        # NOTE:ED - initial size has been moved to resizeEvent in compoundWidget

    def _smilesChanged(self, value):
        view = self.Compoundview.compoundView
        view.setSmiles(value or '')
        # resize to the new items
        view.updateAll()
        view.scene.setSceneRect(view.scene.itemsBoundingRect())
        view.resetView()
        view.zoomLevel = 1.0

    def _moreLessCallback(self, moreLessFrame):
        """Resize the dialog to contain the opened/closed moreLessFrames
        """
        _size = QtCore.QSize(self._baseSize)
        for item in self._moreLessFrames:
            _size += item.sizeHint()

        _size.setWidth(self.width())
        self.resize(_size)
