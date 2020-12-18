#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-03 12:10:02 +0000 (Tue, November 03, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

def ppm2pnt(ppm, npoints, sf, sw, refppm, refpt):
  t = - npoints * sf /   float(sw)
  pnt = t*(ppm - refppm) + refpt
  return pnt

def _pnt2ppm(pnt, npoints, sf, sw, refppm, refpt):
  t = - npoints * sf / float(sw)
  ppm = (pnt - refpt)/t + refppm
  return ppm

def _hz2pnt(hz, npoints, sf, sw, refppm, refpt):
  t = - npoints / float(sw)
  pnt = t*(hz - sf*refppm) + refpt
  return pnt

def _pnt2hz(pnt, npoints, sf, sw, refppm, refpt):
  t = - npoints / float(sw)
  hz = (pnt - refpt)/t + sf*refppm
  return hz

def _genc(spectrum):
    npoints = spectrum.totalPointCounts
    sw = spectrum.spectralWidthsHz
    sf = spectrum.spectrometerFrequencies
    refpt = spectrum.referencePoints
    refppm = spectrum.referenceValues
