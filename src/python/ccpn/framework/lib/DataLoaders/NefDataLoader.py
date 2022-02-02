"""
This module defines the data loading mechanism for loading a NEF file
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-02-02 20:38:18 +0000 (Wed, February 02, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-06-30 10:28:41 +0000 (Fri, June 30, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Union, Optional, Sequence
from contextlib import contextmanager
from time import time
from ccpn.framework.lib.DataLoaders.DataLoaderABC import DataLoaderABC
from ccpn.util import Path
from ccpn.util.Logging import getLogger
from ccpn.util.nef.GenericStarParser import DataBlock
from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import undoStackBlocking, notificationBlanking
from ccpn.core.lib import CcpnNefIo


class NefDataLoader(DataLoaderABC):
    """NEF data loader
    """
    dataFormat = 'nefFile'
    suffixes = ['.nef']  # a list of suffixes that get matched to path
    canCreateNewProject = True
    alwaysCreateNewProject = False

    # def __init__(self, path):
    #     super(NefDataLoader, self).__init__(path)
    #     self.makeNewProject = self.createsNewProject  # A instance 'copy' to allow modification by the Gui

    def load(self):
        """The actual Nef loading method; subclassed to account for special
        circumstances
        raises RunTimeError on error
        :return: a list of [project]
        """
        try:
            if self.createNewProject:
                project = self.application._loadNefFile(self.path, makeNewProject=self.createNewProject)
            else:
                project = self.application._importNef(self.path)

        except (ValueError, RuntimeError) as es:
            raise RuntimeError('Error loading "%s" (%s)' % (self.path, str(es)))

        return [project]

    @staticmethod
    def readNefFile(path: Union[str, Path.aPath], nefValidationPath: Union[str, Path.aPath, None] = None, errorLogging=None, hidePrefix=True):
        """Create a Nef loader object and load a nef file into it together with a Nef validation file.
        If no validation file is specified, the default is taken from PathsAndUrls

        :param path: path to the nef file
        :param nefValidationPath: path to the nef validation file - an mmcif.dic file
        :param errorLogging: level of logging - 'standard', 'silent', 'strict'
        :param hidePrefix: True/False, hide the 'nef_' prefixes in the saveframes
        :return: instance of NefImporter
        """

        from ccpn.util.nef import NefImporter as Nef
        from ccpn.framework.PathsAndUrls import nefValidationPath as defaultNefValidationPath

        # set the default values if not specified
        _errorLogging = errorLogging or Nef.el.NEF_STRICT
        _validation = nefValidationPath or defaultNefValidationPath

        # check the parameters
        if not isinstance(path, (str, Path.Path)):
            raise ValueError(f'path {path} not defined correctly')
        if not isinstance(_validation, (str, Path.Path, type(None))):
            raise ValueError(f'nefValidationPath {_validation} not defined correctly')
        if _errorLogging not in [Nef.el.NEF_STANDARD, Nef.el.NEF_STRICT, Nef.el.NEF_SILENT]:
            raise ValueError(f'errorLogging must be one of: [{repr(Nef.el.NEF_STANDARD)}, {repr(Nef.el.NEF_STRICT)}, {repr(Nef.el.NEF_SILENT)}]')
        if not isinstance(hidePrefix, bool):
            raise ValueError(f'hidePrefix must be a bool')

        # convert to aPath objects
        path = Path.aPath(path) if isinstance(path, str) else path
        _validation = Path.aPath(_validation) if isinstance(_validation, str) else _validation

        # create the nef importer instance
        _importer = Nef.NefImporter(errorLogging=_errorLogging, hidePrefix=hidePrefix)

        # load the nef file and the validation file
        _importer.loadFile(path)
        _importer.loadValidateDictionary(_validation)

        return _importer

    @staticmethod
    def readNefText(text: str, nefValidationPath: Union[str, Path.aPath, None] = None, errorLogging=None, hidePrefix=True):
        """Create a Nef loader object and populate from a text string containing the nef structure together with a Nef validation file.

        If no validation file is specified, the default is taken from PathsAndUrls

        :param text: text containging the nef structure
        :param nefValidationPath: path to the nef validation file - an mmcif.dic file
        :param errorLogging: level of logging - 'standard', 'silent', 'strict'
        :param hidePrefix: True/False, hide the 'nef_' prefixes in the saveframes
        :return: instance of NefImporter
        """

        from ccpn.util.nef import NefImporter as Nef
        from ccpn.framework.PathsAndUrls import nefValidationPath as defaultNefValidationPath

        # set the default values if not specified
        _errorLogging = errorLogging or Nef.el.NEF_STRICT
        _validation = nefValidationPath or defaultNefValidationPath

        # check the parameters
        if not isinstance(text, str):
            raise ValueError(f'text not defined correctly')
        if not isinstance(_validation, (str, Path.Path, type(None))):
            raise ValueError(f'nefValidationPath {_validation} not defined correctly')
        if _errorLogging not in [Nef.el.NEF_STANDARD, Nef.el.NEF_STRICT, Nef.el.NEF_SILENT]:
            raise ValueError(f'errorLogging must be one of: [{repr(Nef.el.NEF_STANDARD)}, {repr(Nef.el.NEF_STRICT)}, {repr(Nef.el.NEF_SILENT)}]')
        if not isinstance(hidePrefix, bool):
            raise ValueError(f'hidePrefix must be a bool')

        # convert to aPath objects
        _validation = Path.aPath(_validation) if isinstance(_validation, str) else _validation

        # create the nef importer instance
        _loader = Nef.NefImporter(errorLogging=_errorLogging, hidePrefix=hidePrefix)

        # load the nef from text, and the validation file
        _loader.loadText(text)
        _loader.loadValidateDictionary(_validation)

        return _loader

    @contextmanager
    def deferredImport(self, path: Union[str, Path.Path], makeNewProject=True) -> Optional[Project]:
        from ccpn.core.lib.ContextManagers import undoBlock, notificationEchoBlocking
        from ccpn.ui.gui.popups.ImportNefPopup import ImportNefPopup, NEFFRAMEKEY_ENABLERENAME, \
            NEFFRAMEKEY_IMPORT, NEFFRAMEKEY_ENABLEMOUSEMENU, NEFFRAMEKEY_PATHNAME, \
            NEFFRAMEKEY_ENABLEFILTERFRAME, NEFFRAMEKEY_ENABLECHECKBOXES
        from ccpn.util.nef import NefImporter as Nef
        from ccpn.util.CcpnNefImporter import CcpnNefImporter
        from ccpn.framework.PathsAndUrls import nefValidationPath

        # # dataBlock = self.nefReader.getNefData(path)
        #
        # # the loader can be subclassed if required, and the type passed as nefImporterClass
        # # _loader = CcpnNefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
        #
        # # _loader = Nef.NefImporter(errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
        # # _loader.loadFile(path)
        # # _loader.loadValidateDictionary(nefValidationPath)
        #
        # # create/read the nef file
        # from ccpn.framework.lib.DataLoaders.DataLoaderABC import checkPathForDataLoader
        #
        # _loader = self.readNefFile(path, nefValidationPath=nefValidationPath, errorLogging=Nef.el.NEF_STRICT, hidePrefix=True)
        #
        # # verify popup here
        # selection = None
        #
        # dialog = ImportNefPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow,
        #                         # nefImporterClass=CcpnNefImporter,
        #                         nefObjects=({NEFFRAMEKEY_IMPORT: self.project,
        #                                      },
        #                                     {NEFFRAMEKEY_IMPORT           : _loader,
        #                                      NEFFRAMEKEY_ENABLECHECKBOXES : True,
        #                                      NEFFRAMEKEY_ENABLERENAME     : True,
        #                                      NEFFRAMEKEY_ENABLEFILTERFRAME: True,
        #                                      NEFFRAMEKEY_ENABLEMOUSEMENU  : True,
        #                                      NEFFRAMEKEY_PATHNAME         : str(path),
        #                                      })
        #                         )
        # with notificationEchoBlocking():
        #     dialog.fillPopup()
        #
        # dialog.setActiveNefWindow(1)
        # valid = dialog.exec_()
        #
        # if valid:
        #     selection = dialog._saveFrameSelection
        #     _nefReader = dialog.getActiveNefReader()
        #
        #     if makeNewProject:
        #         if self.project is not None:
        #             self._closeProject()
        #         self.project = self.newProject(_loader._nefDict.name)
        #
        #     # import from the loader into the current project
        #     self.importFromLoader(_loader, reader=_nefReader)
        #
        #     # self.project.shiftAveraging = False
        #     # # with suspendSideBarNotifications(project=self.project):
        #     #
        #     # with undoBlockWithoutSideBar():
        #     #     with notificationEchoBlocking():
        #     #         with catchExceptions(application=self, errorStringTemplate='Error importing Nef file: %s', printTraceBack=True):
        #     #             # need datablock selector here, with subset selection dependent on datablock type
        #     #
        #     #             _nefReader.importNewProject(self.project, _loader._nefDict, selection)
        #     #
        #     # self.project.shiftAveraging = True
        #
        #     getLogger().info('==> Loaded NEF file: "%s"' % (path,))
        #     return self.project

    @staticmethod
    def _convertToDataBlock(project, skipPrefixes: Sequence = (),
                            expandSelection: bool = True,
                            pidList: list = None):
        """
        Export selected contents of the project to a Nef file.

          skipPrefixes: ( 'ccpn', ..., <str> )
          expandSelection: <bool> }

          Include 'ccpn' in the skipPrefixes list will exclude ccpn specific items from the file
          expandSelection = True  will include all data from the project, this may not be data that
                                  is not defined in the Nef standard.

        PidList is a list of <str>, e.g. 'NC:@-', obtained from the objects to be included.
        The Nef file may also contain further dependent items associated with the pidList.

        :param skipPrefixes: items to skip
        :param expandSelection: expand the selection
        :param pidList: a list of pids
        """
        # from ccpn.core.lib import CcpnNefIo

        with undoStackBlocking():
            with notificationBlanking():
                t0 = time()
                dataBlock = CcpnNefIo.convertToDataBlock(project, skipPrefixes=skipPrefixes,
                                                         expandSelection=expandSelection,
                                                         pidList=pidList)
                t2 = time()
                getLogger().info('File to dataBlock, time = %.2fs' % (t2 - t0))

        return dataBlock

    @staticmethod
    def _writeDataBlockToFile(dataBlock: DataBlock = None, path: str = None,
                              overwriteExisting: bool = False):
        # Export the modified dataBlock to file
        # from ccpn.core.lib import CcpnNefIo

        with undoStackBlocking():
            with notificationBlanking():
                t0 = time()
                CcpnNefIo.writeDataBlock(dataBlock, path=path, overwriteExisting=overwriteExisting)
                t2 = time()
                getLogger().info('Exporting dataBlock to file, time = %.2fs' % (t2 - t0))


NefDataLoader._registerFormat()
