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
__dateModified__ = "$dateModified: 2023-05-11 19:16:28 +0100 (Thu, May 11, 2023) $"
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
from typing import Tuple, List
from .candidates import generate_candidates
from .overlap_functions import non_overlapping_with_points, non_overlapping_with_lines, \
    non_overlapping_with_boxes, inside_plot


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
        draw_all (bool): Draws all texts after allocating as many as possible despite overlap.
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
    for i, box in enumerate(original_boxes):
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

        if box_arr.shape[0] == 0:
            non_orec = np.zeros((candidates.shape[0],)) == 0
        else:
            non_orec = non_overlapping_with_boxes(box_arr, candidates, xmargin, ymargin)

        inside = inside_plot(xmin_bound, ymin_bound, xmax_bound, ymax_bound, candidates)
        inside |= True  # NOTE:ED - HACK, all inside the window

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

        elif draw_all:
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
