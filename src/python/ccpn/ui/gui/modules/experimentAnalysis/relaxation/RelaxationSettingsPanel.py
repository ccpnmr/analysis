# =========================================================================================
# Licence, Reference and Credits
# =========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
# =========================================================================================
# Last code modification
# =========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-09 15:59:57 +0100 (Tue, August 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
# =========================================================================================
# Created
# =========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
# =========================================================================================
# Start of code
# =========================================================================================

"""
This module contains the GUI Settings panels for the Relaxation module.
"""

from collections import OrderedDict as od
######## gui/ui imports ########
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel import GuiSettingPanel, \
    GuiInputDataPanel, GuiCalculationPanel, GuiFittingPanel, AppearancePanel


SettingsWidgeMinimumWidths = (180, 180, 180)
SettingsWidgetFixedWidths = (250, 300, 300)
DividerColour = getColours()[DIVIDER]

#####################################################################
#####################   InputData Panel   ###########################
#####################################################################

class RelaxationGuiInputDataPanel(GuiInputDataPanel):
    tabTipText = guiNameSpaces.TipText_GuiInputDataPanel

#####################################################################
#####################  Calculation Panel  ###########################
#####################################################################

class RelaxationCalculationPanel(GuiCalculationPanel):
    """ Add Relaxation-widget-specific to the general calculation panel """

    tabTipText = guiNameSpaces.TipText_RelaxCalculationPanelPanel

    def setWidgetDefinitions(self):
        """ Relaxation-widget-specific"""

        self.widgetDefinitions = super().setWidgetDefinitions()
        wdict = od((
                    ))
        ## add the new items to the main dict
        self.widgetDefinitions.update(wdict)
        return self.widgetDefinitions

#####################################################################
#####################    Fitting Panel    ###########################
#####################################################################

class RelaxationFittingPanel(GuiFittingPanel):

    def setWidgetDefinitions(self):
        """Add the Relaxation widget specific."""
        self.widgetDefinitions = super().setWidgetDefinitions()
        wdict = od((
        ))
        ## add the new items to the main dict
        self.widgetDefinitions.update(wdict)
        return self.widgetDefinitions

#####################################################################
#####################   Appearance Panel  ###########################
#####################################################################

class RelaxationAppearancePanel(AppearancePanel):

    def _getThresholdValueFromBackend(self, columnName, calculationMode, factor):
        """ Get the threshold value based on selected Y axis. called from _setThresholdValueForData"""
        return super()._getThresholdValueFromBackend(columnName, calculationMode, factor)

    @property
    def _axisYOptions(self):
        return guiNameSpaces.YBarGraphColumnNameOptionsRelax


#####################################################################
#####################   Filtering Panel   ###########################
#####################################################################

## Not yet Implemeted