"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger


class DataSetPopup(CcpnDialog):
    def __init__(self, parent=None, mainWindow=None, dataSet=None, title='DataSet', **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.dataSet = dataSet
        self.dataSetLabel = Label(self, "DataSet Name ", grid=(0, 0))
        self.dataSetText = LineEdit(self, dataSet.title, grid=(0, 1))
        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

    def _setDataSetName(self):
        newName = self.dataSetText.text()
        self.accept()

        try:
            if str(newName) != self.dataSet.title:
                self.dataSet.title = newName
            self.accept()
        except Exception as es:
            showWarning(self.windowTitle(), str(es))

    def _repopulate(self):
        self.dataSetText.setText(self.dataSet.title)

    def _applyChanges(self):
        """
        The apply button has been clicked
        Define an undo block for setting the properties of the object
        If there is an error setting any values then generate an error message
          If anything has been added to the undo queue then remove it with application.undo()
          repopulate the popup widgets
        """
        # ejb - major refactoring

        applyAccept = False
        oldUndo = self.project._undo.numItems()

        from ccpn.core.lib.ContextManagers import undoBlockManager

        with undoBlockManager():
            try:
                newName = self.dataSetText.text()
                if str(newName) != self.dataSet.title:
                    self.dataSet.title = newName

                applyAccept = True
            except Exception as es:
                showWarning(str(self.windowTitle()), str(es))

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)
            if oldUndo != self.project._undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

            # repopulate popup
            self._repopulate()
            return False
        else:
            return True

    def _okButton(self):
        if self._applyChanges() is True:
            self.accept()
