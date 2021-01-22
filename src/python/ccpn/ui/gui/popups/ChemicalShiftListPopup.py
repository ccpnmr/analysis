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
__dateModified__ = "$dateModified: 2021-01-22 18:18:26 +0000 (Fri, January 22, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# from PyQt5 import QtWidgets
# from ccpn.ui.gui.widgets.ButtonList import ButtonList
# from ccpn.ui.gui.widgets.Label import Label
# from ccpn.ui.gui.widgets.LineEdit import LineEdit
# from ccpn.ui.gui.popups.Dialog import CcpnDialog
# from ccpn.ui.gui.widgets.MessageDialog import showWarning
# from ccpn.ui.gui.widgets.ListWidget import ListWidget

from ccpn.ui.gui.popups._GroupEditorPopupABC import _GroupEditorPopupABC
from ccpn.core.ChemicalShiftList import ChemicalShiftList
from ccpn.ui.gui.widgets.PulldownListsForObjects import ChemicalShiftListPulldown


class ChemicalShiftListEditor(_GroupEditorPopupABC):
    """
    A popup to create and manage SpectrumGroups

    Used in 'New' or 'Edit' mode:
    - For creating new SpectrumGroup (editMode==False); optionally uses passed in spectra list
      i.e. NewSpectrumGroup of SideBar and Context menu of SideBar

    - For editing existing SpectrumGroup (editMode==True); requires spectrumGroup argument
      i.e. Edit of SpectrumGroup of SideBar
    or
      For selecting and editing SpectrumGroup (editMode==True)
      i.e. Menu Spectrum->Edit SpectrumGroup...

    """
    _class = ChemicalShiftList
    _classItemAttribute = 'spectra'  # Attribute in _class containing items
    _classPulldown = ChemicalShiftListPulldown

    _projectNewMethod = 'newChemicalShiftList'  # Method of Project to create new _class instance
    _projectItemAttribute = 'spectra'  # Attribute of Project containing items
    _pluralGroupName = 'Chemical Shift Lists'
    _singularGroupName = 'Chemical Shift List'

    _groupPidKey = 'CL'
    _itemPidKey = 'SP'


# class ChemicalShiftListPopup(CcpnDialog):
#     def __init__(self, parent=None, mainWindow=None, chemicalShiftList=None, **kwds):
#         """
#         Initialise the widget
#         """
#         CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit ChemicalShiftList', size=(500, 100), **kwds)
#
#         self.mainWindow = mainWindow
#         self.project = None
#         if mainWindow is not None:
#             self.application = mainWindow.application
#             self.project = mainWindow.application.project
#             self.current = mainWindow.application.current
#
#         self.chemicalShiftList = chemicalShiftList
#
#         row = 0
#         self.chemicalShiftListLabel = Label(self, "Name ", grid=(row, 0))
#         self.chemicalShiftListText = LineEdit(self, grid=(row, 1), gridSpan=(1, 1), textAlignment='left')
#
#         row += 1
#         tip = 'Drag and drop spectra to the current spectra box to link them to the ChemicalShiftList'
#         self.spectraLabel = Label(self, "Current", grid=(row, 1), hAlign='center')
#         self.spectraLabel = Label(self, "Available", grid=(row, 2), hAlign='center', tipText=tip)
#
#         row += 1
#         tipDragHere = 'Drag spectra here to link them to the ChemicalShift List.'
#         self.spectraLabel = Label(self, "Spectra", grid=(row, 0))
#         self.spectraList = ListWidget(self, grid=(row, 1), acceptDrops=True, tipText=tipDragHere)
#         self.availableSpectraList = ListWidget(self, grid=(row, 2), tipText=tip)
#
#         row += 1
#         ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(row, 2))
#
#         self._setData()
#
#     def _setData(self):
#         if self.chemicalShiftList is not None:
#             # for spectrum in self.chemicalShiftList.spectra:
#             #     item = QtWidgets.QListWidgetItem(str(spectrum.id))
#             #     self.spectraList.addItem(item)
#
#             self.chemicalShiftListText.setText(self.chemicalShiftList.name)
#             self.spectraList.setObjects(self.chemicalShiftList.spectra)
#
#         if self.project is not None:
#             # for spectrum in self.project.spectra:
#             #     item = QtWidgets.QListWidgetItem(str(spectrum.id))
#             #     self.availableSpectraList.addItem(item)
#
#             availableSpectra = [sp for sp in self.project.spectra if sp not in self.chemicalShiftList.spectra]
#             self.availableSpectraList.setObjects(availableSpectra)
#
#     def _addSpectraToCSList(self):
#         if self.chemicalShiftList is not None:
#             objs = [self.project.getByPid(text) for text in self.spectraList.getTexts()]
#             self.chemicalShiftList.spectra = objs
#
#     def _okButton(self):
#         newName = self.chemicalShiftListText.text()
#         try:
#             if self.chemicalShiftList is not None:
#                 if str(newName) != self.chemicalShiftList.name:
#                     self.chemicalShiftList.rename(newName)
#                 self._addSpectraToCSList()
#             self.accept()
#
#         except Exception as es:
#             showWarning(self.windowTitle(), str(es))
#             if self.application._isInDebugMode:
#                 raise es
#
#
# if __name__ == '__main__':
#     from ccpn.ui.gui.widgets.Application import TestApplication
#     from ccpn.ui.gui.popups.Dialog import CcpnDialog
#
#
#     app = TestApplication()
#     popup = ChemicalShiftListPopup()
#
#     popup.show()
#     popup.raise_()
#
#     app.start()
