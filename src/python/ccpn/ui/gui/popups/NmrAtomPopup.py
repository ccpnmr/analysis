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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-23 15:38:09 +0000 (Tue, March 23, 2021) $"
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
from ccpn.core.NmrAtom import NmrAtom, UnknownIsotopeCode
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, TextEditorCompoundWidget, \
    PulldownListCompoundWidget, CheckBoxCompoundWidget
from ccpn.util import Constants as ct
from functools import partial

MERGE = 'merge'
Undefined = 'Undefined'
OtherNames = '--  Other Options  --'
OtherByIC  = '-- Name Options --'

def _getNmrAtomIsotopeCodes(cls, nmrAtom):
    priorityIsotopeCodes = [Undefined] + ct.PriorityIsotopeCodes
    cls.isotopeCode.modifyTexts(priorityIsotopeCodes)
    _selectIsotopeCodeForName(cls,  isotopeCode=nmrAtom.isotopeCode)

def _selectIsotopeCodeForName(cls, nmrAtomName=None, isotopeCode=None):
    """
    :param nmrAtomName:
    :return: Select a possible option of IsotopeCode based on its name. If not in List, it is added and selected.
    """
    from ccpn.util.Common import name2IsotopeCode
    nmrAtomName = nmrAtomName or cls.name.getText()
    if not isotopeCode:
        isotopeCode = name2IsotopeCode(str(nmrAtomName).upper())
    currentIsotopeCodes = cls.isotopeCode.pulldownList.texts
    if isotopeCode is None or isotopeCode == UnknownIsotopeCode:
        isotopeCode = Undefined
    if not isotopeCode in currentIsotopeCodes:
        cls.isotopeCode.pulldownList.insertItem(0, isotopeCode)
    cls.isotopeCode.select(isotopeCode)

def _nameChanged(cls, value):
    _selectIsotopeCodeForName(cls)

def _getNmrAtomName(cls, nmrAtom, nmrResidue=None, isotopeCode=None):
    """
    called from edit and new NnmAtom popup.
    :param cls: the popup obj.
    :param nmrAtom: the NmrAtom Obj or its dummy
    :param nmrResidue: the NmrResidue Obj or its dummy
    :return:
    """
    from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import PROTEIN_ATOM_NAMES, ALL_ATOMS_SORTED
    from ccpn.core.lib.AssignmentLib import NEF_ATOM_NAMES

    nmrAtomName = nmrAtom.name # compoundWidget for setting the NmrAtom name
    nameWidget = cls.name
    isotopeCode = isotopeCode or cls.isotopeCode
    atomNameOptions = []
    ## if a residue type is specified: Append all other options for that type only!
    if not nmrResidue:
        nmrResidue = cls._getParentNmrResidue(nmrAtom)
    atomNameOptionsByResType = PROTEIN_ATOM_NAMES.get(nmrResidue.residueType, [])
    ## if residue type is not specify: Append all other NEF options
    if atomNameOptionsByResType:
        atomNameOptions += atomNameOptionsByResType
    else:
        atomNameOptions += getIsotopeListFromCode(None) # all options

    if isotopeCode in NEF_ATOM_NAMES:
        atomsNameOptionsByIC = getIsotopeListFromCode(isotopeCode or nmrAtom.isotopeCode)
        atomNotOfSameIsotopeCode = [x for x in atomNameOptions if x not in atomsNameOptionsByIC]
        atomOfSameIsotopeCode = [x for x in atomNameOptions if x in atomsNameOptionsByIC]
        atomNameOptions = [nmrAtomName]+\
                          [OtherByIC]+\
                          atomOfSameIsotopeCode+\
                          [OtherNames]+\
                          atomNotOfSameIsotopeCode
        nameSeparators = [OtherNames, OtherByIC]
    else:
        atomNameOptions = [nmrAtomName]+\
                          [OtherNames]+\
                          atomNameOptions
        nameSeparators = [OtherNames]

    nameWidget.modifyTexts(atomNameOptions)

    nameWidget.pulldownList.disableLabelsOnPullDown(nameSeparators)

