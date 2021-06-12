from enum import IntEnum
from math import ceil, sqrt, floor
from typing import NamedTuple

from PyQt5.QtCore import QPoint, QRect, QSize
from PyQt5.QtWidgets import QWidget



class Pointer(NamedTuple):
    left: QPoint
    top: QPoint
    bottom: QPoint


class InvalidStateError(ValueError):
    pass


def rect_right(rect: QRect):
    return rect.left() + rect.width()


def rect_bottom(rect: QRect):
    return rect.top() + rect.height()


def rect_bottom_right(rect: QRect):
    return QPoint(rect_bottom(rect), rect_right(rect))


def new_rect_lefttop_rightbottom(left_top, right_bottom):
    width = right_bottom.x() - left_top.x()
    height = right_bottom.y() - left_top.x()
    return QRect(left_top, QSize(width, height))


def new_rect_xleftytop_xrightybottom(xleft, ytop, xright, ybottom):
    width = xright - xleft
    height = ybottom - ytop
    return QRect(QPoint(xleft, ytop), QSize(width, height))


def display_rect(rect, name=''):
    top___ = str(rect.top()).rjust(8)
    left__ = rect.left()
    right_ = rect_right(rect)
    bottom = rect_bottom(rect)

    result = f'''
             {name}

             left  |  {left__}     
                   |                      
    {top___} top - ----------------------
                   |                    |
                   |                    |
                   ---------------------- -- bottom {bottom}
                                        |
                                 right  |  {right_}

    '''

    print(result)


class Side(IntEnum):
    TOP = 1
    LEFT = 0
    RIGHT = 2
    BOTTOM = 3


def _qrect_get_side(rect: QRect, side: Side) -> int:
    if side == Side.TOP:
        result = rect.top()
    elif side == Side.BOTTOM:
        result = rect.top() + rect.height()
    elif side == Side.LEFT:
        result = rect.left()
    else:
        result = rect.left() + rect.width()
    return result


class Axis(IntEnum):
    X = 0,
    Y = 1


POINTER_AXIS = {
    Side.TOP: Axis.Y,
    Side.RIGHT: Axis.X,
    Side.BOTTOM: Axis.Y,
    Side.LEFT: Axis.X
}

OPPOSITE_AXIS = {
    Axis.X: Axis.Y,
    Axis.Y: Axis.X
}

POINTER_SIDES = {
    Side.TOP: (Side.BOTTOM, Side.TOP),
    Side.RIGHT: (Side.LEFT, Side.RIGHT),
    Side.BOTTOM: (Side.TOP, Side.BOTTOM),
    Side.LEFT: (Side.RIGHT, Side.LEFT)
}

# note these are ordered: top  - bottom, left - right
NON_POINTER_SIDES = {
    Side.TOP: (Side.LEFT, Side.RIGHT),
    Side.RIGHT: (Side.TOP, Side.BOTTOM),
    Side.BOTTOM: (Side.LEFT, Side.RIGHT),
    Side.LEFT: (Side.TOP, Side.BOTTOM)
}

SIGNS = [-1, -1, 1, 1]

RECT_NUM_SIDES = 4


