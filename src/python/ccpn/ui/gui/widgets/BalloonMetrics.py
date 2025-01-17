
# TODO move out rect code
from enum import IntEnum
from math import ceil, sqrt, floor
from typing import NamedTuple, Optional, Sequence

from PyQt5.QtCore import QPoint, QRect, QSize



class Pointer(NamedTuple):
    left: QPoint
    top: QPoint
    bottom: QPoint

    class POINTS(IntEnum):
        LEFT = 0
        TOP = 1
        RIGHT = 2


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


OPPOSITE_SIDES = {
    Side.TOP: Side.BOTTOM,
    Side.RIGHT: Side.LEFT,
    Side.BOTTOM: Side.TOP,
    Side.LEFT: Side.RIGHT
}


def rect_get_side(rect: QRect, side: Side) -> int:
    if side == Side.TOP:
        result = rect.top()
    elif side == Side.BOTTOM:
        result = rect.top() + rect.height()
    elif side == Side.LEFT:
        result = rect.left()
    else:
        result = rect.left() + rect.width()
    return result


def calc_side_distance_outside_rect(test_rect: QRect, target_rect: QRect):
    intersection = test_rect.intersected(target_rect)

    result = {}
    for side in Side:
        inter_side = rect_get_side(intersection, side)
        test_side = rect_get_side(test_rect, side)
        if inter_side != test_side:
            result[side] = test_side - inter_side

    return result


class Axis(IntEnum):
    X = 0,
    Y = 1


