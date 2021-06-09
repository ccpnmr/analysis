"""
This module defines the data loading mechanism for spectra; it uses the SpectrumDataSources
rotuines and info
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

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getDataFormats, checkPathForSpectrumFormats, \
      DataSourceTrait
from ccpn.core.lib.DataStore import DataStore, DataStoreTrait
from ccpn.core.Spectrum import _newSpectrumFromDataSource


class SpectrumDataLoader(DataLoaderABC):
    """Spectrum data loader
    """

    dataFormat = 'Spectrum'
    suffixes = list(set([suf for spec in getDataFormats().values()
                         for suf in spec.suffixes if suf is not None]))  # a list of possible spectrum suffixes
    createsNewProject = False


    dataSource = DataSourceTrait(default_value=None)
    dataStore = DataStoreTrait(default_value=None)

    @classmethod
    def checkForValidFormat(cls, path):
        """check if valid format corresponding to dataFormat
        :return: None or instance of the class
        """
        dataStore = DataStore.newFromPath(path)
        dataSoure = checkPathForSpectrumFormats(dataStore.path)
        if dataSoure is not None:
            instance = cls(path)
            instance.dataSource = dataSoure
            instance.dataStore = dataStore
            instance.dataStore.dataFormat = dataSoure.dataFormat
            return instance

        return None

    def load(self):
        """The project loading method
        :return: object representing the data or None on error
        """
        spectrum = _newSpectrumFromDataSource(project=self.project, dataStore=self.dataStore, dataSource=self.dataSource)
        return spectrum

SpectrumDataLoader._registerFormat()