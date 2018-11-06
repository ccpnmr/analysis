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
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Optional, List

SPECTRUMVIEWINDEX = '_spectrumViewIndex'


class OrderedSpectrumViews(object):
    _spectrumViewIndex = None

    def __init__(self, parent=None):
        self._parent = parent
        self.project = parent.project
        self.spectrumViews = parent.spectrumViews

    def _retrieveOrderedSpectrumViewIndex(self):
        """
        retrieve the indexing form the ccpnInternal database
        :return list of ints:
        """
        if isinstance(self._parent._ccpnInternalData, dict) and \
                SPECTRUMVIEWINDEX in self._parent._ccpnInternalData:

            return self._parent._ccpnInternalData[SPECTRUMVIEWINDEX]
        else:
            return None

    def _storeOrderedSpectrumViewIndex(self, spectrumViewIndex:Tuple[int]):
        """
        store the indexing form the ccpnInternal database
        """
        if isinstance(self._parent._ccpnInternalData, dict):
            # _wrappedData._ccpnInternalData won't flag for saving unless the dict changes
            tempCcpn = self._parent._ccpnInternalData.copy()
            tempCcpn[SPECTRUMVIEWINDEX] = spectrumViewIndex
            self._parent._ccpnInternalData = tempCcpn

    # def orderedSpectra(self) -> Optional[Tuple]:
    #     """
    #     The spectra attached to the strip (ordered)
    #     :return tuple of spectra:
    #     """
    #     if self._spectrumViewIndex:
    #         return tuple(x.spectrum for x in self._spectrumViewIndex if not x.isDeleted)
    #     else:
    #         # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
    #         # store by pids
    # 
    #         pids = self._retrieveOrderedSpectrumViewPids()
    #         if pids is None:
    #             self._storeOrderedSpectrumViewPids(tuple(x.pid for x in self.spectrumViews))
    #             views = tuple(x for x in self.spectrumViews)
    #         else:
    #             views = tuple(self.project.getByPid(x) for x in pids if self.project.getByPid(x))
    # 
    #             # this should be the first read from loading the project, so write back without bad pids
    #             self._storeOrderedSpectrumViewPids(tuple(x.pid for x in views))
    # 
    #     self._spectrumViewIndex = views
    #     return tuple(x.spectrum for x in views)

    def orderedSpectrumViews(self, spectrumList, includeDeleted=True) -> Optional[Tuple]:
        """
        The spectrumViews attached to the strip (ordered)
        :return tuple of SpectrumViews:
        """
        if not self._spectrumViewIndex:

            index = self._retrieveOrderedSpectrumViewIndex()
            if index is None:
                index = tuple(ii for ii in range(len(spectrumList)))

            self._spectrumViewIndex = index
            self._storeOrderedSpectrumViewIndex(index)

        # return the reordered spectrumList
        return tuple(spectrumList[index] for index in self._spectrumViewIndex if index < len(spectrumList))
                     # if not spectrumList[index].isDeleted or includeDeleted)

    def getOrderedSpectrumViewsIndex(self) -> Optional[Tuple]:
        """
        The current indexing list
        :return tuple of ints:
        """
        if not self._spectrumViewIndex:

            index = self._retrieveOrderedSpectrumViewIndex()
            if index is None:
                index = tuple(ii for ii in range(len(self._parent.spectrumViews)))

            self._spectrumViewIndex = index
            self._storeOrderedSpectrumViewIndex(index)

        # return the index list
        return self._spectrumViewIndex

    def _setOrderedSpectrumViews(self, spectrumIndex: Tuple):
        self._spectrumViewIndex = tuple(spectrumIndex)
        self._storeOrderedSpectrumViewIndex(spectrumIndex)

    def _undoOrderedSpectrumViews(self, spectrumIndex: Tuple):
        self._spectrumViewIndex = tuple(spectrumIndex)
        self._storeOrderedSpectrumViewIndex(spectrumIndex)

    def setOrderedSpectrumViewsIndex(self, spectrumIndex: Tuple[int]):
        """
        Set the ordering of the spectrumViews attached to the strip/spectrumDisplay
        :param spectrumIndex - tuple of ints:
        """
        # self._parent._startCommandEchoBlock("project.getByPid('%s').setOrderedSpectrumViewIndex(spectrumIndex=%s)" % \
        #                                          (self._parent.pid, spectrumIndex))
        self._parent._startCommandEchoBlock('setOrderedSpectrumViewIndex', spectrumIndex)

        _undo = self.project._undo
        if _undo is not None:
            _undo.increaseBlocking()
        try:
            _oldSpectrumViews = self._spectrumViewIndex
            self._setOrderedSpectrumViews(spectrumIndex=spectrumIndex)

        finally:
            self._parent._endCommandEchoBlock()
        if _undo is not None:
            _undo.decreaseBlocking()

            _undo.newItem(self._undoOrderedSpectrumViews, self._setOrderedSpectrumViews
                          , undoArgs=(_oldSpectrumViews,), redoArgs=(spectrumIndex,))

        # notify that the order has been changed - parent is SpectrumDisplay
        # self._parent._finaliseAction(action='change')

    # def appendSpectrumView(self, spectrumView):
    #     """
    #     Append a SpectrumView to the end of the ordered spectrumviews
    #     :param spectrumView - new spectrumView:
    #     """
    #     if self._spectrumViewIndex:
    #         spectra = (self._spectrumViewIndex, (spectrumView,))
    #         spectra = tuple(j for i in spectra for j in i)
    #     else:
    #         spectra = tuple(spectrumView, )
    #
    #     self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))
    #
    #     values = tuple(x for x in spectra)
    #     self._spectrumViewIndex = values
    #
    # def removeSpectrumView(self, spectrumView):
    #     """
    #     Remove a SpectrumView from the ordered spectrumViews
    #     :param spectrumView - spectrumView:
    #     """
    #     if self._spectrumViewIndex:
    #         spectra = self._spectrumViewIndex
    #     else:
    #         spectra = tuple(spectrumView, )
    #
    #     self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))
    #
    #     values = tuple(x for x in spectra)
    #     self._spectrumViewIndex = values
    #
    # def copyOrderedSpectrumViews(self, fromStrip):
    #     if fromStrip._spectrumViewIndex:
    #         fromSpectraV = fromStrip.orderedSpectrumViews()
    #
    #         newSpectra = []
    #         for fromSP in fromSpectraV:
    #             for selfSPV in self.spectrumViews:
    #
    #                 # fromSP could be a 'deleted' structure, so no 'spectrum' attribute
    #                 if hasattr(fromSP, 'spectrum'):
    #                     if fromSP.spectrum == selfSPV.spectrum:
    #                         newSpectra.append(selfSPV)
    #
    #         self._storeOrderedSpectrumViewPids(tuple(x.pid for x in newSpectra))
    #
    #         values = tuple(x for x in newSpectra)
    #         self._spectrumViewIndex = values
