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
__dateModified__ = "$dateModified: 2022-08-24 16:33:31 +0100 (Wed, August 24, 2022) $"
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


class EntryInformationSaveFrame(SaveFrameABC):
    """A class to manage the BMRB entry_information saveFrame
    Info is imported into a Note
    """
    # NOTE the parser code converts tags to lower case!

    _sf_category = 'entry_information'
    _ENTRY_ID_TAG = 'id'

    _TITLE_TAG = 'title'
    _SUBMISSION_DATE_TAG = 'submission_date'

    # this key contains the NmrLoop with the author data
    _LOOP_KEY = 'entry_author'
    # These keys define the author data
    _AUTHOR_FIRST_NAME_TAG = 'given_name'
    _AUTHOR_MIDDLE_NAME_TAG = 'middle_initials'
    _AUTHOR_LAST_NAME_TAG = 'family_name'

    # This key contains the NmrLoop with the data descriptions
    _DATA_KEY = 'datum'
    # These keys define the data
    _DATA_TYPE_TAG = 'type'
    _DATA_COUNT_TAG = 'count'

    @property
    def authors(self) ->list :
        """:return a list of residues LoopRow's
        """
        if (_loop := self.get(self._LOOP_KEY)) is None:
            return []
        return _loop.data

    @property
    def data(self) ->list :
        """:return a list of data LoopRow's
        """
        if (_loop := self.get(self._DATA_KEY)) is None:
            return []
        return _loop.data

    def importIntoProject(self, project) -> list:
        """Import the data of self into project.
        :param project: a Project instance.
        :return: list of imported V3 objects.
        """
        comment = f'{self.entry_id} Entry information'

        text = f'Data imported from: {self.parent.path}\n'
        text += f'\nBMRB entry: {self.entry_id}\n'
        text += f'Submission date: {self[self._SUBMISSION_DATE_TAG]}\n'
        text += f'\nTitle: {self[self._TITLE_TAG]}\n'
        text += f'\nAuthors:\n'
        for author in self.authors:
             text += f'  {author[self._AUTHOR_FIRST_NAME_TAG]} {author[self._AUTHOR_MIDDLE_NAME_TAG]} {author[self._AUTHOR_LAST_NAME_TAG]}\n'
        text += '\nData content:\n'
        for row in self.data:
            text += f'  {row[self._DATA_COUNT_TAG]} {row[self._DATA_TYPE_TAG]}\n'

        note = project.newNote(name=self.entryName, comment=comment, text=text)

        return [note]

EntryInformationSaveFrame._registerSaveFrame()

