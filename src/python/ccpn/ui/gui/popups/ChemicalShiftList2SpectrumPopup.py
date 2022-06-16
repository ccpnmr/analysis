#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-06-16 18:02:32 +0100 (Thu, June 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.framework.Application import getApplication, getCurrent, getProject
from ccpn.core.lib.CcpnStarIo import _simulatedSpectrumFromCSL
import ccpn.ui.gui.widgets.CompoundWidgets as cw
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Label import Label
from collections import OrderedDict as od

defaultAxesCodesMap = od([  #                   replace with the atom and axes of interest
                        ("N", "N"),
                        ("H", "H"),
                        ])

widgetFixedWidths = (150, 150)

class ChemicalShiftList2SpectrumPopup(CcpnDialogMainWidget):
    """

    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = True

    title = 'Simulate Spectrum from ChemicalShiftList (Alpha)'
    def __init__(self, parent=None, chemicalShiftList=None, title=title, **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(300, 100), minimumSize=None, **kwds)

        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()
        self.chemicalShiftList = chemicalShiftList
        self._axesCodesMap = defaultAxesCodesMap  # Ordered dict as od([("HA","H")]) see info for more

        self._createWidgets()

        # enable the buttons
        self.tipText = ''
        self.setOkButton(callback=self._okCallback, tipText =self.tipText, text='Create', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)
        self.__postInit__()
        self._okButton = self.dialogButtons.button(self.OKBUTTON)

    def _createWidgets(self):

        row = 0
        spectrumName = self.chemicalShiftList.name if self.chemicalShiftList else ''
        self.spectrumNameEntry = cw.EntryCompoundWidget(self.mainWidget,
                                                     labelText='New Spectrum Name', entryText=spectrumName,
                                                     fixedWidths=widgetFixedWidths,
                                                     grid=(row, 0))
        row += 1
        self.atomNamesEntry = cw.EntryCompoundWidget(self.mainWidget,
                                                     labelText='Atom Names', entryText=','.join(self._axesCodesMap.keys()),
                                                     fixedWidths=widgetFixedWidths,
                                                     grid=(row, 0))
        row += 1
        self.assignToSpectumCodes = cw.EntryCompoundWidget(self.mainWidget,
                                                     labelText='Assign To Axes', entryText=','.join(self._axesCodesMap.keys()),
                                                           fixedWidths=widgetFixedWidths,
                                                     grid=(row, 0))



    def _okCallback(self):
        if self.project and self.chemicalShiftList:
            bmrbCodes = self.atomNamesEntry.getText().replace(" ", "").split(',')
            assignToSpectumCodes = self.assignToSpectumCodes.getText().replace(" ", "").split(',')
            for bmrbCode, sac in zip(bmrbCodes, assignToSpectumCodes):
                self._axesCodesMap[bmrbCode] = sac
            spectrumName = self.spectrumNameEntry.getText()
            _simulatedSpectrumFromCSL(self.project, self.chemicalShiftList, self._axesCodesMap, spectrumName=spectrumName)

        self.accept()

if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    app = TestApplication()
    popup = ChemicalShiftList2SpectrumPopup()
    popup.show()
    popup.raise_()
    app.start()

