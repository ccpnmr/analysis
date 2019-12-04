"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ConcentrationsWidget import ConcentrationWidget
from ccpn.util.Common import isIterable

# import re
# from ccpn.core.lib.AssignmentLib import CCP_CODES_SORTED, getNmrResiduePrediction
# from ccpn.ui.gui.widgets.CompoundWidgets import EntryCompoundWidget, PulldownListCompoundWidget
# from ccpn.ui.gui.widgets.PulldownListsForObjects import NmrChainPulldown
# from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
# from ccpn.util.OrderedSet import OrderedSet
# from ccpn.core.NmrResidue import NmrResidue
from ccpn.core.lib.ContextManagers import undoBlock, undoBlockWithoutSideBar
#
# class ConcentrationUnitsKlass():
#     pass


from ccpn.ui.gui.popups.AttributeEditorPopupABC import AttributeEditorPopupABC
from ccpn.ui.gui.widgets.CompoundWidgets import RadioButtonsCompoundWidget, \
    ScientificSpinBoxCompoundWidget, EntryCompoundWidget
from ccpn.util.Constants import concentrationUnits
from ccpn.util.AttrDict import AttrDict


class _ConcentrationUnitsObject():
    """Dummy class to hold a className for the attributeEditorPopup
    """
    className = None

    def __init__(self, name='empty'):
        self.className = name


class ConcentrationUnitsPopup2(AttributeEditorPopupABC):
    EDITMODE = True
    WINDOWPREFIX = 'Setup '

    # an object just to get the classname
    klass = _ConcentrationUnitsObject('ConcentrationUnits')

    def __init__(self, parent=None, mainWindow=None, obj=None,
                 names=[], values=None, unit=None, **kwds):
        self.EDITMODE = True

        # set up the widget klass and attributes here
        # dummy object to hold the concentrations
        obj = _ConcentrationUnitsObject()
        obj.molType = concentrationUnits.index(unit)        #{'molType':0}

        # add the first attribute for the molType
        self.attributes = [('molType', RadioButtonsCompoundWidget, getattr, setattr, None, None, {'texts': concentrationUnits}), ]

        # add attributes for each of the spectra
        for name, value in zip(names, values):
            self.attributes.append((name, ScientificSpinBoxCompoundWidget, getattr, setattr, None, None, {}))
            setattr(obj, name, value)        #obj[name] = value

        super().__init__(parent=parent, mainWindow=mainWindow, obj=obj, **kwds)


class ConcentrationUnitsPopup(CcpnDialogMainWidget):

    def __init__(self, parent=None, mainWindow=None,
                 names=[], values=None, unit=None,
                 title='Setup Concentrations', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self._parent = parent

        if not parent:
            raise TypeError('Error: ConcentrationUnitsPopup - parent not defined')

        # check that the parent methods are defined
        _methodlist = ('_addConcentrationsFromSpectra', '_kDunit', 'bindingPlot', 'fittingPlot')
        for method in _methodlist:
            if not hasattr(self._parent, method):
                raise TypeError('Error: ConcentrationUnitsPopup - parent does not contain %s' % str(method))

        self._names = names
        self._values = values
        self._unit = unit
        self.concentrationWidget = ConcentrationWidget(self.mainWidget, mainWindow=mainWindow,
                                                       names=names, grid=(0, 0))

        # enable the buttons
        self.setOkButton(callback=self._okClicked)
        self.setApplyButton(callback=self._applyClicked)
        self.setCancelButton(callback=self._cancelClicked)
        self.setRevertButton(callback=self._revertClicked)
        self.setDefaultButton(CcpnDialogMainWidget.CANCELBUTTON)
        self.__postInit__()

    def __postInit__(self):
        """post initialise functions - setting up buttons and populating the widgets
        """
        super().__postInit__()
        self._populate()

    def _populate(self):
        if self._values and isIterable(self._values):
            self.concentrationWidget.setValues(self._values)
        self.concentrationWidget.setUnit(self._unit)

    def _okClicked(self):
        self._applyClicked()
        self.accept()

    def _applyClicked(self):
        # get the list of selected spectra
        spectra = self._parent.spectraSelectionWidget.getSelections()

        # get the current values from the concentration widget spinboxes
        vs, u = self.concentrationWidget.getValues(), self.concentrationWidget.getUnit()

        # apply to the spectra
        self._parent._addConcentrationsFromSpectra(spectra, vs, u)
        self._parent._kDunit = u
        self._parent.bindingPlot.setLabel('bottom', self._kDunit)
        self._parent.fittingPlot.setLabel('bottom', self._kDunit)

    def _cancelClicked(self):
        self.reject()

    def _revertClicked(self):
        self._populate()
        self._applyClicked()
