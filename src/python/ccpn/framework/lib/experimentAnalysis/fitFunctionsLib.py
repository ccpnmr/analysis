"""
This module defines the various fitting functions for Series Analysis.
When employed, they are called recursively by the Minimiser (see Minimiser Object)

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
__dateModified__ = "$dateModified: 2022-10-26 15:40:26 +0100 (Wed, October 26, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-02-02 14:08:56 +0000 (Wed, February 02, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from lmfit import lineshapes as ls
import numpy as np
from ccpn.util.Logging import getLogger
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv

## Common built-in functions.
gaussian_func    = ls.gaussian
lorentzian_func  = ls.lorentzian
linear_func      = ls.linear
parabolic_func   = ls.parabolic
lognormal_func   = ls.lognormal
pearson7_func    = ls.pearson7
students_t_func  = ls.students_t
powerlaw_func    = ls.powerlaw




########################################################################################################################
########################            Ligand - Receptor Binding equations        #########################################
########################################################################################################################

"""
    Below a set of library functions used in the Series Analysis, in particular the ChemicalShiftMapping module (CSM).
    They are called recursively from each specific Fitting Model and its Minimiser object.
    Function Arguments (*args) are used/inspected to set the attr to the Minimiser object and other functionality.
    <-> WARNING <-> : Do not change the function signature without amending the Minimiser default parameters or 
    will result in a broken Model. E.g.: oneSiteBinding_func(x, Kd, BMax) to oneSiteBinding_func(x, kd, bmax) will break
    See MinimiserModel _defaultParams for more info. 