SIDE_AXIS = {
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


class SubscriptableQPoint:
    def __init__(self, target):
        self._target = target

    def __getitem__(self, item):

        if item == Axis.X:
            result = self._target.x()
        elif item == Axis.Y:
            result = self._target.y()
        else:
            raise IndexError(f'Error bad index for QPoint {item}')

        return result

    def __setitem__(self, item, value):

        if item == Axis.X:
            self._target.setX(value)
        elif item == Axis.Y:
            self._target.setY(value)
        else:
            raise IndexError(f'Error bad index for QPoint {item}')

    def __str__(self):
        return f'[{self._target.x()},{self._target.y()}]'


class BalloonMetrics:

    def __init__(self, corner_radius=3, pointer_side=Side.RIGHT, pointer_height=10, pointer_width=20):
        self.corner_radius: int = corner_radius
        self.pointer_side: Side = pointer_side
        self.pointer_height: int = pointer_height
        self.pointer_width: int = pointer_width
        self.antialias_margin: int = 1
        self.pointer_alignment: float = 0.5
        self.pointer_position: Optional[QPoint] = None
        self.override_offset: Optional[QPoint] = None


        self._inner: Optional[QRect] = None
        self._outer: Optional[QRect] = None
        self._body_rect: Optional[QRect] = None
        self._pointer_rect: Optional[QRect] = None
        self._pointer: Optional[Pointer] = None


    # TODO replace reset with property change?
    # TODO recalc on last rect set?


    def reset(self):
        self._inner = None
        self._outer = None
        self._body_rect = None
        self._pointer_rect = None
        self._pointer = None
        self.override_offset = None

    @property
    def outer_viewport(self):
        self._raise_invalid_if_required()

        translation = self._outer.topLeft() * -1

        return self._outer.translated(translation)

    @property
    def inner_viewport(self):
        self._raise_invalid_if_required()

        translation = self._outer.topLeft() * -1

        return self._inner.translated(translation)

    @property
    def body_rect_viewport(self):
        self._raise_invalid_if_required()

        translation = self._outer.topLeft() * -1

        return self._body_rect.translated(translation)

    def _pointer_rect_viewport(self):

        translation = self._outer.topLeft() * -1

        return self._pointer_rect.translated(translation)

    @property
    def pointer_viewport(self):
        self._raise_invalid_if_required()

        pointer_rect_viewport = self._pointer_rect_viewport()

        min_left_pointer, max_right_pointer = self._calc_minleft_maxright_pointer_base(pointer_rect_viewport)

        translation = self._outer.topLeft() * -1
        result = [point + translation for point in self._pointer]

        result = self._add_override_offset_pointer(result)

        axis = OPPOSITE_AXIS[SIDE_AXIS[self.pointer_side]]

        left = SubscriptableQPoint(result[Pointer.POINTS.LEFT])
        right = SubscriptableQPoint(result[Pointer.POINTS.RIGHT])

        if left[axis] < min_left_pointer:

            left[axis] = min_left_pointer
            right[axis] = left[axis] + self.pointer_width

            if right[axis] > max_right_pointer:
                right[axis] = max_right_pointer

        elif right[axis] > max_right_pointer:

            right[axis] = max_right_pointer
            left[axis] = right[axis] - self.pointer_width
            if left[axis] < min_left_pointer:
                left[axis] = min_left_pointer

        result = Pointer(*result)

        return result

    def _calc_minleft_maxright_pointer_base(self, pointer_rect_viewport):

        movement_sides = NON_POINTER_SIDES[self.pointer_side]

        values = [rect_get_side(pointer_rect_viewport, side) for side in movement_sides]

        min_left_pointer, max_right_pointer = values

        min_left_pointer += self.corner_radius
        max_right_pointer -= self.corner_radius

        return min_left_pointer, max_right_pointer

    @property
    def outer(self):
        self._raise_invalid_if_required()

        result = QRect(self._outer)

        result = self._translate_to_pointer(result)

        return self._add_override_offset_rect(result)


    def _global_pointer_offset(self):
        result = QPoint()
        if self.pointer_position:
            result = self.pointer_position - self._pointer.top
        return result

    def _translate_to_pointer(self, rect: QRect):
        pointer_offset = self._global_pointer_offset()

        rect.translate(pointer_offset)

        return rect

    def _add_override_offset_rect(self, rect: QRect):

        if self.override_offset:
            rect.translate(self.override_offset)

        return rect

    def _add_override_offset_pointer(self, points: Sequence[QPoint]):

        if self.override_offset:
            points = [QPoint(point) - self.override_offset for point in points]

        return points

    @property
    def inner(self):
        self._raise_invalid_if_required()

        result = QRect(self._inner)

        result = self._translate_to_pointer(result)

        return self._add_override_offset_rect(result)

    @property
    def body_rect(self):
        self._raise_invalid_if_required()

        result = QRect(self._body_rect)

        result = self._translate_to_pointer(result)

        return self._add_override_offset_rect(result)

    @property
    def pointer(self):
        self._raise_invalid_if_required()

        offset = self._global_pointer_offset()

        points = [QPoint(point) + offset for point in self._pointer]

        result = Pointer(*points)

        return self._add_override_offset_pointer(result)

    @property
    def pointer_rect(self):
        self._raise_invalid_if_required()

        return QRect(self._pointer_rect)

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

        if rect != self._inner:

            self._inner = QRect(rect)

            pointer_box = {
                Axis.X: [],
                Axis.Y: []
            }

            result = self._add_central_widget_margins(rect)

            self._body_rect = QRect(result)

            pointer_bottom = rect_get_side(result, self.pointer_side)
            pointer_box[SIDE_AXIS[self.pointer_side]].append(pointer_bottom)

            result = self._add_pointer_margin(result)

            pointer_top = rect_get_side(result, self.pointer_side)
            pointer_box[SIDE_AXIS[self.pointer_side]].append(pointer_top)

            for orthogonal_side in NON_POINTER_SIDES[self.pointer_side]:
                orthogonal_axis = OPPOSITE_AXIS[SIDE_AXIS[self.pointer_side]]
                pointer_box[orthogonal_axis].append(rect_get_side(result, orthogonal_side))

            self._pointer_rect = new_rect_xleftytop_xrightybottom(min(pointer_box[Axis.X]), min(pointer_box[Axis.Y]),
                                                                  max(pointer_box[Axis.X]), max(pointer_box[Axis.Y]))

            result = self._add_antialias_margin(result)

            self._outer = result

            self._calc_pointer_position()

        return self

    def from_outer(self, rect: QRect):

        if rect != self._outer:
            self._outer = QRect(rect)

            pointer_box = {
                Axis.X: [],
                Axis.Y: []
            }

            result = self._add_antialias_margin(rect, multiplier=-1)

            pointer_top = rect_get_side(result, self.pointer_side)
            pointer_box[SIDE_AXIS[self.pointer_side]].append(pointer_top)

            for orthogonal_side in NON_POINTER_SIDES[self.pointer_side]:
                orthogonal_axis = OPPOSITE_AXIS[SIDE_AXIS[self.pointer_side]]
                pointer_box[orthogonal_axis].append(rect_get_side(result, orthogonal_side))

            result = self._add_pointer_margin(result, multiplier=-1)

            pointer_bottom = rect_get_side(result, self.pointer_side)
            pointer_box[SIDE_AXIS[self.pointer_side]].append(pointer_bottom)

            self._pointer_rect = new_rect_xleftytop_xrightybottom(min(pointer_box[Axis.X]), min(pointer_box[Axis.Y]),
                                                                  max(pointer_box[Axis.X]), max(pointer_box[Axis.Y]))

            self._body_rect = QRect(result)

            result = self._add_central_widget_margins(result, multiplier=-1)

            self._inner = result

            self._calc_pointer_position()

        return self

    def _calc_pointer_position(self):

        self._raise_invalid_if_required()

        min_left, max_right = self._calc_minleft_maxright_pointer_base(self._pointer_rect)

        pointer_width_2 = self.pointer_width/2

        if max_right < min_left:
            left = min_left
            right = max_right

            centre = min_left + ((max_right-min_left) / 2)
        else:
            range_left = min_left + pointer_width_2
            range_right = max_right - pointer_width_2

            centre_range = range_right - range_left
            centre = range_left + int(floor(centre_range * self.pointer_alignment))

            left = centre - pointer_width_2
            right = centre + pointer_width_2

        pointer_sides = [rect_get_side(self._pointer_rect, side) for side in POINTER_SIDES[self.pointer_side]]
        bottom, top = pointer_sides

        pointer_axis = SIDE_AXIS[self.pointer_side]
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

        self._pointer = Pointer(QPoint(*pointer_left), QPoint(*pointer_centre), QPoint(*pointer_right))

    def _raise_invalid_if_required(self):
        if self._pointer_rect is None:
            raise InvalidStateError('Error: call from_inner or from_outer first!')


def test_expand():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10, 100))
    assert QRect(QPoint(-3, -3), QSize(16, 106)) == metrics._add_central_widget_margins(test_rect)
    assert QRect(QPoint(0, 0), QSize(20, 100)) == metrics._add_pointer_margin(test_rect)
    assert QRect(QPoint(-1, -1), QSize(12, 102)) == metrics._add_antialias_margin(test_rect)
    assert QRect(QPoint(-4, -4), QSize(28, 108)) == metrics.from_inner(test_rect)._outer


