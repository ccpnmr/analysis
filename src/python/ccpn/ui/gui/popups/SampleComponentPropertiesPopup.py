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
__dateModified__ = "$dateModified: 2020-06-08 13:33:52 +0100 (Mon, June 08, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Constants import concentrationUnits
from ccpn.ui.gui.popups.AttributeEditorPopupABC import ComplexAttributeEditorPopupABC, VList, _blankContainer
from ccpn.core.SampleComponent import SampleComponent
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, ScientificSpinBoxCompoundWidget, \
    RadioButtonsCompoundWidget, PulldownListCompoundWidget


SELECT = '> Select <'
TYPECOMPONENT = [SELECT, 'Compound', 'Solvent', 'Buffer', 'Target', 'Inhibitor ', 'Other']
C_COMPONENT_UNIT = concentrationUnits
TYPENEW = 'Type_New'
LABELLING = ['None', TYPENEW, '15N', '15N,13C', '15N,13C,2H', 'ILV', 'ILVA', 'ILVAT', 'SAIL', '1,3-13C- and 2-13C-Glycerol']
BUTTONSTATES = ['New', 'From Substances']
WIDTH = 150


class SampleComponentPopup(ComplexAttributeEditorPopupABC):
    """
    SampleComponent attributes editor popup
    """

    LABELEDITING = True

    def _get(self, attr, default):
        """change the value from the sample object into an index for the radioButton
        """
        value = getattr(self, attr, default)
        return TYPECOMPONENT.index(value) if value and value in TYPECOMPONENT else 0

    def _set(self, attr, index):
        """change the index from the radioButtons into the string for the sample object
        """
        value = TYPECOMPONENT[index if index and 0 <= index < len(TYPECOMPONENT) else 0]
        setattr(self, attr, value)

    def _getRoleTypes(self, sampleComponent):
        """Populate the role pulldown
        """
        self.role.modifyTexts(TYPECOMPONENT)
        self.role.select(self.obj.role)

    def _getConcentrationUnits(self, sampleComponent):
        """Populate the concentrationUnit pulldown
        """
        self.concentrationUnit.modifyTexts(C_COMPONENT_UNIT)
        self.concentrationUnit.select(self.obj.role)

    def _getLabelling(self, sampleComponent):
        """Populate the labelling pulldown
        """
        labels = LABELLING.copy()
        newLabel = str(self.obj.labelling)
        if newLabel not in labels:
            labels.append(newLabel)
        self.labelling.modifyTexts(labels)
        self.labelling.select(newLabel or 'None')

    def _getCurrentSubstances(self, sampleComponent):
        """Populate the current substances pulldown
        """
        substancePulldownData = [SELECT]
        for substance in self.project.substances:
            substancePulldownData.append(str(substance.id))
        self.Currentsubstances.pulldownList.setData(substancePulldownData)

    klass = SampleComponent  # The class whose properties are edited/displayed
    HWIDTH = 150
    attributes = VList([VList([('Select source', RadioButtonsCompoundWidget, None, None, None, None, {'texts'      : BUTTONSTATES,
                                                                                                      'selectedInd': 1,
                                                                                                      'direction'  : 'h',
                                                                                                      'hAlign'     : 'l'}),
                               ('Current substances', PulldownListCompoundWidget, None, None, _getCurrentSubstances, None, {'editable': False}),
                               ],
                              queueStates=False,
                              hWidth=HWIDTH,
                              ),
                        ('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                        ('labelling', PulldownListCompoundWidget, getattr, setattr, _getLabelling, None, {'editable': True}),
                        ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                        ('role', PulldownListCompoundWidget, getattr, setattr, _getRoleTypes, None, {'editable': False}),
                        ('concentrationUnit', PulldownListCompoundWidget, getattr, setattr, _getConcentrationUnits, None, {'editable': False}),
                        ('concentration', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                        ],
                       hWidth=HWIDTH,
                       )

    FIXEDWIDTH = True
    FIXEDHEIGHT = True
    ENABLEREVERT = True

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 sample=None, sampleComponent=None, newSampleComponent=False, **kwds):
        """
        Initialise the widget
        """
        self.EDITMODE = not newSampleComponent
        self.WINDOWPREFIX = 'New ' if newSampleComponent else 'Edit '

        if sample is None and sampleComponent is not None:
            sample = sampleComponent.sample
        self.sample = sample
        self.sampleComponent = sampleComponent

        if newSampleComponent:
            obj = _blankContainer(self)
        else:
            obj = sampleComponent

        # initialise the widgets in the popup
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)

        # attach callbacks to the new/fromSubstances radioButton
        if self.EDITMODE:
            self.Selectsource.setEnabled(False)
            self.Currentsubstances.setEnabled(False)
            self.Selectsource.setVisible(False)
            self.Currentsubstances.setVisible(False)
            self.name.setEnabled(False)
            self.labelling.setEnabled(False)
        else:
            self.Selectsource.radioButtons.buttonGroup.buttonClicked.connect(self._changeSource)
            self.Currentsubstances.pulldownList.activated.connect(self._fillInfoFromSubstance)

        self.labelling.pulldownList.activated.connect(self._labellingSpecialCases)

        self._firstSize = self.sizeHint()
        self._size = self.sizeHint()
        self._setDialogSize()

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
                self.labelling.setEnabled(self.LABELEDITING)
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
        if not self.EDITMODE:
            self.labelling.setEnabled(True)
            self.labelling.pulldownList.setEditable(self.LABELEDITING)

    def _applyAllChanges(self, changes):
        if self.EDITMODE:
            super()._applyAllChanges(changes)

        if not self.EDITMODE:
            # if new sampleComponent then call the new method - self.obj is container of new attributes
            super()._applyAllChanges(changes)

            for item in list(self.obj.keys()):
                # remove items that are not required in newSampleComponent parameters
                if item not in self._VALIDATTRS:
                    del self.obj[item]
            self.sample.newSampleComponent(**self.obj)
