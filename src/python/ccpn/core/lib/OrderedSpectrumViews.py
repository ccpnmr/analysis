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

from typing import Tuple, Optional

ORDEREDSPECTRUMVIEWS = '_orderedSpectrumViews'


class OrderedSpectrumViews(object):
    _orderedSpectrumViews = None

    def __init__(self, parent=None):
        self.parent = parent
        self.project = parent.project
        self.spectrumViews = parent.spectrumViews

    def _retrieveOrderedSpectrumViewPids(self):
        if isinstance(self.parent._ccpnInternalData, dict) and ORDEREDSPECTRUMVIEWS in self.parent._ccpnInternalData:
            return self.parent._ccpnInternalData[ORDEREDSPECTRUMVIEWS]
        else:
            return None

    def _storeOrderedSpectrumViewPids(self, spectrumViewPids):
        if isinstance(self.parent._ccpnInternalData, dict):
            # _wrappedData._ccpnInternalData won't flag for saving unless the dict changes
            tempCcpn = self.parent._ccpnInternalData.copy()
            tempCcpn[ORDEREDSPECTRUMVIEWS] = spectrumViewPids
            self.parent._ccpnInternalData = tempCcpn

    def orderedSpectra(self) -> Optional[Tuple]:
        """
        The spectra attached to the strip (ordered)
        :return tuple of spectra:
        """
        if self._orderedSpectrumViews:
            return tuple(x.spectrum for x in self._orderedSpectrumViews if not x.isDeleted)
        else:
            # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
            # store by pids

            pids = self._retrieveOrderedSpectrumViewPids()
            if pids is None:
                self._storeOrderedSpectrumViewPids(tuple(x.pid for x in self.spectrumViews))
                views = tuple(x for x in self.spectrumViews)
            else:
                views = tuple(self.project.getByPid(x) for x in pids if self.project.getByPid(x))

                # this should be the first read from loading the project, so write back without bad pids
                self._storeOrderedSpectrumViewPids(tuple(x.pid for x in views))

        self._orderedSpectrumViews = views
        return tuple(x.spectrum for x in views)

    def orderedSpectrumViews(self, includeDeleted=True) -> Optional[Tuple]:
        """
        The spectrumViews attached to the strip (ordered)
        :return tuple of SpectrumViews:
        """
        if self._orderedSpectrumViews:
            views = self._orderedSpectrumViews
            return tuple(value for value in views if not value.isDeleted or includeDeleted)
        else:
            # create a dataset with the spectrumViews attached (will be alphabetical) if doesn't exist
            # store by pid

            pids = self._retrieveOrderedSpectrumViewPids()
            if pids is None:
                self._storeOrderedSpectrumViewPids(tuple(x.pid for x in self.spectrumViews))
                views = tuple(x for x in self.spectrumViews)
            else:
                views = tuple(self.project.getByPid(x) for x in pids if self.project.getByPid(x))

                # this should be the first read from loading the project, so write back without bad pids
                self._storeOrderedSpectrumViewPids(tuple(x.pid for x in views))

        self._orderedSpectrumViews = views
        return views

    def _setOrderedSpectrumViews(self, spectrumViews: Tuple):
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectrumViews))

        spectrumViews = list(spectrumViews)
        for ii, spec in enumerate(self._orderedSpectrumViews):
            if spec.isDeleted:
                spectrumViews.insert(ii, spec)

        self._orderedSpectrumViews = tuple(spectrumViews)

    def _undoOrderedSpectrumViews(self, spectrumViews: Tuple):
        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectrumViews))

        spectrumViews = list(spectrumViews)
        for ii, spec in enumerate(self._orderedSpectrumViews):
            if spec.isDeleted:
                spectrumViews.insert(ii, spec)

        self._orderedSpectrumViews = tuple(spectrumViews)

    def setOrderedSpectrumViews(self, spectrumViews: Tuple):
        """
        Set the ordering of the spectrumViews attached to the strip/spectrumDisplay
        :param spectrumViews - tuple of spectrumView:
        """
        pidStr = ','.join(["project.getByPid('%s')" % sp.pid for sp in spectrumViews])
        self.project._appBase._startCommandBlock("project.getByPid('%s').setOrderedSpectrumViews(spectrumViews=(%s))" % \
                                                 (self.parent.pid, pidStr))
        _undo = self.project._undo
        if _undo is not None:
            _undo.increaseBlocking()

        try:
            _oldSpectrumViews = self.orderedSpectrumViews()
            self._setOrderedSpectrumViews(tuple(spectrumViews))

        finally:
            self.project._appBase._endCommandBlock()

        if _undo is not None:
            _undo.decreaseBlocking()

            _undo.newItem(self._undoOrderedSpectrumViews, self._setOrderedSpectrumViews
                          , undoArgs=(_oldSpectrumViews,), redoArgs=(spectrumViews,))

        # notify that the order has been changed
        self.parent.spectrumDisplay._finaliseAction(action='change')

    def appendSpectrumView(self, spectrumView):
        """
        Append a SpectrumView to the end of the ordered spectrumviews
        :param spectrumView - new spectrumView:
        """
        if self._orderedSpectrumViews:
            spectra = (self._orderedSpectrumViews, (spectrumView,))
            spectra = tuple(j for i in spectra for j in i)
        else:
            spectra = tuple(spectrumView, )

        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))

        values = tuple(x for x in spectra)
        self._orderedSpectrumViews = values

    def removeSpectrumView(self, spectrumView):
        """
        Remove a SpectrumView from the ordered spectrumViews
        :param spectrumView - spectrumView:
        """
        if self._orderedSpectrumViews:
            spectra = self._orderedSpectrumViews
        else:
            spectra = tuple(spectrumView, )

        self._storeOrderedSpectrumViewPids(tuple(x.pid for x in spectra))

        values = tuple(x for x in spectra)
        self._orderedSpectrumViews = values

    def copyOrderedSpectrumViews(self, fromStrip):
        if fromStrip._orderedSpectrumViews:
            fromSpectraV = fromStrip.orderedSpectrumViews()

            newSpectra = []
            for fromSP in fromSpectraV:
                for selfSPV in self.spectrumViews:

                    # fromSP could be a 'deleted' structure, so no 'spectrum' attribute
                    if hasattr(fromSP, 'spectrum'):
                        if fromSP.spectrum == selfSPV.spectrum:
                            newSpectra.append(selfSPV)

            self._storeOrderedSpectrumViewPids(tuple(x.pid for x in newSpectra))

            values = tuple(x for x in newSpectra)
            self._orderedSpectrumViews = values
