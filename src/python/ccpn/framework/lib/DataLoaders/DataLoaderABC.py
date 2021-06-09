"""
This module defines the data loading mechanism.

Loader instances have all the information regarding a particular data type
(e.g. a ccpn project, a NEF file, a PDB file, etc. and include a hander function to to the actual
work of loading the data into the project.
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict

from ccpn.util.Path import aPath
from ccpn.util.traits.TraitBase import TraitBase
from ccpn.util.traits.CcpNmrTraits import Unicode, Any, List, Bool, CPath, Odict
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton
from ccpn.framework.Framework import getApplication


# from sandbox.Geerten.Refactored.dataLoaders.loadCcpNmr import loadCcpNmrV3, isCcpNmrV2Project, \
#     loadCcpNmrV2, loadCcpNmrTgzCompressed, loadCcpNmrZipCompressed
# from sandbox.Geerten.Refactored.dataLoaders.loadNef import loadNef
# from sandbox.Geerten.Refactored.dataLoaders.loadSparky import loadSparky
# from sandbox.Geerten.Refactored.dataLoaders.loadPdb import loadPdb, isPdbFile
# from sandbox.Geerten.Refactored.dataLoaders.loadSpectrum import loadSpectrum, isSpectrum
#
# from sandbox.Geerten.Refactored.dataLoaders.loadExcel import loadExcel
# from sandbox.Geerten.Refactored.decorators import debug2Enter, debug2Leave


#--------------------------------------------------------------------------------------------
# matching functions; Need to review lib/io/Formats.py and ioFormats.analyseUrl(path)
#--------------------------------------------------------------------------------------------

def caseInsensitiveSuffix(pattern, path):
    """match pattern to path as case-insentive suffix"""
    return path.lower().endswith(pattern.lower())




CCPNMRV2PROJECT = 'ccpNmrV2Project'
CCPNMRTGZCOMPRESSED = 'ccpNmrTgzCompressed'
CCPNMRZIPCOMPRESSED = 'ccpNmrZipCompressed'

NEFFILE = 'nefFile'
UCSFSPECTRUM = 'ucsfSpectrum'
SPARKYFILE = 'sparkyFile'
PDBFILE = 'pdbFile'
EXCELFILE = 'excelFile'

SPECTRUM = 'Spectrum'

AZARASPECTRUM = 'azaraSpectrum'
BRUKERSPECTRUM = 'brukerSpectrum'
FELIXSPECTRUM = 'felixSpectrum'
HDF5SPECTRUM = 'hdf5Spectrum'
NMRPIPESPECTRUM = 'nmrpipeSpectrum'
NMRVIEWSPECTRUM = 'nmrviewSpectrum'
VARIANSPECTRUM = 'varianSpectrum'
XEASYSPECTRUM = 'xeasySpectrum'

def getDataLoaders():
    """Get data loader classes
    :return: a dictionary of (format-identifier-strings, DataLoader classes) as (key, value) pairs
    """
    #--------------------------------------------------------------------------------------------
    # The following imports are just to assure that all the classes have been imported
    # hierarchy matters!
    # It is local to prevent circular imports
    #--------------------------------------------------------------------------------------------
    from ccpn.framework.lib.DataLoaders.CcpNmrV3ProjectDataLoader import CcpNmrV3ProjectDataLoader
    from ccpn.framework.lib.DataLoaders.SpectrumDataLoader import SpectrumDataLoader

    return DataLoaderABC._dataLoaders


def checkPathForDataLoader(path):
    """Check path if it corresponds to any defined data format

    return: a DataLoader instance or None if there was no match
    """
    for fmt, cls in getDataLoaders().items():
        instance = cls.checkForValidFormat(path)
        if instance is not None:
            return instance  # we found a valid format for path
    return None

#--------------------------------------------------------------------------------------------
# DataLoader class
#--------------------------------------------------------------------------------------------

class DataLoaderABC(TraitBase):
    """A DataLoaderABC: has definition for patterns

    Maintains a load(project) methods to do the actual loading
    """

    #=========================================================================================
    # to be subclassed
    #=========================================================================================
    dataFormat = None
    suffixes = []  # a list of suffixes that gets matched to path
    createsNewProject = False

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        raise NotImplementedError()

    def load(self):
        """The actual loading method; to be subclassed
        :return: object representing the data or None on error
        """
        raise NotImplementedError()

    #=========================================================================================
    # end to be subclassed
    #=========================================================================================

    # traits
    path = CPath().tag(info='a path to a file to be loaded')
    application = Any(default_value=None, allow_none=True)
    project = Any(default_value=None, allow_none=True)

    # A dict of registered DataLoaders: filled by _registerFormat classmethod, called
    # once after each definition of a new derived class (e.g. PdbDataLoader)
    _dataLoaders = OrderedDict()

    @classmethod
    def _registerFormat(cls):
        "register cls.dataFormat"
        if cls.dataFormat in DataLoaderABC._dataLoaders:
            raise RuntimeError('dataLoader "%s" was already registered' % cls.dataFormat)
        DataLoaderABC._dataLoaders[cls.dataFormat] = cls

    #=========================================================================================
    # start of methods
    #=========================================================================================
    def __init__(self, path):
        super().__init__()
        self.path = aPath(path)
        if not self.path.exists():
            raise ValueError('Invalid path "%s"' % path)

        self.application = getApplication()
        self.project = self.application.project




