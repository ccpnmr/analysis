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
__date__ = "$Date: 2020-08-24 10:28:41 +0000 (Wed, August 24, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from ccpn.util.Logging import getLogger
from ccpn.util.nef.GenericStarParser import LoopRow
from ccpn.framework.lib.ccpnNmrStarIo.SaveFrameABC import SaveFrameABC

# from sandbox.Geerten.NTdb.NTdbLib import getNefName
from ccpn.framework.lib.NTdb.NTdbDefs import getNTdbDefs


class EntitySaveFrame(SaveFrameABC):
    """A class to manage the BMRB Entity saveFrame
    Creates a new Chain
    """
    # NOTE the parser code converts tags to lower case!

    _sf_category = 'entity'

    # this key contains the NmrLoop with the residue data
    _LOOP_KEY = 'entity_poly_seq'

    # These keys map the row onto the V3 ChemicalShift object
    _SEQUENCE_CODE_TAG = 'comp_index_id'
    _RESIDUE_TYPE_TAG = 'mon_id'

    @property
    def residues(self) ->list :
        """:return a list of residues LoopRow's
        """
        if (_loop := self.get(self._LOOP_KEY)) is None:
            return []
        return _loop.data

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        :param project: a Project instance.
        :return: list of imported V3 objects.
        """
        chainCode = self.parent.chainCode if self.parent.chainCode else \
                    self.entryName
        comment = f'Chain {chainCode} ({self.name}) from {self.entryName}'

        sequence = [res[self._RESIDUE_TYPE_TAG] for res in self.residues]
        startNumber = min([res[self._SEQUENCE_CODE_TAG] for res in self.residues])

        chain = project.newChain(shortName=chainCode,
                                 sequence=sequence, startNumber=startNumber,
                                 comment=comment)

        text = f'\n==> saveFrame "{self.name}"\n'
        text += f'Imported as {chain}  ({len(chain.residues)} Residues, {len(chain.atoms)} Atoms)\n'
        self.parent.note.appendText(text)

        return [chain]

EntitySaveFrame._registerSaveFrame()
