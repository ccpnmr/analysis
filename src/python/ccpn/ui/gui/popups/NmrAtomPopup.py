"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-03-14 14:18:53 +0000 (Sun, March 14, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.util.Common import greekKey, getIsotopeListFromCode
from ccpn.core.NmrAtom import NmrAtom
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, TextEditorCompoundWidget, \
    PulldownListCompoundWidget, CheckBoxCompoundWidget
from ccpn.util import Constants as ct

MERGE = 'merge'


class NmrAtomNewPopup(AttributeEditorPopupABC):
    """
    NmrAtom attributes new popup
    """

    def _getNewNmrAtomTypes(self, nmrAtom):
        """Populate the nmrAtom pulldown
        """
        defaultName = nmrAtom.name
        atomNames = getIsotopeListFromCode(None)
        self.name.modifyTexts([defaultName]+sorted(list(set(atomNames)), key=greekKey))

    def _getNewNmrResidueTypes(self, nmrResidue):
        """Populate the nmrResidue pulldown
        """
        self.nmrResidue.modifyTexts([x.id for x in self.project.nmrResidues])
        self.nmrResidue.select(self._parentNmrResidue.id)

    def _getNmrAtomIsotopeCodes(self, nmrAtom):
        """ Add a SHORT list of possible isotopeCodes """
        priorityIsotopeCodes = ct.PriorityIsotopeCodes
        self.isotopeCode.modifyTexts(priorityIsotopeCodes)
        self._selectIsotopeCodeForName()

    def _selectIsotopeCodeForName(self, nmrAtomName=None):
        """
        :param nmrAtomName:
        :return: Select a possible option of IsotopeCode based on its name. If not in List, it is added and selected.
        """
        from ccpn.util.Common import name2IsotopeCode
        nmrAtomName = nmrAtomName or self.name.getText()
        guessedIC = name2IsotopeCode(str(nmrAtomName).upper())
        currentIsotopeCodes = self.isotopeCode.pulldownList.texts
        if not guessedIC in currentIsotopeCodes:
            self.isotopeCode.pulldownList.addItem(guessedIC)
        self.isotopeCode.select(guessedIC)

    def _nameChanged(self, value, *fgd):
        self._selectIsotopeCodeForName()

    klass = NmrAtom
    attributes = [('Name', PulldownListCompoundWidget, getattr, None, _getNewNmrAtomTypes, None, {'editable': True}),
                  ('NmrResidue', PulldownListCompoundWidget, getattr, setattr, _getNewNmrResidueTypes, None, {'editable': False},),
                  ('IsotopeCode', PulldownListCompoundWidget, getattr, setattr, _getNmrAtomIsotopeCodes, None, {'editable': True}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  # ('comment', TextEditorCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <',
                  #                                                                      'addWordWrap': True}),
                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        self._parentNmrResidue = obj
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)
        self.name.pulldownList.pulldownTextReady.connect(self._nameChanged)

    def _applyAllChanges(self, changes):
        """Apply all changes - update nmrAtom name
        """
        atomName = self.name.getText()
        nmrResidue = self.nmrResidue.getText()
        comment = self.comment.getText()
        isotopeCode =  self.isotopeCode.getText()
        isotopeCode = isotopeCode if isotopeCode in ct.DEFAULT_ISOTOPE_DICT.values() else None

        destNmrResidue = self.project.getByPid('NR:{}'.format(nmrResidue))
        if not destNmrResidue:
            raise TypeError('nmrResidue does not exist')

        if not destNmrResidue.getNmrAtom(atomName):
            destNmrResidue.newNmrAtom(name=atomName, comment=comment, isotopeCode=isotopeCode)
        else:
            raise TypeError('nmrAtom {}.{} already exists'.format(nmrResidue, atomName))

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        pass

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        pass

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass


class NmrAtomEditPopup(AttributeEditorPopupABC):
    """
    NmrAtom attributes edit existing popup
    """

    def _getNmrAtomTypes(self, nmrAtom):
        """Populate the nmrAtom pulldown
        """
        isotopeCode = self.obj.isotopeCode
        atomNames = getIsotopeListFromCode(isotopeCode)

        if self.obj.name not in atomNames:
            atomNames.insert(0, self.obj.name)

        self.name.modifyTexts(sorted(list(set(atomNames)), key=greekKey))
        if self.obj.name:
            self.name.select(self.obj.name)

    def _getNmrResidueTypes(self, nmrResidue):
        """Populate the nmrResidue pulldown
        """
        self.nmrResidue.modifyTexts([x.id for x in self.obj.project.nmrResidues])
        self.nmrResidue.select(self.obj.nmrResidue.id)

    klass = NmrAtom
    attributes = [('Pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('Name', PulldownListCompoundWidget, getattr, None, _getNmrAtomTypes, None, {'editable': True}),
                  ('NmrResidue', PulldownListCompoundWidget, getattr, setattr, _getNmrResidueTypes, None, {'editable': False}),
                  ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  # ('comment', TextEditorCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <',
                  #                                                                      'addWordWrap': True}),
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - update nmrAtom name
        """
        atomName = self.name.getText()
        nmrResidue = self.nmrResidue.getText()
        comment = self.comment.getText()

        destNmrResidue = self.project.getByPid('NR:{}'.format(nmrResidue))
        if not destNmrResidue:
            raise TypeError('nmrResidue does not exist')

        destNmrAtom = destNmrResidue.getNmrAtom(atomName)
        merge = self.mergetoExisting.isChecked()

        if destNmrAtom and destNmrAtom == self.obj:
            # same nmrAtom so skip
            self.obj.comment = comment

        elif destNmrAtom:
            # different name and/or different nmrResidue
            if not merge:
                # raise error to notify popup
                raise ValueError('Cannot re-assign NmrAtom to an existing NmrAtom of another NmrResidue without merging')
            destNmrAtom.mergeNmrAtoms(self.obj)
            destNmrAtom.comment = comment

        else:
            # assign to a new nmrAtom
            self.obj.assignTo(chainCode=destNmrResidue.nmrChain.shortName,
                              sequenceCode=destNmrResidue.sequenceCode,
                              residueType=destNmrResidue.residueType,
                              name=atomName,
                              mergeToExisting=merge)
            self.obj.comment = comment

            self.pid.setText(self.obj.pid)

    def storeWidgetState(self):
        """Store the state of the checkBoxes between popups
        """
        merge = self.mergetoExisting.isChecked()
        NmrAtomEditPopup._storedState[MERGE] = merge

    def restoreWidgetState(self):
        """Restore the state of the checkBoxes
        """
        self.mergetoExisting.set(NmrAtomEditPopup._storedState.get(MERGE, False))

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass
