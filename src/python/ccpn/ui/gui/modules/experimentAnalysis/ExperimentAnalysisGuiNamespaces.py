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
__dateModified__ = "$dateModified: 2023-01-25 22:24:05 +0000 (Wed, January 25, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as seriesVariables
import ccpn.ui.gui.guiSettings as gs

LASTDISPLAY = 'Last Opened'
NEW = '<New Item...>'
EmptySpace = '< >'
ToolBar = 'ToolBar'
DELTA = '\u0394'
Delta = '\u03B4'

#### colours
BackgroundColour = gs.getColours()[gs.CCPNGLWIDGET_HEXBACKGROUND]

## Default fallback colours for BarGraph.
BAR_aboveBrushHex       = '#1020aa'     # dark blue
BAR_belowBrushHex       = '#FF0000'     # red
BAR_untracBrushHex      = '#b0b0b0'     # light grey
BAR_thresholdLineHex    = '#0000FF'     # blue

## Startup colour-names for BarGraph-settings.
BAR_aboveBrush          = 'CCPNgreen'
BAR_belowBrush          = 'CCPNyellow'
BAR_untracBrush         = 'CCPNpurple'
BAR_thresholdLine       = 'blue'

##### SETTINGS  ######

SETTINGS                = 'settings'
WidgetVarName_          = 'VarName'
Label_                  = 'Label'
tipText_                = 'tipText'

SingleClick             = 'Single Click'
DoubleClick             = 'Double Click'
Disabled                = 'Disabled'

####################################################
##########  TAB: GuiInputDataPanel
####################################################

WidgetVarName_InputCollectionSeparator  = 'InputCollectionSeparator'
Label_InputCollection                   = 'Input Collection'
TipText_InputCollection                 = 'Select the top parent Collection containing all subset of peakCollections'

WidgetVarName_SetupCollection           = 'CreateCollectionButton'
Label_SetupCollection                   = 'Setup the input Collection'
TipText_SetupCollection                 = 'Setup the top Collection and its subset of peakCollections'

WidgetVarName_InputCollectionSelection  = 'InputCollectionSelection'
Label_InputCollectionSelection          = Label_InputCollection
TipText_InputCollectionSelection        = TipText_InputCollection

Label_InputData                         = 'Input data'
TipText_GuiInputDataPanel               = 'This tab will allow user to create and set the input DataTable(s)'

WidgetVarName_GeneralSetupSeparator     = 'GeneralSetupSeparator'
Label_GeneralSetup                      = 'General Setup'
TipText_GeneralSetup                    = 'General setup section. Create here a new input SpectrumGroup, collections etc...'

WidgetVarName_CreateSGroup              = 'CreateSGroupButton'
Label_CreateSGroup                      = 'Create SpectrumGroup'
TipText_CreateSGroup                    = 'Create the input SpectrumGroup to use in the analysis'

WidgetVarName_SpectrumGroupsSelection   = 'SpectrumGroupsSelection'
Label_SelectSpectrumGroups              = 'SpectrumGroup'
TipText_SpectrumGroupSelectionWidget    = 'Select the SpectrumGroup containing the series of interest to create a new Input DataTable'

WidgetVarName_DataTableName             = 'dataTableName'
Label_InputDataTableName                = 'Input DataTable Name'
TipText_dataTableNameSelectionWidget    = 'Select the name for the new DataTable input.'

WidgetVarName_CreateDataTable           = 'CreateDataTableName'
Label_CreateInput                       = 'Create Input DataTable'
TipText_createInputdataTableWidget      = 'Create the new input DataTable for the selected SpectrumGroup'

WidgetVarName_DataTableSeparator        = 'DataTableSeparator'
Label_DataTables                        = 'Input DataTables'
TipText_DataTableSeparator              = 'DataTable Section. Select input DataTable(s) to start the Experiment Analysis. If None available, create one using a SpectrumGroup.'

WidgetVarName_DataTablesSelection       = 'DataTablesSelection'
Label_SelectDataTable                   = 'Input DataTable(s)'
TipText_DataTableSelection              = 'Select input DataTable(s) to start the Experiment Analysis'

