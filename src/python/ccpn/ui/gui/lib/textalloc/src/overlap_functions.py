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
__dateModified__ = "$dateModified: 2023-05-18 18:49:18 +0100 (Thu, May 18, 2023) $"
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
                                                                    candidates[:, 1][:, None] - ymargin < lines_xyxy[:, 3],
                                                                    np.bitwise_and(
                                                                            candidates[:, 2][:, None] + xmargin > lines_xyxy[:, 2],
                                                                            candidates[:, 3][:, None] + ymargin > lines_xyxy[:, 3],
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


def non_overlapping_with_lines_to_boxes(
        candidate_lines: np.ndarray, boxes: np.ndarray, xmargin: float, ymargin: float
        ) -> np.ndarray:
    """Finds boxes not overlapping with lines.

    boxes must be sorted min_x, min_y, max_x, max_y.

    Args:
        candidate_lines (np.ndarray): candidate line segments
        boxes (np.ndarray): target boxes
        xmargin (float): fraction of the x-dimension to use as margins for text boxes
        ymargin (float): fraction of the y-dimension to use as margins for text boxes

    Returns:
        np.ndarray: Boolean array of shape (K,) with True for non-overlapping boxes with lines.
    """
    non_intersecting = np.invert(
            np.any(
                    np.bitwise_or(
                            line_intersect(
                                    candidate_lines,
                                    np.hstack(
                                            [
                                                # left-hand side of box
                                                boxes[:, 0:1] - xmargin,  # bottom-left
                                                boxes[:, 1:2] - ymargin,
                                                boxes[:, 0:1] - xmargin,  # top-left
                                                boxes[:, 3:] + ymargin,
                                                ]
                                            ),
                                    ),
                            np.bitwise_or(
                                    line_intersect(
                                            candidate_lines,
                                            np.hstack(
                                                    [
                                                        # top-edge of box
                                                        boxes[:, 0:1] - xmargin,  # top-left
                                                        boxes[:, 3:] + ymargin,
                                                        boxes[:, 2:3] + xmargin,  # top-right
                                                        boxes[:, 3:] + ymargin,
                                                        ]
                                                    ),
                                            ),
                                    np.bitwise_or(
                                            line_intersect(
                                                    candidate_lines,
                                                    np.hstack(
                                                            [
                                                                # right-hand side of box
                                                                boxes[:, 2:3] + xmargin,  # top-right
                                                                boxes[:, 3:] + ymargin,
                                                                boxes[:, 2:3] + xmargin,  # bottom-right
                                                                boxes[:, 1:2] - ymargin,
                                                                ]
                                                            ),
                                                    ),
                                            line_intersect(
                                                    candidate_lines,
                                                    np.hstack(
                                                            [
                                                                # bottom-edge of box
                                                                boxes[:, 2:3] + xmargin,  # bottom-right
                                                                boxes[:, 1:2] - ymargin,
                                                                boxes[:, 0:1] - xmargin,  # bottom-left
                                                                boxes[:, 1:2] - ymargin,
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
                            candidate_lines[:, 0][:, None] + xmargin < boxes[:, 0],
                            np.bitwise_and(
                                    candidate_lines[:, 1][:, None] + ymargin < boxes[:, 1],
                                    np.bitwise_and(
                                            candidate_lines[:, 2][:, None] - xmargin > boxes[:, 0],
                                            np.bitwise_and(
                                                    candidate_lines[:, 3][:, None] - ymargin > boxes[:, 1],
                                                    np.bitwise_and(
                                                            candidate_lines[:, 0][:, None] + xmargin < boxes[:, 2],
                                                            np.bitwise_and(
                                                                    candidate_lines[:, 1][:, None] + ymargin < boxes[:, 3],
                                                                    np.bitwise_and(
                                                                            candidate_lines[:, 2][:, None] - xmargin > boxes[:, 2],
                                                                            candidate_lines[:, 3][:, None] - ymargin > boxes[:, 3],
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


def non_overlapping_with_lines_to_lines(candidates_lines: np.ndarray, lines_xyxy: np.ndarray) -> np.ndarray:
    """Checks if line segments intersect for all candidates and line segments.

    Args:
        candidates_lines (np.ndarray): line segments in candidates
        lines_xyxy (np.ndarray): line segments plotted

    Returns:
        np.ndarray: Boolean array with True for non-overlapping line segments with candidates.
    """
    return np.invert(np.any(line_intersect(candidates_lines, lines_xyxy),
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


def main():
    MAX_ANGS = 8
    LOOPS = 3
    xmindistance = ymindistance = 10
    xmaxdistance = ymaxdistance = 100
    x, y = 5, 5

    # import sys
    # import numpy as np
    # from PyQt5 import QtGui, QtWidgets
    #
    # app = QtWidgets.QApplication(sys.argv)

    angs = np.tile(np.linspace(0.0, np.pi * 2.0 - (2 * np.pi / MAX_ANGS), MAX_ANGS), LOOPS)
    ll = np.linspace(min(xmindistance, ymindistance), max(xmaxdistance, ymaxdistance), LOOPS)

    distx = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)
    disty = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)

    ss = x + np.sin(angs) * distx
    cc = y + np.cos(angs) * disty

    # plot a figure to check the size
    import matplotlib

    matplotlib.use('Qt5Agg')
    from mpl_toolkits import mplot3d
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 8), dpi=100)
    axS = fig.gca()

    axS.plot(ss, cc, label='Best Fit')

    lines = np.vstack([np.tile([x, y], (ss.shape[0], 1)).transpose(), ss, cc]).transpose()
    lines_xyxy = np.array([[36, -45, 47, 16], [-71, 11, -21, -32], [60, 44, 87, 20]])

    lInt = line_intersect(lines, lines_xyxy)
    print(lInt)
    print(np.invert(np.any(lInt, axis=1)))  # good lines

    # need to order min -> max?
    boxes_xyxy = np.array([[36, -45, 47, 16], [-71, -32, -21, 1], [60, 20, 87, 44], [12, -16, -5, -20]])
    print(non_overlapping_with_lines_to_boxes(lines,
                                              boxes_xyxy, 0, 0))
    plt.show()


if __name__ == '__main__':
    main()
