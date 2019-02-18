"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Frame import Frame


class MainWindow(QtWidgets.QMainWindow, Base):

    def __init__(self, parent=None, title='', location=None, hide=False, **kwds):

        super().__init__(parent=parent)
        Base._init(self, **kwds)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.mainFrame = Frame(self, setLayout=1)
        self.setCentralWidget(self.mainFrame)
        self.mainFrame.setAccessibleName('MainWindow Frame')

        self.setWindowTitle(title)

        if location:
            self.move(*location)

        if hide:
            self.hide()
        else:
            self.show()
            self.raise_()

    def setSize(self, width, height):
        "set the width and height of the Mainwindow"
        self.setGeometry(self.x(), self.y(), width, height)


class DockWidget(QtGui.QDockWidget):
    AREA_DICT = dict(
            left=QtCore.Qt.LeftDockWidgetArea,
            top=QtCore.Qt.TopDockWidgetArea,
            right=QtCore.Qt.RightDockWidgetArea,
            bottom=QtCore.Qt.LeftDockWidgetArea,
            )

    def __init__(self, parent=None, title='', widget=None, floating=False,
                 allowedAreas=None,
                 **kwds):

        # QtWidgets.QMainWindow.__init__(self, title, parent=parent) FIXME: GWV doesn't get this
        super().__init__(parent)
        Base._init(self, **kwds)

        self.setTitle(title)

        if widget is not None:
            self.setWidget(widget)

        if allowedAreas is not None:
            areas = 0
            for a in allowedAreas:
                areas = areas | self.AREA_DICT.get(a, 0)
            self.setAllowedAreas(areas)


if __name__ == '__main__':
    class testWindow(MainWindow):

        def __init__(self):
            MainWindow.__init__(self, title='Test Window')

            self.setDockNestingEnabled(True)

            self.sideBar = Frame(self, showBorder=True)
            self.sideBar.setMinimumWidth(200)
            self.sideBar.setMinimumHeight(300)
            self.sideBarDock = DockWidget(self, title='SideBar', widget=self.sideBar, allowedAreas=['left'])
            self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.sideBarDock)

            button1 = Button(self, text='hit me', callback=self.callback)
            button2 = Button(self, text='quit', callback=None)

            dock1 = DockWidget(self, title='dock1', widget=button1, allowedAreas=['top', 'right', 'bottom'])
            dock2 = DockWidget(self, title='dock2', widget=button2, allowedAreas=['top', 'right', 'bottom'])
            dock3 = DockWidget(self, title='dock3', widget=button1, allowedAreas=['top', 'right', 'bottom'])
            self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock1)
            self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock2)
            self.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock3)

        def callback(self):
            print('callback')


    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.Button import Button


    def callback():
        print('callback')


    app = TestApplication()

    # window = MainWindow(title='Test MainWindow')
    # button1 = Button(window.mainFrame, grid=(0,0), text='hit me', callback=callback)
    # button2 = Button(window.mainFrame, grid=(1,0), text='quit', callback=app.quit)
    #
    # window.setDockNestingEnabled(True)
    # dock1 = DockWidget(window, title='dock1', widget=button1)
    # dock2 = DockWidget(window, title='dock2', widget=button2)
    # window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock1)
    # window.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock2)

    window = testWindow()

    app.start()
