"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-11-30 11:22:05 +0000 (Wed, November 30, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-11-09 19:19:21 +0000 (Wed, November 9, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import contextlib

from PyQt5 import QtWidgets, QtGui


def alignWidgets(self, columnScale=None):
    """Align the first column of widgets
    """
    from ccpn.ui.gui.widgets.Font import getTextDimensionsFromFont

    # get all the children that are QWidgets
    widgets = self.findChildren(QtWidgets.QWidget)
    maxW = 0
    for widg in widgets:
        with contextlib.suppress(Exception):
            # try and read a font from the widget
            fontMetric = QtGui.QFontMetricsF(widg.font())
            bbox = fontMetric.boundingRect

            # get an estimate for the width
            maxW = max(maxW, bbox(f'{widg.get()}__').width())

    if maxW:
        # set the size of the first column for normal widgets
        if (layout := self.getLayout()):
            layout.setColumnMinimumWidth(0, maxW)
            if columnScale:
                layout.setColumnMinimumWidth(1, maxW * columnScale)

        # try and align the compound-widgets
        for widg in widgets:
            with contextlib.suppress(Exception):
                if columnScale:
                    widths = [maxW] + [maxW * columnScale] * (len(widg._widgets) - 1)
                else:
                    widths = [maxW] + [None] * (len(widg._widgets) - 1)
                widg.setFixedWidths(widths)
