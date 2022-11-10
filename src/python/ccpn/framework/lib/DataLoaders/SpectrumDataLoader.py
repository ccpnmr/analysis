"""
This module defines the data loading mechanism for spectra; it uses the SpectrumDataSources
rotuines and info
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-11-10 13:35:48 +0000 (Thu, November 10, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC, NO_SUFFIX, ANY_SUFFIX
from ccpn.core.Spectrum import _newSpectrumFromDataSource
from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import getDataFormats, checkPathForSpectrumFormats, \
      DataSourceTrait
from ccpn.core.lib.DataStore import DataStore, DataStoreTrait


class SpectrumDataLoaderABC(DataLoaderABC):
    """Spectrum loader ABC; defined by a SpectrumDataSource derived class
    that have essential settings (and do the actual work).
    """
    spectumDataSourceClass = None

    @classmethod
    def _initClass(cls):
        """Init the class attributes from the SpectrumDataSource class;
        register the class
        """
        cls.__doc__ = cls.spectumDataSourceClass.__doc__
        cls.dataFormat = cls.spectumDataSourceClass.dataFormat + 'Spectrum'
        cls.suffixes = cls.spectumDataSourceClass.suffixes
        cls.allowDirectory = cls.spectumDataSourceClass.allowDirectory
        cls._registerFormat()

    alwaysCreateNewProject = False
    canCreateNewProject = False
    isSpectrumLoader = True

    dataSource = DataSourceTrait(default_value=None)
    dataStore = DataStoreTrait(default_value=None)

    def __init__(self, path):
        """
        :param path: path to (binary) spectrum file; may contain redirections (e.g $DATA)
        """
        self.dataStore = DataStore.newFromPath(path, dataFormat=self.spectumDataSourceClass.dataFormat)
        self.dataSource = self.spectumDataSourceClass(self.dataStore.aPath())

        super().__init__(path=self.dataStore.aPath())

    def checkValid(self) -> bool:
        """check if path defines one of the valid spectrum data formats
        :param path: path to (binary) spectrum file; may contain redirections (e.g $DATA)
        Calls super-class which does_checkPath and _checkSuffix
        sets self.isValid and self.errorString
        :returns True if ok or False otherwise
        """
        if not super().checkValid():
            return False

        self.isValid = False
        self.errorString = 'Checking validity'

        if self.dataSource is None:
            self.errorString = f'"{self.path}": Failed to initiate a {self.spectumDataSourceClass.__name__} instance'
            return False

        self.isValid = self.dataSource.isValid
        self.shouldBeValid = self.dataSource.shouldBeValid
        self.errorString = self.dataSource.errorString
        return self.isValid

    def getAllFilePaths(self) -> list:
        """
        Get all the files handles by this loader. Generally, this will be the path that
        the loader represented, but sometimes there might be more; i.e. for certain spectrum
        loaders that handle more files; like a binary and a parameter file.
        To be subclassed for those instances

        :return: list of Path instances
        """
        if self.dataSource is None:
            raise RuntimeError('dataSource undefined: unable to get files')
        return self.dataSource.getAllFilePaths()

    @classmethod
    def _documentClass(cls) -> str:
        """:return a documentation string comprised of __doc__ and some class attributes
        """
        result = f'Spectrum binary data.\n'+\
            super()._documentClass() + '\n' +\
            f'    DataSource format:   {cls.spectumDataSourceClass.dataFormat}\n' +\
            f'    Has writing ability: {cls.spectumDataSourceClass.hasWritingAbility}'
        return result

    def load(self):
        """The actual spectrum loading method;
        raises RunTimeError on error
        :return: a list of [spectrum]
        """
        if self.dataSource is None:
            raise RuntimeError(f'DataSource is None')

        if not self.dataSource.isValid:
            raise RuntimeError(f'Error: {self.dataSource.errorString}')

        spectrum = _newSpectrumFromDataSource(project=self.project,
                                              dataStore=self.dataStore,
                                              dataSource=self.dataSource)

        return [spectrum]

    def existsInProject(self) -> bool:
        """Check for existance of spectra with the identical binary data.
        :return True if such a spectrum exists in the project
        """
        # check the dataSources of all spectra of the project for file pointers to the same file
        _binaryData = self.dataSource.path if self.dataSource is not None else ''
        for ds in [sp.dataSource for sp in self.project.spectra if sp.hasValidPath()]:
            _p = ds.path
            if _p is not None and len(_p) > 0 and _p == _binaryData:
                return True
        return False


class BrukerSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.BrukerSpectrumDataSource import BrukerSpectrumDataSource
    spectumDataSourceClass = BrukerSpectrumDataSource
BrukerSpectrumLoader._initClass()  # also registers


class NmrPipeSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.NmrPipeSpectrumDataSource import NmrPipeSpectrumDataSource
    spectumDataSourceClass = NmrPipeSpectrumDataSource
NmrPipeSpectrumLoader._initClass()   # also registers


class Hdf5SpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.Hdf5SpectrumDataSource import Hdf5SpectrumDataSource
    spectumDataSourceClass = Hdf5SpectrumDataSource
Hdf5SpectrumLoader._initClass()   # also registers


class UcsfSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.UcsfSpectrumDataSource import UcsfSpectrumDataSource
    spectumDataSourceClass = UcsfSpectrumDataSource
UcsfSpectrumLoader._initClass()   # also registers


class AzaraSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.AzaraSpectrumDataSource import AzaraSpectrumDataSource
    spectumDataSourceClass = AzaraSpectrumDataSource

AzaraSpectrumLoader._initClass()   # also registers


class FelixSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.FelixSpectrumDataSource import FelixSpectrumDataSource
    spectumDataSourceClass = FelixSpectrumDataSource
FelixSpectrumLoader._initClass()   # also registers


class XeasySpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.XeasySpectrumDataSource import XeasySpectrumDataSource
    spectumDataSourceClass = XeasySpectrumDataSource
XeasySpectrumLoader._initClass()   # also registers


class NmrViewSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.NmrViewSpectrumDataSource import NmrViewSpectrumDataSource
    spectumDataSourceClass = NmrViewSpectrumDataSource
NmrViewSpectrumLoader._initClass()   # also registers


class JcampSpectrumLoader(SpectrumDataLoaderABC):
    from ccpn.core.lib.SpectrumDataSources.JcampSpectrumDataSource import JcampSpectrumDataSource
    spectumDataSourceClass = JcampSpectrumDataSource
JcampSpectrumLoader._initClass()   # also registers