def test_reduce():
    metrics = BalloonMetrics()

    test_rect = QRect(QPoint(0, 0), QSize(10, 100))

    assert QRect(QPoint(1, 1), QSize(8, 98)) == metrics._add_antialias_margin(test_rect, multiplier=-1)
    assert QRect(QPoint(3, 3), QSize(4, 94)) == metrics._add_central_widget_margins(test_rect, multiplier=-1)
    assert QRect(QPoint(0, 0), QSize(0, 100)) == metrics._add_pointer_margin(test_rect, multiplier=-1)
    assert test_rect == metrics.from_outer(QRect(QPoint(-4, -4), QSize(28, 108)))._inner


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

        assert metrics.pointer_rect == expected_for_side[side]


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

        assert metrics.pointer_rect == expected


def test_viewport_views():
    test_rect = QRect(QPoint(0, 0), QSize(200, 100))
    expected_outer = QRect(QPoint(0, 0), QSize(218, 108))
    expected_inner = QRect(QPoint(4, 4), QSize(200, 100))
    expected_pointer = Pointer(QPoint(207, 44), QPoint(217, 54), QPoint(207, 64))

    metrics = BalloonMetrics()
    metrics.from_inner(test_rect)

    assert metrics.outer_viewport == expected_outer
    assert metrics.inner_viewport == expected_inner
    assert metrics.pointer_viewport == expected_pointer