class BalloonMetrics:

    def __init__(self, corner_radius=3, pointer_side=Side.RIGHT, pointer_height=10, pointer_width=20):
        self.corner_radius = corner_radius
        self.pointer_side = pointer_side
        self.pointer_height = pointer_height
        self.pointer_width = pointer_width
        self.antialias_margin = 1
        self.pointer_position = 0.5

        self.inner = None
        self.outer = None
        self._pointer_rect = None
        self.pointer = None

    # TODO replace reset with property change?
    # TODO recalc on last rect set?
    def reset(self):
        self.inner = None
        self.outer = None
        self._pointer_rect = None
        self.pointer = None

    def _get_corner_margin(self):
        result = self.corner_radius / sqrt(2)
        result = int(ceil(result))

        return result

    @staticmethod
    def _add_margins(rect: QRect, margin, multiplier=1):
        margins = [margin * multiplier] * 4
        margins = [margins[i] * SIGNS[i] for i in range(RECT_NUM_SIDES)]

        return rect.adjusted(*margins)

    def _add_central_widget_margins(self, rect: QRect, multiplier=1):
        return self._add_margins(rect, self._get_corner_margin(), multiplier)

    def _add_pointer_margin(self, rect: QRect, multiplier=1):

        signs = [SIGNS[i] * multiplier for i in range(RECT_NUM_SIDES)]
        margin = [self.pointer_height] * RECT_NUM_SIDES

        margin = [margin[i] * signs[i] for i in range(RECT_NUM_SIDES)]

        mask = [0] * RECT_NUM_SIDES
        mask[self.pointer_side] = 1

        pointer_margins = [margin[i] * mask[i] for i in range(RECT_NUM_SIDES)]

        result = rect.adjusted(*pointer_margins)

        return result

    def _add_antialias_margin(self, rect: QRect, multiplier=1):

        return self._add_margins(rect, self.antialias_margin, multiplier)

    def from_inner(self, rect: QRect):

        self.inner = QRect(rect)

        pointer_box = {
            Axis.X: [],
            Axis.Y: []
        }

        result = self._add_central_widget_margins(rect)

        pointer_bottom = _qrect_get_side(result, self.pointer_side)
        pointer_box[POINTER_AXIS[self.pointer_side]].append(pointer_bottom)

        result = self._add_pointer_margin(result)

        pointer_top = _qrect_get_side(result, self.pointer_side)
        pointer_box[POINTER_AXIS[self.pointer_side]].append(pointer_top)

        for orthogonal_side in NON_POINTER_SIDES[self.pointer_side]:
            orthogonal_axis = OPPOSITE_AXIS[POINTER_AXIS[self.pointer_side]]
            pointer_box[orthogonal_axis].append(_qrect_get_side(result, orthogonal_side))

        self._pointer_rect = new_rect_xleftytop_xrightybottom(min(pointer_box[Axis.X]), min(pointer_box[Axis.Y]),
                                                              max(pointer_box[Axis.X]), max(pointer_box[Axis.Y]))

        result = self._add_antialias_margin(result)

        self.outer = result

        self._calc_pointer_position()

        return self

    def from_outer(self, rect: QRect):

        self.outer = QRect(rect)

        pointer_box = {
            Axis.X: [],
            Axis.Y: []
        }

        result = self._add_antialias_margin(rect, multiplier=-1)

        pointer_top = _qrect_get_side(result, self.pointer_side)
        pointer_box[POINTER_AXIS[self.pointer_side]].append(pointer_top)

        for orthogonal_side in NON_POINTER_SIDES[self.pointer_side]:
            orthogonal_axis = OPPOSITE_AXIS[POINTER_AXIS[self.pointer_side]]
            pointer_box[orthogonal_axis].append(_qrect_get_side(result, orthogonal_side))

        result = self._add_pointer_margin(result, multiplier=-1)

        pointer_bottom = _qrect_get_side(result, self.pointer_side)
        pointer_box[POINTER_AXIS[self.pointer_side]].append(pointer_bottom)

        self._pointer_rect = new_rect_xleftytop_xrightybottom(min(pointer_box[Axis.X]), min(pointer_box[Axis.Y]),
                                                              max(pointer_box[Axis.X]), max(pointer_box[Axis.Y]))

        result = self._add_central_widget_margins(result, multiplier=-1)

        self.inner = result

        self._calc_pointer_position()

        return self

    def _calc_pointer_position(self):

        self._raise_invalid_if_required()

        movement_sides = NON_POINTER_SIDES[self.pointer_side]
        values = [_qrect_get_side(self._pointer_rect, side) for side in movement_sides]

        min_left, max_right = values

        pointer_width_2 = self.pointer_width/2

        min_left += self.corner_radius
        max_right -= self.corner_radius

        if max_right < min_left:
            left = min_left
            right = max_right

            centre = min_left + ((max_right-min_left) / 2)
        else:
            range_left = min_left + pointer_width_2
            range_right = max_right - pointer_width_2

            centre_range = range_right - range_left
            centre = range_left + int(floor(centre_range * self.pointer_position))

            left = centre - pointer_width_2
            right = centre + pointer_width_2


        display_rect(self._pointer_rect, 'pointer rect')
        pointer_sides = [_qrect_get_side(self._pointer_rect, side) for side in POINTER_SIDES[self.pointer_side]]
        bottom, top = pointer_sides

        pointer_axis = POINTER_AXIS[self.pointer_side]
        range_axis = OPPOSITE_AXIS[pointer_axis]

        pointer_centre = [0] * 2
        pointer_left = [0] * 2
        pointer_right = [0] * 2

        pointer_centre[pointer_axis] = top
        pointer_centre[range_axis] = int(centre)

        pointer_left[pointer_axis] = bottom
        pointer_left[range_axis] = int(left)

        pointer_right[pointer_axis] = bottom
        pointer_right[range_axis] = int(right)

        self.pointer = QPoint(*pointer_left), QPoint(*pointer_centre), QPoint(*pointer_right)

    def _raise_invalid_if_required(self):
        if self._pointer_rect is None:
            raise InvalidStateError('Error: call from_inner or from_outer first!')


