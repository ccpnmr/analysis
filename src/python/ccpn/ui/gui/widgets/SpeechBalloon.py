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


DEFAULT_SEPARATOR = '|'
LEFT_LABEL = 0
MIDDLE_LABEL = 1
RIGHT_LABEL = 2


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

    def __init__(self, side=Side.BOTTOM, percentage=50, owner=None, parent=None, on_top=False):

        super(SpeechBalloon, self).__init__(parent)

        flags = Qt.FramelessWindowHint
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_NoSystemBackground)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

        self._pointer_height = 10
        self._pointer_width = 20
        self._pointer_side = side
        self._display_rect = self._calc_display_rect()
        self._percentage = percentage / 100.0

        self._corner_radius = 3
        self._pen_width = 0

        self._owner = owner

        self.setMargins()

    @pyqtProperty(int)
    def cornerRadius(self):
        return self._corner_radius

    @cornerRadius.setter
    def cornerRadius(self, radius):
        self._corner_radius = radius
        self.update()

    @pyqtProperty(int)
    def pointerHeight(self):
        return self._pointer_height

    @pointerHeight.setter
    def pointerHeight(self, height):
        self._pointer_height = height
        self.update()

    @pyqtProperty(int)
    def pointerWidth(self):
        return self._pointer_width

    @pointerWidth.setter
    def pointerWidth(self, width):
        self._pointer_width = width
        self.update()

    @pyqtProperty(Side)
    def pointerSide(self):
        return self._pointer_side

    @pointerSide.setter
    def pointerSide(self, side):
        self._pointer_side = side
        self.update()

    @pyqtProperty(float)
    def pointerSideOffset(self):
        return self._percentage

    @pointerSideOffset.setter
    def pointerSideOffset(self, percentage):
        self._percentage = percentage
        self.update()

    def _calc_display_rect(self):
        result = self._calc_usable_rect()

        offsets = [0, 0, 0, 0]
        offset_direction = (1, 1, -1, -1)

        side = int(self._pointer_side)
        offsets[side] = self._pointer_height * offset_direction[side]

        result.adjust(*offsets)

        return result

    def _calc_usable_rect(self):

        # this allows for anti-aliasing
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

        pointer_pos = None
        if self._pointer_side in (Side.TOP, Side.BOTTOM):
            min_pos_x = pointer_width_2 + self._corner_radius
            max_pos_x = width - pointer_width_2 - self._corner_radius
            pointer_pos_x = int(min_pos_x + ((max_pos_x - min_pos_x) * self._percentage))

            if self._pointer_side == Side.TOP:
                pointer_pos = QPoint(pointer_pos_x, top - pointer_height)
            elif self._pointer_side == Side.BOTTOM:
                pointer_pos = QPoint(pointer_pos_x, bottom + pointer_height)
        else:
            min_pos_y = self._corner_radius + pointer_width_2
            max_pos_y = height - pointer_width_2 - self._corner_radius
            pointer_pos_y = int(min_pos_y + ((max_pos_y - min_pos_y) * self._percentage))

            if self._pointer_side == Side.LEFT:
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
        pointer_points = None
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
        children = [child for child in self.children() if isinstance(child, QWidget)]
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


class DoubleLabel(QFrame):

    def __init__(self, parent=None):
        super(DoubleLabelWidget, self).__init__(parent=parent)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # if you ever allow this to be set you will need to
        # call setLabelText to reset the text widths
        self._margin = 2

        self._labels = [None] * 3
        left_label = QLabel()
        left_label.setAlignment(Qt.AlignRight)
        layout.addWidget(left_label, 0, 0)
        left_label.setMargin(self._margin)
        self._labels[LEFT_LABEL] = left_label

        center_label = QLabel(DEFAULT_SEPARATOR)
        center_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(center_label, 0, 1)
        self._labels[MIDDLE_LABEL] = center_label

        right_label = QLabel()
        right_label.setAlignment(Qt.AlignLeft)
        right_label.setMargin(self._margin)
        layout.addWidget(right_label, 0, 2)
        self._labels[RIGHT_LABEL] = right_label

        self.setLayout(layout)

        self._max_digit_width = self._get_max_digit_width()

    def _get_max_digit_width(self):
        self._font = self._labels[LEFT_LABEL].font()
        self._font_metrics = QFontMetrics(self._font)
        widths = [self._font_metrics.boundingRect(digit).width() for digit in list('01234567890-')]
        return max(widths)

    def setLabelText(self, widget_id, text):
        self._check_widget_index(widget_id)

        self._labels[widget_id].setText(text)

        x = self._labels[LEFT_LABEL].text()
        y = self._labels[RIGHT_LABEL].text()

        width_x = (self._max_digit_width * len(x)) + self._margin * 2
        width_y = (self._max_digit_width * len(y)) + self._margin * 2

        width = max(width_x, width_y)

        self._labels[LEFT_WIDGET].setFixedWidth(width)
        self._labels[RIGHT_WIDGET].setFixedWidth(width)

    @staticmethod
    def _check_widget_index(widget_id):
        if widget_id < LEFT_LABEL or widget_id > RIGHT_LABEL:
            raise ValueError('Error widget id should be one of  LEFT_WIDGET, MIDDLE_WIDGET or RIGHT_WIDGET')

    def setLabelVisible(self, widget_id, visible):
        self._check_widget_index(widget_id)
        self._labels[widget_id].setVisible(visible)

        if not self._labels[LEFT_LABEL].isVisible() and not self._labels[LEFT_LABEL].isVisible():
            self._labels[MIDDLE_LABEL].setMargin(self._margin)
        else:
            self._labels[MIDDLE_LABEL].setMargin(0)



class MousePositionLabel(DoubleLabel):
    def __init__(self, parent=None):
        super(MousePositionLabel, self).__init__(parent=parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.get_position)
        self.timer.setInterval(50)
        self.timer.start()

    def get_position(self):
        ev = QCursor.pos()

        x = '%i' % ev.x()
        y = '%i' % ev.y()

        self.setLabelText(LEFT_WIDGET, x)
        self.setLabelText(RIGHT_WIDGET, y)


if __name__ == '__main__':
    app = MyApplication(sys.argv)

    window2 = SpeechBalloon()
    window2.cornerRadius = 3

    app.setActiveWindow(window2)

    label = MousePositionLabel(parent=window2)

    window2.setCentralWidget(label)
    window2.show()

    app.exec_()
