from ccpn.core.lib.SpectrumLib import arPLS_Implementation, als, WhittakerSmooth, arPLS, airPLS, polynomialFit, nmrGlueBaselineCorrector
import numpy as np

'''

Run Examples

import as 
from ccpn.core.lib.testing.Testing1DBaselineCorrection import runExample_als, runExample_WhittakerSmooth, runExample_arPLS, runExample_airPLS, runExample_polynomialFit, runExample_arPLS_Implementation

aslSpectrum = project.spectra[-1]
whittakerSmoothSpectrum = project.spectra[-1]
arPLS_Spectrum = project.spectra[-1]
airPLS_Spectrum = project.spectra[-1]
polynomialFitSpectrum = project.spectra[-1]

'''


def runExample_arPLS_Implementation(spectrum, lambdaValue=5.e4, maxValue=1e6, minValue=-1e6, itermax=10, interpolate=True):
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    aPi = arPLS_Implementation(yOriginal, lambdaValue, maxValue, minValue, itermax, interpolate)
    yNew = yOriginal - aPi
    params = ' arPLS_Implementation; lambdaValue=%s maxValue=%s, minValue=%s itermax=%s interpolate=%s' \
             % (str(lambdaValue), str(maxValue), str(minValue), str(itermax), str(interpolate))
    spectrum.intensities = yNew
    return spectrum


def runExample_als(spectrum, lam=10 ** 2, p=0.001, nIter=10):
    ''' default parameters: lam=10**2, p=0.001, nIter=10 '''
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    baselineAls = als(yOriginal, lam, p, nIter)
    yNew = yOriginal - baselineAls
    spectrum.intensities = yNew
    return spectrum


def runExample_WhittakerSmooth(spectrum, lambda_=100, differences=1):
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    w = np.ones(yOriginal.shape[0])
    ws = WhittakerSmooth(yOriginal, w, lambda_, differences)
    yNew = yOriginal - ws
    spectrum.intensities = yNew
    return spectrum


def runExample_arPLS(spectrum, lambda_=5.e5, ratio=1.e-6, itermax=50):
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    aP = arPLS(yOriginal, lambda_=lambda_, ratio=ratio, itermax=itermax)
    yNew = yOriginal - aP
    params = ' arPLS; lambda_=%s, ratio=%s, itermax=%s' % (str(lambda_), str(ratio), str(itermax))
    spectrum.intensities = yNew
    return spectrum


def runExample_airPLS(spectrum, lambda_=100, porder=1, itermax=15):
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    a = airPLS(yOriginal, lambda_=lambda_, porder=porder, itermax=itermax)
    yNew = yOriginal - a
    spectrum.intensities = yNew
    return spectrum


def runExample_polynomialFit(spectrum, order=1):
    xOriginal, yOriginal, spectrumName = spectrum.positions, spectrum.intensities, spectrum.name
    p = polynomialFit(xOriginal, yOriginal, order)
    yNew = yOriginal - p
    spectrum.intensities = yNew
    return spectrum

def runExample_polynomialFit2(spectrum):
    runExample_polynomialFit(spectrum, order=2)
    return spectrum

def runExample_polynomialFit3(spectrum):
    runExample_polynomialFit(spectrum, order=3)
    return spectrum

def runExample_Bdc(spectrum) :
    y = nmrGlueBaselineCorrector(spectrum.intensities)
    spectrum.intensities = y
    return spectrum

