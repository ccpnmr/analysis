

# TODO needs to prioritise screen of button on show at
# TODO needs to pin base of pointer if showat will move pointer below
# TODO needs a license
# TODO display of body rect gives double thickness lines, anti aliasing bug?
# TODO it would be good to clip the interior widget for edge to edge views
# TODO it would be good to check the recommendations in https://www.vikingsoftware.com/creating-custom-widgets
# TODO add extra margin on override offset
# TODO override offset could have a better name
# TODO profile

import sys
from functools import  singledispatchmethod

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, Qt, QRect, QPoint, pyqtProperty, QTimer, QEvent, QSize
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor, QBrush, QPolygon, QPolygonF, QPixmap, QPalette, QCursor, \
    QFontMetrics, QGuiApplication
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QFrame

from BalloonMetrics import Side, BalloonMetrics, OPPOSITE_SIDES, rect_get_side, calc_side_distance_outside_rect, \
    SIDE_AXIS, OPPOSITE_AXIS
from ccpn.core.lib.ContextManagers import AntiAliasedPaintContext

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
    r""" Popover window class
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

        self._metrics = BalloonMetrics()

        self._metrics.pointer_height = 10
        self._metrics.pointer_width = 20
        self._metrics.pointer_side = side
        self._metrics.alignment = percentage / 100.0
        self._metrics.corner_radius = 3

        self._screen_margin = 10

        self._pen_width = 0

        self._owner = owner

        self._central_widget:QWidget = None


    def event(self, event: QtCore.QEvent) -> bool:
        if event.type() == QEvent.LayoutRequest:
            self._layout()
            result = True
        else:
            result = super(SpeechBalloon, self).event(event)

        return result


    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super(SpeechBalloon, self).resizeEvent(event)
        new_outer = QRect(self.geometry())
        new_outer.setSize(event.size())
        self._metrics.from_outer(new_outer)
        self._central_widget.setGeometry(self._metrics.inner_viewport)

    @pyqtProperty(int)
    def cornerRadius(self):
        return self._metrics.corner_radius

    @cornerRadius.setter
    def cornerRadius(self, radius):
        self._metrics.corner_radius = radius
        self._metrics.reset()
        self.updateGeometry()

    @pyqtProperty(int)
    def pointerHeight(self):
        return self._metrics.pointer_height

    @pointerHeight.setter
    def pointerHeight(self, height):
        self._metrics.pointer_height = height
        self._metrics.reset()
        self.updateGeometry()

    @pyqtProperty(int)
    def pointerWidth(self):
        return self._metrics.pointer_width

    @pointerWidth.setter
    def pointerWidth(self, width):
        self._metrics.pointer_width = width
        self._metrics.reset()
        self.updateGeometry()

    @pyqtProperty(Side)
    def pointerSide(self):
        return self._metrics.pointer_side

    @pointerSide.setter
    def pointerSide(self, side):
        self._metrics.pointer_side = side
        self._metrics.reset()
        self.updateGeometry()

    @pyqtProperty(float)
    def pointerAlignment(self):
        return self._metrics.pointer_alignment

    @pointerAlignment.setter
    def pointerAlignment(self, alignment):
        self.metrics.pointer_alignment = alignment
        self._metrics.reset()
        self.updateGeometry()

    @pyqtProperty(int)
    def screenMargin(self):
        return self._screen_margin

    @screenMargin.setter
    def cornerRadius(self, screen_margin):
        self._screen_margin = screen_margin
        self.updateGeometry()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:

        self.setMask(self.window_mask())

        painterPath = self.window_path()

        with AntiAliasedPaintContext(QPainter(self)) as painter:

            pal = self.palette()
            fgColor = pal.color(QPalette.Active, QPalette.Text)
            bgColor = pal.color(QPalette.Active, QPalette.Window)

            brush = QBrush(bgColor)
            pen = QPen(fgColor)
            pen.setWidth(self._pen_width)
            painter.fillPath(painterPath, brush)
            painter.strokePath(painterPath, pen)


        return super(SpeechBalloon, self).paintEvent(a0)

    def window_path(self):

        self._metrics.pointer_side = self.pointerSide

        self._metrics.from_outer(self.frameGeometry())

        path = QPainterPath()

        corner_radius = self._metrics.corner_radius
        path.addRoundedRect(QRectF(self._metrics.body_rect_viewport), corner_radius, corner_radius)

        pointer_polygon = QPolygonF(QPolygon(self._metrics.pointer_viewport))
        path.addPolygon(pointer_polygon)

        path = path.simplified()

        return path

    def window_mask(self):
        path = self.window_path()

        pixmap = QPixmap(int(path.boundingRect().width() + 2), int(path.boundingRect().height() + 2))

        with AntiAliasedPaintContext(QPainter(pixmap)) as painter:

            brush = QBrush(QColor('white'))
            painter.fillRect(pixmap.rect(), brush)

            brush = QBrush(QColor('black'))
            painter.setBrush(brush)

            painter.drawPath(path)


        result = pixmap.createHeuristicMask(False)

        return result

    def _pointer_offset(self):

        pointer_pos = self.mapToGlobal(self._metrics.pointer_viewport.top)

        return pointer_pos - self.pos()

    def move_pointer_to(self, pos):

        self._metrics.pointer_position = pos

        self.setGeometry(self._metrics.outer)

    def setCentralWidget(self, central_widget):

        self._central_widget = central_widget

        self._central_widget.setParent(self)
        self._central_widget.show()



    def centralWidget(self):
        return self._central_widget

    def _central_widget_size(self):
        result = self._central_widget.sizeHint()
        if self._central_widget.minimumWidth() == self._central_widget.maximumWidth():
            result.setWidth(self._central_widget.minimumWidth())
        if self._central_widget.minimumHeight() == self._central_widget.maximumHeight():
            result.setHeight(self._central_widget.minimumHeight())
        return result

    def _layout(self):


        self._metrics.from_inner(QRect(QPoint(0, 0), self._central_widget_size()))

        self.setGeometry(self._metrics.outer)

        self._central_widget.setGeometry(self._metrics.inner_viewport)

    def show(self):
        self._central_widget.show()
        super(SpeechBalloon, self).show()
        self._layout()

    def _rect_middle_sides(self, global_rect: QRect):

        width = global_rect.width()
        height = global_rect.height()
        width_2 = int(width / 2)
        height_2 = int(height / 2)

        result = {}

        for side in Side:
            if side == Side.BOTTOM:
                result[side] = QPoint(global_rect.x() + width_2, global_rect.y() + height)
            elif side == Side.TOP:
                result[side] = QPoint(global_rect.x() + width_2, global_rect.y())
            elif side == Side.LEFT:
                result[side] = QPoint(global_rect.x(), global_rect.y() + height_2)
            else:  # side == Side.RIGHT:
                result[side] = QPoint(global_rect.x() + width, global_rect.y() + height_2)

        return result

    @singledispatchmethod
    def showAt(self, point: QPoint, preferred_side=Side.RIGHT,
               side_priority=(Side.RIGHT, Side.LEFT, Side.BOTTOM, Side.TOP), target_screen=None):


        self._showAtList(QRect(point,QSize(1,1)), preferred_side=preferred_side, side_priority=side_priority,
                         target_screen = target_screen)

    @showAt.register
    def _showAtRect(self, rect: QRect, preferred_side=Side.RIGHT,
                    side_priority=(Side.RIGHT, Side.LEFT, Side.BOTTOM, Side.TOP), target_screen = None):
        """choose a side to show based on: maximal screen-window overlap, maximal screen button overlap
                                                   side priority or a general priority order"""

        best_side = None

        best_screen = target_screen
        if not target_screen:
            best_screen = self._best_screen_overlap(rect)

        side_by_overlap = self._calc_screen_overlap_all_sides(rect, best_screen)

        best_sides_key = max(side_by_overlap.keys())

        best_sides = side_by_overlap[best_sides_key]

        if preferred_side in best_sides:
            best_side = preferred_side
        else:
            for side in side_priority:
                if side in best_sides:
                    best_side = side
                    break

        side_positions = self._rect_middle_sides(rect)
        position = side_positions[best_side]

        self._setup_metrics(position, best_side, best_screen)
        self._layout()

        self.show()

    def _setup_metrics(self, position, side, screen):
        self._metrics.override_offset = 0
        self._metrics.pointer_position = position
        self._metrics.pointer_side = OPPOSITE_SIDES[side]
        self._metrics.from_inner(self._central_widget.geometry())
        screen_rect = screen.availableGeometry()
        distances = calc_side_distance_outside_rect(self._metrics.body_rect, screen_rect)
        offset = self._distances_to_offset(distances)
        self._metrics.override_offset = offset

    def _best_screen_overlap(self, rect):
        screen_button_overlap = self._calc_screen_by_overlap(rect)
        best_screen_for_button = screen_button_overlap[max(screen_button_overlap.keys())]
        return best_screen_for_button

    def _distances_to_offset(self, distances, extra = 5):

        offsets = [0, 0]
        for side, distance in distances.items():
            axis = SIDE_AXIS[side]
            offsets[axis] -= distance

        pointer_axis = SIDE_AXIS[self._metrics.pointer_side]
        offsets[pointer_axis] = 0

        if offsets[OPPOSITE_AXIS[pointer_axis]] > 0:
            offsets[OPPOSITE_AXIS[pointer_axis]] += 10
        elif offsets[OPPOSITE_AXIS[pointer_axis]] < 0:
            offsets[OPPOSITE_AXIS[pointer_axis]] -= 10


        return QPoint(*offsets)

    @staticmethod
    def _calc_screen_by_overlap(body_rect):
        result = {}
        for screen in QGuiApplication.screens():
            screen_rect = screen.availableGeometry()
            intersection = screen_rect.intersected(body_rect)
            intersection_area = intersection.width() * intersection.height()

            # note ties by intersection are are removed by default
            result[intersection_area] = screen
        return result

    def _calc_screen_overlap_all_sides(self, rect, target_screen):

        result = {}
        side_position = self._rect_middle_sides(rect)
        for side, middle_pos in side_position.items():
            opposite_side = OPPOSITE_SIDES[side]

            metrics = BalloonMetrics(pointer_side=opposite_side)
            metrics.from_inner(self._central_widget.geometry())
            metrics.pointer_position = middle_pos

            outer_rect = metrics.outer
            screen_by_overlap = self._calc_screen_by_overlap(outer_rect)

            max_area = outer_rect.width() * outer_rect.height()
            for intersection_area, screen in screen_by_overlap.items():
                if not screen or screen == target_screen:
                    result.setdefault(intersection_area / max_area, []).append(side)
        return result

    @staticmethod
    def find_side_outside_rect_offset(test_rect: QRect, target_rect: QRect):
        intersection = test_rect.intersected(target_rect)

        result = {}
        for side in Side:
            inter_side = rect_get_side(intersection, side)
            test_side = rect_get_side(test_rect, side)
            if inter_side != test_side:
                result[side] = inter_side - test_side

        return result

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        if self._owner:
            self._owner.leaveEvent(a0)


class DoubleLabel(QFrame):

    def __init__(self, text=('',), parent=None):
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
        self.updateGeometry()

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

        self.updateGeometry()

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

        self.setLabels([x, y])


if __name__ == '__main__':


    app = MyApplication(sys.argv)

    window2 = SpeechBalloon()
    window2.cornerRadius = 3

    app.setActiveWindow(window2)

    label = MousePositionLabel(parent=window2)

    window2.setCentralWidget(label)
    window2.show()

    app.exec_()
