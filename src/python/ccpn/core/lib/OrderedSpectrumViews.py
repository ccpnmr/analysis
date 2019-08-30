"""
  ejb - orderedSpectrumViews, orderedSpectra
  store the current orderedSpectrumViews in the internal data store _ccpnInternalData
  so it is hidden from external users

  accessed with the functions:
      strip.orderedSpectra()        returns tuple(spectra) or None
      strip.orderedSpectrumViews    returns tuple(spectrumViews) or None

  use setOrderedSpectrumViews(<tuple>) to set the list
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2018-12-20 15:53:01 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Optional, List
from functools import partial
from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlock


SPECTRUMVIEWINDEX = '_spectrumViewIndex'


class OrderedSpectrumViews(object):
    # _spectrumViewIndex = None

    def __init__(self, parent=None):
        self._parent = parent
        self.project = parent.project
        self.spectrumViews = parent.spectrumViews

    def _retrieveOrderedSpectrumViewIndex(self):
        """
        Retrieve the indexing form the ccpnInternal database
        :return: tuple of ints
        """
        if isinstance(self._parent._ccpnInternalData, dict) and \
                SPECTRUMVIEWINDEX in self._parent._ccpnInternalData:
            return self._parent._ccpnInternalData[SPECTRUMVIEWINDEX]

    def _storeOrderedSpectrumViewIndex(self, spectrumViewIndex: Tuple[int]):
        """
        Store the indexing from the ccpnInternal database
        """
        if isinstance(self._parent._ccpnInternalData, dict):
            # _wrappedData._ccpnInternalData won't flag for saving unless the dict changes
            tempCcpn = self._parent._ccpnInternalData.copy()
            tempCcpn[SPECTRUMVIEWINDEX] = spectrumViewIndex
            self._parent._ccpnInternalData = tempCcpn

    def orderedSpectrumViews(self, spectrumList, includeDeleted=True) -> Optional[Tuple]:
        """
        The spectrumViews attached to the strip (ordered)
        :return: tuple of SpectrumViews
        """
        # if not self._spectrumViewIndex:
        # index = self._retrieveOrderedSpectrumViewIndex()
        # if index is None:
        #     index = tuple(ii for ii in range(len(spectrumList)))
        #
        # self._spectrumViewIndex = index
        # self._storeOrderedSpectrumViewIndex(index)

        _spectrumViewIndex = self._retrieveOrderedSpectrumViewIndex()
        if _spectrumViewIndex is None:
            _spectrumViewIndex = tuple(ii for ii in range(len(spectrumList)))

        # if there are too many spectrumViews then increase the length of the list
        while len(_spectrumViewIndex) < len(spectrumList):
            _spectrumViewIndex += (len(_spectrumViewIndex),)

        self._storeOrderedSpectrumViewIndex(_spectrumViewIndex)

        # return the reordered spectrumList
        return tuple(spectrumList[index] for index in _spectrumViewIndex if index < len(spectrumList))
        # if not spectrumList[index].isDeleted or includeDeleted)

    def getOrderedSpectrumViewsIndex(self) -> Optional[Tuple]:
        """
        The current indexing list
        :return: tuple of ints
        """
        # if not self._spectrumViewIndex:
        #
        #     index = self._retrieveOrderedSpectrumViewIndex()
        #     if index is None:
        #         index = tuple(ii for ii in range(len(self._parent.spectrumViews)))
        #
        #     self._spectrumViewIndex = index
        #     self._storeOrderedSpectrumViewIndex(index)

        _spectrumViewIndex = self._retrieveOrderedSpectrumViewIndex()
        if _spectrumViewIndex is None:
            _spectrumViewIndex = tuple(ii for ii in range(len(self._parent.spectrumViews)))

        self._storeOrderedSpectrumViewIndex(_spectrumViewIndex)

        # return the index list
        return _spectrumViewIndex

    # def _setOrderedSpectrumViews(self, spectrumIndex: Tuple):
    #     self._spectrumViewIndex = tuple(spectrumIndex)
    #     self._storeOrderedSpectrumViewIndex(spectrumIndex)
    #
    # def _undoOrderedSpectrumViews(self, spectrumIndex: Tuple):
    #     self._spectrumViewIndex = tuple(spectrumIndex)
    #     self._storeOrderedSpectrumViewIndex(spectrumIndex)

    def setOrderedSpectrumViewsIndex(self, spectrumIndex: Tuple[int]):
        """
        Set the ordering of the spectrumViews attached to the strip/spectrumDisplay
        :param spectrumIndex: tuple of ints
        """
        with undoBlock():
            with undoStackBlocking() as addUndoItem:
                # _oldSpectrumViews = self._spectrumViewIndex
                _oldSpectrumViews = self._retrieveOrderedSpectrumViewIndex()
                self._storeOrderedSpectrumViewIndex(spectrumViewIndex=spectrumIndex)

                addUndoItem(undo=partial(self._storeOrderedSpectrumViewIndex, _oldSpectrumViews),
                            redo=partial(self._storeOrderedSpectrumViewIndex, spectrumIndex))
