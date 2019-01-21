"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-05-17 13:51:05 +0000 (Wed, May 17, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets, QtCore


class Spacer(QtWidgets.QSpacerItem):
    """
    Widget used to put spaces into modules and popups.
    """

    def __init__(self, parent, width, height, *args, **kwds):
        """
        Add a spacer item to the layout of parent
        :param parent: parent widget (required)
        :param args: passed to SpacerItem
        :param kwds: grid
        """
        QtWidgets.QSpacerItem.__init__(self, width, height, *args)

        if parent is None:
            raise ValueError('Spacer: parent parameter cannot be None')

        grid = kwds.get('grid')
        if not isinstance(grid, (list,tuple)) or len(grid) != 2:
            raise ValueError('grid parameter is required and should be a tuple or list with two elements (row, column)')

        gridSpan = kwds.setdefault('gridSpan', (1,1))
        if not isinstance(gridSpan, (list,tuple)) or len(grid) != 2:
            raise ValueError('gridSpan parameter should be a tuple or list with two elements (rowSpan, columnSpan)')

        parent.getLayout().addItem(self, grid[0], grid[1], gridSpan[0], gridSpan[1])
