import sys

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore, QtWidgets, QtGui, QtSvg
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame


class ImageView(Widget):
    _sizeHint = QSize()

    def __init__(self, parent=None, pixmap=None, **kwds) -> None:
        super().__init__(parent=parent)
        self._pixmap = None
        self.scaledImage = None
        self.setPixmap(pixmap)

    @property
    def pixmap(self):
        return self._pixmap

    @pixmap.setter
    def pixmap(self, value):
        if isinstance(value, QPixmap):
            self._pixmap = value
            self._sizeHint = value.size()

        self.updateGeometry()
        self.rescale()

    def setPixmap(self, pixmap):
        self.pixmap = pixmap

    @property
    def scaledImage(self):
        return self._scaledImage

    @scaledImage.setter
    def scaledImage(self, value):
        self._scaledImage = value

    def sizeHint(self):
        return self._sizeHint

    def rescale(self):
        if self.pixmap:
            self.scaledImage = self.pixmap.scaled(self.size() , QtCore.Qt.KeepAspectRatio)
        self.update()

    def resizeEvent(self, a0):
        self.rescale()

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QtGui.QPainter(self)
        rgn = self.scaledImage.rect()
        rgn.moveCenter(self.rect().center())
        painter.drawPixmap(rgn, self.scaledImage)
        painter.end()


class ImageViewSVG(Widget):
    _sizeHint = QSize()

    def __init__(self, parent=None, svg=None, **kwds) -> None:
        super().__init__(parent=parent)
        self._svg = None
        self.svg = svg

    @property
    def svg(self):
        return self._svg

    @svg.setter
    def svg(self, value):
        self._svg = value
        self.renderer = QtSvg.QSvgRenderer(self.svg)
        self.renderer.setAspectRatioMode(QtCore.Qt.KeepAspectRatio)

    def setSvg(self, svg):
        self.svg = svg

    def paintEvent(self, event):
        if not self.svg:
            return

        painter = QtGui.QPainter(self)

        painter.restore()
        self.renderer.render(painter)


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.Splitter import Splitter
    from ccpn.util import Path

    app = TestApplication()

    window = Widget(parent=None)
    window.setLayout(QtWidgets.QVBoxLayout())

    split = Splitter(parent=None, horizontal=True)
    window.getLayout().addWidget(split)

    topDir = Path.aPath(Path.getTopDirectory())

    image = ImageView(parent=None,
                      pixmap=QPixmap(f'{topDir}' + '/internal/launcher/Images/trace.png'))
    image2 = ImageViewSVG(parent=None,
                          svg=(f'{topDir}' + r'/internal/launcher/Images/trace.svg'))

    split.addWidget(image)
    split.addWidget(image2)

    window.show()
    window.raise_()
    app.start()





