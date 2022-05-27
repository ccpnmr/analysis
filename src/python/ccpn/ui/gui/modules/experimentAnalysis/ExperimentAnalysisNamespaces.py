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
__dateModified__ = "$dateModified: 2022-05-27 17:10:19 +0100 (Fri, May 27, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

LASTDISPLAY = 'Last Opened'
NEW = '<New Item...>'
EmptySpace = '< >'
ToolBar = 'ToolBar'

# colours
import ccpn.ui.gui.guiSettings as gs
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]

##### TOOLBAR ######

# GuiInputDataPanel names
tipText_GuiInputDataPanel               = 'This tab will allow user to create and set the input DataTable(s)'
TipText_SpectrumGroupsSeparator         = 'SpectrumGroup Section. Create here a new input DataTable if none is already available.'
TipText_SpectrumGroupSelectionWidget    = 'Select the SpectrumGroup containing the series of interest'
TipText_PeakPropertySelectionWidget     = 'Select the Peak property to follow'
TipText_dataTableNameSelectionWidget    = 'Select the name for the new DataTable input'
TipText_createInputdataTableWidget      = 'Create the new input DataTable for the selected SpectrumGroup'
TipText_DataTableSeparator              = 'DataTable Section. Select input DataTable(s) to start the Experiment Analysis'
TipText_DataTableSelection              = 'Select input DataTable(s) to start the Experiment Analysis'
WidgetVarName_PeakProperty              = 'peakProperty'
WidgetVarName_SpectrumGroupsSelection   = 'SpectrumGroupsSelection'
WidgetVarName_DataTablesSelection       = 'DataTablesSelection'
WidgetVarName_DataTables                = 'DataTables'
WidgetVarName_DataTableName             = 'dataTableName'
WidgetVarName_CreateDataTable           = 'CreateDataTableName'
WidgetVarName_DataTableSeparator        = 'DataTableSeparator'
WidgetVarName_SpectrumGroupsSeparator   = 'SpectrumGroupsSeparator'
Label_InputData                         = 'Input data'
Label_SpectrumGroups                    = '--- SpectrumGroups ---'
Label_DataTables                        = '---   DataTables   ---'
Label_SelectSpectrumGroups              = 'Select SpectrumGroup'
Label_SelectDataTable                   = 'Select DataTable(s)'
Label_PeakProperty                      = 'Peak Property'
Label_InputDataTableName                = 'Input DataTable Name'
Label_CreateInput                       = 'Create Input DataTable'
