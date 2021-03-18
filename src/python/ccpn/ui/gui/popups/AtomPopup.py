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
__dateModified__ = "$dateModified: 2021-03-18 15:11:52 +0000 (Thu, March 18, 2021) $"
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
from ccpn.util.Common import greekKey, getIsotopeListFromCode, makeIterableList
from ccpn.core.Atom import Atom
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, TextEditorCompoundWidget, \
    PulldownListCompoundWidget, CheckBoxCompoundWidget
from ccpn.util import Constants as ct
from functools import partial

MERGE = 'merge'

_NameSeparator = '-- NEF Atoms --'

def _setAtomNames(cls, atom, residue = None):
    from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES, ALL_ATOMS_SORTED
    from ccpn.core.lib.AssignmentLib import NEF_ATOM_NAMES
    compoundWidget = cls.name
    pulldown = compoundWidget.pulldownList
    atomsNameOptions = []
    if not residue:
        residue = cls._getParentResidue()
        residueAtomNames = residue._getChemAtomNames()
        NEF_atomNames = makeIterableList(NEF_ATOM_NAMES.values())
        atomsNameOptions = residueAtomNames + [_NameSeparator] + [x for x in NEF_atomNames if x not in residueAtomNames]

    compoundWidget.modifyTexts(atomsNameOptions)

    separatorItemIndex = pulldown.getItemIndex(_NameSeparator) #this bit could be done at higher level. We need a Separator Object.
    separatorItem = pulldown.model().item(separatorItemIndex)
    if separatorItem:
        separatorItem.setEnabled(False)


def _setResidue(cls, atom):
    parentResidue = cls._getParentResidue()
    if parentResidue:
        cls.residue.modifyTexts([parentResidue.id])
        cls.residue.select(parentResidue.id)
    else:
        cls.residue.modifyTexts([])




class AtomNewPopup(AttributeEditorPopupABC):
    """
    Atom attributes new popup
    """

    def _setAtomName(self, atom):
        self.name.modifyTexts([self.obj.name])

    klass = Atom
    attributes = [('Name', PulldownListCompoundWidget, getattr, None, _setAtomName, None, {'editable': False}),
                  ('Residue', PulldownListCompoundWidget, getattr, None, _setResidue, None, {'editable': False},),
                  # ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),

                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        self._parentResidue = obj
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)
        self.residue.pulldownList.setEnabled(False)

    def _getParentResidue(self):
        return self._parentResidue

    def _applyAllChanges(self, changes):
        """Apply all changes - update atom name
        """
        atomName = self.name.getText()
        residue = self.residue.getText()
        residue = self.project.getByPid('MR:{}'.format(residue))
        if not residue:
            raise TypeError('Residue does not exist')

        if not residue.getAtom(atomName):
            residue.newAtom(name=atomName,)# comment=comment)
        else:
            raise TypeError('Atom {}.{} already exists'.format(residue, atomName))

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


class AtomEditPopup(AttributeEditorPopupABC):
    """
    Atom attributes edit existing popup
    """

    def _getParentResidue(self):
        if self.obj:
            parentResidue = self.obj.residue
            return parentResidue

    def _setAtomName(self, atom):
        self.name.modifyTexts([self.obj.name])

    klass = Atom
    attributes = [('Pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('Name', PulldownListCompoundWidget, getattr, None, _setAtomName, None, {'editable': False}),
                  ('Residue', PulldownListCompoundWidget, getattr, None, _setResidue, None, {'editable': False}),
                  # ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {}),
                  # ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    def _applyAllChanges(self, changes):
        """Apply all changes - update Atom name
        """

        pass


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