WidgetVarName_OutPutDataTableName       = 'ResultDataTableName'
Label_OutputDataTableName               = 'Results DataTable Name'
TipText_OutputDataTableName             = 'Select the name for the Results DataTable. Create new if not existing, otherwise override exsiting.'

WidgetVarName_OutputDataTableSeparator  = 'DataTableSeparator2'
Label_OutputDataTable                   = 'Results DataTable'
TipText_OutputDataTableSeparator        = 'Results DataTable Section. Select the results DataTable to display results'

WidgetVarName_FitInputData              = 'FitInputData'
Label_FitInput                          = 'Fit and Fetch Results Data'
TipText_createOutputdataTableWidget     = 'Fit or refit input DataTable and store outputs in a results dataTable.'

WidgetVarName_OutputDataTablesSelection = 'ResultDataTablesSelection'
Label_SelectOutputDataTable             = 'Results DataTable'
TipText_OutputDataTableSelection        = 'Select Results DataTable(s) to display the Experiment Analysis results'

#############################################################
##########  TAB: Calculation
#############################################################

WidgetVarName_IncludeAtoms              = 'IncludeAtoms'
Label_IncludeAtoms                      = 'Include NmrAtoms'
TipText_IncludeAtoms                    = 'Consider only the selected NmrAtoms in the calculation. E.g.: H, N'

WidgetVarName_IncludeGroups             = 'IncludeGroups'
Label_IncludeGroups                     = 'Include Groups'
TipText_FollowGroups                    = 'Include grouped NmrAtoms in the calculation. E.g.: H, N for Backbone group'

WidgetVarName_ExcludeResType            = 'ExcludeResidueType'
Label_ExcludeResType                    = 'Exclude NmrResidue Type'
TipText_ExcludeResType                  = 'Exclude the selected NmrResidue Type from the calculation. E.g.: Pro'

WidgetVarName_UntraceablePeak           = 'UntraceablePeak'
Label_UntraceablePeak                   = f'{DELTA}{Delta} for Untraceable Observations'
TipText_UntraceablePeak                 = f'Set a fixed {DELTA}{Delta} value for Untraceable Observations.' \
                                          f'This situation could happen when a peak in a series disappeared or is impossible to calculate the {DELTA}{Delta} '

WidgetVarName_CalculateDeltaDelta       = 'CalculateDeltaDelta'
Label_CalculateDeltaDelta               = f'Calculate {DELTA}{Delta}'
Button_CalculateDeltaDelta              = f'Re-Calculate '
TipText_CalculateDeltaDelta             = f'Calculate {DELTA}{Delta} values based on current settings'

WidgetVarName_CalculateFitting          = 'CalculateFitting'
Label_CalculateFitting                  = f'Start Fitting'
Button_CalculateFitting                 = f'Re-Fit'
TipText_CalculateFitting                = f'Perform the fitting based on current settings'

#############################################################
##########  TAB: Calculation ChemicalShiftMapping
#############################################################

Label_Calculation                       = 'Calculation'
TipText_CSMCalculationPanelPanel        = 'Set the various calculation modes and options for the Chemical Shift Mapping Analysis'

## General
Journal_WilliamsonSection               = '\n4.2. Weighting of shifts from different nuclei'
Journal_WilliamsonReference             = '\nM.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).'
AtomName                                = 'AtomName'
FactorValue                             = 'FactorValue'
JournalReference                        = 'JournalReference'

## widgets
WidgetVarName_DeltaDeltasSeparator      = 'DeltaDeltaSeparator'
Label_DeltaDeltas                       = 'Chemical Shift Mapping Options'
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

#############################################################
##########  TAB: Calculation Relaxation
#############################################################

TipText_RelaxCalculationPanelPanel      = 'Set the various calculation modes and options for the Relaxation Analysis'


## widgets
WidgetVarName_RelaxSeparator            = 'RelaxSeparator'
Label_RelaxOption                       = 'Relaxation Options'
TipText_RelaxSeparator                  = f''

