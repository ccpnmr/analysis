
"""
This macro simulates a 1D spectrum from an excel file (.xlsx) containing the following structure:
+============================================+
| Res |	CA   | CB  | CO   | N    | HN  | HA  |
|	1 |	152. | 19. | 178. | 125. | 8.  | 4.  |
+============================================+

Fill the parameters below as need it.
"""

# spectra params
excelFilePath = '/Users/luca/Desktop/simulatedSP.xlsx'
AxisCode = 'HN'  #  or 'HA' . Use this name as it appears in the excel file (Only H Spectra are currently supported)
SpectrumName = 'Simulated_'+AxisCode

LW = 0.0023
Height = 1000
Noise = 10

UseRandomValues = True # Set True if you want add random Heights and LineWidths within the following limits
lwLimits = (0.001, 0.005)
heightLimits = (100, 10000)

#####################################################################################################################

import pandas as pd
import numpy as np
import random
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.util.Common import name2IsotopeCode


def _lorentzian(points, center, linewidth, intensity=1):
    points = np.asarray(points)
    tau = 2 / linewidth
    delta = center - points
    x = delta * tau
    absorptive = (1 / (1 + x ** 2)) / linewidth
    normCoeff = absorptive.max()
    return intensity * absorptive / normCoeff

def _isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

df = pd.read_excel(excelFilePath)
if not AxisCode in df:
    showWarning('AxisCode not in Table', 'Check AxisCode parameter in this macro or the input file.')
else:
    peaks = df.get(AxisCode)
    isotopeCodes = [name2IsotopeCode(x) for x in [AxisCode]]
    sp = project.newEmptySpectrum(isotopeCodes=isotopeCodes, name=str(SpectrumName))
    # sp.positions = np.arange(*sp.spectrumLimits[0], 0.001)
    # can just call sp.positions which will fill of position is None, but here for clarity
    sp.positions = sp.getPpmArray(dimension=1)

    noise = np.random.normal(size=sp.positions.shape, scale=Noise)
    peakLines = []
    if peaks is not None:
        for pos in peaks.values:
            if _isfloat(pos):
                if UseRandomValues:
                    LW = random.choice(np.arange(min(lwLimits), max(lwLimits), 0.0001))
                    Height = random.choice(np.arange(min(heightLimits), max(heightLimits), 10))
                l = _lorentzian(sp.positions, pos, linewidth=LW, intensity=Height)
                peakLines.append(l)
        sp.intensities = noise + sum(peakLines)
    else:
        showWarning('','No chemicalShifts found.')