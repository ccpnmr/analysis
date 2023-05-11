"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2023-05-11 19:16:27 +0100 (Thu, May 11, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-05-05 09:54:35 +0100 (Fri, May 5, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets, QtGui
from tqdm import tqdm
import numpy as np
import time
from typing import List, Tuple, Union


MAX_ANGS = 16
LOOPS = 16


#===================================================
# overlap_functions

def non_overlapping_with_points(
        scatter_xy: np.ndarray, candidates: np.ndarray, xmargin: float, ymargin: float
        ) -> np.ndarray:
    """Finds candidates not overlapping with points.

    Args:
        scatter_xy (np.ndarray): Array of shape (N,2) containing coordinates for all scatter-points
        candidates (np.ndarray): Array of shape (K,4) with K candidate boxes
        xmargin (float): fraction of the x-dimension to use as margins for text boxes
        ymargin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping candidates with points
    """
    return np.invert(
            np.bitwise_or.reduce(
                    np.bitwise_and(
                            candidates[:, 0][:, None] - xmargin < scatter_xy[:, 0],
                            np.bitwise_and(
                                    candidates[:, 2][:, None] + xmargin > scatter_xy[:, 0],
                                    np.bitwise_and(
                                            candidates[:, 1][:, None] - ymargin < scatter_xy[:, 1],
                                            candidates[:, 3][:, None] + ymargin > scatter_xy[:, 1],
                                            ),
                                    ),
                            ),
                    axis=1,
                    )
            )


