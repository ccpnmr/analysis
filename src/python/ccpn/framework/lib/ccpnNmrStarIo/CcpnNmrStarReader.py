"""
Module to manage Star files in ccpn context
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
__dateModified__ = "$dateModified: 2022-02-17 19:09:52 +0000 (Thu, February 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2020-02-17 10:28:41 +0000 (Thu, February 17, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger
from ccpn.util.nef.StarIo import NmrDataBlock, NmrSaveFrame, NmrLoop, parseNmrStarFile
from ccpn.util.nef.GenericStarParser import PARSER_MODE_STANDARD, LoopRow

from ccpn.framework.lib.ccpnNmrStarIo.SaveFrameABC import SaveFrameABC, getSaveFrames


class CcpnNmrStarReader():
    """Class to read/parse and import (bmrb) NmrStar files
    """

    def __init__(self, project):
        """Initialise CcpnStarReader instance
        :param project: a Project instance
        """
        self.project = project
        self.path = None  # Absolute path to star file used to fill self
        self._dataBlock = None

    @property
    def dataBlock(self):
        """:return the NmrDataBlock or None, depending of a file has been parsed
        """
        return self._dataBlock

    def parse(self, path, mode=PARSER_MODE_STANDARD):
        """
        :param path: path of the star-file to parse
        :param mode: parsing mode: any of ('lenient', 'strict', 'standard', 'IUCr')
        :return self, i.e. an NmrDataBlock instance
        """
        if path is None:
            raise ValueError('Undefined path')

        path = aPath(path)
        if not path.exists():
            raise RuntimeError('Path "%s" does not exists')

        _data = parseNmrStarFile(path.asString(), mode=mode, wrapInDataBlock=True)
        if len(_data) == 0:
            raise RuntimeError(f'CcpnStarReader.parse: no valid NmrDataBlock obtained from "{path.asString()}"')
        elif len(_data) > 1:
            getLogger().warning(f'CcpnStarReader.parse: multiple NmrDataBlock\'s were obtained from "{path.asString()}"; using first one only')

        #_data is a NamedOrderedDict instance of (key, NmrDataBlock) instances;
        # get the first key-ed value
        _keys = list(_data.keys())
        _dataBlock = _data[_keys[0]]
        # now check if we have to do any saveFrame "updates"
        saveFrameDefs = getSaveFrames()
        for key, saveFrame in _dataBlock.items():
            if (klass := saveFrameDefs.get(saveFrame.category)) is not None:
                instance = klass.newFromSaveFrame(parent=self, saveFrame=saveFrame)
                _dataBlock[key] = instance

        self._dataBlock = _dataBlock
        self.path = path

        return self

    def importIntoProject(self) -> list:
        """Import the data of the saveFrame's of self into project
        :return A list of imported V3 objects
        """
        result = []
        for key, saveFrame in self.dataBlock.items():
            if not isinstance(saveFrame, SaveFrameABC):
                getLogger().warning(f'CcpNmrStarReader.importIntoProject: cannot import "{key}" (category {saveFrame.category})')
            else:
                objs = saveFrame.importIntoProject(project=self.project)
                result.extend(objs)
        return result

    def __str__(self):
        return f'<{self.__class__.__name__}: path={self.path}>'
