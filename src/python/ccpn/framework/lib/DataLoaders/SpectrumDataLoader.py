"""
This module defines the data loading mechanism for spectra; it uses the SpectrumDataSources
rotuines and info
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-09 17:40:32 +0000 (Tue, November 09, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getDataFormats, checkPathForSpectrumFormats, \
      DataSourceTrait
from ccpn.core.lib.DataStore import DataStore, DataStoreTrait
from ccpn.core.Spectrum import _newSpectrumFromDataSource
from ccpn.core.lib.ContextManagers import logCommandManager


class SpectrumDataLoader(DataLoaderABC):
    """Spectrum data loader
    """
    dataFormat = 'Spectrum'
    suffixes = list(set([suf for spec in getDataFormats().values()
                         for suf in spec.suffixes if suf is not None]))  # a list of possible spectrum suffixes

    dataSource = DataSourceTrait(default_value=None)
    dataStore = DataStoreTrait(default_value=None)

    @classmethod
    def checkForValidFormat(cls, path):
        """check if path defines one of the valid spectrum data formats
        :return: None or instance of the class
        """
        dataStore, dataSoure = cls._checkPathForSpectrumFormat(path)
        if dataSoure is not None:
            instance = cls(path)
            instance.dataSource = dataSoure
            instance.dataStore = dataStore
            return instance

        return None

    @staticmethod
    def _checkPathForSpectrumFormat(path):
        """Check if path yields a valid Spectrum dataSource
        return: (dataStore, dataSource) tuple, or None's if some failed
        """
        dataStore = DataStore.newFromPath(path)
        if not dataStore.exists():
            return (None, None)

        dataSoure = checkPathForSpectrumFormats(dataStore.path)
        if dataSoure is None:
            return (dataStore, None)
        dataStore.dataFormat = dataSoure.dataFormat

        return (dataStore, dataSoure)

    def load(self):
        """The actual spectrum loading method;
        raises RunTimeError on error
        :return: a list of [spectrum]
        """
        with logCommandManager('application', 'loadData', self.path):
            if self.dataSource is None:
                self.dataStore, self.dataSource = self._checkPathForSpectrumFormat(self.path)

            if self.dataSource is None:
                raise RuntimeError('Error loading "%s"' % self.path)

            try:
                spectrum = _newSpectrumFromDataSource(project=self.project,
                                                      dataStore=self.dataStore,
                                                      dataSource=self.dataSource)
            except (RuntimeError, ValueError) as es:
                raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return [spectrum]

    def existsInProject(self) -> bool:
        """:return True if spectrum exists in the project
        """
        # check the dataSources of all spectra of the project for open file pointers to the same file
        for ds in [sp._dataSource for sp in self.project.spectra if sp.hasValidPath()]:
            if ds.path == self.dataStore.aPath() and ds.hasOpenFile():
                return True
        return False



SpectrumDataLoader._registerFormat()
