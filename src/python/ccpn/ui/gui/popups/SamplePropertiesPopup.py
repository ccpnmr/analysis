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
__dateModified__ = "$dateModified: 2020-06-02 09:52:53 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.core.Sample import Sample
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, ScientificSpinBoxCompoundWidget, \
    RadioButtonsCompoundWidget, SpinBoxCompoundWidget


OTHER_UNIT = ['µ', 'm', 'n', 'p']
CONCENTRATION_UNIT = ['µM', 'mM', 'nM', 'pM']
VOLUME_UNIT = ['µL', 'mL', 'nL', 'pL']
MASS_UNIT = ['µg', 'kg', 'g', 'mg', 'ng', 'pg']
SAMPLE_STATES = ['Liquid', 'Solid', 'Ordered', 'Powder', 'Crystal', 'Other']
AMOUNT_UNIT = ['L', 'g', 'mole']


class SamplePropertiesPopup(AttributeEditorPopupABC):
    """
    Sample attributes editor popup
    """

    def _get(self, attr, default):
        """change the value from the sample object into an index for the radioButton
        """
        value = getattr(self, attr, default)
        return AMOUNT_UNIT.index(value) if value and value in AMOUNT_UNIT else 0

    def _set(self, attr, index):
        """change the index from the radioButtons into the string for the sample object
        """
        value = AMOUNT_UNIT[index if index and 0 <= index < len(AMOUNT_UNIT) else 0]
        setattr(self, attr, value)

    klass = Sample  # The class whose properties are edited/displayed
    attributes = [('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                  ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                  ('amountUnit', RadioButtonsCompoundWidget, _get, _set, None, None, {'texts'      : AMOUNT_UNIT,
                                                                                      'selectedInd': 1,
                                                                                      'direction'  : 'h'}),
                  ('amount', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                  ('pH', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'max': 14, 'decimals': 2}),
                  ('ionicStrength', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                  ('batchIdentifier', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                  ('plateIdentifier', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                  ('rowNumber', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'step': 1}),
                  ('columnNumber', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'step': 1}),
                  ]

    hWidth = 120
    FIXEDWIDTH = True
    FIXEDHEIGHT = True
    ENABLEREVERT = True

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 sample=None, **kwds):
        obj = sample
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)
