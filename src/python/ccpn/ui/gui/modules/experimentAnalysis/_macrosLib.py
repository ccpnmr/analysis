"""
A set of private functions called for building custom macros.

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-02-17 17:35:26 +0000 (Fri, February 17, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-02-17 14:03:22 +0000 (Fri, February 17, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.util.Common import percentage
import numpy as np
from ccpn.util.Path import aPath
import matplotlib.pyplot as plt
import math
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MultipleLocator
from ccpn.ui.gui.widgets.DrawSS import plotSS
from ccpn.ui.gui.widgets.MessageDialog import showWarning


def _makeFigureLayoutWithOneColumn(numberOfRows,  height_ratios, figsize=(5, 3.5), dpi=300):
    fig = plt.figure(figsize=figsize, dpi=dpi)
    if len(height_ratios) != numberOfRows:
        height_ratios = [1]*numberOfRows
    spec = fig.add_gridspec(nrows=numberOfRows, ncols=1, height_ratios=height_ratios)
    axes= []
    for row in range(numberOfRows):
        axis = fig.add_subplot(spec[row, 0])
        axes.append(axis)
    return fig,  axes

def _setRightTopSpinesOff(ax):
    ax.spines[['right', 'top']].set_visible(False)

def _setYLabelOffset(ax, xoffset=-0.05, yoffset=0.5):
    # align the labels to vcenter and middle
    ax.yaxis.set_label_coords(xoffset, yoffset)  # align the labels to vcenter and middle

def _setXTicks(ax, labelMajorSize, labelMinorSize):
    ml = MultipleLocator(1)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(ml)
    ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)

def _setCommonYLim(ax, ys):
    extraY = np.ceil(percentage(30, np.max(ys)))
    ylim = np.max(ys) + extraY
    ax.set_ylim([0, ylim])

def _setJoinedX(mainAxis, otherAxes):
    mainAxis.get_shared_x_axes().join(mainAxis, *otherAxes)


def _getExportingPath(macroPath, exportingFilePath=None, suffix='.pdf'):

    """
    :param macroPath: the filepath of the running macro
    :param exportingFilePath:  a user defined path or None to use the default as the macro directory and macro name
    :param suffix: default '.pdf'
    :return: aPath
    ## get the path. no complex checking for paths. This is just for a macro!
    """
    if exportingFilePath is None:  # use the macro file name
        filePath = aPath(macroPath).withoutSuffix()
    else:
        filePath = aPath(exportingFilePath)
    filePath = filePath.assureSuffix(suffix)
    return filePath


def _getDataTableForMacro(dataTableName):
    from ccpn.core.DataTable import DataTable
    from ccpn.core.lib.Pid import createPid
    from ccpn.framework.Application import  getProject

    project = getProject()
    if project is None:
        raise RuntimeError('Cannot find Project. This macro can be run only within the Analysis V3 application')
    DT = DataTable.shortClassName
    pid = createPid(DT, dataTableName)
    dataTable = project.getByPid(pid)
    if dataTable is None:
        errorMess = f'''\nCannot find the datatable named:  "{dataTableName}" . 
        \n
        Ensure you have the correct dataTable in the project and set the same name in the macro. 
        (See the User-Data section and general documentation on this macro). '''
        showWarning('Datatable not found', errorMess)
        raise RuntimeError(errorMess)
    return dataTable
