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
__dateModified__ = "$dateModified: 2022-06-30 14:25:23 +0100 (Thu, June 30, 2022) $"
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

SETTINGS = 'settings'
WidgetVarName_         = 'VarName'
Label_                 = 'Label'
tipText_               = 'tipText'

####################################################
##########     TAB: GuiInputDataPanel     ##########
####################################################

Label_InputData                         = 'Input data'
TipText_GuiInputDataPanel               = 'This tab will allow user to create and set the input DataTable(s)'

WidgetVarName_SpectrumGroupsSeparator   = 'SpectrumGroupsSeparator'
Label_SpectrumGroups                    = 'SpectrumGroups'
TipText_SpectrumGroupsSeparator         = 'SpectrumGroup Section. Create here a new input DataTable if none is already available.'

WidgetVarName_SpectrumGroupsSelection   = 'SpectrumGroupsSelection'
Label_SelectSpectrumGroups              = 'Select SpectrumGroup'
TipText_SpectrumGroupSelectionWidget    = 'Select the SpectrumGroup containing the series of interest'

WidgetVarName_PeakProperty              = 'peakProperty'
Label_PeakProperty                      = 'Peak Property'
TipText_PeakPropertySelectionWidget     = 'Select the Peak property to follow'


WidgetVarName_DataTableName             = 'dataTableName'
Label_InputDataTableName                = 'Input DataTable Name'
TipText_dataTableNameSelectionWidget    = 'Select the name for the new DataTable input'

WidgetVarName_CreateDataTable           = 'CreateDataTableName'
Label_CreateInput                       = 'Create Input DataTable'
TipText_createInputdataTableWidget      = 'Create the new input DataTable for the selected SpectrumGroup'

WidgetVarName_DataTableSeparator        = 'DataTableSeparator'
Label_DataTables                        = 'DataTables'
TipText_DataTableSeparator              = 'DataTable Section. Select input DataTable(s) to start the Experiment Analysis'

WidgetVarName_DataTablesSelection       = 'DataTablesSelection'
Label_SelectDataTable                   = 'Select DataTable(s)'
TipText_DataTableSelection              = 'Select input DataTable(s) to start the Experiment Analysis'


####################################################
##########    TAB: ChemicalShiftMapping   ##########
####################################################

Label_Calculation                       = 'Calculation'
TipText_CSMCalculationPanelPanel        = 'Set the various calculation modes and options for the Chemical Shift Mapping Analysis'

## General
Journal_WilliamsonSection               = '\n4.2. Weighting of shifts from different nuclei'
Journal_WilliamsonReference             = '\nM.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).'
AtomName                                = 'AtomName'
FactorValue                             = 'FactorValue'
JournalReference                        = 'JournalReference'

## widgets
WidgetVarName_DeltaDeltasSeparator      = 'SpectrumGroupsSeparator'
Label_DeltaDeltas                       = 'Chemical Shift Perturbation Options'
TipText_DeltaDeltasSeparator            = f'{TipText_CSMCalculationPanelPanel} \n For weighting factors, see reference: ' \
                                          f'{Journal_WilliamsonReference}{Journal_WilliamsonSection}'

WidgetVarName_DDCalculationMode         = 'DeltaDeltaCalculationMode'
Label_DDCalculationMode                 = f'{DELTA}{Delta} Shift Calculation Mode'
TipText_DDCalculationMode               = f'Select the calculation mode for {DELTA}{Delta} shifts. See References.'

WidgetVarName_Factor                    = f'{{{AtomName}}}_Factor' ## 3}}} to get one } as string for this formatting "{AtomName}" as we are setting from an other dict in GUI Module."
Label_Factor                            = f'{{{AtomName}}} Alpha Factor'
TipText_Factor                          = f'Factors are weighting of shifts (0-1) for different nuclei. ' \
                                          f'Default for {{{AtomName}}}: {{{FactorValue}}}. See references.'
ALPHA_FACTORS                           = 'AlphaFactors'

WidgetVarName_FollowAtoms               = 'FollowAtoms'
Label_FollowAtoms                       = 'Follow (nmr)Atoms'
TipText_FollowAtoms                     = 'Consider only the selected (nmr)Atoms in the calculation. E.g.: H, N'

WidgetVarName_ExcludeResType            = 'ExcludeResidueType'
Label_ExcludeResType                    = 'Exclude (Nmr)Residue Type'
TipText_ExcludeResType                  = 'Exclude the selected (Nmr)Residue Type from the calculation. E.g.: Pro'

WidgetVarName_DDOtherCalculationMode    = 'DeltaDeltaCalculationOtherMode'
Label_DDOtherCalculationMode            = f'{DELTA}{Delta} Height/Volume \nCalculation Mode'
TipText_DDOtherCalculationMode          = f'Select the calculation mode for other {DELTA}{Delta} analysis. E.g.: Height and Volume.'

WidgetVarName_DisappearedPeak           = 'DisappearedPeak'
Label_DisappearedPeak                   = f'{DELTA}{Delta} for Untraceable Perturbations'
TipText_DisappearedPeak                 = f'Set a fixed {DELTA}{Delta} value for Untraceable Perturbations. E.g.: when a peak in a series disappeared'

