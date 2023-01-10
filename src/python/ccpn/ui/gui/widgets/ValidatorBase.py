"""
Base class for Widget validation; e.g. as in LineEdit, using the Qvalidator class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-01-10 14:30:46 +0000 (Tue, January 10, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-12-06 10:28:41 +0000 (Tue, December 6, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt5 import QtWidgets, QtGui


class WidgetValidator(QtGui.QValidator):
    """A validator for a widget
    """

    WIDGET_VALUE_ATTRIBUTE = None   # optional widget attribute to obtain its value
    WIDGET_VALUE_FUNCTION = None    # optional widget function to obtain its value

    def __init__(self, widget=None, callback=None):
        QtGui.QValidator.__init__(self, parent=widget)
        self._widget = widget
        self._callback = callback
        self.isValid = True  # The result of the validator

    def validate(self, p_str, p_int) -> tuple:
        """This routine is called by PyQT when editing the widget
        """
        self.isValid = self._callback(p_str.strip())
        if self.isValid:
            state = QtGui.QValidator.Acceptable
        else:
            state = QtGui.QValidator.Intermediate

        return state, p_str, p_int

    def doValidate(self) -> bool:
        """Get the value of widget and call validator callback
        """
        if self.WIDGET_VALUE_ATTRIBUTE:
            value = getattr(self._widget, self.WIDGET_VALUE_ATTRIBUTE)
        elif self.WIDGET_VALUE_FUNCTION:
            value = self.WIDGET_VALUE_FUNCTION(self._widget)
        else:
            raise RuntimeError(f'Unable to get widget value')

        self.isValid = self._callback(value)
        return self.isValid


class ValidatorBase(object):
    """This class implements the methods to validate widgets such as LineEdit
    It requires initialisation with a function:

      def validatorCallback(value) -> bool:

    which is called upon changes to the value of the Widget. It should return True/False.
    """
    def __init__(self, widget, validatorCallback):
        if validatorCallback is None:
            raise ValueError(f'validatorCallback argument cannot be None')

        self._validator = WidgetValidator(widget=widget, callback=validatorCallback)
        widget.setValidator(self._validator)

    @property
    def isValid(self)-> bool:
        """Validity of the widget; maintained by validator instance
        """
        return self._validator.isValid

    @isValid.setter
    def isValid(self, value):
        self._validator.isValid = value

    def validate(self) -> bool:
        """Validate self using the validator instance
        :return True or False
        """
        self._validator.doValidate()
        return self.isValid
