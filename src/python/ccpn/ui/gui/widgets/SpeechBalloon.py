import string
import sys
from enum import IntEnum
from math import sqrt, ceil, floor

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, Qt, QRect, QPoint, pyqtProperty, QTimer
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor, QBrush, QPolygon, QPolygonF, QPixmap, QPalette, QCursor, \
    QGuiApplication, QFontMetrics
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLayout, QTableWidget, QTableWidgetItem, QFrame
from icecream import ic


class Side(IntEnum):
    TOP = 1
    LEFT = 0
    RIGHT = 2
    BOTTOM = 3

class MyApplication(QApplication):
    def __init__(self, arg):
        super(MyApplication, self).__init__(arg)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(0)

    def _update(self):
        pos = QCursor.pos()
        window = self.activeWindow()

        if window:
            window.move_pointer_to(pos)

class SpeechBalloon(QWidget):
    """
        inspired by but not sharing any code with FUKIDASHI
        aka https://github.com/sharkpp/qtpopover (MIT licensed!)

         *__/\___                 * = 原点 - origin
         |      |      時計回りに描画 -  draw clockwise
         +------+
    """

    def __init__(self, side=Side.BOTTOM, percentage=50, owner=None, parent=None, ontop=False):

        super(SpeechBalloon, self).__init__(parent)

        flags = Qt.FramelessWindowHint
        if ontop:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_NoSystemBackground)

        layout = QGridLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._pointer_height = 10
        self._pointer_width = 20
        self._pointer_side = side
        self._display_rect = self._calc_display_rect()
        self._percentage = percentage / 100.0

        self._corner_radius = 3
        self._pen_width = 0

        self._owner = owner

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

        self.setMargins()



    @pyqtProperty(int)
    def cornerRadius(self):
        return self._corner_radius

    @cornerRadius.setter
    def cornerRadius(self, radius):
        self._corner_radius = radius

    @pyqtProperty(int)
    def pointerHeight(self):
        return self._pointer_height

    @pointerHeight.setter
    def pointerHeight(self, height):
        self._pointer_height = height

    @pyqtProperty(int)
    def pointerWidth(self):
        return self._pointer_width

    @pointerHeight.setter
    def pointerWidth(self, width):
        self._pointer_width = width

    @pyqtProperty(Side)
    def pointerSide(self):
        return self._pointer_side

    @pointerSide.setter
    def pointerSide(self, side):
        self._pointer_side = side

    @pyqtProperty(float)
    def pointerSideOffset(self):
        return self._percentage

    @pointerSideOffset.setter
    def pointerSideOffset(self, percentage):
        self._percentage = percentage

    def _calc_display_rect(self):
        result = self._calc_usable_rect()

        offsets = [0, 0, 0, 0]
        offset_direction = (1, 1, -1, -1)

        side = int(self._pointer_side)
        offsets[side] = self._pointer_height * offset_direction[side]

        result.adjust(*offsets)

        return result

    def _calc_usable_rect(self):

        # this allows for anti-aliaising
        return self.frameGeometry().adjusted(1, 1, -1, -1)

    def _calc_local_usable_rect(self):
        return self._rect_to_local(self._calc_usable_rect())

    def resizeEvent(self, event):
        self.setMask(self.window_mask())

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:

        painterPath = self.window_path()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        pal = self.palette()
        fgColor = pal.color(QPalette.Active, QPalette.Text)
        bgColor = pal.color(QPalette.Active, QPalette.Window)

        brush = QBrush(bgColor)
        pen = QPen(fgColor)
        pen.setWidth(self._pen_width)
        painter.fillPath(painterPath, brush)
        painter.strokePath(painterPath, pen)

        return super(SpeechBalloon, self).paintEvent(a0)

    def _get_pointer_position(self):
        width = self._local_display_rect().width()
        top = self._local_display_rect().top()
        bottom = self._local_display_rect().bottom()
        left = self._local_display_rect().left()
        right = self._local_display_rect().right()
        height = self._local_display_rect().height()

        pointer_height = self._pointer_height

        pointer_width_2 = int(self._pointer_width / 2)

        if self._pointer_side in (Side.TOP, Side.BOTTOM):
            min_pos_x = pointer_width_2 + self._corner_radius
            max_pos_x = width - pointer_width_2 - self._corner_radius
            pointer_pos_x = int(min_pos_x + ((max_pos_x - min_pos_x) * self._percentage))
        else:
            min_pos_y = self._corner_radius + pointer_width_2
            max_pos_y = height - pointer_width_2 - self._corner_radius
            pointer_pos_y = int(min_pos_y + ((max_pos_y - min_pos_y) * self._percentage))

        if self._pointer_side == Side.TOP:
            pointer_pos = QPoint(pointer_pos_x, top - pointer_height)
        elif self._pointer_side == Side.BOTTOM:
            pointer_pos = QPoint(pointer_pos_x, bottom + pointer_height)
        elif self._pointer_side == Side.LEFT:
            pointer_pos = QPoint(left - pointer_height, pointer_pos_y)
        elif self._pointer_side == Side.RIGHT:
            pointer_pos = QPoint(right + pointer_height, pointer_pos_y)

        return pointer_pos

    def window_path(self):
        display_rect = QRectF(self._local_display_rect())

        path = QPainterPath()
        path.addRoundedRect(display_rect, self._corner_radius, self._corner_radius)

        width = self._local_display_rect().width()
        width_2 = int(width / 2)
        top = self._local_display_rect().top()
        bottom = self._local_display_rect().bottom()
        left = self._local_display_rect().left()
        right = self._local_display_rect().right()
        # height = self._local_display_rect().height()

        pointer_width_2 = int(self._pointer_width / 2)

        pointer_pos = self._get_pointer_position()
        if self._pointer_side == Side.TOP:
            pointer_points = [QPoint(pointer_pos.x() - pointer_width_2, top),
                              pointer_pos,
                              QPoint(pointer_pos.x() + pointer_width_2, top)]
        elif self._pointer_side == Side.BOTTOM:
            pointer_points = [QPoint(width_2 - pointer_width_2, bottom + 1),
                              pointer_pos,
                              QPoint(width_2 + pointer_width_2, bottom + 1)]
        elif self._pointer_side == Side.LEFT:
            pointer_points = [QPoint(left, pointer_pos.y() - pointer_width_2),
                              pointer_pos,
                              QPoint(left, pointer_pos.y() + pointer_width_2)]
        elif self._pointer_side == Side.RIGHT:
            pointer_points = [QPoint(right + 1, pointer_pos.y() - pointer_width_2),
                              pointer_pos,
                              QPoint(right + 1, pointer_pos.y() + pointer_width_2)]

        pointer_polygon = QPolygonF(QPolygon(pointer_points))
        path.addPolygon(pointer_polygon)

        path = path.simplified()
        return path

    def window_mask(self):
        path = self.window_path()

        pixmap = QPixmap(int(path.boundingRect().width() + 2), int(path.boundingRect().height() + 2))

        painter = QPainter()

        painter.begin(pixmap)

        brush = QBrush(QColor('white'))
        painter.fillRect(pixmap.rect(), brush)

        brush = QBrush(QColor('black'))
        painter.setBrush(brush)

        painter.drawPath(path)

        painter.end()

        result = pixmap.createHeuristicMask(False)

        return result

    def _local_display_rect(self):
        self._display_rect = self._calc_display_rect()
        local_display_rect = self._rect_to_local(self._display_rect)
        return local_display_rect

    def _rect_to_local(self, rect):
        result = QRect()
        result.setTopLeft(self.mapFromGlobal(rect.topLeft()))
        result.setSize(rect.size())
        return result

    def _pointer_offset(self):

        pointer_pos = self.mapToGlobal(self._get_pointer_position())

        return pointer_pos - self.pos()

    def move_pointer_to(self, pos):
        offset = self._pointer_offset()

        self.setGeometry(QRect(pos - offset, self.geometry().size()))

    def setCentralWidget(self, central_widget):

        self.layout().addWidget(central_widget, 0, 0)

    def centralWidget(self):
        children = [child for child in self.children() if isinstance(child,QWidget)]
        result = children[0] if len(children) else None
        return result

    def setMargins(self):
        self.layout().setContentsMargins(0, 0, 0, 0)
        corner_margin = self._corner_radius / sqrt(2)
        corner_margin = int(ceil(corner_margin))
        new_margins = [corner_margin, ] * 4
        new_margins[self._pointer_side] += self._pointer_height
        self.layout().setContentsMargins(*new_margins)

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        if self._owner:
            self._owner.leaveEvent(a0)


if __name__ == '__main__':
    app = MyApplication(sys.argv)

    window2 = SpeechBalloon()
    window2.cornerRadius = 1
    window2.setGeometry(200, 200, 50, 30)

    app.setActiveWindow(window2)

    label = QLabel('test', parent=window2)
    label.setAlignment(Qt.AlignCenter)
    window2.set_central_widget(label)
    window2.show()

    app.exec_()