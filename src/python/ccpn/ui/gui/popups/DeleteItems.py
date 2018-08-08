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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank$"
__date__ = "$Date: 9/05/2017 $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier


class DeleteItemsPopup(CcpnDialog):
    """
    Open a small popup to allow deletion of selected 'current' items
    Items is a tuple of tuples: indexed by the name of the items, containing a list of the items for deletion
    i.e. (('Peaks', peakList), ('Multiplets',multipletList))
    """

    def __init__(self, parent=None, mainWindow=None, title='Delete Items', items=None, **kw):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        row = 0
        self.noteLabel = Label(self, "Delete selected items: ", grid=(row, 0))

        self.deleteList = []
        for item in items:
            itemName, values = item

            row += 1
            # add a check box for each item
            newCheckBox = CheckBoxCompoundWidget(self,
                                                 grid=(row, 0), vAlign='top', stretch=(0, 0), hAlign='left',
                                                 orientation='right',
                                                 labelText=itemName,
                                                 checked=True if itemName in ['peaks', 'Peaks'] else False
                                                 )
            self.deleteList.append((itemName, values, newCheckBox))

        row += 1
        # add close buttons at the bottom
        self.buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(row, 1))
        self.buttonList.buttons[0].setFocus()

        self.GLSignals = GLNotifier(parent=self)

    def _refreshGLItems(self):
        # emit a signal to rebuild all peaks and multiplets
        self.GLSignals.emitEvent(triggers=[GLNotifier.GLALLPEAKS, GLNotifier.GLALLMULTIPLETS])

    def _okButton(self):
        """
        When ok button pressed: delete and exit
        """
        applyAccept = False
        undo = self.project._undo
        oldUndo = undo.numItems()

        self.project._startCommandEchoBlock('_applyChanges', quiet=True)
        try:
            for delItem in self.deleteList:
                if delItem[2].isChecked():
                    self.project.deleteObjects(*delItem[1])

            # add item here to redraw items
            undo.newItem(self._refreshGLItems, self._refreshGLItems)

            applyAccept = True
        except Exception as es:
            showWarning(str(self.windowTitle()), str(es))
        finally:
            self.project._endCommandEchoBlock()

        # redraw the items
        self._refreshGLItems()

        if applyAccept is False:
            # should only undo if something new has been added to the undo deque
            # may cause a problem as some things may be set with the same values
            # and still be added to the change list, so only undo if length has changed
            errorName = str(self.__class__.__name__)

            if oldUndo != undo.numItems():
                self.project._undo.undo()
                getLogger().debug('>>>Undo.%s._applychanges' % errorName)
            else:
                getLogger().debug('>>>Undo.%s._applychanges nothing to remove' % errorName)

        self.accept()
