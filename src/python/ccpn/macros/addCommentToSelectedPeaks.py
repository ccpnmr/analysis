from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets import Entry
from ccpn.core.lib.ContextManagers import undoBlock

class AddCommentToSelectedPeaks(CcpnDialog):
    title = 'Add Comment to Selected Peaks'

    def __init__(self, parent=None, mainWindow=None, title=title,  **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

        self._createWidgets()

    def _createWidgets(self):
        Label(self, text='Enter the comment:', grid=(0, 0))
        self.EntryBox = Entry.Entry(self, grid=(1, 0), editable=True)
        Button(self, text='OK', grid=(2,0), callback=self._okCallback)
        Button(self, text='Cancel', grid=(3,0), callback=self._cancelCallback)

    def _okCallback(self, *args):
        with undoBlock():
            self._addComment(self.EntryBox.get())
        return self.accept()

    def _addComment(self, comment):
        for pk in current.peaks:
            pk.comment = comment

    def _cancelCallback(self, *args):
        return self.reject()


if __name__ == "__main__":
    popup = AddCommentToSelectedPeaks(mainWindow=mainWindow)
    popup.show()
    popup.raise_()