def _isotopeCodeCallback(cls, value):
    from ccpn.core.lib.AssignmentLib import NEF_ATOM_NAMES
    _isotopeCode = value if value in NEF_ATOM_NAMES else None
    _getNmrAtomName(cls, cls.obj, isotopeCode=value)

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

    def _getNewNmrResidueTypes(self, nmrAtom):
        """Populate the nmrResidue pulldown
        """
        self.nmrResidue.modifyTexts([x.id for x in self.project.nmrResidues])
        self.nmrResidue.select(self._parentNmrResidue.id)
        _getNmrAtomName(self, nmrAtom)

    def _nmrResidueCallback(self, value):
        nmrResidue = self.project.getByPid('NR:{}'.format(value))
        _getNmrAtomName(self, self.obj, nmrResidue=nmrResidue)


    klass = NmrAtom
    attributes = [('Name', PulldownListCompoundWidget, getattr, None, _getNmrAtomName, None, {'editable': True}),
                  ('NmrResidue', PulldownListCompoundWidget, getattr, setattr, _getNewNmrResidueTypes, _nmrResidueCallback, {'editable': False},),
                  ('IsotopeCode', PulldownListCompoundWidget, getattr, setattr, _getNmrAtomIsotopeCodes, _isotopeCodeCallback, {'editable': True}),
                  ('Comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  # ('comment', TextEditorCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <',
                  #                                                                      'addWordWrap': True}),
                  ]

    def __init__(self, parent=None, mainWindow=None, obj=None, **kwds):
        self._parentNmrResidue = obj
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)
        # self.name.pulldownList.pulldownTextReady.connect(partial(_nameChanged, self)) # don't automatically change anything.

    def _getParentNmrResidue(self, nmrAtom):
        return self._parentNmrResidue

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

    def _getParentNmrResidue(self, nmrAtom):
        parentNmrResidue = nmrAtom.nmrResidue
        # nmrResidueName = self.nmrResidue.getText()
        # _parentNmrResidue = self.project.getByPid('NR:{}'.format(nmrResidueName))
        return parentNmrResidue

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

    def _getNmrResidueTypes(self, nmrAtom):
        """Populate the nmrResidue pulldown
        """
        self.nmrResidue.modifyTexts([x.id for x in self.obj.project.nmrResidues])
        self.nmrResidue.select(self.obj.nmrResidue.id)
        _getNmrAtomName(self, nmrAtom)

    def _nmrResidueCallback(self, value):
        nmrResidue = self.project.getByPid('NR:{}'.format(value))
        _getNmrAtomName(self, self.obj, nmrResidue=nmrResidue)

    klass = NmrAtom
    attributes = [('Pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('Name', PulldownListCompoundWidget, getattr, None, _getNmrAtomName, None, {'editable': True}),
                  ('NmrResidue', PulldownListCompoundWidget, getattr, setattr, _getNmrResidueTypes, _nmrResidueCallback, {'editable': False}),
                  ('IsotopeCode', PulldownListCompoundWidget, getattr, setattr, _getNmrAtomIsotopeCodes, _isotopeCodeCallback, {'editable': True}),
                  ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {'checkable':True}),
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
        isotopeCode = self.isotopeCode.getText()
        isotopeCode = isotopeCode if isotopeCode in ct.DEFAULT_ISOTOPE_DICT.values() else None

        destNmrResidue = self.project.getByPid('NR:{}'.format(nmrResidue))
        if not destNmrResidue:
            raise TypeError('nmrResidue does not exist')

        destNmrAtom = destNmrResidue.getNmrAtom(atomName)
        merge = self.mergetoExisting.isChecked()

        if destNmrAtom and destNmrAtom == self.obj:
            # same nmrAtom so skip
            self.obj.comment = comment
            self.obj.isotopeCode = isotopeCode

        elif destNmrAtom:
            # different name and/or different nmrResidue
            if not merge:
                # raise error to notify popup
                raise ValueError('Cannot re-assign NmrAtom to an existing NmrAtom of another NmrResidue without merging')
            destNmrAtom.mergeNmrAtoms(self.obj)
            destNmrAtom.comment += ' - '+comment
            destNmrAtom.isotopeCode = isotopeCode

        else:
            # assign to a new nmrAtom
            self.obj.assignTo(chainCode=destNmrResidue.nmrChain.shortName,
                              sequenceCode=destNmrResidue.sequenceCode,
                              residueType=destNmrResidue.residueType,
                              name=atomName,
                              mergeToExisting=merge)
            self.obj.comment = comment
            self.obj.isotopeCode = isotopeCode
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
