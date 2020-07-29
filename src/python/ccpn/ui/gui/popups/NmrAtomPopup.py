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
__dateModified__ = "$dateModified: 2020-07-29 15:42:53 +0100 (Wed, July 29, 2020) $"
__version__ = "$Revision: 3.0.1 $"
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
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget, CheckBoxCompoundWidget


class NmrAtomPopup(AttributeEditorPopupABC):
    """
    NmrAtom attributes editor popup
    """

    def _getNmrAtomTypes(self, nmrAtom):
        """Populate the nmrAtom pulldown
        """
        isotopeCode = self.obj.isotopeCode
        atomNames = getIsotopeListFromCode(isotopeCode)

        if self.obj.name not in atomNames:
            atomNames.insert(0, self.obj.name)

        self.nmrAtomname.modifyTexts(sorted(list(set(atomNames)), key=greekKey))
        if self.obj.name:
            self.nmrAtomname.select(self.obj.name)

    def _getNmrResidueTypes(self, nmrResidue):
        """Populate the nmrResidue pulldown
        """
        self.nmrResidue.modifyTexts([x.id for x in self.obj.project.nmrResidues])
        self.nmrResidue.select(self.obj.nmrResidue.id)

    klass = NmrAtom
    attributes = [('pid', EntryCompoundWidget, getattr, None, None, None, {}),
                  ('nmrAtom name', PulldownListCompoundWidget, getattr, None, _getNmrAtomTypes, None, {'editable': True}),
                  ('nmrResidue', PulldownListCompoundWidget, getattr, setattr, _getNmrResidueTypes, None, {}),
                  ('Merge to Existing', CheckBoxCompoundWidget, None, None, None, None, {}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ]

    hWidth = 120

    def _applyAllChanges(self, changes):
        """Apply all changes - update nmrAtom name
        """
        atomName = self.nmrAtomname.getText()
        nmrResidue = self.nmrResidue.getText()

        destNmrResidue = self.project.getByPid('NR:{}'.format(nmrResidue))
        if not destNmrResidue:
            raise TypeError('nmrResidue does not exist')

        destNmrAtom = destNmrResidue.getNmrAtom(atomName)
        merge = self.MergetoExisting.isChecked()

        if destNmrAtom and destNmrAtom == self.obj:
            # same nmrAtom so skip
            pass
        elif destNmrAtom:
            # different name and/or different nmrResidue
            if not merge:
                # raise error to notify popup
                raise ValueError('Cannot re-assign NmrAtom to an existing NmrAtom of another NmrResidue without merging')
            destNmrAtom.mergeNmrAtoms(self.obj)

        else:
            # assign to a new nmrAtom
            self.obj.assignTo(chainCode=destNmrResidue.nmrChain.shortName,
                              sequenceCode=destNmrResidue.sequenceCode,
                              residueType=destNmrResidue.residueType,
                              name=atomName,
                              mergeToExisting=merge)

            self.pid.setText(self.obj.pid)

    def _setValue(self, attr, setFunction, value):
        """Not needed here - subclass so does no operation
        """
        pass