"""

def oneSiteBinding_func(x, Kd, BMax):
    """
    The one-site Specific Binding equation for a saturation binding experiment.

    Y = Bmax*X/(Kd + X)

    :param x:   1d array. The data to be fitted.
                In the CSM it's the array of deltas (deltas among chemicalShifts, CS, usually in ppm positions)

    :param Kd:  Defines the equilibrium dissociation constant. The value to get a half-maximum binding at equilibrium.
                In the CSM the initial value is calculated from the ligand concentration.
                The ligand concentration is inputted in the SpectrumGroup Series values.

    :param BMax: Defines the max specific binding.
                In the CSM the initial value is calculated from the CS deltas.
                Note, The optimised BMax will be (probably always) larger than the measured CS.

    :return:    Y array same shape of x. Represents the points for the fitted curve Y to be plotted.
                When plotting BMax is the Y axis, Kd the X axis.
    """
    return (BMax * x) / (x + Kd)


def oneSiteNonSpecBinding_func(x, NS, B=1):
    """
    The  one-site non specific Binding equation for a saturation binding experiment.

    Y = NS*X + B

    :param x:  1d array. The data to be fitted.
               In the CSM it's the array of deltas (deltas among chemicalShifts, CS, usually in ppm positions)

    :param NS: the slope of non-specific binding
    :param B:  The non specific binding without ligand.

    :return:   Y array same shape of x. Represents the points for the fitted curve Y to be plotted.
               When plotting BMax is the Y axis, Kd the X axis.
    """

    YnonSpecific = NS * x + B

    return YnonSpecific


def fractionBound_func(x, Kd, BMax):
    """
    The one-site fractionBound equation for a saturation binding experiment.
    V2 equation.
    Y = BMax * (Kd + x - sqrt((Kd + x)^2 - 4x))

    ref: 1) In-house calculations (V2 - wayne - Double check )

    :param x:   1d array. The data to be fitted.
                In the CSM it's the array of deltas (deltas among chemicalShifts, CS, usually in ppm positions)

    :param Kd:  Defines the equilibrium dissociation constant. The value to get a half-maximum binding at equilibrium.
                In the CSM the initial value is calculated from the ligand concentration.
                The ligand concentration is inputted in the SpectrumGroup Series values.

    :param BMax: Defines the max specific binding.
                In the CSM the initial value is calculated from the CS deltas.
                Note, The optimised BMax will be (probably always) larger than the measured CS.

    :return:    Y array same shape of x. Represents the points for the fitted curve Y to be plotted.
                When plotting BMax is the Y axis, Kd the X axis.
    """

    qd = np.sqrt((Kd+x)**2 - 4*x)
    Y = BMax * (Kd + x - qd)

    return Y

def fractionBoundWithPro_func(x, Kd, BMax, T=1):
    """
    The one-site fractionBound equation for a saturation binding experiment.
    V2 equation.
    Y = BMax * ( (P + x + Kd) - sqrt(P + x + Kd)^2 - 4*P*x)) / 2 * P

    ref: 1) M.P. Williamson. Progress in Nuclear Magnetic Resonance Spectroscopy 73, 1–16 (2013).


    :param x:   1d array. The data to be fitted.
                In the CSM it's the array of deltas (deltas among chemicalShifts, CS, usually in ppm positions)

    :param Kd:  Defines the equilibrium dissociation constant. The value to get a half-maximum binding at equilibrium.
                In the CSM the initial value is calculated from the ligand concentration.
                The ligand concentration is inputted in the SpectrumGroup Series values.

    :param BMax: Defines the max specific binding.
                In the CSM the initial value is calculated from the CS deltas.
                Note, The optimised BMax will be (probably always) larger than the measured CS.
                
    :param T: Target concentration.

    :return:    Y array same shape of x. Represents the points for the fitted curve Y to be plotted.
                When plotting BMax is the Y axis, Kd the X axis.
    """

    Y = BMax * ((T + x + Kd) - np.sqrt((T + x + Kd)**2 - 4 * T * x)) / 2 * T
    return Y


def cooperativity_func(x, Kd, BMax, Hs):
    """
    The cooperativity equation for a saturation binding experiment.

    Y = Bmax*X^Hs/(Kd^Hs + X^Hs)

    :param x:   1d array. The data to be fitted.
                In the CSM it's the array of deltas (deltas among chemicalShifts, CS, usually in ppm positions)

    :param Kd:  Defines the equilibrium dissociation constant. The value to get a half-maximum binding at equilibrium.
                In the CSM the initial value is calculated from the ligand concentration.
                The ligand concentration is inputted in the SpectrumGroup Series values.

    :param BMax: Defines the max specific binding.
                In the CSM the initial value is calculated from the CS deltas.
                Note, The optimised BMax will be (probably always) larger than the measured CS.
    :param Hs: hill slope. Default 1 to assume no cooperativity.
                Hs = 1: ligand/monomer binds to one site with no cooperativity.
                Hs > 1: ligand/monomer binds to multiple sites with positive cooperativity.
                Hs < 0: ligand/monomer binds to multiple sites with variable affinities or negative cooperativity.
    :return:    Y array same shape of x. Represents the points for the fitted curve Y to be plotted.
                When plotting BMax is the Y axis, Kd the X axis.
    """

    Y =  (BMax * x **Hs) / (x**Hs + Kd**Hs)
    return Y


########################################################################################################################
########################                     Various Fitting Functions                       ###########################
########################################################################################################################

def inversionRecovery_func(x, decay=1, amplitude=1):
    """ Function used to describe the T1 decay
    """
    decay = ls.not_zero(decay)
    return amplitude * (1 - np.exp(-x / decay))

def exponentialDecay_func(x, decay=1, amplitude=1):
    """ Function used to describe the T2 decay
    """
    decay = ls.not_zero(decay)
    return amplitude * np.exp(-x / decay)

def exponential_func(x, amplitude, decay):
    return amplitude * np.exp(decay * x)

def blank_func(x, argA, argB):
    """
    A mock fitting function. Used for a Blank model.
    :param x: example argument. Not in use.
    :param argA: example argument. Not in use.
    :param argB: example argument. Not in use.
    :return: None
    """
    return

########################################################################################################################
########################                     Various Calculation Functions                   ###########################
########################################################################################################################

def r2_func(y, redchi):
    """
    Calculate the R2 (called from the minimiser results).
    :param redchi: Chi-square. From the Minimiser Obj can be retrieved as "result.redchi"
    :return: r2
    """
    var = np.var(y, ddof=2)
    if var != 0:
        r2 = 1 - redchi / var
        return r2

def euclideanDistance_func(array1, array2, alphaFactors):
    """
    Calculate the  Euclidean Distance of two set of coordinates using scaling factors. Used in CSM DeltaDeltas
    :param array1: (1d array), coordinate 1
    :param array2: (1d array), coordinate 2 of same shape of array1
    :param alphaFactors: the scaling factors.  same shape of array1 and 2.
    :return: float
    Ref.: Eq.(9) from: M.P. Williamson Progress in Nuclear Magnetic Resonance Spectroscopy 73 (2013) 1–16
    """
    deltas = []
    for a, b, factor in zip(array1, array2, alphaFactors):
        delta = a - b
        delta *= factor
        delta **= 2
        deltas.append(delta)
    return np.sqrt(np.mean(np.array(deltas)))

def _checkValidValues(values):
    """
    Check if values contain 0, None or np.nan
    :param values: list
    :return: bool
    """
    notAllowed = [0, None, np.nan]
    for i in values:
        if i in notAllowed:
            return False
    return True

def peakErrorBySNR(snrPeak1, snrPeak2, factor=1):
    """
    Calculate the Error of NOE measurements (as in AnalysisV2)
    :param factor: float, correction factor.
    :param snrPeak1: float, signal to noise ratio for Peak 1
    :param snrPeak2: float, signal to noise ratio for Peak 2
    :return: float or None
    Ref.: 1) eq. 4 from Kharchenko, V., et al. Dynamic 15N{1H} NOE measurements: a tool for studying protein dynamics.
             J Biomol NMR 74, 707–716 (2020). https://doi.org/10.1007/s10858-020-00346-6
    """
    if not _checkValidValues([snrPeak1, snrPeak2, factor]):
        return
    error = abs(factor) * np.sqrt(snrPeak1**-2 + snrPeak2**-2)
    return error

def hetNoeError(sat, nonSat, noiseSat, noiseNonSat, factor=1):
    """
    Calculate the Error of NOE measurements (as in AnalysisV2)
    :param factor: float, correction factor. E.g.: intensity  ratio value for the saturated/unsaturated
    :param sat: float, intensity value for the saturated Peak
    :param nonSat: float, intensity value for the unsaturated(reference) Peak
    :param noiseSat: float, noise value for the saturated Spectrum
    :param noiseNonSat: float, noise value for the unsaturated Spectrum
    :return:
    Ref.:
    """
    error = factor * np.sqrt((noiseSat / sat) ** 2 + (noiseNonSat / nonSat) ** 2)
    return error

def _scaleMinMaxData(data, minMaxRange=(1.e-5, 1)):
    """
    :param data: 1d Array
    :return 1d Array
    Scale data  to value minMaxRange"""
    from sklearn.preprocessing import MinMaxScaler
    data = data.reshape(-1, 1)
    scaler = MinMaxScaler(feature_range=minMaxRange)
    scaler = scaler.fit(data)
    scaledData = scaler.transform(data)
    scaledData = scaledData.flatten()
    return scaledData

def _scaleStandardData(data, with_mean=True, with_std=True):
    """
    :param data: 1d Array
    :return 1d Array
    Scale data to StandardScale; Standardise features by removing the mean and scaling to unit variance.
    see sklearn StandardScaler for more information"""
    from sklearn.preprocessing import StandardScaler
    data = data.reshape(-1, 1)
    scaler = StandardScaler(with_mean=with_mean, with_std=with_std)
    scaler = scaler.fit(data)
    scaledData = scaler.transform(data)
    return scaledData.flatten()

def _formatValue(value, maxInt=3, floatPrecision=3, expDigits=1):
    """Convert value to numeric when possible """
    try:
        if isinstance(value, (float, int)):
            if len(str(int(value))) > maxInt:
                value = np.format_float_scientific(value, precision=floatPrecision, exp_digits=expDigits)
            else:
                value = round(value, 4)
    except Exception as ex:
        getLogger().debug2(f'Impossible to format {value}. Error:{ex}')
    return value

CommonStatFuncs = {
                sv.MEAN     : np.mean,
                sv.MEDIAN   : np.median,
                sv.STD      : np.std,
                sv.VARIANCE : np.var,
                }


# import matplotlib.pyplot as plt
# x = np.arange(1, 1000)
# Kd, BMax, P = 56, 0.18, 1
# ys = oneSiteBinding_func(x, Kd, BMax )
# yns = oneSiteNonSpecBinding_func(x, -0.01 )
# plt.plot(ys)
# plt.plot(yns)
# plt.show()
