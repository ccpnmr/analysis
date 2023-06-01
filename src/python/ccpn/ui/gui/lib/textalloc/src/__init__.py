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
__dateModified__ = "$dateModified: 2023-06-01 19:39:57 +0100 (Thu, June 01, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Christoffer Kjellson $"
__date__ = "$Date: 2022 $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui
import numpy as np
import time
from typing import List, Tuple, Union, Optional
from .non_overlapping_boxes import get_non_overlapping_boxes


# from ccpn.util.decorators import profile
#
#
# @profile()
def allocate_text(
        x: Union[np.ndarray, List[float]],
        y: Union[np.ndarray, List[float]],
        text_list: List[str],
        x_points: Union[np.ndarray, List[float]] = None,
        y_points: Union[np.ndarray, List[float]] = None,
        x_lines: List[Union[np.ndarray, List[float]]] = None,
        y_lines: List[Union[np.ndarray, List[float]]] = None,
        x_boxes: List[Union[np.ndarray, List[float]]] = None,
        y_boxes: List[Union[np.ndarray, List[float]]] = None,
        a_ellipses: Union[np.ndarray, List[float]] = None,
        b_ellipses: Union[np.ndarray, List[float]] = None,
        textsize: int = 10,
        x_margin: float = 2,
        y_margin: float = 2,
        minx_distance: float = 2,
        maxx_distance: float = 100,
        miny_distance: float = 2,
        maxy_distance: float = 100,
        verbose: bool = False,
        draw_lines: bool = True,
        linecolor: str = "r",
        draw_all: bool = True,
        linewidth: float = 1,
        textcolor: str = "k",
        x_lims: Optional[Tuple] = (0, 1),
        y_lims: Optional[Tuple] = (0, 1),
        include_new_lines=False,
        include_new_boxes=False,
        ):
    """Main function of allocating text-boxes.

    Args:
        x (Union[np.ndarray, List[float]]): x-coordinates of texts 1d array/list.
        y (Union[np.ndarray, List[float]]): y-coordinates of texts 1d array/list.
        text_list (List[str]): list of texts.
        x_points (Union[np.ndarray, List[float]], optional): x-coordinates of all scattered points in plot 1d array/list. Defaults to None.
        y_points (Union[np.ndarray, List[float]], optional): y-coordinates of all scattered points in plot 1d array/list. Defaults to None.
        x_lines (List[Union[np.ndarray, List[float]]], optional): x-coordinates of all lines in plot list of 1d arrays/lists. Defaults to None.
        y_lines (List[Union[np.ndarray, List[float]]], optional): y-coordinates of all lines in plot list of 1d arrays/lists. Defaults to None.
        x_boxes (List[Union[np.ndarray, List[float]]], optional): x-coordinates of all boxes in plot list of 1d arrays/lists. Defaults to None.
        y_boxes (List[Union[np.ndarray, List[float]]], optional): y-coordinates of all boxes in plot list of 1d arrays/lists. Defaults to None.
        a_ellipses (Union[np.ndarray, List[float]], optional): axis size for ellipses in the x-direction, maps to x_points. Defaults to None.
        b_ellipses (Union[np.ndarray, List[float]], optional): axis size for ellipses in the y-direction, maps to y_points. Defaults to None.
        textsize (int, optional): size of text. Defaults to 10.
        x_margin (float, optional): x-axis margin between objects in pixels. Defaults to 2.
        y_margin (float, optional): y-axis margin between objects in pixels. Defaults to 2.
        minx_distance (float, optional): parameter for min distance between text and origin in pixels. Defaults to 2.
        maxx_distance (float, optional): parameter for max distance between text and origin in pixels. Defaults to 100.
        miny_distance (float, optional): parameter for min distance between text and origin in pixels. Defaults to 2.
        maxy_distance (float, optional): parameter for max distance between text and origin in pixels. Defaults to 100.
        verbose (bool, optional): prints progress using tqdm. Defaults to False.
        draw_lines (bool, optional): draws lines from original points to textboxes. Defaults to True.
        linecolor (str, optional): color code of the lines between points and text-boxes. Defaults to "r".
        draw_all (bool, optional): Draws all texts after allocating as many as possible despit overlap. Defaults to True.
        linewidth (float, optional): width of line. Defaults to 1.
        textcolor (str, optional): color code of the text. Defaults to "k".
        x_lims (Tuple[float, float]): x-limits of plot in pixels.
        y_lims (Tuple[float, float]): y-limits of plot in pixels.
        include_new_lines (bool): Avoid the newly added line-segments between points and labels as new labels are found.
        include_new_boxes (bool): Avoid the newly added boxes between points and labels as new labels are found.
    """
    t0 = time.time()

    # Ensure good inputs
    assert len(x) == len(y)
    x = np.array(x)
    y = np.array(y)

    if x_points is not None:
        assert y_points is not None
    if y_points is not None:
        assert x_points is not None
        assert len(y_points) == len(x_points)
        x_points = np.array(x_points)
        y_points = np.array(y_points)

    if a_ellipses is not None:
        assert x_points is not None
        assert b_ellipses is not None
    if b_ellipses is not None:
        assert a_ellipses is not None
        assert len(b_ellipses) == len(a_ellipses)
        a_ellipses = np.array(a_ellipses)
        b_ellipses = np.array(b_ellipses)

    if a_ellipses is None and x_points is not None:
        # create ellipses of size 1-pixel
        a_ellipses = np.ones_like(x_points)
        b_ellipses = np.ones_like(y_points)

    if x_lines is not None:
        assert y_lines is not None
    if y_lines is not None:
        assert x_lines is not None
        assert all(len(x_line) == len(y_line) for x_line, y_line in zip(x_lines, y_lines))
        x_lines = [np.array(x_line) for x_line in x_lines]
        y_lines = [np.array(y_line) for y_line in y_lines]

    if x_boxes is not None:
        assert y_boxes is not None
    if y_boxes is not None:
        assert x_boxes is not None
        assert all(len(x_box) == len(y_box) for x_box, y_box in zip(x_boxes, y_boxes))
        x_boxes = [np.array(x_box) for x_box in x_boxes]
        y_boxes = [np.array(y_box) for y_box in y_boxes]

    assert minx_distance <= maxy_distance
    assert minx_distance >= x_margin
    assert miny_distance <= maxy_distance
    assert miny_distance >= y_margin

    # Create boxes in original plot
    if verbose:
        print("Creating boxes from texts")
    fontMetric = QtGui.QFontMetricsF(QtGui.QFont("Open Sans", textsize))

    original_boxes = []  # currently a mix of co-ordinates and texts
    for x_coord, y_coord, s in zip(x, y, text_list):
        rect = fontMetric.boundingRect(s)
        w, h = rect.width(), rect.height()

        original_boxes.append((x_coord, y_coord, w, h, s))  # check the width of the strings

    # Process extracted text-boxes
    if verbose:
        print("Processing")
    if x_points is None:
        scatter_xy = None
    else:
        scatter_xy = np.transpose(np.vstack([x_points, y_points]))

    if a_ellipses is None:
        ellipses_xyab = None
    else:
        ellipses_xyab = np.transpose(np.vstack([x_points, y_points, a_ellipses, b_ellipses]))

    lines_xyxy = None if x_lines is None else lines_to_segments(x_lines, y_lines)
    boxes_xyxy = None if x_boxes is None else boxes_to_segments(x_boxes, y_boxes)

    non_overlapping_boxes, overlapping_boxes_inds = get_non_overlapping_boxes(
            original_boxes,
            x_lims,
            y_lims,
            x_margin,
            y_margin,
            minx_distance,
            maxx_distance,
            miny_distance,
            maxy_distance,
            verbose,
            draw_all,
            include_new_lines,
            include_new_boxes,
            scatter_xy=scatter_xy,
            lines_xyxy=lines_xyxy,
            boxes_xyxy=boxes_xyxy,
            ellipses_xyab=ellipses_xyab,
            )

    if verbose:
        print(f"Finished in {time.time() - t0}s")

    return non_overlapping_boxes, overlapping_boxes_inds


