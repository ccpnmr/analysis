"""
This file contains CcpnNefImporter class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-02-15 16:47:14 +0000 (Tue, February 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-02-05 10:28:48 +0000 (Saturday, February 5, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.Application import getApplication
from ccpn.framework.lib.ccpnNef.CcpnNefIo import CcpnNefReader

from ccpn.util.Logging import getLogger
from ccpn.util.nef.NefImporter import NefImporter
from ccpn.util.nef.ErrorLog import NEF_STANDARD, NEF_STRICT
from ccpn.core.lib.ContextManagers import catchExceptions, undoBlockWithoutSideBar, notificationEchoBlocking


class CcpnNefImporter(NefImporter):
    """A class for customization of the general NefImporter class
    """
    _DATANAME = 'ccpn_structuredata_name'
    _DATANAME_DEFAULT = 'structureFromNef'
    _DATANAME_DEPRECATED = 'ccpn_dataset_id'

    def __init__(self, errorLogging=NEF_STANDARD, validateDictPath=None, hidePrefix=True):
        """
        Initialise the CcpNefImporter instance. This will attach the logger and optionally a  Nef validation
        dictionary.
        :param errorLogging: Nef error logging level: one of (NEF_SILENT, NEF_STANDARD, NEF_STRICT)
        :param validateDictPath: Path to a Nef validation dictory definition (in star format)
        :param hidePrefix: hide nef prefixes
        """

        _app = getApplication()
        super().__init__(programName=_app.applicationName,
                         programVersion=_app.applicationVersion,
                         errorLogging=errorLogging,
                         hidePrefix=hidePrefix)

        # set the ccpn logger
        _logger = getLogger().error if errorLogging == NEF_STRICT else getLogger().warning
        self.logger = _logger

        self._reader = None
        self._application = _app
        self._collections = None

        if validateDictPath is not None:
            self.loadValidateDictionary(validateDictPath)

    def loadFile(self, fileName=None, mode='standard'):
        super(CcpnNefImporter, self).loadFile(fileName, mode)

        # process the data to replace ccpn_dataset_id wth ccpn_structuredata_name
        self.upgradeDataSetIds()

        return self.data

    def loadText(self, text, mode='standard'):
        super(CcpnNefImporter, self).loadText(text, mode)

        # process the data to replace ccpn_dataset_id wth ccpn_structuredata_name
        self.upgradeDataSetIds()

        return self.data

    def importIntoProject(self, project):
        """Import the data of self into project, using a previously attached
        reader (auto-generated if None).

        :param project: a Project instance
        """
        if self._reader is None:
            _reader = CcpnNefReader(application=self._application)
        else:
            _reader = self._reader

        _reader.importExistingProject(project, self.data)

        # finalise the project
        #   - add the collections from the importNefPopup to the project
        if self._collections:
            for col, itms in self._collections.items():
                # ignore collections that haven't had items imported
                _itms = [project.getByPid(itm) if isinstance(itm, str) else itm for itm in itms]
                _itms = list(filter(lambda obj: obj is not None and project.isCoreObject(obj), _itms))
                if _itms:
                    collection = project.fetchCollection(name=col)
                    itms = set(_itms) - set(collection.items)
                    collection.addItems(itms)

    @property
    def collections(self):
        return self._collections

    @collections.setter
    def collections(self, value):
        """Set the collections to be created from the imortNefPopup
        """
        if not isinstance(value, (dict, type(None))):
            raise ValueError('collections must be a dict or None')

        self._collections = value

    def upgradeDataSetIds(self):
        """Update the saveFrames
        Replace occurrences of DATANAME_DEPRECATED with DATANAME
        """
        getLogger().debug(f'>>> replacing tags {self._DATANAME_DEPRECATED} -> {self._DATANAME}')
        # search through the saveframes for occurrences of DATANAME
        _sfNames = self.getSaveFrameNames()
        for sf in _sfNames:
            sFrame = self.getSaveFrame(sf)
            if sFrame is not None and sFrame._nefFrame:

                sf = sFrame._nefFrame
                # replace the deprecated tag with the new tag
                if self._DATANAME_DEPRECATED in sf:
                    if self._DATANAME not in sf:
                        sf[self._DATANAME] = sf.get(self._DATANAME_DEPRECATED) or self._DATANAME_DEFAULT  # cannot be empty
                    del sf[self._DATANAME_DEPRECATED]  # remove as new tag takes priority
