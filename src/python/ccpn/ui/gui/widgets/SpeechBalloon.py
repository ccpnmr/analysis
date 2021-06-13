import sys
from math import sqrt, ceil

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, Qt, QRect, QPoint, pyqtProperty, QTimer, QEvent, QSize
from PyQt5.QtGui import QPainterPath, QPainter, QPen, QColor, QBrush, QPolygon, QPolygonF, QPixmap, QPalette, QCursor, \
    QFontMetrics
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QLayout, QFrame

from BalloonMetrics import Side, BalloonMetrics

from BalloonMetrics import Side, BalloonMetrics, OPPOSITE_SIDES

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


# class Pointer(IntEnum):
#     LEFT = 0
#     MIDDLE = 1
#     RIGHT = 2




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

        # layout = QGridLayout()
        # layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(0)
        # layout.setSizeConstraint(QLayout.SetFixedSize)
        # self.setLayout(layout)

        self._pointer_height = 10
        self._pointer_width = 20
        self._pointer_side = side
        self._metrics = BalloonMetrics()

        self._percentage = percentage / 100.0

        self._corner_radius = 3
        self._pen_width = 0

        self._owner = owner

        self._central_widget:QWidget = None

        # self.setMargins()

    def event(self, e: QtCore.QEvent) -> bool:
        if e.type() == QEvent.LayoutRequest:
            ic('got layout')
            ic(self.geometry(),self._central_widget.geometry())
            self._layout()
            result = True
        else:
            result = super(SpeechBalloon, self).event(e)

        if e.type() == QEvent.LayoutRequest:
            ic('after layout')
            ic(self.geometry(),self._central_widget.geometry())

        return result

    # def get_central_widget_geometry(self):
    #     result = QSize(self._central_widget.sizeHint())
    #     if self._central_widget
    #


    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:


        # self.set_central_widget_geometry()
        ic('resize before', self.geometry(), self._central_widget.geometry())
        super(SpeechBalloon, self).resizeEvent(a0)
        ic('resize after', self.geometry(), self._central_widget.geometry())

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
        self._metrics.pointer_side = side
        self._metrics.reset()
        self.update()

    @pyqtProperty(float)
    def pointerSideOffset(self):
        return self._percentage

    @pointerSideOffset.setter
    def pointerSideOffset(self, percentage):
        self._percentage = percentage
        self.update()


    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:

        self.setMask(self.window_mask())

        painterPath = self.window_path()

        with PaintContext(QPainter(self)) as painter:

            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

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

        self._metrics.pointer_side = self._pointer_side

        self._metrics.from_outer(self.frameGeometry())

        path = QPainterPath()
        path.addRoundedRect(QRectF(self._metrics.body_rect_viewport), self._corner_radius, self._corner_radius)

        pointer_polygon = QPolygonF(QPolygon(self._metrics.pointer_viewport))
        path.addPolygon(pointer_polygon)

        path = path.simplified()

        return path

    def window_mask(self):
        path = self.window_path()

        pixmap = QPixmap(int(path.boundingRect().width() + 2), int(path.boundingRect().height() + 2))

        with PaintContext(QPainter(pixmap)) as painter:

            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.HighQualityAntialiasing)

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

        ic(self.geometry())

    def show(self):
        self._central_widget.show()
        super(SpeechBalloon, self).show()
        self._layout()


    def showAt(self, screen, side_pos_alternatives):

        # for side, pos in side_pos_alternatives:
        #     ic(side_pos_alternatives)
        #     ic(self._get_side_preferences(screen, side, pos))

        side, pointer_pos = side_pos_alternatives[0]

        self._metrics.pointer_side = OPPOSITE_SIDES[side]
        self._layout()
        self._metrics.pointer_position = pointer_pos


        # margins = self._get_margins()
        # size_hint = self.centralWidget().sizeHint()
        #
        # geometry = QRect()
        # geometry.setSize(size_hint)
        #
        #
        # geometry.adjust(*margins)
        # pointer_pos_on_geometry = self._get_pointer_position(geometry, on_border=True)
        #
        # offset = pointer_pos - pointer_pos_on_geometry
        #
        # geometry.translate(offset.x(), offset.y())
        #
        # #  there's an error in the layout...
        # # these are approximately correct till we correct it
        # CORRECTIONS = {
        #     Side.BOTTOM: (-1, -1),
        #     Side.RIGHT: (-1, -1),
        #     Side.TOP: (-1, 0),
        #     Side.LEFT: (0, -1)
        # }
        #
        # correction = CORRECTIONS[self._pointer_side]
        # scale = self._get_corner_margins()[0] + 1
        # geometry.translate(scale * correction[0], scale * correction[1])
        #
        # self.setGeometry(geometry)

        self.show()


    @staticmethod
    def _get_screen_side(screen, side):
        screen_rect = screen.availableGeometry()

        # TODO: sides are in a strange order should be top left bottom right
        # TODO: add side selection by x and y into Side also opposites
        screen_coords = [screen_rect.top(), screen_rect.left(),
                         screen_rect.right(), screen_rect.bottom()]

        return screen_coords[side]

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
        new_margins = self._get_corner_margins(multiplier)
        new_margins[self._pointer_side] += (self._pointer_height * multiplier)
        return new_margins

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
