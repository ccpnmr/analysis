import string
import sys
from enum import IntEnum
from math import sqrt, ceil, floor

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, Qt, QRect, QPoint, pyqtProperty, QTimer
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor, QBrush, QPolygon, QPolygonF, QPixmap, QPalette, QCursor, \
    QFontMetrics, QScreen
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLayout, QFrame
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


class PaintContext:
    def __init__(self, painter):
        self._painter = painter

    def __enter__(self):
        return self._painter

    def __exit__(self, *args):
        self._painter.end()
        return True

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

class BalloonMetrics:
    NUM_SIDES = 4
    SIGNS = [-1, -1, 1, 1]

    def __init__(self, corner_radius=3, pointer_side=Side.RIGHT, pointer_height=10, pointer_width=20):
        self.corner_radius = corner_radius
        self.pointer_side = pointer_side
        self.pointer_height = pointer_height
        self.pointer_width = pointer_width
        self.antialias_margin = 1

    def _get_corner_margin(self):
        result = self.corner_radius / sqrt(2)
        result = int(ceil(result))

        return result

    def _add_margins(self, rect: QRect, margin, multiplier=1):
        margins = [margin * multiplier] * 4
        margins = [margins[i] * self.SIGNS[i] for i in range(self.NUM_SIDES)]

        return rect.adjusted(*margins)

    def _add_central_widget_margins(self, rect: QRect, multiplier=1):
        return self._add_margins(rect, self._get_corner_margin(), multiplier)

    def _add_pointer_margin(self, rect: QRect, multiplier=1):

        signs = [self.SIGNS[i] * multiplier for i in range(self.NUM_SIDES)]
        margin = [self.pointer_height] * self.NUM_SIDES

        margin = [margin[i] * signs[i] for i in range(self.NUM_SIDES)]

        mask = [0] * self.NUM_SIDES
        mask[self.pointer_side] = 1

        pointer_margins = [margin[i] * mask[i] for i in range(self.NUM_SIDES)]

        return rect.adjusted(*pointer_margins)

    def _add_antialias_margin(self, rect: QRect, multiplier=1):

        return self._add_margins(rect, self.antialias_margin, multiplier)


    def expand_to_perimeter(self, rect: QRect):

        result = self._add_central_widget_margins(rect)
        result = self._add_pointer_margin(result)
        result = self._add_antialias_margin(result)

        return result

    def reduce_to_inside(self, rect: QRect):

        result = self._add_antialias_margin(rect, multiplier=-1)
        result = self._add_pointer_margin(result, multiplier=-1)
        result = self._add_central_widget_margins(result, multiplier=-1)

        return result


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
        self.layout().setContentsMargins(*self._get_margins())
        self.layout().activate()
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

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:

        self.setMask(self.window_mask())

        painterPath = self.window_path()

        with PaintContext(QPainter(self)) as painter:

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

    def _get_pointer_position(self, rect=None, on_border=False):

        if rect == None:
            local_display_rect = self._local_display_rect()
        else:
            local_display_rect = rect

        width = local_display_rect.width()
        top = local_display_rect.top()
        bottom = local_display_rect.bottom()
        left = local_display_rect.left()
        right = local_display_rect.right()
        height = local_display_rect.height()

        pointer_height = 0 if on_border else self._pointer_height

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

        with PaintContext(QPainter(pixmap)) as painter:


            brush = QBrush(QColor('white'))
            painter.fillRect(pixmap.rect(), brush)

            brush = QBrush(QColor('black'))
            painter.setBrush(brush)

            painter.drawPath(path)


        result = pixmap.createHeuristicMask(False)

        return result

    def _local_display_rect(self):
        display_rect = self._calc_display_rect()
        local_display_rect = self._rect_to_local(display_rect)
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

        # otherwise geometry isn't known when the window is shown on osx
        # and you get the message 'qt.qpa.cocoa.window: Window position outside any known screen, using primary screen'
        # https://stackoverflow.com/questions/541 7201/qt-place-new-window-correctly-on-screen-center-over-mouse-move-into-screen
        self.layout().activate()


    def centralWidget(self):
        children = [child for child in self.children() if isinstance(child, QWidget)]
        result = children[0] if len(children) else None
        return result

    def showAt(self, screen, side_pos_alternatives):

        for side, pos in side_pos_alternatives:
            ic(side_pos_alternatives)
            ic(self._get_side_preferences(screen, side, pos))

        side, pointer_pos = side_pos_alternatives[0]
        margins = self._get_margins(1)
        size_hint = self.centralWidget().sizeHint()

        geometry = QRect()
        geometry.setSize(size_hint)


        geometry.adjust(*margins)
        pointer_pos_on_geometry = self._get_pointer_position(geometry, on_border=True)

        offset = pointer_pos - pointer_pos_on_geometry

        geometry.translate(offset.x(), offset.y())

        #  there's an error in the layout...
        # these are approximately correct till we correct it
        CORRECTIONS ={
            Side.BOTTOM: (-1,-1),
            Side.RIGHT: (-1,-1),
            Side.TOP: (-1,0),
            Side.LEFT: (0,-1)
        }

        correction = CORRECTIONS[self._pointer_side]
        scale = self._get_corner_margins()[0] + 1
        geometry.translate(scale * correction[0], scale * correction[1])

        self.setGeometry(geometry)

        self.show()


    def _get_screen_side(self, screen, side):
        screen_rect = screen.availableGeometry()

        #TODO: sides are in a strange order should be top left bottom right
        #TODO: add side selection by x and y into Side also opposites
        screen_cooords = [screen_rect.top(), screen_rect.left(),
                          screen_rect.right(), screen_rect.bottom()]

        return screen_cooords[side]

    def _get_side_preferences(self, screen, side, pos):

        dists = {}
        for side in Side:

            screen_side_coord = self._get_screen_side(screen, side)

            if side in (Side.TOP, Side.BOTTOM):
                dist = screen_side_coord - pos.y()
            else:
                dist = screen_side_coord - pos.x()
            dists[side] = abs(dist)

        return dists




    def setMargins(self):
        self.layout().setContentsMargins(0, 0, 0, 0)
        new_margins = self._get_margins()
        self.layout().setContentsMargins(*new_margins)

    def _get_corner_margins(self, multiplier=1):
        corner_margin = self._corner_radius / sqrt(2)
        corner_margin = int(ceil(corner_margin))
        new_margins = [corner_margin * multiplier, ] * 4

        return new_margins

    def _get_margins(self, multiplier=1):
        new_margins= self._get_corner_margins(multiplier)
        new_margins[self._pointer_side] += (self._pointer_height * multiplier)
        return new_margins

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        if self._owner:
            self._owner.leaveEvent(a0)


