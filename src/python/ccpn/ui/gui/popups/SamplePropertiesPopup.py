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
__dateModified__ = "$dateModified: 2020-07-09 16:49:59 +0100 (Thu, July 09, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from ccpn.ui.gui.popups.AttributeEditorPopupABC import ComplexAttributeEditorPopupABC, VList, HList
from ccpn.core.Sample import Sample
from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, ScientificSpinBoxCompoundWidget, \
    SpinBoxCompoundWidget, PulldownListCompoundWidget
from ccpn.util.Constants import AMOUNT_UNITS, amountUnits


class SamplePropertiesPopup(ComplexAttributeEditorPopupABC):
    """
    Sample attributes editor popup
    """

    def _get(self, attr, default):
        """change the value from the sample object into an index for the radioButton
        """
        value = getattr(self, attr, default)
        return amountUnits.index(value) if value and value in amountUnits else 0

    def _set(self, attr, index):
        """change the index from the radioButtons into the string for the sample object
        """
        value = amountUnits[index if index and 0 <= index < len(amountUnits) else 0]
        setattr(self, attr, value)

    def _getUnits(self, obj, unitType=None, unitList=None):
        """Populate the units pulldowns
        """
        units = [val for val in unitList]
        value = getattr(self.obj, unitType)
        newUnit = str(value) if value else ''
        if newUnit and newUnit not in units:
            units.append(newUnit)
        getattr(self, unitType).modifyTexts(units)
        getattr(self, unitType).select(newUnit or '')

    klass = Sample  # The class whose properties are edited/displayed
    HWIDTH = 140
    SHORTWIDTH = 140
    attributes = VList([('name', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Enter name <'}),
                        ('comment', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': '> Optional <'}),
                        # ('amountUnit', RadioButtonsCompoundWidget, _get, _set, None, None, {'texts'      : AMOUNT_UNITS,
                        #                                                                     'selectedInd': 1,
                        #                                                                     'direction'  : 'h'}),
                        HList([('amount', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                               ('amountUnits', PulldownListCompoundWidget,
                                getattr, setattr, partial(_getUnits, unitType='amountUnits', unitList=('',) + AMOUNT_UNITS), None,
                                {'editable': False}), ],
                              hWidth=SHORTWIDTH,
                              ),
                        HList([('ionicStrength', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0}),
                               ('ionicStrengthUnits', PulldownListCompoundWidget,
                                getattr, setattr, partial(_getUnits, unitType='ionicStrengthUnits', unitList=('',) + AMOUNT_UNITS), None,
                                {'editable': False}), ],
                              hWidth=SHORTWIDTH,
                              ),
                        ('pH', ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'max': 14, 'decimals': 2}),
                        ('batchIdentifier', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                        ('plateIdentifier', EntryCompoundWidget, getattr, setattr, None, None, {'backgroundText': ''}),
                        ('rowNumber', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'step': 1}),
                        ('columnNumber', SpinBoxCompoundWidget, getattr, setattr, None, None, {'min': 0, 'step': 1}),
                        ],
                       hWidth=HWIDTH,
                       )

    hWidth = 120
    FIXEDWIDTH = True
    FIXEDHEIGHT = True
    ENABLEREVERT = True

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 sample=None, **kwds):
        obj = sample
        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)
