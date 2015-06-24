__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from pyqtgraph.widgets.VerticalLabel import VerticalLabel

from ccpncore.gui.Font import Font

class DockLabel(VerticalLabel):

    sigClicked = QtCore.Signal(object, object)

    def __init__(self, text, dock):
        self.dim = False
        self.fixedWidth = False
        VerticalLabel.__init__(self, text.upper(), orientation='horizontal', forceWidth=False)
        self.setAlignment(QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter)
        self.dock = dock
        self.updateStyle()
        self.setAutoFillBackground(False)
        self.setFont(Font(semiBold=True, size=13))
        # self.setFixedHeight(13)

    #def minimumSizeHint(self):
        ##sh = QtGui.QWidget.minimumSizeHint(self)
        #return QtCore.QSize(20, 20)

    def updateStyle(self):
        r = '1px'
        if self.dim:
            fg = '#122043'
            bg = '#BEC4F3'
            border = '#00092D'
        else:
            fg = '#122043'
            bg = '#BEC4F3'
            border = '#55B'

        if self.orientation == 'vertical':
            self.vStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: 1px;
                border-top-left-radius: %s;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: %s;
                border-width: 0px;
                border-right: 1px solid %s;
                padding-top: 3px;
                padding-bottom: 3px;
            }""" % (bg, fg, r, r, border)
            self.setStyleSheet(self.vStyle)
        else:
            self.hStyle = """DockLabel {
                background-color : %s;
                color : %s;
                border-top-right-radius: %s;
                border-top-left-radius: %s;
                border-bottom-right-radius: 0px;
                border-bottom-left-radius: 0px;
                border-width: 0px;
                border-bottom: 2px solid %s;
                padding-left: 3px;
                padding-right: 3px;
            }""" % (bg, fg, r, r, border)
            self.setStyleSheet(self.hStyle)

    def setDim(self, d):
        if self.dim != d:
            self.dim = d
            self.updateStyle()

    def setOrientation(self, o):
        VerticalLabel.setOrientation(self, o)
        # self.updateStyle()

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pressPos = ev.pos()
            self.startedDrag = False
            ev.accept()

    def mouseMoveEvent(self, ev):
        if not self.startedDrag and (ev.pos() - self.pressPos).manhattanLength() > QtGui.QApplication.startDragDistance():
            self.dock.startDrag()
        ev.accept()
        #print ev.pos()

    def mouseReleaseEvent(self, ev):
        if not self.startedDrag:
            #self.emit(QtCore.SIGNAL('clicked'), self, ev)
            self.sigClicked.emit(self, ev)
        ev.accept()

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.dock.float()