WidgetVarName_CalculateDeltaDelta       = 'CalculateDeltaDelta'
Label_CalculateDeltaDelta               = f'Calculate {DELTA}{Delta}'
Button_CalculateDeltaDelta              = f'Re-Calculate '
TipText_CalculateDeltaDelta             = f'Calculate {DELTA}{Delta} values based on current settings'


WidgetVarName_CalculateFitting          = 'CalculateFitting'
Label_CalculateFitting                  = f'Start Fitting'
Button_CalculateFitting                 = f'Re-Fit'
TipText_CalculateFitting                = f'Perform the fitting based on current settings'

############################################################
##########  TAB: Appearance ChemicalShiftMapping  ##########
############################################################

WidgetVarName_GenAppearanceSeparator    = 'GeneralAppearanceSeparator'
Label_GeneralAppearance                 = 'General Appearance'
TipText_GeneralAppearance               = 'General Appearance settings'

WidgetVarName_ThreshValue               = 'ThreshValue'
Label_ThreshValue                       = 'Threshold Value'
TipText_ThreshValue                     = 'Select the threshold line.'

WidgetVarName_PredefThreshValue         = 'PredefinedThreshValue'
Label_PredefThreshValue                 = 'Predefined Threshold setter'
TipText_PredefThreshValue               = 'Predefined threshold value setters based on the current data'

Label_StdThreshValue                    = 'Set to 1 SD'
TipText_StdThreshValue                  = 'Calculate 1 Standard Deviation of the current data and set the value to the Threshold Line'

WidgetVarName_AboveThrColour            = 'AboveThrColour'
Label_AboveThrColour                    = 'Above Threshold Colour'
TipText_AboveThrColour                  = 'Select the colour for bars above a threshold line value in the BarPlot'

WidgetVarName_BelowThrColour            = 'BelowThrColour'
Label_BelowThrColour                    = 'Below Threshold Colour'
TipText_BelowThrColour                  = 'Select the colour for bars below a threshold line value in the BarPlot'

WidgetVarName_UntraceableColour         = 'UntraceableColour'
Label_UntraceableColour                 = 'Untraceable Perturbation Colour'
TipText_UntraceableColour               = 'Select the colour for for Untraceable Perturbations.'

WidgetVarName_MolStrucSeparator         = 'MolStructureSeparator'
Label_MolStrucSeparator                 = 'Molecular Structure'
TipText_MolStrucSeparator               = ''

WidgetVarName_MolStructureFile          = 'MolStructureFile'
Label_MolStructureFile                  = 'Molecular Structure File'
TipText_MolStructureFile                = 'Select the molecular structure file path.'



############################################################
##########  TAB: Fitting ChemicalShiftMapping     ##########
############################################################

WidgetVarName_FittingSeparator          = 'FittingSeparator'
Label_FittingSeparator                  = 'Fitting Options'
TipText_FittingSeparator                = 'General fitting options'

WidgetVarName_FittingModel              = 'FittingModel'
Label_FittingModel                      = 'Fitting Model'
TipText_FittingModel                    = 'Select the Fitting Model'

WidgetVarName_OptimiserSeparator        = 'OptimiserSeparator'
Label_OptimiserSeparator                = 'Optimiser Options'
TipText_OptimiserSeparator              = 'General Optimiser options'

WidgetVarName_OptimiserMethod           = 'OptimiserMethod'
Label_OptimiserMethod                   = 'Optimiser Method'
TipText_OptimiserMethod                 = 'Select the Optimiser Method'

WidgetVarName_ErrorMethod               = 'ErrorMethod'
Label_ErrorMethod                       = 'Fitting Error Method'
TipText_ErrorMethod                     = 'Select the Fitting Error calculation Method'



############################################################
##########  Panel: TABLES                         ##########
############################################################

## Table nameSpaces
ASHTAG = '#'

DELTAdelta = f'{DELTA}{Delta}'
UNICODE_CHISQUARE = '\u03A7\u00b2'
UNICODE_RED_CHISQUARE = f'Red-{UNICODE_CHISQUARE}'
UNICODE_R2 = 'R\u00b2'

ColumnDdelta = DELTAdelta
ColumnR2 = UNICODE_R2
ColumnCHISQUARE = UNICODE_CHISQUARE
ColumnREDCHISQUARE = UNICODE_RED_CHISQUARE

ColumnChainCode = 'Chain Code'
ColumnResidueCode = 'Residue Code'
ColumnResidueType = 'Residue Type'
ColumnAtoms = 'Atoms'

_COLUM_FLOAT_FORM = '%0.3f'

############################################################
##########          Panel: ToolBar                ##########
############################################################
# ToolBar
FilterButton = 'filterButton'
UpdateButton = 'updateButton'
ShowStructureButton = 'showStructureButton'
Callback = 'Callback'


############################################################
##########  Panel: ChemicalShiftMapping          ##########
############################################################

CSMTablePanel = 'CSMTablePanel'
CSMBarPlotPanel = 'CSMBarPlotPanel'
CSMFittingPlotPanel = 'CSMFittingPlotPanel'

RelativeDisplacement = 'Relative Displacement'
AppearancePanel = 'AppearancePanel'
ToolbarPanel = 'ToolbarPanel'