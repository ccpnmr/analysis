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
__dateModified__ = "$dateModified: 2022-05-31 10:23:00 +0100 (Tue, May 31, 2022) $"
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
DELTA = '\u0394'
Delta = '\u03B4'

# colours
import ccpn.ui.gui.guiSettings as gs
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]

##### SETTINGS  ######

# TAB: GuiInputDataPanel names
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
tipText_GuiInputDataPanel               = 'This tab will allow user to create and set the input DataTable(s)'
TipText_SpectrumGroupsSeparator         = 'SpectrumGroup Section. Create here a new input DataTable if none is already available.'
TipText_SpectrumGroupSelectionWidget    = 'Select the SpectrumGroup containing the series of interest'
TipText_PeakPropertySelectionWidget     = 'Select the Peak property to follow'
TipText_dataTableNameSelectionWidget    = 'Select the name for the new DataTable input'
TipText_createInputdataTableWidget      = 'Create the new input DataTable for the selected SpectrumGroup'
TipText_DataTableSeparator              = 'DataTable Section. Select input DataTable(s) to start the Experiment Analysis'
TipText_DataTableSelection              = 'Select input DataTable(s) to start the Experiment Analysis'

## ChemicalShiftMapping TAB
## TAB: CSMCalculationPanel names
Journal_WilliamsonSection               = '\n4.2. Weighting of shifts from different nuclei'
Journal_WilliamsonReference             = '\nM.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).'
WidgetVarName_DeltaDeltasSeparator      = 'SpectrumGroupsSeparator'
AtomName                                = 'AtomName'
FactorValue                             = 'FactorValue'
JournalReference                        = 'JournalReference'
WidgetVarName_Factor                    = f'{{{AtomName}}}Factor' ## 3}}} to get one } as string for this formatting "{AtomName}" as we are setting from an other dict in GUI Module."
WidgetVarName_DDCalculationMode         = 'DeltaDeltaCalculationMode'
WidgetVarName_FollowAtoms               = 'FollowAtoms'
WidgetVarName_ExcludeResType            = 'ExcludeResidueType'
Label_DDCalculationMode                 = f'{DELTA}{Delta} Calculation Mode'
Label_Factor                            = f'{{{AtomName}}} Alpha Factor'
Label_DeltaDeltas                       = '--- Chemical Shift Perturbation Options ---'
Label_Calculation                       = 'Calculation'
Label_FollowAtoms                       = 'Follow (nmr)Atoms'
Label_ExcludeResType                    = 'Exclude (Nmr)Residue Type'
TipText_CSMCalculationPanelPanel        = 'Set the various calculation modes and options for the Chemical Shift Mapping Analysis'
TipText_DeltaDeltasSeparator            = f'{TipText_CSMCalculationPanelPanel} \n For weighting factors, see reference: ' \
                                          f'{Journal_WilliamsonReference}{Journal_WilliamsonSection}'
TipText_Factor                          = f'Factors are weighting of shifts (0-1) for different nuclei. ' \
                                          f'Default for {{{AtomName}}}: {{{FactorValue}}}. See references.'
TipText_DDCalculationMode                 = f'Select the calculation mode for {DELTA}{Delta} shifts. See References.'
TipText_FollowAtoms                       = 'Consider only the selected (nmr)Atoms in the calculation. E.g.: H, N'
TipText_ExcludeResType                    = 'Exclude the selected (Nmr)Residue Type from the calculation. E.g.: Pro'
