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
__modifiedBy__ = "$modifiedBy: gvuister $"
__dateModified__ = "$dateModified: 2021-01-12 10:28:40 +0000 (Tue, January 12, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2021-01-12 10:28:40 +0000 (Tue, January 12, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys

from ccpn.framework import Framework
from ccpn.framework.Version import applicationVersion

from ccpn.core.lib.SpectrumDataSources.NmrPipeSpectrumDataSource import NmrPipeSpectrumDataSource, \
    NmrPipeInputStreamDataSource
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getSpectrumDataSource

# class Application(Framework):
#     pass


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Process arguments')

    parser.add_argument('--in', dest='inputPath',
                        default=None,
                        help='Input file; if ommitted read from <stdin>'
                        )

    parser.add_argument('--out', dest='outputPath',
                        default=None, required=True,
                        help='Output file (required)'
                        )

    parser.add_argument('--debug', dest='debug', action='store_true', help='Set logging level to debug')
    # parser.add_argument('--debug1', dest='debug', action='store_true', help='Set logging level to debug1 (=debug)')
    # parser.add_argument('--debug2', dest='debug2', action='store_true', help='Set logging level to debug2')
    # parser.add_argument('--debug3', dest='debug3', action='store_true', help='Set logging level to debug3')

    args = parser.parse_args()

    if args.inputPath is None:
        inPath = '<stdin>'
        pipeSource = NmrPipeInputStreamDataSource(temporaryBuffer=False, bufferPath=args.outputPath)
        hdf5Source = pipeSource.hdf5buffer

    else:
        inPath = args.inputPath
        pipeSource = NmrPipeSpectrumDataSource(path=inPath).readParameters()
        hdf5Source = pipeSource.initialiseHdf5Buffer(temporaryBuffer=False, path=args.outputPath)

    pipeSource.closeFile()

    sys.stderr.write('pipe2hdf5: Converted data from %r to %r' % (inPath, str(hdf5Source.path)))
