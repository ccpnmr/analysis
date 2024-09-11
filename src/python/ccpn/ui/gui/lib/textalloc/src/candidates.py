"""
Module Documentation here

Expanded from the original.
Original by Christoffer Kjellson.
Available from github; https://github.com/ckjellson/textalloc
"""

# MIT License

# Copyright (c) 2022 Christoffer Kjellson

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-08-07 16:25:09 +0100 (Wed, August 07, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Original by Christoffer Kjellson $"
__date__ = "$Date: 2022 $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np


MIN_ANGS = 16
MAX_ANGS = 64
LOOPS = 16


def generate_coordinates(w, h, minx_distance, maxx_distance, miny_distance, maxy_distance):
    """Generate the coordinates for the candidates locations.
    Returns sin/cos coordinates in concentric circles.
    """
    # angs = np.tile(np.linspace(0.0, np.pi * 2.0 - (2 * np.pi / MAX_ANGS), MAX_ANGS), LOOPS)
    # ll = np.linspace(min(minx_distance, miny_distance), max(maxx_distance, maxy_distance), LOOPS)
    # distx = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)
    # disty = np.tile(ll, (MAX_ANGS, 1)).transpose().reshape(MAX_ANGS * LOOPS)
    # ss = np.sin(angs) * (distx + min(w, h) / 2)
    # cc = np.cos(angs) * (disty + min(w, h) / 2)
    #
    all_points = np.zeros((0, 2))

    num_points_per_ring = np.linspace(MIN_ANGS, MAX_ANGS, LOOPS)
    radii = np.linspace(min(minx_distance, miny_distance) + min(w, h) / 2, max(maxx_distance, maxy_distance), LOOPS)

    for ring_idx, num_points, radius in zip(range(LOOPS), num_points_per_ring, radii):
        int_points = int(num_points)
        theta = np.linspace(0, 2 * np.pi - (2 * np.pi / int_points), int_points)
        x = radius * np.sin(theta)
        y = radius * np.cos(theta)
        points = np.column_stack((x, y))
        all_points = np.vstack([all_points, points])

    return all_points[:, 0], all_points[:, 1]


def generate_candidates(
        w: float,
        h: float,
        x: float,
        y: float,
        minx_distance: float,
        miny_distance: float,
        maxx_distance: float,
        maxy_distance: float,
        ) -> np.ndarray:
    """Generates MAX_ANGS*LOOPS candidate boxes, in concentric rings from the target point.

    Candidates boxes are centred on the coordinates, ordered bottom-left -> top-right.

    Args:
        w (float): width of box
        h (float): height of box
        x (float): xmin of box
        y (float): ymin of box
        minx_distance (float): fraction of the x-dimension to use as margins for text bboxes
        miny_distance (float): fraction of the y-dimension to use as margins for text bboxes
        maxx_distance (float): fraction of the x-dimension to use as max distance for text bboxes
        maxy_distance (float): fraction of the y-dimension to use as max distance for text bboxes

    Returns:
        np.ndarray: candidate boxes array
    """
    ss, cc = generate_coordinates(w, h, minx_distance, maxx_distance, miny_distance, maxy_distance)

    # return np.column_stack([ss + (x - w / 2), cc + (y - h / 2), ss + (x + w / 2), cc + (y + h / 2)])
    return np.column_stack([ss + x, cc + y, ss + (x + w), cc + (y + h)])


def generate_candidate_lines(
        w: float,
        h: float,
        x: float,
        y: float,
        minx_distance: float,
        miny_distance: float,
        maxx_distance: float,
        maxy_distance: float,
        ) -> np.ndarray:
    """Generates MAX_ANGS*LOOPS candidate lines, from concentric rings to the target point.

    Args:
        w (float): width of box
        h (float): height of box
        x (float): xmin of box
        y (float): ymin of box
        minx_distance (float): fraction of the x-dimension to use as margins for text bboxes
        miny_distance (float): fraction of the y-dimension to use as margins for text bboxes
        maxx_distance (float): fraction of the x-dimension to use as max distance for text bboxes
        maxy_distance (float): fraction of the y-dimension to use as max distance for text bboxes

    Returns:
        np.ndarray: candidate boxes array
    """
    ss, cc = generate_coordinates(w, h, minx_distance, maxx_distance, miny_distance, maxy_distance)

    ones = np.ones_like(ss)
    # return np.column_stack([x * ones, y * ones, x + ss, y + cc])
    return np.column_stack([x * ones, y * ones, ss + (x + w / 2), cc + (y + h / 2)])


def main():
    _TESTPLOT = True

    # plot a figure to check the size
    import matplotlib

    matplotlib.use('Qt5Agg')
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(10, 10), dpi=100)
    axS = fig.gca()
    # axS.plot(ss, cc, label='Best Fit')

    lines_xyxy = generate_candidate_lines(70, 20, 90, 90, 10, 10, 300, 300)

    for ii in range(lines_xyxy.shape[0]):
        row = lines_xyxy[ii, :]
        axS.plot(row[::2], row[1::2], linewidth=3)

    plt.show()


if __name__ == '__main__':
    main()
