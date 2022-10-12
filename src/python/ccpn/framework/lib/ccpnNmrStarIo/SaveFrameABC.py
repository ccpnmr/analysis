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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-12 15:27:08 +0100 (Wed, October 12, 2022) $"
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


def getSaveFrames() -> dict:
    """:return the dict with saveFrame class definitions
    """
    # local import here to effectuate the registering
    from ccpn.framework.lib.ccpnNmrStarIo.ChemicalShiftSaveFrame import ChemicalShiftSaveFrame
    from ccpn.framework.lib.ccpnNmrStarIo.EntitySaveFrame import EntitySaveFrame
    from ccpn.framework.lib.ccpnNmrStarIo.EntryInformationSaveFrame import EntryInformationSaveFrame
    return SaveFrameABC._registeredSaveFrames


class SaveFrameABC(NmrSaveFrame):
    """A class to manage; i.e. register the various saveFrames
    """
    # To be subclassed

    _sf_category = None
    _ENTRY_ID_TAG = 'entry_id'  # Different saveFrames hve different tag names for this (!!)

    # end subclass

    # dict for registering the classes
    _registeredSaveFrames = {}

    def __init__(self, parent, *args, **kwds):
        NmrSaveFrame.__init__(self, *args, *kwds)
        self._parent = parent

    @property
    def parent(self):
        return self._parent

    @property
    def entry_id(self) -> str:
        """:return the entry-Id as a str
        """
        _id = self.get(self._ENTRY_ID_TAG)
        if _id is None:
            return None
        return str(_id)

    @property
    def entryName(self) -> str:
        """:return the entryName (derived from entry_id) as a str
        """
        return  f'bmrb{self.entry_id}'

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        Needs subclassing
        :param project: a Project instance
        :return list of imported V3 objects
        """
        raise  NotImplementedError('importIntoProject requires subclassing')

    @classmethod
    def newFromSaveFrame(cls, parent, saveFrame:NmrSaveFrame):
        """return an instance, updated with the data from saveFrame
        """
        instance = cls(parent=parent, name=saveFrame.name)
        instance.update(saveFrame)
        instance.__dict__.update(saveFrame.__dict__)
        return instance

    @classmethod
    def _registerSaveFrame(cls):
        """Register the class
        """
        if cls._sf_category is None:
            raise RuntimeError(f'Undefined _sf_category for class "{cls.__name}"')
        cls._registeredSaveFrames[cls._sf_category] = cls

    def __str__(self):
        return f'<{self.__class__.__name__}: {self.name}>'

    __repr__ = __str__






