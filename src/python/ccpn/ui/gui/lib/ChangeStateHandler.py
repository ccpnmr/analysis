"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-27 16:10:33 +0100 (Wed, May 27, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-27 09:44:50 +0000 (Wed, May 27, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import namedtuple, OrderedDict
from contextlib import contextmanager


changeState = namedtuple('changeState', ('widget',
                                         'allChanges',
                                         'applyState',
                                         'revertState',
                                         'okButton',
                                         'applyButton',
                                         'revertButton',
                                         'numApplies',
                                         ))


class ChangeDict(OrderedDict):
    """Dict that contains the changes that are applied to a popup
    Can be enabled or disabled
    """

    def __init__(self, enabled=True, *args, **kwds):
        super(ChangeDict, self).__init__(*args, **kwds)
        self._enabled = enabled
        self._blockingLevel = 0
        self._lastEnabledState = True

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if isinstance(value, bool):
            self._enabled = value
        else:
            raise TypeError('{} must be a bool'.format(value))

    @contextmanager
    def blockChanges(self):
        """Block all changes to the dict
        """
        self._blockChanges()
        try:
            yield  # yield control to the calling process

        except Exception as es:
            raise es
        finally:
            self._unblockChanges()

    def _blockChanges(self):
        """Block all Changes to the dict
        """
        if not hasattr(self, '_blockingLevel'):
            self._blockingLevel = 0

        # block all changes on first entry
        if self._blockingLevel == 0:
            # remember last state
            self._lastEnabledState = self._enabled
            self._enabled = False

        self._blockingLevel += 1

    def _unblockChanges(self):
        """Unblock all changes to the dict
        """
        if self._blockingLevel > 0:
            self._blockingLevel -= 1

            # unblock all signals on last exit
            if self._blockingLevel == 0:
                self._enabled = self._lastEnabledState

        else:
            raise RuntimeError('Changes blocking already at 0')