def test_expand():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10, 100))
    assert QRect(QPoint(-3, -3), QSize(16, 106)) == metrics._add_central_widget_margins(test_rect)
    assert QRect(QPoint(0, 0), QSize(20, 100)) == metrics._add_pointer_margin(test_rect)
    assert QRect(QPoint(-1, -1), QSize(12, 102)) == metrics._add_antialias_margin(test_rect)
    assert QRect(QPoint(-4, -4), QSize(28, 108)) == metrics.from_inner(test_rect).outer


def test_reduce():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10, 100))

    assert QRect(QPoint(1, 1), QSize(8, 98)) == metrics._add_antialias_margin(test_rect, multiplier=-1)
    assert QRect(QPoint(3, 3), QSize(4, 94)) == metrics._add_central_widget_margins(test_rect, multiplier=-1)
    assert QRect(QPoint(0, 0), QSize(0, 100)) == metrics._add_pointer_margin(test_rect, multiplier=-1)
    assert test_rect == metrics.from_outer(QRect(QPoint(-4, -4), QSize(28, 108))).inner


def test_expand_sides():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    expected = {
        Side.TOP: QRect(QPoint(0, -10), QSize(200, 110)),
        Side.RIGHT: QRect(QPoint(0, 0), QSize(210, 100)),
        Side.BOTTOM: QRect(QPoint(0, 0), QSize(200, 110)),
        Side.LEFT: QRect(QPoint(-10, 0), QSize(210, 100))
    }

    for side, expanded in expected.items():
        metrics.pointer_side = side
        assert expanded == metrics._add_pointer_margin(test_rect)


def test_rects_from_outer():

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    expected_for_side = {
        Side.TOP: new_rect_xleftytop_xrightybottom(-3, -13, 203, -3),
        Side.RIGHT: new_rect_xleftytop_xrightybottom(203, -3, 213, 103),
        Side.BOTTOM: new_rect_xleftytop_xrightybottom(-3, 103, 203, 113),
        Side.LEFT: new_rect_xleftytop_xrightybottom(-13, -3, -3, 103)
    }

    for side in expected_for_side:

        metrics = BalloonMetrics(pointer_side=side)
        metrics.from_inner(test_rect)

        # display_rect(metrics._pointer_rect)
        assert metrics._pointer_rect == expected_for_side[side]


def test_inners_from_outer():

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    outer_for_side = {
        Side.TOP: new_rect_xleftytop_xrightybottom(-4, -14, 204, 104),
        Side.RIGHT: new_rect_xleftytop_xrightybottom(-4, -4, 214, 104),
        Side.BOTTOM: new_rect_xleftytop_xrightybottom(-4, -4, 204, 114),
        Side.LEFT: new_rect_xleftytop_xrightybottom(-14, -4, 204, 104)
    }

    for side, outer in outer_for_side.items():

        metrics = BalloonMetrics(pointer_side=side)
        metrics.from_outer(outer)

        assert metrics.inner == test_rect


