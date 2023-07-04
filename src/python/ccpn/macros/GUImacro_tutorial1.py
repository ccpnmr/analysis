
import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.PulldownListsForObjects import PeakListPulldown, ChemicalShiftListPulldown, ChainPulldown
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets import CheckBox
from ccpn.ui.gui.widgets import Entry
from ccpn.ui.gui.widgets.HLine import LabeledHLine

class GUIMacroTutorial1(CcpnDialogMainWidget):
    """
    Basic setup principals of GUI based macros
    """
    FIXEDWIDTH = True
    FIXEDHEIGHT = False

    _GREY = '#888888'

    title = 'GUIMacroTutorial1'

    def __init__(self, parent=None, mainWindow=None, title=title,  **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title,
                         size=(500, 10), minimumSize=None, **kwds)

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project

        else:
            self.mainWindow = None
            self.application = None
            self.current = None
            self.project = None

        self._createWidgets()

        # enable the buttons

        self.setOkButton(callback=self._okCallback, tipText ='Okay', text='OK', enabled=True)
        self.setCloseButton(callback=self.reject, tipText='Close')
        self.setDefaultButton(CcpnDialogMainWidget.CLOSEBUTTON)

        # initialise the buttons and dialog size
        self._postInit()

    def _getPathFromDialog(self):
        """Select a new path from using a dialog
        """
        _path = self.project.application.dataPath
        dialog = ProjectFileDialog(parent=self.mainWindow, directory=str(_path))
        dialog._show()

        if (path := dialog.selectedFile()) is not None:
            self.pathData.setText(str(path))
            self._loadRunData()

    def _createWidgets(self):
        """Make the widgets
        """

        Label(parent=self.mainWidget, text="A Text Label", grid=(0, 0), textColour='Blue')

        self.checkBox2 = CheckBox.CheckBox(self.mainWidget, grid=(1, 1),  checked=True)


        self.EntryBox = Entry.Entry(self.mainWidget, grid=(2, 0), editable=True, text="Input", width=400)

        self.pathData = PathEdit(self.mainWidget, grid=(3, 0), vAlign='t', editable=False)
        self.pathData.setMinimumWidth(400)
        _b = Button(self.mainWidget, grid=(3, 1), callback=self._getPathFromDialog,
                    icon='icons/directory', hPolicy='fixed')





        # # This creates a 4*3 grid of elements
        # Label(parent=self.mainWidget, text="I'm a label at (0,0)", grid=(0, 0), textColour='Blue')
        # Label(parent=self.mainWidget, text="I'm a label at (1,2)", grid=(1, 2), textColour='Red')
        # Label(parent=self.mainWidget, text="I'm a label at (2,1)", grid=(2, 1), textColour='Green')
        # Label(parent=self.mainWidget, text="I'm a label at (3,2)", grid=(3, 2), textColour='Orange')



        #
        # # The parent of these Labels is the mainWidget
        # Label(parent=self.mainWidget, text="mainWidget (0,0)", grid=(0, 0), textColour='Blue')
        # Label(parent=self.mainWidget, text="mainWidget (0,1)", grid=(0, 1), textColour='Blue')
        # Label(parent=self.mainWidget, text="mainWidget (0,2)", grid=(0, 2), textColour='Blue')
        # Label(parent=self.mainWidget, text="mainWidget (1,0)", grid=(1, 0), textColour='Blue')
        #
        # # Define the Frame (myFrame). This frame starts at (1,1) and spans 1 row and 2 columns.
        # myFrame = Frame(self.mainWidget, grid=(1, 1), gridSpan=(1, 2), setLayout=True)
        #
        # # Place the elements in a grid inside the Frame (myFrame)
        # Label(parent=myFrame, text="myFrame (0,0)", grid=(0, 0), textColour='Red')
        # Label(parent=myFrame, text="myFrame (0,1)", grid=(0, 1), textColour='Red')
        # Label(parent=myFrame, text="myFrame (0,2)", grid=(0, 2), textColour='Red')
        # Label(parent=myFrame, text="myFrame (1,0)", grid=(1, 0), textColour='Red')
        # Label(parent=myFrame, text="myFrame (1,1)", grid=(1, 1), textColour='Red')
        # Label(parent=myFrame, text="myFrame (1,2)", grid=(1, 2), textColour='Red')
        # Label(parent=myFrame, text="myFrame (2,0)", grid=(2, 0), textColour='Red')
        # Label(parent=myFrame, text="myFrame (2,1)", grid=(2, 1), textColour='Red')
        # Label(parent=myFrame, text="myFrame (2,2)", grid=(2, 2), textColour='Red')
        #

        # row += 1
        # self.processButton = Button(self.mainWidget, grid=(row, 1), text='Process',
        #                             callback=self._process,
        #                             hPolicy='expanding')
        # self.processButton.setFixedHeight(_height)
        #
        # self.processButton2 = Button(self.mainWidget, grid=(row, 3), text='Process',
        #                             callback=self._process,
        #                             hPolicy='expanding')
        # self.processButton2.setFixedHeight(_height)

    def _okCallback(self):
        """Clicked 'OK':
        """

        if not self.project:
            raise RuntimeError('Project is not defined')


        MessageDialog.showInfo(self.title,
                               f'OK pressed'
                               )


if __name__ == '__main__':

    popup = GUIMacroTutorial1()
    popup.show()
    popup.raise_()

