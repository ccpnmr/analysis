#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-15 19:08:16 +0100 (Mon, August 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
######## gui/ui imports ########
import ccpn.ui.gui.widgets.GuiTable as gt
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiTable import _ExperimentalAnalysisTableABC, TablePanel


class _RelaxationGuiTable(_ExperimentalAnalysisTableABC):

    className = guiNameSpaces.RelaxationTablePanel

    _fittingColumnsDefs = {
        sv.DECAY: {gt.NAME: sv.DECAY,
            gt.GETTER: lambda row: gt._getValueByHeader(row, sv.DECAY),
            gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
            gt.TIPTEXT: gt._makeTipText(sv.DECAY, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: False
            },
        sv.DECAY_ERR: {gt.NAME: sv.DECAY_ERR,
            gt.GETTER: lambda row: gt._getValueByHeader(row,  sv.DECAY_ERR),
            gt.TIPTEXT: gt._makeTipText(sv.DECAY_ERR, ""),
            gt.WIDTH: 70,
            gt.HIDDEN: True
            },
        sv.AMPLITUDE: {gt.NAME: sv.AMPLITUDE,
                       gt.GETTER: lambda row: gt._getValueByHeader(row, sv.AMPLITUDE),
                       gt.TIPTEXT: gt._makeTipText(sv.AMPLITUDE, ""),
                       gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
                       gt.WIDTH: 70,
                       gt.HIDDEN: False
                       },
        sv.AMPLITUDE_ERR: {gt.NAME: sv.AMPLITUDE_ERR,
                           gt.GETTER: lambda row: gt._getValueByHeader(row, sv.AMPLITUDE_ERR),
                           gt.TIPTEXT: gt._makeTipText(sv.AMPLITUDE_ERR, ""),
                           gt.FORMAT: guiNameSpaces._COLUM_FLOAT_FORM,
                           gt.WIDTH: 70,
                           gt.HIDDEN: True
                           },
        }


class RelaxationTablePanel(TablePanel):

    panelName = guiNameSpaces.CSMTablePanel
    TABLE = _RelaxationGuiTable