def test_pointer_rects_from_outer():

    outer_for_side = {
        Side.TOP: new_rect_xleftytop_xrightybottom(-4, -14, 204, 104),
        Side.RIGHT: new_rect_xleftytop_xrightybottom(-4, -4, 214, 104),
        Side.BOTTOM: new_rect_xleftytop_xrightybottom(-4, -4, 204, 114),
        Side.LEFT: new_rect_xleftytop_xrightybottom(-14, -4, 204, 104)
    }

    expected_for_side = {
        Side.TOP: new_rect_xleftytop_xrightybottom(-3, -13, 203, -3),
        Side.RIGHT: new_rect_xleftytop_xrightybottom(203, -3, 213, 103),
        Side.BOTTOM: new_rect_xleftytop_xrightybottom(-3, 103, 203, 113),
        Side.LEFT: new_rect_xleftytop_xrightybottom(-13, -3, -3, 103)
    }

    for side, outer in outer_for_side.items():
        expected = expected_for_side[side]

        metrics = BalloonMetrics(pointer_side=side)
        metrics.from_outer(outer)

        assert metrics._pointer_rect == expected


def test_reset():
    import pytest
    metrics = BalloonMetrics()

    assert metrics.inner is None
    assert metrics.outer is None
    assert metrics._pointer_rect is None

    assert metrics.pointer == None

    metrics.from_outer(QRect(0, 0, 100, 200))

    assert metrics.inner is not None
    assert metrics.outer is not None
    assert metrics._pointer_rect is not None
    assert metrics.pointer is not None

    metrics.reset()

    assert metrics.inner is None
    assert metrics.outer is None
    assert metrics._pointer_rect is None
    assert metrics.pointer is None


def test_pointer_positions():
    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    expected = {
        (0.0, Side.TOP): Pointer(QPoint(0, -3), QPoint(10, -13), QPoint(20, -3)),
        (0.0, Side.RIGHT): Pointer(QPoint(203, 0), QPoint(213, 10), QPoint(203, 20)),
        (0.0, Side.BOTTOM): Pointer(QPoint(0, 103), QPoint(10, 113), QPoint(20, 103)),
        (0.0, Side.LEFT): Pointer(QPoint(-3, 0), QPoint(-13, 10), QPoint(-3, 20)),

        (0.5, Side.TOP): Pointer(QPoint(90, -3), QPoint(100, -13), QPoint(110, -3)),
        (0.5, Side.RIGHT): Pointer(QPoint(203, 40), QPoint(213, 50), QPoint(203, 60)),
        (0.5, Side.BOTTOM): Pointer(QPoint(90, 103), QPoint(100, 113), QPoint(110, 103)),
        (0.5, Side.LEFT): Pointer(QPoint(-3, 40), QPoint(-13, 50), QPoint(-3, 60)),

        (1.0, Side.TOP): Pointer(QPoint(180, -3), QPoint(190, -13), QPoint(200, -3)),
        (1.0, Side.RIGHT): Pointer(QPoint(203, 80), QPoint(213, 90), QPoint(203, 100)),
        (1.0, Side.BOTTOM): Pointer(QPoint(180, 103), QPoint(190, 113), QPoint(200, 103)),
        (1.0, Side.LEFT): Pointer(QPoint(-3, 80), QPoint(-13, 90), QPoint(-3, 100)),
    }

    for (percentage, side), expected in expected.items():

        metrics = BalloonMetrics(pointer_side=side)
        metrics.pointer_position = percentage
        metrics.from_inner(test_rect)

        # display_rect(metrics._pointer_rect, f'pointer rect {side.name}')

        assert expected == metrics.pointer


def _run_tests():
    import pytest
    pytest.main([__file__])


if __name__ == '__main__':
    _run_tests()
