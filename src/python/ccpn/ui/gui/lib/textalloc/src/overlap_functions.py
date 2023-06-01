"""
Module Documentation here

Modified from the original by Christoffer Kjellson.
Available from github; https://github.com/ckjellson/textalloc
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-01 19:39:58 +0100 (Thu, June 01, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Christoffer Kjellson $"
__date__ = "$Date: 2022 $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np


def non_overlapping_with_points(
        points_xy: np.ndarray, boxes_xyxy: np.ndarray, x_margin: float, y_margin: float
        ) -> np.ndarray:
    """Finds boxes_xyxy not overlapping with points.

    Args:
        points_xy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-points
        boxes_xyxy (np.ndarray): Array of shape (K,4) with K candidate boxes
        x_margin (float): fraction of the x-dimension to use as margins for text boxes
        y_margin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes_xyxy with points
    """
    # # ensure that the boxes are bottom-left -> top-right
    # boxes_xyxy = np.stack([np.min([boxes_xyxy[:, 0], boxes_xyxy[:, 2]], axis=0),
    #                        np.min([boxes_xyxy[:, 1], boxes_xyxy[:, 3]], axis=0),
    #                        np.max([boxes_xyxy[:, 0], boxes_xyxy[:, 2]], axis=0),
    #                        np.max([boxes_xyxy[:, 1], boxes_xyxy[:, 3]], axis=0),
    #                        ], axis=1)

    return np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_and(
                            boxes_xyxy[:, 0:1] - x_margin < points_xy[:, 0],
                            np.bitwise_and(
                                    boxes_xyxy[:, 2:3] + x_margin > points_xy[:, 0],
                                    np.bitwise_and(
                                            boxes_xyxy[:, 1:2] - y_margin < points_xy[:, 1],
                                            boxes_xyxy[:, 3:4] + y_margin > points_xy[:, 1],
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )


def non_overlapping_points_to_boxes(
        points_xy: np.ndarray, boxes_xyxy: np.ndarray, x_margin: float, y_margin: float,
        *, by_points: bool = None, by_boxes: bool = None,
        ) -> np.ndarray:
    """Finds boxes not overlapping with points.

    Return the list of points-in-boxes, or boxes-containing-points.

    If by_points is True, it will return an array of length points_xy referenced by points, i.e., points that are not in boxes.
    If False, it will return an array of length boxes_xy referenced by boxes, i.e., boxes that don't contain points.
    by_boxes can also be used to specify returning by boxes (opposite of by_points).

    Returns True for non-overlapping, i.e., the points are not in a box, or a box does not contain a point.

    Args:
        points_xy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-points.
        boxes_xyxy (np.ndarray): Array of shape (K,4) with K candidate boxes.
        x_margin (float): fraction of the x-dimension to use as margins for text boxes.
        y_margin (float): fraction of the y-dimension to use as margins for text boxes.
        by_points (bool): return the list referenced by points or boxes.
        by_boxes (bool): return the list referenced by boxes or points.

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes_xyxy with points.

    Raises:
        ValueError if by_points and by_boxes are both specified.
    """
    if by_points is not None and by_boxes is not None:
        raise ValueError('non_overlapping_points_to_boxes: use either by_points or by_boxes')

    if by_points is None and by_boxes is None:
        # default to reference by points
        by_points = True
    elif by_boxes is not None:
        by_points = not by_boxes

    return np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_and(
                            boxes_xyxy[:, 0:1] - x_margin < points_xy[:, 0],
                            np.bitwise_and(
                                    boxes_xyxy[:, 2:3] + x_margin > points_xy[:, 0],
                                    np.bitwise_and(
                                            boxes_xyxy[:, 1:2] - y_margin < points_xy[:, 1],
                                            boxes_xyxy[:, 3:4] + y_margin > points_xy[:, 1],
                                            ),
                                    ),
                            ),
                    axis=int(not by_points),  # can choose whether to collate by points_xy or boxes_xyxy
                    )
            )


def non_overlapping_points_to_ellipses(
        points_xy: np.ndarray, ellipses_xyab: np.ndarray, x_margin: float, y_margin: float,
        *, by_points: bool = None, by_ellipses: bool = None,
        ) -> np.ndarray:
    """Finds ellipses not overlapping with points.

    Return the list of points-in-ellipses, or ellipses-containing-points.

    Points are of the form: [[x, y], ...]
    Ellipses are of the form: [[x, y, a, b], ...]
        where [x, y] is the center of the ellipse, 'a' is the length of the semi-major x-axis,
        and 'b' is the length of the semi-minor y-axis.
    Ellipses are aligned with the x-axis.
    
    If by_points is True, it will return an array of length points_xy referenced by points, i.e., points that are not in ellipses.
    If False, it will return an array of length ellipses_xy referenced by ellipses, i.e., ellipses that don't contain points.
    by_ellipses can also be used to specify returning by ellipses (opposite of by_points).

    Returns True for non-overlapping, i.e., the points are not in an ellipse, or an ellipse does not contain a point.

    Args:
        points_xy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-points.
        ellipses_xyab (np.ndarray): Array of shape (K,4) with K candidate ellipses.
        x_margin (float): fraction of the x-dimension to use as margins for text ellipses in pixels.
        y_margin (float): fraction of the y-dimension to use as margins for text ellipses in pixels.
        by_points (bool): return the list referenced by points or ellipses.
        by_ellipses (bool): return the list referenced by ellipses or points.

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping points with ellipses.

    Raises:
        ValueError if by_points and by_ellipses are both specified.
    """
    if by_points is not None and by_ellipses is not None:
        raise ValueError('non_overlapping_points_to_ellipses: use either by_points or by_ellipses')

    if by_points is None and by_ellipses is None:
        # default to reference by points
        by_points = True
    elif by_ellipses is not None:
        by_points = not by_ellipses

    return np.invert(
            np.bitwise_or.reduce(
                    ((points_xy[:, 0] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                    ((points_xy[:, 1] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,
                    axis=int(not by_points),  # can choose whether to collate by points_xy or ellipses_xyab
                    )
            )


def non_overlapping_with_lines(
        lines_xyxy: np.ndarray, boxes_xyxy: np.ndarray, x_margin: float, y_margin: float
        ) -> np.ndarray:
    """Finds boxes_xyxy not overlapping with lines

    Args:
        lines_xyxy (np.ndarray): line segments
        boxes_xyxy (np.ndarray): candidate boxes
        x_margin (float): fraction of the x-dimension to use as margins for text boxes
        y_margin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes_xyxy with lines.
    """
    non_intersecting = np.invert(
            np.any(
                    np.bitwise_or(
                            line_intersect(
                                    np.hstack(
                                            [
                                                boxes_xyxy[:, 0:1] - x_margin,
                                                boxes_xyxy[:, 1:2] - y_margin,
                                                boxes_xyxy[:, 0:1] - x_margin,
                                                boxes_xyxy[:, 3:4] + y_margin,
                                                ]
                                            ),
                                    lines_xyxy,
                                    ),
                            np.bitwise_or(
                                    line_intersect(
                                            np.hstack(
                                                    [
                                                        boxes_xyxy[:, 0:1] - x_margin,
                                                        boxes_xyxy[:, 3:4] + y_margin,
                                                        boxes_xyxy[:, 2:3] + x_margin,
                                                        boxes_xyxy[:, 3:4] + y_margin,
                                                        ]
                                                    ),
                                            lines_xyxy,
                                            ),
                                    np.bitwise_or(
                                            line_intersect(
                                                    np.hstack(
                                                            [
                                                                boxes_xyxy[:, 2:3] + x_margin,
                                                                boxes_xyxy[:, 3:4] + y_margin,
                                                                boxes_xyxy[:, 2:3] + x_margin,
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                ]
                                                            ),
                                                    lines_xyxy,
                                                    ),
                                            line_intersect(
                                                    np.hstack(
                                                            [
                                                                boxes_xyxy[:, 2:3] + x_margin,
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                boxes_xyxy[:, 0:1] - x_margin,
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                ]
                                                            ),
                                                    lines_xyxy,
                                                    ),
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )

    non_inside = np.invert(
            np.any(
                    np.bitwise_and(
                            boxes_xyxy[:, 0:1] - x_margin < lines_xyxy[:, 0],
                            np.bitwise_and(
                                    boxes_xyxy[:, 1:2] - y_margin < lines_xyxy[:, 1],
                                    np.bitwise_and(
                                            boxes_xyxy[:, 2:3] + x_margin > lines_xyxy[:, 0],
                                            np.bitwise_and(
                                                    boxes_xyxy[:, 3:4] + y_margin > lines_xyxy[:, 1],
                                                    np.bitwise_and(
                                                            boxes_xyxy[:, 0:1] - x_margin < lines_xyxy[:, 2],
                                                            np.bitwise_and(
                                                                    boxes_xyxy[:, 1:2] - y_margin < lines_xyxy[:, 3],
                                                                    np.bitwise_and(
                                                                            boxes_xyxy[:, 2:3] + x_margin > lines_xyxy[:, 2],
                                                                            boxes_xyxy[:, 3:4] + y_margin > lines_xyxy[:, 3],
                                                                            ),
                                                                    ),
                                                            ),
                                                    ),
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )
    return np.bitwise_and(non_intersecting, non_inside)


def non_overlapping_lines_to_boxes(
        lines_xyxy: np.ndarray, boxes_xyxy: np.ndarray, x_margin: float, y_margin: float
        ) -> np.ndarray:
    """Finds boxes_xyxy not overlapping with lines.

    boxes_xyxy must be sorted min_x, min_y, max_x, max_y.

    Args:
        lines_xyxy (np.ndarray): candidate line segments
        boxes_xyxy (np.ndarray): target boxes_xyxy
        x_margin (float): fraction of the x-dimension to use as margins for text boxes_xyxy
        y_margin (float): fraction of the y-dimension to use as margins for text boxes_xyxy

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes_xyxy with lines.
    """
    non_intersecting = np.invert(
            np.any(
                    np.bitwise_or(
                            line_intersect(
                                    lines_xyxy,
                                    np.hstack(
                                            [
                                                # left-hand side of box
                                                boxes_xyxy[:, 0:1] - x_margin,  # bottom-left
                                                boxes_xyxy[:, 1:2] - y_margin,
                                                boxes_xyxy[:, 0:1] - x_margin,  # top-left
                                                boxes_xyxy[:, 3:4] + y_margin,
                                                ]
                                            ),
                                    ),
                            np.bitwise_or(
                                    line_intersect(
                                            lines_xyxy,
                                            np.hstack(
                                                    [
                                                        # top-edge of box
                                                        boxes_xyxy[:, 0:1] - x_margin,  # top-left
                                                        boxes_xyxy[:, 3:4] + y_margin,
                                                        boxes_xyxy[:, 2:3] + x_margin,  # top-right
                                                        boxes_xyxy[:, 3:4] + y_margin,
                                                        ]
                                                    ),
                                            ),
                                    np.bitwise_or(
                                            line_intersect(
                                                    lines_xyxy,
                                                    np.hstack(
                                                            [
                                                                # right-hand side of box
                                                                boxes_xyxy[:, 2:3] + x_margin,  # top-right
                                                                boxes_xyxy[:, 3:4] + y_margin,
                                                                boxes_xyxy[:, 2:3] + x_margin,  # bottom-right
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                ]
                                                            ),
                                                    ),
                                            line_intersect(
                                                    lines_xyxy,
                                                    np.hstack(
                                                            [
                                                                # bottom-edge of box
                                                                boxes_xyxy[:, 2:3] + x_margin,  # bottom-right
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                boxes_xyxy[:, 0:1] - x_margin,  # bottom-left
                                                                boxes_xyxy[:, 1:2] - y_margin,
                                                                ]
                                                            ),
                                                    ),
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )

    non_inside = np.invert(
            np.any(
                    np.bitwise_and(
                            lines_xyxy[:, 0:1] + x_margin < boxes_xyxy[:, 0],
                            np.bitwise_and(
                                    lines_xyxy[:, 1:2] + y_margin < boxes_xyxy[:, 1],
                                    np.bitwise_and(
                                            lines_xyxy[:, 2:3] - x_margin > boxes_xyxy[:, 0],
                                            np.bitwise_and(
                                                    lines_xyxy[:, 3:4] - y_margin > boxes_xyxy[:, 1],
                                                    np.bitwise_and(
                                                            lines_xyxy[:, 0:1] + x_margin < boxes_xyxy[:, 2],
                                                            np.bitwise_and(
                                                                    lines_xyxy[:, 1:2] + y_margin < boxes_xyxy[:, 3],
                                                                    np.bitwise_and(
                                                                            lines_xyxy[:, 2:3] - x_margin > boxes_xyxy[:, 2],
                                                                            lines_xyxy[:, 3:4] - y_margin > boxes_xyxy[:, 3],
                                                                            ),
                                                                    ),
                                                            ),
                                                    ),
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )
    return np.bitwise_and(non_intersecting, non_inside)


def non_overlapping_lines_to_lines(cand_xyxy: np.ndarray, lines_xyxy: np.ndarray) -> np.ndarray:
    """Checks if line segments intersect for all candidates and line segments.

    Args:
        cand_xyxy (np.ndarray): line segments in candidates
        lines_xyxy (np.ndarray): line segments plotted

    Returns:
        np.ndarray: Boolean array with True for non-overlapping line segments with candidates.
    """
    return np.invert(np.any(line_intersect(cand_xyxy, lines_xyxy),
                            axis=1)
                     )


def line_intersect(cand_xyxy: np.ndarray, lines_xyxy: np.ndarray) -> np.ndarray:
    """Checks if line segments intersect for all line segments and candidates.

    Args:
        cand_xyxy (np.ndarray): line segments in candidates
        lines_xyxy (np.ndarray): line segments plotted

    Returns:
        np.ndarray: Boolean array with True for non-overlapping candidate segments with line segments.
    """
    return np.bitwise_and(
            ccw(cand_xyxy[:, :2], lines_xyxy[:, :2], lines_xyxy[:, 2:], False)
            != ccw(cand_xyxy[:, 2:], lines_xyxy[:, :2], lines_xyxy[:, 2:], False),
            ccw(cand_xyxy[:, :2], cand_xyxy[:, 2:], lines_xyxy[:, :2], True)
            != ccw(cand_xyxy[:, :2], cand_xyxy[:, 2:], lines_xyxy[:, 2:], True),
            )


def ccw(x1y1: np.ndarray, x2y2: np.ndarray, x3y3: np.ndarray, cand: bool) -> np.ndarray:
    """CCW used in line intersect

    Args:
        x1y1 (np.ndarray):
        x2y2 (np.ndarray):
        x3y3 (np.ndarray):
        cand (bool): using candidate positions (different broadcasting)

    Returns:
        np.ndarray:
    """
    # pycharm doesn't recognise this as a numpy np.ndarray :|
    if cand:
        return (
                (-(x1y1[:, 1:2] - x3y3[:, 1]))
                * np.repeat(x2y2[:, 0:1] - x1y1[:, 0:1], x3y3.shape[0], axis=1)
        ) > (
                np.repeat(x2y2[:, 1:2] - x1y1[:, 1:2], x3y3.shape[0], axis=1)
                * (-(x1y1[:, 0:1] - x3y3[:, 0]))
        )
    return (
            (-(x1y1[:, 1:2] - x3y3[:, 1])) * (-(x1y1[:, 0:1] - x2y2[:, 0]))
    ) > ((-(x1y1[:, 1:2] - x2y2[:, 1])) * (-(x1y1[:, 0:1] - x3y3[:, 0])))


def non_overlapping_boxes_to_boxes(
        boxes_xyxy: np.ndarray, cand_xyxy: np.ndarray, x_margin: float, y_margin: float
        ) -> np.ndarray:
    """Finds cand_xyxy not overlapping with allocated boxes.

    Args:
        boxes_xyxy (np.ndarray): array with allocated boxes
        cand_xyxy (np.ndarray): candidate boxes
        x_margin (float): fraction of the x-dimension to use as margins for text boxes
        y_margin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping cand_xyxy with boxes.
    """
    return np.invert(
            np.any(
                    np.invert(
                            np.bitwise_or(
                                    cand_xyxy[:, 0:1] - x_margin > boxes_xyxy[:, 2],
                                    np.bitwise_or(
                                            cand_xyxy[:, 2:3] + x_margin < boxes_xyxy[:, 0],
                                            np.bitwise_or(
                                                    cand_xyxy[:, 1:2] - y_margin > boxes_xyxy[:, 3],
                                                    cand_xyxy[:, 3:4] + y_margin < boxes_xyxy[:, 1],
                                                    ),
                                            ),
                                    )
                            ),
                    axis=1,
                    )
            )


def non_overlapping_boxes_to_ellipses(
        boxes_xyxy: np.ndarray, ellipses_xyab: np.ndarray, x_margin: float, y_margin: float,
        *, by_boxes: bool = None, by_ellipses: bool = None,
        ) -> np.ndarray:
    """Finds ellipses not overlapping with boxes.

    Return the list of boxes-in-ellipses, or ellipses-containing-boxes.

    Boxes are of the form: [[x0, y0, x1, y1], ...]
        where [x0, y0] is the bottom-left corner of the box and [x1, y1] is the top-right corner.
    Ellipses are of the form: [[x, y, a, b], ...]
        where [x, y] is the center of the ellipse, 'a' is the length of the semi-major x-axis,
        and 'b' is the length of the semi-minor y-axis.
    Ellipses are aligned with the x-axis.

    If by_boxes is True, it will return an array of length boxes_xyxy referenced by boxes, i.e., boxes that are not in ellipses.
    If False, it will return an array of length ellipses_xy referenced by ellipses, i.e., ellipses that don't contain boxes.
    by_ellipses can also be used to specify returning by ellipses (opposite of by_boxes).

    Returns True for non-overlapping, i.e., the boxes are not overlapping ellipses, or ellipses are not overlapping boxes.

    Args:
        boxes_xyxy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-boxes.
        ellipses_xyab (np.ndarray): Array of shape (K,4) with K candidate ellipses.
        x_margin (float): fraction of the x-dimension to use as margins for text ellipses in pixels.
        y_margin (float): fraction of the y-dimension to use as margins for text ellipses in pixels.
        by_boxes (bool): return the list referenced by boxes or ellipses.
        by_ellipses (bool): return the list referenced by ellipses or boxes.

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes with ellipses.

    Raises:
        ValueError if by_boxes and by_ellipses are both specified.
    """
    if by_boxes is not None and by_ellipses is not None:
        raise ValueError('non_overlapping_boxes_to_ellipses: use either by_boxes or by_ellipses')

    if by_boxes is None and by_ellipses is None:
        # default to reference by boxes
        by_boxes = True
    elif by_ellipses is not None:
        by_boxes = not by_ellipses

    return np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_or.reduce([
                        ((boxes_xyxy[:, 0] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                        ((boxes_xyxy[:, 1] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,

                        ((boxes_xyxy[:, 2] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                        ((boxes_xyxy[:, 3] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,

                        ((boxes_xyxy[:, 0] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                        ((boxes_xyxy[:, 3] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,

                        ((boxes_xyxy[:, 2] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                        ((boxes_xyxy[:, 1] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,
                        ]),
                    axis=int(not by_boxes),  # can choose whether to collate by boxes_xyxy or ellipses_xyab
                    )
            )


def non_overlapping_lines_to_ellipses(
        lines_xyxy: np.ndarray, ellipses_xyab: np.ndarray, x_margin: float, y_margin: float,
        *, by_lines: bool = None, by_ellipses: bool = None,
        ) -> np.ndarray:
    """Finds ellipses not overlapping with lines.

    Return the list of lines-in-ellipses, or ellipses-containing-lines.

    Lines are of the form: [[x0, y0, x1, y1], ...]
        where [x0, y0] is the start of the line and [x1, y1] is the end.
    Ellipses are of the form: [[x, y, a, b], ...]
        where [x, y] is the center of the ellipse, 'a' is the length of the semi-major x-axis,
        and 'b' is the length of the semi-minor y-axis.
    Ellipses are aligned with the x-axis.

    If by_lines is True, it will return an array of length lines_xyxy referenced by lines, i.e., lines that are not in ellipses.
    If False, it will return an array of length ellipses_xy referenced by ellipses, i.e., ellipses that don't contain lines.
    by_ellipses can also be used to specify returning by ellipses (opposite of by_lines).

    Returns True for non-overlapping, i.e., the lines are not in an ellipse, or an ellipse does not contain a point.

    Args:
        lines_xyxy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-lines.
        ellipses_xyab (np.ndarray): Array of shape (K,4) with K candidate ellipses.
        x_margin (float): fraction of the x-dimension to use as margins for text ellipses in pixels.
        y_margin (float): fraction of the y-dimension to use as margins for text ellipses in pixels.
        by_lines (bool): return the list referenced by lines or ellipses.
        by_ellipses (bool): return the list referenced by ellipses or lines.

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping lines with ellipses.

    Raises:
        ValueError if by_lines and by_ellipses are both specified.
    """
    if by_lines is not None and by_ellipses is not None:
        raise ValueError('non_overlapping_lines_to_ellipses: use either by_lines or by_ellipses')

    if by_lines is None and by_ellipses is None:
        # default to reference by lines
        by_lines = True
    elif by_ellipses is not None:
        by_lines = not by_ellipses

    _ellipse_angs = 8
    angs = np.linspace(0.0, np.pi * 2.0 - (2 * np.pi / _ellipse_angs), _ellipse_angs)
    itrs = np.linspace(0, _ellipse_angs - 1, _ellipse_angs, dtype=int)

    # generate points around the ellipses and offset to centres
    ellipses_x = np.apply_along_axis(lambda col: col + ellipses_xyab[:, 0], 0, (ellipses_xyab[:, 2:3] + x_margin) * np.cos(angs))
    ellipses_y = np.apply_along_axis(lambda col: col + ellipses_xyab[:, 1], 0, (ellipses_xyab[:, 3:4] + y_margin) * np.sin(angs))

    non_intersecting = np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_or.reduce([
                        line_intersect(
                                np.hstack(
                                        [
                                            ellipses_x[:, itr:itr + 1],
                                            ellipses_y[:, itr:itr + 1],
                                            ellipses_x[:, (itr + 1) % _ellipse_angs:1 + (itr + 1) % _ellipse_angs],
                                            ellipses_y[:, (itr + 1) % _ellipse_angs:1 + (itr + 1) % _ellipse_angs],
                                            ]
                                        ),
                                lines_xyxy,
                                )
                        for itr in itrs]),
                    axis=int(not by_lines),  # can choose whether to collate by lines_xyxy or ellipses_xyab
                    )
            )

    non_inside = np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_or(
                            ((lines_xyxy[:, 0] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                            ((lines_xyxy[:, 1] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1,

                            ((lines_xyxy[:, 2] - ellipses_xyab[:, 0:1])**2 / (ellipses_xyab[:, 2:3] + x_margin)**2) +
                            ((lines_xyxy[:, 3] - ellipses_xyab[:, 1:2])**2 / (ellipses_xyab[:, 3:4] + y_margin)**2) <= 1
                            ),
                    axis=int(not by_lines)
                    )
            )

    return np.bitwise_and(non_intersecting, non_inside)


def inside_plot(
        xmin_bound: float,
        ymin_bound: float,
        xmax_bound: float,
        ymax_bound: float,
        boxes_xyxy: np.ndarray,
        ) -> np.ndarray:
    """Finds boxes_xyxy that are inside the plot bounds

    Args:
        xmin_bound (float):
        ymin_bound (float):
        xmax_bound (float):
        ymax_bound (float):
        boxes_xyxy (np.ndarray): candidate boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes_xyxy with boxes.
    """
    return np.invert(
            np.bitwise_or(
                    boxes_xyxy[:, 0] < xmin_bound,
                    np.bitwise_or(
                            boxes_xyxy[:, 1] < ymin_bound,
                            np.bitwise_or(
                                    boxes_xyxy[:, 2] > xmax_bound, boxes_xyxy[:, 3] > ymax_bound
                                    ),
                            ),
                    )
            )


def main():
    MAX_ANGS = 12
    LOOPS = 4
    xmindistance = ymindistance = 10
    xmaxdistance = ymaxdistance = 130
    x, y = 5, 5

    angs = np.tile(np.linspace(0.0, np.pi * 2.0 - (2 * np.pi / MAX_ANGS), MAX_ANGS), LOOPS)
    ll = np.linspace(min(xmindistance, ymindistance), max(xmaxdistance, ymaxdistance), LOOPS)

    distx = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)
    disty = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)

    ss = x + np.sin(angs) * distx
    cc = y + np.cos(angs) * disty

    # plot a figure to check the size
    import matplotlib

    matplotlib.use('Qt5Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Ellipse

    fig = plt.figure(figsize=(10, 8), dpi=100)
    axS = fig.gca()

    # axS.plot(ss, cc, label='End-points')
    for ii in range(len(ss)):
        axS.plot([ss[ii], x], [cc[ii], y], 'x-', linewidth=1, markersize=12)

    lines = np.vstack([np.tile([x, y], (ss.shape[0], 1)).transpose(), ss, cc]).transpose()
    lines_xyxy = np.array([[47, 16, 36, -45],
                           [-71, 11, -21, -32],
                           [60, 72, 87, 20],
                           [-10, 110, 20, 110],
                           [-80, 100, -60, 60],
                           [-10, -60, -22, -95]
                           ])

    lInt = line_intersect(lines, lines_xyxy)
    print(lInt)
    print(np.invert(np.any(lInt, axis=1)))  # good lines

    print('lines_to_lines - should be same as above')
    print(non_overlapping_lines_to_lines(lines, lines_xyxy))

    # need to order min -> max?
    print('lines_to_boxes')
    boxes_xyxy = np.array([[36, -45, 36 + 47, -47 + 16],
                           [-50, -15, -50 - 41, -15 + 151],
                           [60, 20, 60 + 87, 20 + 60],
                           [-30, -20, -30 + 30, -20 + 55],
                           [90, 90, 140, 130]])

    # ensure that the boxes are bottom-left -> top-right
    boxes_xyxy = np.stack([np.min([boxes_xyxy[:, 0], boxes_xyxy[:, 2]], axis=0),
                           np.min([boxes_xyxy[:, 1], boxes_xyxy[:, 3]], axis=0),
                           np.max([boxes_xyxy[:, 0], boxes_xyxy[:, 2]], axis=0),
                           np.max([boxes_xyxy[:, 1], boxes_xyxy[:, 3]], axis=0),
                           ], axis=1)

    print(non_overlapping_lines_to_boxes(lines,
                                         boxes_xyxy, 0, 0))

    print('points_to_boxes')
    points = np.vstack([ss, cc]).transpose()
    print(non_overlapping_points_to_boxes(points,
                                          boxes_xyxy, 0, 0))
    print(non_overlapping_points_to_boxes(points,
                                          boxes_xyxy, 0, 0, by_points=False))

    ellipses_xyab = np.array([[61, -90, 50 / 2, 50 / 2],
                              [-50, -15, 60 / 2, 45 / 2],
                              [60, 20, 9 / 2, 34 / 2],
                              [12, -0, 12 / 2, 12 / 2],
                              [-68, 80, 80 / 2, 80 / 2],
                              [70, 110, 67 / 2, 24 / 2],
                              [-22, -95, 50 / 2, 50 / 2],
                              [52.5, -9, 20 / 2, 20 / 2],
                              ])
    print('points_to_ellipses')
    print(non_overlapping_points_to_ellipses(points, ellipses_xyab, 0, 0))
    print(non_overlapping_points_to_ellipses(points, ellipses_xyab, 0, 0, by_points=False))

    print('boxes_to_ellipses')
    print(non_overlapping_boxes_to_ellipses(boxes_xyxy, ellipses_xyab, 0, 0))
    print(non_overlapping_boxes_to_ellipses(boxes_xyxy, ellipses_xyab, 0, 0, by_boxes=False))

    for ii in range(lines_xyxy.shape[0]):
        row = lines_xyxy[ii, :]
        axS.plot(row[::2], row[1::2], linewidth=3)
        axS.text(row[0], row[1], str(ii), fontsize=12)

    for ii in range(boxes_xyxy.shape[0]):
        row = boxes_xyxy[ii, :]
        axS.add_patch(Rectangle(row[:2], row[2] - row[0], row[3] - row[1], linewidth=1, fill=False))
        axS.text(row[0], row[1], str(ii), fontsize=12)

    for ii in range(ellipses_xyab.shape[0]):
        row = ellipses_xyab[ii, :]
        # convert semi-major to major axes
        axS.add_patch(Ellipse(row[:2], row[2] * 2, row[3] * 2, linewidth=1, fill=False))
        axS.text(row[0], row[1], str(ii), fontsize=12)

    print('lines_to_ellipses')
    for margin in range(3):
        print(non_overlapping_lines_to_ellipses(lines_xyxy, ellipses_xyab, margin, margin))
        print(non_overlapping_lines_to_ellipses(lines_xyxy, ellipses_xyab, margin, margin, by_lines=False))

    plt.show()


if __name__ == '__main__':
    main()
