import sys

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap
from PyQt5 import QtCore, QtWidgets, QtGui, QtSvg
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame


class ImageView(Widget):
    """A widget to add a pixmap image to a layout.

    Takes a QPixmap object renders it based on the available size.
    Uses KeepAspectRatio to ensure proper scaling when the widget is resized.

    Example provided at the bottom of the file on how to use the widget.
    """

    _sizeHint = QSize()

    def __init__(self, parent=None, pixmap=None, **kwds) -> None:
        super().__init__(parent=parent)
        self._pixmap = None
        self.scaledImage = None
        self.setPixmap(pixmap)

    @property
    def pixmap(self):
        """The pixmap to be rendered"""
        return self._pixmap

    @pixmap.setter
    def pixmap(self, value):
        """Sets pixmap

        Rescales the image
        """
        if isinstance(value, QPixmap):
            self._pixmap = value
            self._sizeHint = value.size()
        else:
            return

        self.rescale()

    def setPixmap(self, pixmap):
        """Sets the pixmap to be rendered

        Added to be the same style PyQt5.
        """
        self.pixmap = pixmap

    @property
    def scaledImage(self):
        """Scaled pixmap"""
        return self._scaledImage

    @scaledImage.setter
    def scaledImage(self, value):
        """Sets the scaled pixmap"""
        self._scaledImage = value

    def sizeHint(self):
        return self._sizeHint

    def rescale(self):
        """Rescales the pixmap

        Keeps the aspect ratio of the image and sets to
        the size of the widget.
        """
        if self.pixmap:
            self.scaledImage = self.pixmap.scaled(self.size() , QtCore.Qt.KeepAspectRatio)
        self.update()

    def resizeEvent(self, a0):
        self.rescale()

    def paintEvent(self, event):
        """Paint event for the image"""
        if not self.pixmap:
            return

        painter = QtGui.QPainter(self)
        rgn = self.scaledImage.rect()
        rgn.moveCenter(self.rect().center())
        painter.drawPixmap(rgn, self.scaledImage)
        painter.end()


class ImageViewSVG(Widget):
    """A widget to add a svg image to a layout.

    Takes a path and adds provides svg rendering.
    Uses KeepAspectRatio to ensure proper scaling when the widget is resized.

    Example provided at the bottom of the file on how to use the widget.
    """
    _sizeHint = QSize()

    def __init__(self, parent=None, svg: str | None = None, **kwds) -> None:
        super().__init__(parent=parent)
        self._svg = None
        self.svg = svg

    @property
    def svg(self):
        """The path to the svg"""
        return self._svg

    @svg.setter
    def svg(self, value):
        """Sets the svg renderer on the path given"""
        if not value:
            return

        self._svg = value
        self.renderer = QtSvg.QSvgRenderer(self.svg)
        self._sizeHint = self.renderer.defaultSize()
        self.renderer.setAspectRatioMode(QtCore.Qt.KeepAspectRatio)

    def setSvg(self, svg):
        """Sets the svg renderer on the path given

        Added to be the same style PyQt5.
        """
        self.svg = svg

    def sizeHint(self):
        return self._sizeHint

    def paintEvent(self, event):
        """Subclassed from widget to us an svg renderer.
        """
        if not self.svg:
            return

        painter = QtGui.QPainter(self)
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