def test_reset():
    import pytest
    metrics = BalloonMetrics()

    # noinspection PyStatementEffect
    def check_raises():
        with pytest.raises(InvalidStateError):
            metrics.inner

        with pytest.raises(InvalidStateError):
            metrics.outer

        with pytest.raises(InvalidStateError):
            metrics.pointer_rect

        with pytest.raises(InvalidStateError):
            metrics.pointer

        with pytest.raises(InvalidStateError):
            metrics.body_rect

    check_raises()

    metrics.from_outer(QRect(0, 0, 100, 200))

    assert metrics.inner is not None
    assert metrics.outer is not None
    assert metrics.pointer_rect is not None
    assert metrics.pointer is not None

    metrics.reset()

    check_raises()


def test_body_rect():
    test_rect = QRect(QPoint(0, 0), QSize(200, 100))
    expected = QRect(QPoint(-3, -3), QSize(206, 106))

    expected_local = {
        Side.TOP: QRect(QPoint(1, 11), QSize(206, 106)),
        Side.LEFT: QRect(QPoint(11, 1), QSize(206, 106)),
        Side.BOTTOM: QRect(QPoint(1, 1), QSize(206, 106)),
        Side.RIGHT: QRect(QPoint(1, 1), QSize(206, 106))
    }

    for side in Side:
        metrics = BalloonMetrics(pointer_side=side)
        metrics.from_inner(test_rect)

        assert expected == metrics.body_rect
        assert expected_local[side] == metrics.body_rect_viewport


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
        metrics.pointer_alignment = percentage
        metrics.from_inner(test_rect)

        assert expected == metrics.pointer


def test_pointer_position():

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    expected_pointer = Pointer(QPoint(90, 90), QPoint(100, 100), QPoint(90, 110))
    expected_outer = QRect(QPoint(-117, 46), QSize(218, 108))
    expected_inner = QRect(QPoint(-113, 50), QSize(200, 100))
    expected_body = QRect(QPoint(-116, 47), QSize(206, 106))

    metrics = BalloonMetrics()
    metrics.from_inner(test_rect)
    metrics.pointer_position = QPoint(100, 100)

    assert expected_pointer == metrics.pointer
    assert expected_outer == metrics.outer
    assert expected_inner == metrics.inner
    assert expected_body == metrics.body_rect


def test_find_side_outside_rect_offset():

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))
    inside_rect = QRect(QPoint(1, 1), QSize(198, 98))
    above_rect = QRect(QPoint(1, -1), QSize(198, 98))
    below_rect = QRect(QPoint(0, 0), QSize(200, 101))
    above_below_rect = QRect(QPoint(0, -1), QSize(200, 102))
    outside_rect = QRect(QPoint(-1, -1), QSize(202, 102))

    assert calc_side_distance_outside_rect(inside_rect, test_rect) == {}
    assert calc_side_distance_outside_rect(above_rect, test_rect) == {Side.TOP: -1}
    assert calc_side_distance_outside_rect(below_rect, test_rect) == {Side.BOTTOM: 1}
    assert calc_side_distance_outside_rect(above_below_rect, test_rect) == {Side.TOP: -1, Side.BOTTOM: 1}
    assert calc_side_distance_outside_rect(outside_rect, test_rect) == {Side.TOP: -1, Side.BOTTOM: 1,
                                                                        Side.LEFT: -1, Side.RIGHT: 1}


def test_override_offset():

    test_rect = QRect(QPoint(0, 0), QSize(200, 100))

    offset = (10, -5)

    expected_inner = QRect(QPoint(10, -5), QSize(200, 100))
    expected_outer = QRect(QPoint(6, -19), QSize(208, 118))
    expected_body_rect = QRect(QPoint(7, -8), QSize(206, 106))

    point_offset = QPoint(*offset)

    metrics = BalloonMetrics(pointer_side=Side.TOP)
    metrics.from_inner(test_rect)
    metrics.override_offset = point_offset

    assert metrics.inner == expected_inner
    assert metrics.outer == expected_outer
    assert metrics.body_rect == expected_body_rect


def _run_tests():
    import pytest
    # pytest.main(['%s::test_reset' % __file__])
    pytest.main([__file__, '-vv'])


if __name__ == '__main__':
    _run_tests()