class DoubleLabel(QFrame):

    def __init__(self, text=[''], parent=None):
        super(DoubleLabel, self).__init__(parent=parent)

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

        self._separator = DEFAULT_SEPARATOR

        self.setLabels(text)

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

        self._labels[LEFT_LABEL].setFixedWidth(width)
        self._labels[RIGHT_LABEL].setFixedWidth(width)

    def setLabels(self, text):
        if len(text) not in (1, 2):
            raise ValueError("Error double label supports 1 or 2 labels")

        if len(text) == 1:
            self.setLabelVisible(LEFT_LABEL, False)
            self.setLabelVisible(MIDDLE_LABEL, True)
            self.setLabelVisible(RIGHT_LABEL, False)

            self.setLabelText(MIDDLE_LABEL, text[0])
        else:
            self.setLabelVisible(LEFT_LABEL, True)
            self.setLabelVisible(MIDDLE_LABEL, True)
            self.setLabelVisible(RIGHT_LABEL, True)

            self.setLabelText(LEFT_LABEL, text[0])
            self.setLabelText(MIDDLE_LABEL, self._separator)
            self.setLabelText(RIGHT_LABEL, text[1])


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

        self.setLabels([x,y])


def run_tests():
    import pytest
    pytest.main([__file__])


def test_expand():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10, 100))
    assert QRect(QPoint(-3, -3), QSize(16, 106)) == metrics._add_central_widget_margins(test_rect)
    assert QRect(QPoint(0,0), QSize(20, 100)) == metrics._add_pointer_margin(test_rect)
    assert QRect(QPoint(-1, -1), QSize(12, 102)) == metrics._add_antialias_margin(test_rect)
    assert QRect(QPoint(-4, -4), QSize(28, 108)) == metrics.expand_to_perimeter(test_rect)


def test_reduce():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10,100))

    assert QRect(QPoint(1, 1), QSize(8, 98)) == metrics._add_antialias_margin(test_rect, multiplier=-1)
    assert QRect(QPoint(3, 3), QSize(4, 94)) == metrics._add_central_widget_margins(test_rect, multiplier=-1)
    assert QRect(QPoint(0, 0), QSize(0, 100)) == metrics._add_pointer_margin(test_rect, multiplier=-1)
    assert test_rect == metrics.reduce_to_inside(QRect(QPoint(-4, -4), QSize(28, 108)))


def test_expand_sides():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(100, 100))

    metrics.pointer_side = Side.BOTTOM
    assert QRect(QPoint(0,0), QSize(100, 110)) == metrics._add_pointer_margin(test_rect)
    metrics.pointer_side = Side.TOP
    assert QRect(QPoint(0, -10), QSize(100, 110)) == metrics._add_pointer_margin(test_rect)
    metrics.pointer_side = Side.LEFT
    assert QRect(QPoint(-10, 0), QSize(110, 100)) == metrics._add_pointer_margin(test_rect)
    metrics.pointer_side = Side.RIGHT
    assert QRect(QPoint(0, 0), QSize(110, 100)) == metrics._add_pointer_margin(test_rect)


if __name__ == '__main__':

    if '-t' in sys.argv:
        run_tests()
    else:
        app = MyApplication(sys.argv)

        window2 = SpeechBalloon()
        window2.cornerRadius = 3

        app.setActiveWindow(window2)

        label = MousePositionLabel(parent=window2)

        window2.setCentralWidget(label)
        window2.show()

        app.exec_()