WidgetVarName_CalcModeSeparator         = 'CalcModeSeparator'
Label_CalcModeSeparator                 = 'Calculation Options'
TipText_CalculationSeparator            = f''

WidgetVarName_CalcMode                  = 'CalculationOptions'
Label_CalculationOptions                = 'Calculation Options'
TipText_CalculationOptions              = f''

WidgetVarName_FilteringAtomsSeparator   = 'FilteringAtomsSeparator'
Label_FilteringAtomsSeparator           = 'Filtering'
TipText_FilteringAtomsSeparator         = f''

WidgetVarName_CalcPeakProperty          = 'PeakProperty'
Label_CalcPeakProperty                  = 'Peak Property'
TipText_CalcPeakProperty                = 'Select the Peak property to follow'

WidgetVarName_ExperimentSeparator   = 'ExperimentSeparator'
Label_ExperimentSeparator           = 'Experiment'
TipText_ExperimentSeparator         = f''

WidgetVarName_ExperimentName   = 'ExperimentName'
Label_ExperimentOption          = 'Experiment Name'
TipText_ExperimentOption        = f''


############################################################
##########  TAB: Fitting
############################################################
Label_Fitting                           = 'Fitting'
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
##########  TAB: Appearance
############################################################

WidgetVarName_GenAppearanceSeparator    = 'GeneralAppearanceSeparator'
Label_GeneralAppearance                 = 'Appearance'
TipText_GeneralAppearance               = 'General Appearance settings'

WidgetVarName_SpectrumDisplSeparator    = 'SpectrumDisplaySeparator'
Label_SpectrumDisplSeparator            = 'SpectrumDisplay'
TipText_SpectrumDisplSeparator          = 'General Appearance settings for SpectrumDisplay'

WidgetVarName_SpectrumDisplSelection    = 'SpectrumDisplaySelection'
Label_SpectrumDisplSelection            = 'Navigate to SpectrumDisplay'
TipText_SpectrumDisplSelection          = 'Navigate to Peaks/NmrResidues in the selected SpectrumDisplay(s)'

WidgetVarName_NavigateToOpt             = 'NavigateToOnClick'
Label_NavigateToOpt                     = 'Navigate trigger'
TipText_NavigateToOpt                   = 'Navigate to Peaks/NmrResidues in the selected SpectrumDisplay(s) using Single or Double click on the main table'

WidgetVarName_BarGraphSeparator         = 'GeneralAppearanceSeparator'
Label_BarGraphAppearance                = 'BarGraph'
TipText_BarGraphAppearance              = 'General Appearance settings for the BarGraph'

WidgetVarName_BarGraphXcolumnName       = 'XcolumnName'
Label_XcolumnName                       = 'X Axis Data'
TipText_XcolumnName                     = 'Set the BarGraph X Axis Data'

WidgetVarName_BarGraphYcolumnName       = 'YcolumnName'
Label_YcolumnName                       = 'Y Axis Data'
TipText_YcolumnName                     = 'Set the BarGraph Y Axis Data'

WidgetVarName_ThreshValue               = 'ThreshValue'
Label_ThreshValue                       = 'Threshold Value'
TipText_ThreshValue                     = 'Select the threshold line.'

WidgetVarName_PredefThreshValue         = 'PredefinedThreshValue'
Label_PredefThreshValue                 = 'Predefined Threshold setter'
TipText_PredefThreshValue               = 'Predefined threshold value setters based on the current data'

Label_setThreshValue                    = 'Recalculate Threshold'
TipText_setThreshValue                  = 'Recalculate the threshold value from the current data and set the line on the graph'

WidgetVarName_ThreshValueCalcOptions    = 'ThreshValueCalcOptions'
Label_ThreshValueCalcOptions            = 'Threshold Value Calculation'
TipText_ThreshValueCalcOptions          = 'Select the calculation method for the threshold line.'

WidgetVarName_ThreshValueFactor         = 'ThreshValueCalcFactor'
Label_ThreshValueFactor                 = 'Threshold Factor'
TipText_ThreshValueFactor               = 'Increase (multiply) the threshold value by a factor.'

