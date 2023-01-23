"""
This module defines base classes for Series Analysis
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
__dateModified__ = "$dateModified: 2023-01-23 11:35:50 +0000 (Mon, January 23, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.DataEnum import DataEnum
from lmfit.models import update_param_vals
import numpy as np
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.DataTable import TableFrame
from ccpn.framework.lib.experimentAnalysis.FittingModelABC import FittingModelABC, MinimiserModel, MinimiserResult, CalculationModel
from ccpn.framework.lib.experimentAnalysis.SeriesTablesBC import RelaxationOutputFrame, HetNoeOutputFrame

#####################################################
###########        Minimisers        ################
#####################################################

class _RelaxationBaseMinimiser(MinimiserModel):
    """
    A base model for T1/T2
    """
    FITTING_FUNC = lf.exponentialDecay_func
    AMPLITUDEstr = sv.AMPLITUDE
    DECAYstr = sv.DECAY
    # _defaultParams must be set. They are required. Also Strings must be exactly as they are defined in the FITTING_FUNC arguments!
    # There is a clever signature inspection that set the args as class attributes. This was too hard/dangerous to change!
    defaultParams = {
                        AMPLITUDEstr:1,
                        DECAYstr:0.5
                      }


    def __init__(self, independent_vars=['x'], prefix='', nan_policy=sv.RAISE_MODE, **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy, 'independent_vars': independent_vars})
        super().__init__(lf.exponentialDecay_func, **kwargs)
        self.name = self.MODELNAME
        self.params = self.make_params(**self.defaultParams)

    def guess(self, data, x, **kwargs):
        """Estimate initial model parameter values from data."""
        try:
            sval, oval = np.polyfit(x, np.log(abs(data)+1.e-15), 1)
        except TypeError:
            sval, oval = 1., np.log(abs(max(data)+1.e-9))
        params = self.make_params(amplitude=np.exp(oval), decay=-1.0/sval)
        return update_param_vals(params, self.prefix, **kwargs)


class InversionRecoveryMinimiser(_RelaxationBaseMinimiser):
    """
    A model based on the T1 fitting function.
    """
    FITTING_FUNC = lf.inversionRecovery_func
    MODELNAME = 'InversionRecoveryMinimiser'


class ExponentialDecayMinimiser(_RelaxationBaseMinimiser):
    """
    A model based on the Exponential Decay fitting function.
    """
    FITTING_FUNC = lf.exponentialDecay_func
    MODELNAME = 'ExponentialDecayMinimiser'

#####################################################
###########       FittingModel       ################
#####################################################

class _RelaxationBaseFittingModel(FittingModelABC):
    """
    A Base model class for T1/T2
    """
    PeakProperty =  sv._HEIGHT


    def fitSeries(self, inputData:TableFrame, rescale=True, *args, **kwargs) -> TableFrame:
        """
        :param inputData:
        :param rescale:
        :param args:
        :param kwargs:
        :return:
        """
        getLogger().warning(sv.UNDER_DEVELOPMENT_WARNING)
        ## Keep only one IsotopeCode as we are using only Height/Volume 15N?
        inputData = inputData[inputData[sv.ISOTOPECODE] == inputData[sv.ISOTOPECODE].iloc[0]]
        inputData[self.ySeriesStepHeader] = inputData[self.PeakProperty]
        self._ySeriesLabel = self.PeakProperty
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([self.xSeriesStepHeader], inplace=True)
            seriesSteps = Xs = groupDf[self.xSeriesStepHeader].values
            seriesValues = Ys = groupDf[self.ySeriesStepHeader].values
            minimiser = self.Minimiser()
            try:
                params = minimiser.guess(Ys, Xs)
                result = minimiser.fit(Ys, params, x=Xs)
            except:
                getLogger().warning(f'Fitting Failed for collectionId: {collectionId} data.')
                params = minimiser.params
                result = MinimiserResult(minimiser, params)

            for ix, row in groupDf.iterrows():
                for resultName, resulValue in result.getAllResultsAsDict().items():
                    inputData.loc[ix, resultName] = resulValue
                inputData.loc[ix, sv.MODEL_NAME] = self.ModelName
                inputData.loc[ix, sv.MINIMISER_METHOD] = minimiser.method
                nmrAtomNames = inputData._getAtomNamesFromGroupedByHeaders(groupDf)
                inputData.loc[ix, sv.NMRATOMNAMES] = nmrAtomNames[0] if len(nmrAtomNames) > 0 else ''

        return inputData

class InversionRecoveryFittingModel(_RelaxationBaseFittingModel):
    """
    InversionRecovery model class containing fitting equation and fitting information
    """
    ModelName   = sv.InversionRecovery
    Info        = '''Inversion Recovery fitting model.
                  '''
    Description = '''Model:
                  Y = amplitude * (1 - e^{-time/decay})
                  '''
    References  = '''
                  NIY
                  '''
    # Minimiser = InversionRecoveryMinimiser
    # MaTex =  r'$amplitude*(1 - e^{-time/decay})$'
    FullDescription = f'{Info}\n{Description}'

class ExponentialDecayFittingModel(_RelaxationBaseFittingModel):
    """
    ExponentialDecay FittingModel model class containing fitting equation and fitting information
    """
    ModelName   = sv.ExponentialDecay
    Info        = '''Exponential Decay fitting model
                  '''
    Description = '''Model:
                  Y = amplitude * (e^{-time/decay})
                  '''
    References  = '''
                  NIY
                  '''
    Minimiser = ExponentialDecayMinimiser
    # MaTex = r'$amplitude *(e^{-time/decay})$'
    FullDescription = f'{Info}\n{Description}'

#####################################################
##########  Calculation Models   ####################
#####################################################

class HetNoeDefs(DataEnum):
    """
    NOT YET ENABLED. Experimental
    Definitions used for converting one of  potential variable name used to
    describe a series value for the HetNOE spectrumGroup, e.g.: 'saturated' to 1.
    Series values can be int/float or str.
    Definitions:
        The unSaturated condition:  0 or one of  ('unsat', 'unsaturated', 'nosat', 'noNOE')
        the Saturated: 1 or  one of  ('sat',  'saturated', 'NOE')
    see  ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables for variables

    """

    UNSAT = 0,  sv.UNSAT_OPTIONS
    SAT = 1, sv.SAT_OPTIONS

    @staticmethod
    def getValueForDescription(description: str) -> int:
        """ Get a value as int for a description if  is present in the list of possible description for the DataEnum"""
        for value, descriptions in zip(HetNoeDefs.values(), HetNoeDefs.descriptions()):
            _descriptions = [str(i).lower() for i in descriptions] + [str(value)]
            if str(description).lower() in _descriptions:
                return value

        errorMessage = f'''Description "{description}" not recognised as a HetNOE series value. Please use one of {HetNoeDefs.descriptions()}'''
        getLogger().warning(errorMessage)

class HetNoeCalculation(CalculationModel):
    """
    Calculate HeteroNuclear NOE Values
    """
    ModelName = sv.HETNOE
    Info        = '''Calculate HeteroNuclear NOE Values using peak Intensity (Height or Volume).
    Define your series value with 0 for the unsaturated experiment while 
    use the value 1 for the saturated experiment '''

    Description = '''Model:
                  HnN = I_Sat / I_UnSat
                  Sat = Peak Intensity for the Saturated Spectrum;
                  UnSat = Peak Intensity for the UnSaturated Spectrum, 
                  Value Error calculated as:
                  error = factor * √SNR_Sat^-2 + SNR_UnSat^-2
                  factor = I_Sat/I_UnSat'''
    References  = '''
                1) Kharchenko, V., et al. Dynamic 15N{1H} NOE measurements: a tool for studying protein dynamics. 
                J Biomol NMR 74, 707–716 (2020). https://doi.org/10.1007/s10858-020-00346-6
                '''
    # MaTex       = r'$I_{Sat} / I_{UnSat}$'
    FullDescription = f'{Info}\n{Description}'
    PeakProperty = sv._HEIGHT
    _allowedIntensityTypes = (sv._HEIGHT, sv._VOLUME)

    @property
    def modelArgumentNames(self):
        """ The list of parameters as str used in the calculation model.
            These names will appear as column headers in the output result frames. """
        return [sv.HETNOE_VALUE, sv.HETNOE_VALUE_ERR]

    def calculateValues(self, inputData:TableFrame) -> TableFrame:
        """
        Calculate the DeltaDeltas for an input SeriesTable.
        :param inputData: CSMInputFrame
        :return: outputFrame
        """
        outputFrame = self._getHetNoeOutputFrame(inputData)
        return outputFrame

    #########################
    ### Private functions ###
    #########################

    def _convertNoeLabelToInteger(self, inputData):
        """ Convert a label 'sat' to ones  and 'unsat' to zeros"""

        satDef = HetNoeDefs(1)
        unsatDef = HetNoeDefs(0)
        # df = inputData #.copy()
        inputData[sv.SERIES_STEP_X_label] =  inputData[self.xSeriesStepHeader]
        for i, row in inputData.iterrows():
            seriesStep = row[self.xSeriesStepHeader]
            seriesStepIndex = HetNoeDefs.getValueForDescription(seriesStep)
            noeDef = HetNoeDefs(seriesStepIndex)
            if noeDef.value == satDef.value:
                inputData.loc[i, self.xSeriesStepHeader] = satDef.value
            if noeDef.value == unsatDef.value:
                inputData.loc[i, self.xSeriesStepHeader] = unsatDef.value
        return inputData

    def _getHetNoeOutputFrame(self, inputData):
        """
        Calculate the HetNoe for an input SeriesTable.
        The non-Sat peak is the first in the SpectrumGroup series.
        :param inputData: SeriesInputFrame
        :return: outputFrame (HetNoeOutputFrame)
        """
        unSatIndex = 0 
        satIndex = 1
        outputFrame = HetNoeOutputFrame()
    
        ## Keep only one IsotopeCode as we are using only 15N
        inputData = inputData[inputData[sv.ISOTOPECODE] == '15N']
        grouppedByCollectionsId = inputData.groupby([sv.COLLECTIONID])
        for collectionId, groupDf in grouppedByCollectionsId:
            groupDf.sort_values([self.xSeriesStepHeader], inplace=True)
            seriesValues = groupDf[self.PeakProperty]
            nmrAtomNames = inputData._getAtomNamesFromGroupedByHeaders(groupDf) # join the atom names from different rows in a list
            seriesUnits = groupDf[sv.SERIESUNIT].unique()
            satPeakSNR = groupDf[sv._SNR].values[satIndex]
            unSatPeakSNR = groupDf[sv._SNR].values[unSatIndex]
            unSatValue = seriesValues.values[unSatIndex]
            satValue = seriesValues.values[satIndex]
            ratio = satValue/unSatValue
            error = lf.peakErrorBySNRs([satPeakSNR, unSatPeakSNR], factor=ratio, power=-2, method='sum')
            # build the outputFrame
            outputFrame.loc[collectionId, sv.COLLECTIONID] = collectionId
            outputFrame.loc[collectionId, sv.PEAKPID] = groupDf[sv.PEAKPID].values[0]
            outputFrame.loc[collectionId, sv.COLLECTIONPID] = groupDf[sv.COLLECTIONPID].values[-1]
            outputFrame.loc[collectionId, sv.NMRRESIDUEPID] = groupDf[sv.NMRRESIDUEPID].values[-1]
            outputFrame.loc[collectionId, sv.SERIESUNIT] = seriesUnits[-1]
            outputFrame.loc[collectionId,self.modelArgumentNames[0]] = ratio
            outputFrame.loc[collectionId, self.modelArgumentNames[1]] = error
            outputFrame.loc[collectionId, sv.GROUPBYAssignmentHeaders] = groupDf[sv.GROUPBYAssignmentHeaders].values[0]
            outputFrame.loc[collectionId, sv.NMRATOMNAMES] = nmrAtomNames[0] if len(nmrAtomNames)>0 else ''
        return outputFrame

#####################################################
###########      Register models    #################
#####################################################
FittingModels            = [
                    ExponentialDecayFittingModel,
                    InversionRecoveryFittingModel,
                    ]


CalculationModels = [
                    HetNoeCalculation
                    ]