def find_nearest_point_on_box(
        xmin: float, ymin: float, w: float, h: float, x: float, y: float
        ) -> Union[Tuple[float, float], Tuple[None, None]]:
    """Finds nearest point on box from point.
    Returns None,None if point inside box

    Args:
        xmin (float): xmin of box
        ymin (float): ymin of box
        w (float): width of box
        h (float): height of box
        x (float): x-coordinate of point
        y (float): y-coordinate of point

    Returns:
        Tuple[float, float]: x,y coordinate of nearest point
    """
    xmax = xmin + w
    ymax = ymin + h
    if x < xmin:
        if y < ymin:
            return xmin, ymin
        elif y > ymax:
            return xmin, ymax
        else:
            return xmin, y
    elif x > xmax:
        if y < ymin:
            return xmax, ymin
        elif y > ymax:
            return xmax, ymax
        else:
            return xmax, y
    elif y < ymin:
        return x, ymin
    elif y > ymax:
        return x, ymax

    return None, None


def lines_to_segments(
        x_lines: List[np.ndarray],
        y_lines: List[np.ndarray],
        ) -> np.ndarray:
    """Sets up

    Args:
        x_lines (List[np.ndarray]): x-coordinates of all lines in plot list of 1d arrays
        y_lines (List[np.ndarray]): y-coordinates of all lines in plot list of 1d arrays

    Returns:
        np.ndarray: 2d array of line segments
    """
    assert len(x_lines) == len(y_lines)
    n_x_segments = np.sum([len(line_x) - 1 for line_x in x_lines])
    n_y_segments = np.sum([len(line_y) - 1 for line_y in y_lines])
    assert n_x_segments == n_y_segments
    lines_xyxy = np.zeros((n_x_segments, 4))
    itr = 0
    for line_x, line_y in zip(x_lines, y_lines):
        for i in range(len(line_x) - 1):
            lines_xyxy[itr, :] = [line_x[i], line_y[i], line_x[i + 1], line_y[i + 1]]  # start-end
            itr += 1
    return lines_xyxy


def boxes_to_segments(
        x_boxes: List[np.ndarray],
        y_boxes: List[np.ndarray],
        ) -> np.ndarray:
    """Sets up

    Args:
        x_boxes (List[np.ndarray]): x-coordinates of all boxes in plot list of 1d arrays
        y_boxes (List[np.ndarray]): y-coordinates of all boxes in plot list of 1d arrays

    Returns:
        np.ndarray: 2d array of box segments, as co-ordinates: bottom-left -> top-right
    """
    assert len(x_boxes) == len(y_boxes)
    n_x_segments = np.sum([len(box_x) - 1 for box_x in x_boxes])
    n_y_segments = np.sum([len(box_y) - 1 for box_y in y_boxes])
    assert n_x_segments == n_y_segments
    boxes_xyxy = np.zeros((n_x_segments, 4))
    itr = 0
    for box_x, box_y in zip(x_boxes, y_boxes):
        for i in range(len(box_x) - 1):
            boxes_xyxy[itr, :] = [min(box_x[i], box_x[i + 1]),  # bottom-left
                                  min(box_y[i], box_y[i + 1]),
                                  max(box_x[i], box_x[i + 1]),  # top-right
                                  max(box_y[i], box_y[i + 1])]
            itr += 1
    return boxes_xyxy