def non_overlapping_with_lines(
        lines_xyxy: np.ndarray, candidates: np.ndarray, xmargin: float, ymargin: float
        ) -> np.ndarray:
    """Finds candidates not overlapping with lines

    Args:
        lines_xyxy (np.ndarray): line segments
        candidates (np.ndarray): candidate boxes
        xmargin (float): fraction of the x-dimension to use as margins for text boxes
        ymargin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping candidates with lines.
    """
    non_intersecting = np.invert(
            np.any(
                    np.bitwise_or(
                            line_intersect(
                                    np.hstack(
                                            [
                                                candidates[:, 0:1] - xmargin,
                                                candidates[:, 1:2] - ymargin,
                                                candidates[:, 0:1] - xmargin,
                                                candidates[:, 3:] + ymargin,
                                                ]
                                            ),
                                    lines_xyxy,
                                    ),
                            np.bitwise_or(
                                    line_intersect(
                                            np.hstack(
                                                    [
                                                        candidates[:, 0:1] - xmargin,
                                                        candidates[:, 3:] + ymargin,
                                                        candidates[:, 2:3] + xmargin,
                                                        candidates[:, 3:] + ymargin,
                                                        ]
                                                    ),
                                            lines_xyxy,
                                            ),
                                    np.bitwise_or(
                                            line_intersect(
                                                    np.hstack(
                                                            [
                                                                candidates[:, 2:3] + xmargin,
                                                                candidates[:, 3:] + ymargin,
                                                                candidates[:, 2:3] + xmargin,
                                                                candidates[:, 1:2] - ymargin,
                                                                ]
                                                            ),
                                                    lines_xyxy,
                                                    ),
                                            line_intersect(
                                                    np.hstack(
                                                            [
                                                                candidates[:, 2:3] + xmargin,
                                                                candidates[:, 1:2] - ymargin,
                                                                candidates[:, 0:1] - xmargin,
                                                                candidates[:, 1:2] - ymargin,
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
                            candidates[:, 0][:, None] - xmargin < lines_xyxy[:, 0],
                            np.bitwise_and(
                                    candidates[:, 1][:, None] - ymargin < lines_xyxy[:, 1],
                                    np.bitwise_and(
                                            candidates[:, 2][:, None] + xmargin > lines_xyxy[:, 0],
                                            np.bitwise_and(
                                                    candidates[:, 3][:, None] + ymargin > lines_xyxy[:, 1],
                                                    np.bitwise_and(
                                                            candidates[:, 0][:, None] - xmargin < lines_xyxy[:, 2],
                                                            np.bitwise_and(
                                                                    candidates[:, 1][:, None] - ymargin
                                                                    < lines_xyxy[:, 3],
                                                                    np.bitwise_and(
                                                                            candidates[:, 2][:, None] + xmargin
                                                                            > lines_xyxy[:, 2],
                                                                            candidates[:, 3][:, None] + ymargin
                                                                            > lines_xyxy[:, 3],
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


def line_intersect(cand_xyxy: np.ndarray, lines_xyxy: np.ndarray) -> np.ndarray:
    """Checks if line segments intersect for all line segments and candidates.

    Args:
        cand_xyxy (np.ndarray): line segments in candidates
        lines_xyxy (np.ndarray): line segments plotted

    Returns:
        np.ndarray: Boolean array with True for non-overlapping candidate segments with line segments.
    """
    intersects = np.bitwise_and(
            ccw(cand_xyxy[:, :2], lines_xyxy[:, :2], lines_xyxy[:, 2:], False)
            != ccw(cand_xyxy[:, 2:], lines_xyxy[:, :2], lines_xyxy[:, 2:], False),
            ccw(cand_xyxy[:, :2], cand_xyxy[:, 2:], lines_xyxy[:, :2], True)
            != ccw(cand_xyxy[:, :2], cand_xyxy[:, 2:], lines_xyxy[:, 2:], True),
            )
    return intersects


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
    if cand:
        return (
                (-(x1y1[:, 1][:, None] - x3y3[:, 1]))
                * np.repeat(x2y2[:, 0:1] - x1y1[:, 0:1], x3y3.shape[0], axis=1)
        ) > (
                np.repeat(x2y2[:, 1:2] - x1y1[:, 1:2], x3y3.shape[0], axis=1)
                * (-(x1y1[:, 0][:, None] - x3y3[:, 0]))
        )
    return (
            (-(x1y1[:, 1][:, None] - x3y3[:, 1])) * (-(x1y1[:, 0][:, None] - x2y2[:, 0]))
    ) > ((-(x1y1[:, 1][:, None] - x2y2[:, 1])) * (-(x1y1[:, 0][:, None] - x3y3[:, 0])))


def non_overlapping_with_boxes(
        box_arr: np.ndarray, candidates: np.ndarray, xmargin: float, ymargin: float
        ) -> np.ndarray:
    """Finds candidates not overlapping with allocated boxes.

    Args:
        box_arr (np.ndarray): array with allocated boxes
        candidates (np.ndarray): candidate boxes
        xmargin (float): fraction of the x-dimension to use as margins for text boxes
        ymargin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping candidates with boxes.
    """
    return np.invert(
            np.any(
                    np.invert(
                            np.bitwise_or(
                                    candidates[:, 0][:, None] - xmargin > box_arr[:, 2],
                                    np.bitwise_or(
                                            candidates[:, 2][:, None] + xmargin < box_arr[:, 0],
                                            np.bitwise_or(
                                                    candidates[:, 1][:, None] - ymargin > box_arr[:, 3],
                                                    candidates[:, 3][:, None] + ymargin < box_arr[:, 1],
                                                    ),
                                            ),
                                    )
                            ),
                    axis=1,
                    )
            )


def inside_plot(
        xmin_bound: float,
        ymin_bound: float,
        xmax_bound: float,
        ymax_bound: float,
        candidates: np.ndarray,
        ) -> np.ndarray:
    """Finds candidates that are inside the plot bounds

    Args:
        xmin_bound (float):
        ymin_bound (float):
        xmax_bound (float):
        ymax_bound (float):
        candidates (np.ndarray): candidate boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping candidates with boxes.
    """
    return np.invert(
            np.bitwise_or(
                    candidates[:, 0] < xmin_bound,
                    np.bitwise_or(
                            candidates[:, 1] < ymin_bound,
                            np.bitwise_or(
                                    candidates[:, 2] > xmax_bound, candidates[:, 3] > ymax_bound
                                    ),
                            ),
                    )
            )


#===================================================
# candidates

def generate_candidates(
        w: float,
        h: float,
        x: float,
        y: float,
        xmindistance: float,
        ymindistance: float,
        xmaxdistance: float,
        ymaxdistance: float,
        nbr_candidates: int,
        ) -> np.ndarray:
    """Generates 36 candidate boxes

    Args:
        w (float): width of box
        h (float): height of box
        x (float): xmin of box
        y (float): ymin of box
        xmindistance (float): fraction of the x-dimension to use as margins for text bboxes
        ymindistance (float): fraction of the y-dimension to use as margins for text bboxes
        xmaxdistance (float): fraction of the x-dimension to use as max distance for text bboxes
        ymaxdistance (float): fraction of the y-dimension to use as max distance for text bboxes
        nbr_candidates (int): nbr of candidates to use. If <1 or >36 uses all 36

    Returns:
        np.ndarray: candidate boxes array
    """
    angs = np.tile(np.linspace(0.0, np.pi * 2.0 - (2 * np.pi / MAX_ANGS), MAX_ANGS), LOOPS)
    ll = np.linspace(min(xmindistance, ymindistance), max(xmaxdistance, ymaxdistance), LOOPS)

    distx = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)
    disty = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)

    ss = x + np.sin(angs) * (distx + min(w, h) / 2)
    cc = y + np.cos(angs) * (disty + min(w, h) / 2)

    # # plot a figure to check the size
    # import matplotlib
    #
    # matplotlib.use('Qt5Agg')
    # from mpl_toolkits import mplot3d
    # import matplotlib.pyplot as plt
    #
    # fig = plt.figure(figsize=(10, 8), dpi=100)
    # axS = fig.gca()
    #
    # axS.plot(ss, cc, label = 'Best Fit')

    return np.vstack([ss - w / 2, cc - h / 2, ss + w / 2, cc + h / 2]).transpose()


#===================================================
# non_overlapping_boxes

def get_non_overlapping_boxes(
        original_boxes: list,
        xlims: Tuple[float, float],
        ylims: Tuple[float, float],
        margin: float,
        minx_distance: float,
        maxx_distance: float,
        miny_distance: float,
        maxy_distance: float,
        verbose: bool,
        nbr_candidates: int,
        draw_all: bool,
        include_arrows: bool,
        scatter_xy: np.ndarray = None,
        lines_xyxy: np.ndarray = None,
        boxes_xyxy: np.ndarray = None,
        ) -> Tuple[List[Tuple[float, float, float, float, str, int]], List[int]]:
    """Finds boxes that do not have an overlap with any other objects.

    Args:
        original_boxes (np.ndarray): original boxes containing texts.
        xlims (Tuple[float, float]): x-limits of plot gotten from ax.get_ylim()
        ylims (Tuple[float, float]): y-limits of plot gotten from ax.get_ylim()
        margin (float): parameter for margins between objects. Increase for larger margins to points and lines.
        minx_distance (float): parameter for max distance between text and origin.
        maxx_distance (float): parameter for max distance between text and origin.
        miny_distance (float): parameter for max distance between text and origin.
        maxy_distance (float): parameter for max distance between text and origin.
        verbose (bool): prints progress using tqdm.
        nbr_candidates (int): Sets the number of candidates used.
        draw_all (bool): Draws all texts after allocating as many as possible despit overlap.
        include_arrows (bool): Successively add line-segments between points and labels as new labels are found.
        scatter_xy (np.ndarray, optional): 2d array of scattered points in plot.
        lines_xyxy (np.ndarray, optional): 2d array of line segments in plot.
        boxes_xyxy (np.ndarray, optional): 2d array of boxes in plot.

    Returns:
        Tuple[List[Tuple[float, float, float, float, str, int]], List[int]]: data of non-overlapping boxes and indices of overlapping boxes.
    """
    xmin_bound, xmax_bound = xlims
    ymin_bound, ymax_bound = ylims

    xmargin = 0  # (xmax_bound - xmin_bound) * margin
    ymargin = 0  # (ymax_bound - ymin_bound) * margin
    xmindistance = 2  # (xmax_bound - xmin_bound) * minx_distance
    ymindistance = 2  # (ymax_bound - ymin_bound) * miny_distance
    xmaxdistance = 200  # (xmax_bound - xmin_bound) * maxx_distance
    ymaxdistance = 200  # (ymax_bound - ymin_bound) * maxy_distance

    box_arr = np.zeros((0, 4))

    # Iterate original boxes and find ones that do not overlap by creating multiple candidates
    non_overlapping_boxes = []
    overlapping_boxes_inds = []
    for i, box in tqdm(enumerate(original_boxes), disable=not verbose):
        x_original, y_original, w, h, s = box

        candidates = generate_candidates(
                w,
                h,
                x_original,
                y_original,
                xmindistance,
                ymindistance,
                xmaxdistance,
                ymaxdistance,
                nbr_candidates=nbr_candidates,
                )

        # Check for overlapping
        if scatter_xy is None:
            non_op = np.zeros((candidates.shape[0],)) == 0
        else:
            non_op = non_overlapping_with_points(
                    scatter_xy, candidates, xmargin, ymargin
                    )
        if lines_xyxy is None:
            non_ol = np.zeros((candidates.shape[0],)) == 0
        else:
            non_ol = non_overlapping_with_lines(
                    lines_xyxy, candidates, xmargin, ymargin
                    )

        if boxes_xyxy is None:
            non_ob = np.zeros((candidates.shape[0],)) == 0
        else:
            non_ob = non_overlapping_with_boxes(
                    boxes_xyxy, candidates, xmargin, ymargin
                    )

        # NOTE:ED - add non_overlapping with other boxes?

        if box_arr.shape[0] == 0:
            non_orec = np.zeros((candidates.shape[0],)) == 0
        else:
            non_orec = non_overlapping_with_boxes(box_arr, candidates, xmargin, ymargin)

        inside = inside_plot(xmin_bound, ymin_bound, xmax_bound, ymax_bound, candidates)
        inside |= True  # NOTE:ED - HACK all inside the window
        #   need to change to pixels as the peak bounds can be larger than the spectrum-display

        # Validate (could use logical_and here, not sure which is quicker)
        ok_candidates = np.where(
                np.bitwise_and(
                        non_ob, np.bitwise_and(
                                non_ol, np.bitwise_and(
                                        non_op, np.bitwise_and(non_orec, inside))
                                )
                        )
                )[0]

        if len(ok_candidates) > 0:
            # find the index of the nearest candidate to the original-point
            centres = np.tile(np.array([x_original, y_original, 0.0, 0.0]).transpose(), (len(ok_candidates), 1))
            offset = candidates[ok_candidates] - centres
            min_dists = np.linalg.norm(offset[:, :2], axis=1)
            ind = np.argmin(min_dists)

            # # plot a figure to check the size
            # import matplotlib
            #
            # matplotlib.use('Qt5Agg')
            # from mpl_toolkits import mplot3d
            # import matplotlib.pyplot as plt
            #
            # fig = plt.figure(figsize=(10, 8), dpi=100)
            # axS = fig.gca()
            #
            # axS.plot(offset[:, 0], offset[:, 1], label = 'Offset')

            best_candidate = candidates[ok_candidates[ind], :]
            box_arr = np.vstack(
                    [
                        box_arr,
                        np.array(
                                [
                                    best_candidate[0],
                                    best_candidate[1],
                                    best_candidate[0] + w,
                                    best_candidate[1] + h,
                                    ]
                                ),
                        ]
                    )
            non_overlapping_boxes.append(
                    (best_candidate[0], best_candidate[1], w, h, s, i)
                    )

            if include_arrows:
                # add a new line to exclude between the symbol and the best candidate position
                # NOTE:ED - this only accounts for previous edges, does not check if the new edge would overlay an existing label
                #   needs another validate check for that - doesn't actually make much difference :|
                new_line = np.array([[x_original, y_original, best_candidate[0] + w / 2, best_candidate[1] + h / 2]])
                lines_xyxy = new_line if lines_xyxy is None else np.vstack([lines_xyxy, new_line])

        else:
            if draw_all:
                ok_candidates = np.where(np.bitwise_and(non_orec, inside))[0]
                if len(ok_candidates) > 0:
                    best_candidate = candidates[ok_candidates[0], :]
                    box_arr = np.vstack(
                            [
                                box_arr,
                                np.array(
                                        [
                                            best_candidate[0],
                                            best_candidate[1],
                                            best_candidate[0] + w,
                                            best_candidate[1] + h,
                                            ]
                                        ),
                                ]
                            )
                    non_overlapping_boxes.append(
                            (best_candidate[0], best_candidate[1], w, h, s, i)
                            )

                    if include_arrows:
                        # add a new line to exclude between the symbol and the best candidate position
                        new_line = np.array([[x_original, y_original, best_candidate[0] + w / 2, best_candidate[1] + h / 2]])
                        lines_xyxy = new_line if lines_xyxy is None else np.vstack([lines_xyxy, new_line])

                else:
                    overlapping_boxes_inds.append(i)
            else:
                overlapping_boxes_inds.append(i)

    return non_overlapping_boxes, overlapping_boxes_inds


#===================================================
# __init__


# from ccpn.util.decorators import profile
#
#
# @profile()
def allocate_text(
        x: Union[np.ndarray, List[float]],
        y: Union[np.ndarray, List[float]],
        text_list: List[str],
        x_scatter: Union[np.ndarray, List[float]] = None,
        y_scatter: Union[np.ndarray, List[float]] = None,
        x_lines: List[Union[np.ndarray, List[float]]] = None,
        y_lines: List[Union[np.ndarray, List[float]]] = None,
        x_boxes: List[Union[np.ndarray, List[float]]] = None,  # merge then separate in method?
        y_boxes: List[Union[np.ndarray, List[float]]] = None,
        textsize: int = 10,
        margin: float = 0.01,
        minx_distance: float = 0.015,
        maxx_distance: float = 0.07,
        miny_distance: float = 0.015,
        maxy_distance: float = 0.07,
        verbose: bool = False,
        draw_lines: bool = True,
        linecolor: str = "r",
        draw_all: bool = True,
        nbr_candidates: int = 100,
        linewidth: float = 1,
        textcolor: str = "k",
        xlims: tuple = (0, 1),
        ylims: tuple = (0, 1),
        include_arrows = False,
        ):
    """Main function of allocating text-boxes in matplotlib plot

    Args:
        x (Union[np.ndarray, List[float]]): x-coordinates of texts 1d array/list.
        y (Union[np.ndarray, List[float]]): y-coordinates of texts 1d array/list.
        text_list (List[str]): list of texts.
        x_scatter (Union[np.ndarray, List[float]], optional): x-coordinates of all scattered points in plot 1d array/list. Defaults to None.
        y_scatter (Union[np.ndarray, List[float]], optional): y-coordinates of all scattered points in plot 1d array/list. Defaults to None.
        x_lines (List[Union[np.ndarray, List[float]]], optional): x-coordinates of all lines in plot list of 1d arrays/lists. Defaults to None.
        y_lines (List[Union[np.ndarray, List[float]]], optional): y-coordinates of all lines in plot list of 1d arrays/lists. Defaults to None.
        x_boxes (List[Union[np.ndarray, List[float]]], optional): x-coordinates of all boxes in plot list of 1d arrays/lists. Defaults to None.
        y_boxes (List[Union[np.ndarray, List[float]]], optional): y-coordinates of all boxes in plot list of 1d arrays/lists. Defaults to None.
        textsize (int, optional): size of text. Defaults to 10.
        margin (float, optional): parameter for margins between objects. Increase for larger margins to points and lines. Defaults to 0.01.
        minx_distance (float, optional): parameter for min distance between text and origin. Defaults to 0.015.
        maxx_distance (float, optional): parameter for max distance between text and origin. Defaults to 0.07.
        miny_distance (float, optional): parameter for min distance between text and origin. Defaults to 0.015.
        maxy_distance (float, optional): parameter for max distance between text and origin. Defaults to 0.07.
        verbose (bool, optional): prints progress using tqdm. Defaults to False.
        draw_lines (bool, optional): draws lines from original points to textboxes. Defaults to True.
        linecolor (str, optional): color code of the lines between points and text-boxes. Defaults to "r".
        draw_all (bool, optional): Draws all texts after allocating as many as possible despit overlap. Defaults to True.
        nbr_candidates (int, optional): Sets the number of candidates used. Defaults to 0.
        linewidth (float, optional): width of line. Defaults to 1.
        textcolor (str, optional): color code of the text. Defaults to "k".
        include_arrows (bool): successively add line segments between points and labels as new labels are found.
    """
    t0 = time.time()

    # Ensure good inputs
    assert len(x) == len(y)
    x = np.array(x)
    y = np.array(y)

    if x_scatter is not None:
        assert y_scatter is not None
    if y_scatter is not None:
        assert x_scatter is not None
        assert len(y_scatter) == len(x_scatter)
        x_scatter = np.array(x_scatter)
        y_scatter = np.array(y_scatter)

    if x_lines is not None:
        assert y_lines is not None
    if y_lines is not None:
        assert x_lines is not None
        assert all(
                [len(x_line) == len(y_line) for x_line, y_line in zip(x_lines, y_lines)]
                )
        x_lines = [np.array(x_line) for x_line in x_lines]
        y_lines = [np.array(y_line) for y_line in y_lines]

    if x_boxes is not None:
        assert y_boxes is not None
    if y_boxes is not None:
        assert x_boxes is not None
        assert all(
                [len(x_box) == len(y_box) for x_box, y_box in zip(x_boxes, y_boxes)]
                )
        x_boxes = [np.array(x_box) for x_box in x_boxes]
        y_boxes = [np.array(y_box) for y_box in y_boxes]

    assert minx_distance <= maxy_distance
    assert minx_distance >= margin
    assert miny_distance <= maxy_distance
    assert miny_distance >= margin

    # Create boxes in original plot
    if verbose:
        print("Creating boxes from texts")
    fontMetric = QtGui.QFontMetricsF(QtGui.QFont("Open Sans", textsize))
    bbox = fontMetric.boundingRect

    original_boxes = []  # currently a mix of co-ordinates and texts
    for x_coord, y_coord, s in tqdm(zip(x, y, text_list), disable=not verbose):
        rect = bbox(s)
        w, h = rect.width(), rect.height()

        original_boxes.append((x_coord, y_coord, w, h, s))  # check the width of the strings

    # Process extracted text-boxes
    if verbose:
        print("Processing")
    if x_scatter is None:
        scatterxy = None
    else:
        scatterxy = np.transpose(np.vstack([x_scatter, y_scatter]))

    if x_lines is None:
        lines_xyxy = None
    else:
        lines_xyxy = lines_to_segments(x_lines, y_lines)

    if x_boxes is None:
        boxes_xyxy = None
    else:
        boxes_xyxy = boxes_to_segments(x_boxes, y_boxes)

    non_overlapping_boxes, overlapping_boxes_inds = get_non_overlapping_boxes(
            original_boxes,
            xlims,
            ylims,
            margin,
            minx_distance,
            maxx_distance,
            miny_distance,
            maxy_distance,
            verbose,
            nbr_candidates,
            draw_all,
            include_arrows,
            scatter_xy=scatterxy,
            lines_xyxy=lines_xyxy,
            boxes_xyxy=boxes_xyxy,
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
    else:
        if y < ymin:
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


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# NOTE:ED - needs to be moved to textalloc folder when done


# from sandbox.Ed.textalloc.src import allocate_text


if current.strip:
    spectrumDisplay = current.strip.spectrumDisplay

    # get the list of texts/positions/points
    v3views = list(spectrumDisplay.peakViews)
    strip = current.strip  # spectrumDisplay.strips[0]
    px, py = strip._CcpnGLWidget.pixelX, strip._CcpnGLWidget.pixelY  # ppm-per-pixel
    ppmPoss = strip.positions
    ppmWidths = strip.widths

    _data2Obj = strip.project._data2Obj
    labels = [(_data2Obj.get(pLabel.stringObject._wrappedData.findFirstPeakView(peakListView=plv._wrappedData.peakListView)),
               pLabel)
              for plv, ss in strip._CcpnGLWidget._GLPeaks._GLLabels.items() if plv.isDisplayed
              for pLabel in ss.stringList]

    # now have labels.text..
    # pixel width/height -> labels.width/height

    posnX = []
    posnY = []
    facsX = []
    facsY = []
    pppX = []
    pppY = []
    data = []
    ws = []
    hs = []

    for view, label in labels:
        corePeak = view.peak
        peak = corePeak._wrappedData

        dims = spectrumDisplay.spectrumViews[0].displayOrder  # 1-based for the model
        ppmPerPoints = corePeak.spectrum.ppmPerPoints
        peakDimX = peak.findFirstPeakDim(dim=dims[0])
        peakDimY = peak.findFirstPeakDim(dim=dims[1])

        posnX.append(int(peakDimX.value / px))  # pixelPosition
        if spectrumDisplay.is1D:
            posnY.append(int(corePeak.height / py))
        else:
            posnY.append(int(peakDimY.value / py))
        ws.append(label.width)
        hs.append(label.height)

    posnX, posnY = np.array(posnX), np.array(posnY)
    minX, maxX = np.min(posnX), np.max(posnX)
    minY, maxY = np.min(posnY), np.max(posnY)
    meanX, meanY = np.mean(posnX), np.mean(posnY)
    maxW, maxH = max(ws), max(hs)
    maxX -= minX
    maxY -= minY

    # process from the mean peak-position outwards
    sortPos = np.argsort((posnX - meanX)**2 + (posnY - meanY)**2)
    posnX = posnX[sortPos]
    posnY = posnY[sortPos]
    labels = [labels[ind] for ind in sortPos]

    kx, ky = 2, 2
    xlims = (0, maxX + kx * 2 * maxW)
    ylims = (0, maxY + ky * 2 * maxH)

    posnX = posnX - minX + kx * maxW
    posnY = posnY - minY + ky * maxH

    texts = [val.text for _, val in labels]  # grab the labels

    HALF_POINTSIZE = 12 // 2
    x_boxes = [np.array([xx - HALF_POINTSIZE, xx + HALF_POINTSIZE]) for xx in posnX]
    y_boxes = [np.array([yy - HALF_POINTSIZE, yy + HALF_POINTSIZE]) for yy in posnY]

    output = allocate_text(posnX, posnY, text_list=texts,
                           xlims=xlims,
                           ylims=ylims,
                           x_boxes=x_boxes, y_boxes=y_boxes,  # boxes to avoid
                           textsize=15,
                           nbr_candidates=300,
                           margin=0.0,
                           minx_distance=0.02,  # sort this, have changed internally to pixels
                           maxx_distance=0.2,
                           miny_distance=0.03,
                           maxy_distance=1.0,
                           include_arrows=False,
                           )

    non_over, over_ind = output

    # need to check which over_ind are bad and discard
    for posx, posy, moved, (view, ss) in zip(posnX, posnY, non_over, labels):
        # view.textOffset = (moved[0] - posx, moved[1] - posy)  # pixels
        # offset is always orientated +ve to the top-right
        view.textOffset = (moved[0] - posx) * np.abs(px), (moved[1] - posy) * np.abs(py)  # ppm

    if over_ind:
        print(f'Contains bad labels {over_ind}')
