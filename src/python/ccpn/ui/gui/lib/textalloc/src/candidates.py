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
__dateModified__ = "$dateModified: 2023-05-18 18:49:17 +0100 (Thu, May 18, 2023) $"
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


MAX_ANGS = 16
LOOPS = 24


def generate_candidates(
        w: float,
        h: float,
        x: float,
        y: float,
        xmindistance: float,
        ymindistance: float,
        xmaxdistance: float,
        ymaxdistance: float,
        ) -> np.ndarray:
    """Generates MAX_ANGS*LOOPS candidate boxes, in concentric rings from the target point.

    Args:
        w (float): width of box
        h (float): height of box
        x (float): xmin of box
        y (float): ymin of box
        xmindistance (float): fraction of the x-dimension to use as margins for text bboxes
        ymindistance (float): fraction of the y-dimension to use as margins for text bboxes
        xmaxdistance (float): fraction of the x-dimension to use as max distance for text bboxes
        ymaxdistance (float): fraction of the y-dimension to use as max distance for text bboxes

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


def generate_candidate_lines(
        w: float,
        h: float,
        x: float,
        y: float,
        xmindistance: float,
        ymindistance: float,
        xmaxdistance: float,
        ymaxdistance: float,
        ) -> np.ndarray:
    """Generates MAX_ANGS*LOOPS candidate lines, from concentric rings to the target point.

    Args:
        w (float): width of box
        h (float): height of box
        x (float): xmin of box
        y (float): ymin of box
        xmindistance (float): fraction of the x-dimension to use as margins for text bboxes
        ymindistance (float): fraction of the y-dimension to use as margins for text bboxes
        xmaxdistance (float): fraction of the x-dimension to use as max distance for text bboxes
        ymaxdistance (float): fraction of the y-dimension to use as max distance for text bboxes

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

    return np.vstack([np.tile([x, y], (ss.shape[0], 1)).transpose(), ss, cc]).transpose()
