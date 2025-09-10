"""
Get the slice Data at a peak position and save it as a new spectrum per each dimension.

Select a peak, Run the macro.
"""

import numpy as np
from ccpn.core.lib.ContextManagers import undoBlockWithSideBar
from ccpn.util.Path import fetchDir, joinPath, aPath
from ccpn.core.Spectrum import _extractRegionToFile

## ~ New spectrum  name formatting
decimalSeparator = '-' # replace the . (dot) with an underscore. Specify here an alternative. Not Allowed: . % $ @ ! | \ ' ; : ? ~ `
ppmRounding = 2
namesSeparator = '_'


peak = current.peak
spectrum = peak.spectrum
if project.spectraPath is None:
    raise RuntimeError('You need to set your project path Directory in Preferences.')
projectSpectraPath = project.spectraPath

for dim in spectrum.dimensions:
    pointPositions = np.array(peak.pointPositions, dtype=int)
    ppmPositionsStr = f'{namesSeparator}'.join([f'{i:.{ppmRounding}f}'.replace('.', decimalSeparator) for i in peak.ppmPositions])
    axisCodes = spectrum.getByDimensions('axisCodes',dimensions=[dim])
    with undoBlockWithSideBar():
        # set everything as a single undo-operation
        spectrumName = f'{spectrum.name}{namesSeparator}{axisCodes[0]}{namesSeparator}[{ppmPositionsStr}_ppm]'
        savingPath = aPath(joinPath(project.spectraPath, spectrumName, ))
        savingPath = savingPath.assureSuffix('ndf5')
        sp = spectrum.extractSliceToFile(axisCodes[0], pointPositions, path=savingPath)
        sp.noiseLevel = spectrum.noiseLevel