WidgetVarName_BarXTickOpt               = 'BarXTickOpt'
Label_BarXTickOpt                       = 'X axis Ticks'
TipText_BarXTickOpt                     = 'Display X axis ticks option. Display all ticks or show major/minor depending on zoom levels'

### Threshold Values for BarGraph options

WidgetVarName_AboveThrColour            = 'AboveThrColour'
Label_AboveThrColour                    = 'Above Threshold Colour'
TipText_AboveThrColour                  = 'Select the colour for bars above a threshold line value in the BarPlot'

WidgetVarName_BelowThrColour            = 'BelowThrColour'
Label_BelowThrColour                    = 'Below Threshold Colour'
TipText_BelowThrColour                  = 'Select the colour for bars below a threshold line value in the BarPlot'

WidgetVarName_UntraceableColour         = 'UntraceableColour'
Label_UntraceableColour                 = 'Untraceable Observation Colour'
TipText_UntraceableColour               = 'Select the colour for for Untraceable Observations.'

WidgetVarName_ThrColour                 = 'ThresholdColour'
Label_ThrColour                         = 'Threshold Line Colour'
TipText_ThrColour                       = 'Select the colour for the threshold line in the BarPlot'

WidgetVarName_MolStrucSeparator         = 'MolStructureSeparator'
Label_MolStrucSeparator                 = 'Molecular Viewer'
TipText_MolStrucSeparator               = ''

WidgetVarName_MolStructureFile          = 'MolStructureFile'
Label_MolStructureFile                  = 'Molecular Structure File'
TipText_MolStructureFile                = 'Select the molecular structure file path. (.pdb only)'


WidgetVarName_TableSeparator            = 'TableSeparator'
Label_TableSeparator                    = 'Table Options'
TipText_TableSeparator                  = ''

WidgetVarName_TableView                 = 'TableView'
Label_TableView                         = 'Display Columns'
TipText_TableView                       = 'Select the group of columns to display'

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

ColumnID = 'Id'
ColumnCollection = 'Collection'
ColumnCollectionPid = 'Collection Pid'
ColumnChainCode = 'Chain'
ColumnResidueCode = 'Code'
ColumnResidueType = 'Type'
ColumnAtoms = 'Atoms'
ColumnCodeType = 'Code-Type'

_COLUM_FLOAT_FORM = '%0.3f'

############################################################
##########          Panel: ToolBar                ##########
############################################################
# ToolBar
FilterButton = 'filterButton'
UpdateButton = 'updateButton'
ShowStructureButton = 'showStructureButton'
Callback = 'Callback'
RefitButton = 'refitButton'


BarPlotPanel = 'BarPlotPanel'
RelaxationFittingPlotPanel = 'RelaxationFittingPlotPanel'



CSMFittingPlotPanel = 'CSMFittingPlotPanel'
ToolbarPanel = 'ToolbarPanel'
TablePanel = 'TablePanel'
PymolScriptName = 'chemicalShiftMapping_Pymol_Template.py'
PYMOL = 'pymol'

# Table Groupping Headers
_Assignments = 'Assignments'
_SeriesSteps = 'SeriesSteps'
_Calculation = 'Calculation'
_Stats = 'Stats'
_Errors = 'Errors'
_Fitting = 'Fitting'
TableGrouppingHeaders = [_Assignments, _SeriesSteps, _Calculation, _Fitting, _Stats, _Errors]

### Appearance BarGraph X axis
XBarGraphColumnNameOptions =  [
                                seriesVariables.ASHTAG,
                                ColumnID,
                                ColumnCollectionPid,
                                ColumnResidueCode,
                                ColumnCodeType,
                                ]




### Threshold Values calculation options
ThrValuesCalcOptions  = [seriesVariables.MAD,
                        seriesVariables.AAD,
                        seriesVariables.MEAN,
                        seriesVariables.MEDIAN,
                        seriesVariables.STD,
                        seriesVariables.VARIANCE]



