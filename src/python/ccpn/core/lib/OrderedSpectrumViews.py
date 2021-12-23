"""
  ejb - orderedSpectrumViews, orderedSpectra
  store the current orderedSpectrumViews in the internal data store _ccpnInternalData
  so it is hidden from external users

  accessed with the methods:
      strip.getSpectra()          returns tuple(spectra) or None
      strip.getSpectrumViews()    returns tuple(spectrumViews) or None

  use order = <tuple> to set the list
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-12-23 10:00:05 +0000 (Thu, December 23, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Tuple, Optional, List, Union
from functools import partial
from ccpn.core.lib.ContextManagers import undoStackBlocking, undoBlockWithoutSideBar


class OrderedItemsABC(object):
    """
    Class handler for ordering of a list of items

    If parent is specified, the ordering is stored in the _ccpnInternalData of parent,
    and will be persistent when saving a project.
    Otherwise it is stored internally.
    """
    _ORDER = '_ordering'

    def __init__(self, parent=None, undoEnabled=True):
        """
        Initialise the class
        parent defines the ccpn core object that will contain the persistent list
        If None then list is stored internally.

        undoEnabled is True/False.
        If True, an undo/redo operation will be added to the stack if the order changes

        :param parent: container for _ccpnInternalData storage
        :param undoEnabled: True/False
        """
        self._parent = parent
        self._internalOrder = None
        self._undoEnabled = undoEnabled

    def _retrieveOrder(self):
        """
        Retrieve the indexing from the _parent ccpnInternal database
        :return: tuple of ints
        """
        if self._parent:
            return self._parent._getInternalParameter(self._ORDER)
        else:
            return self._internalOrder

    def _storeOrder(self, order: Tuple[int]):
        """
        Store the indexing in the _parent ccpnInternal database
        """
        if self._parent:
            self._parent._setInternalParameter(self._ORDER, order)
        else:
            self._internalOrder = order

    def _clearOrder(self):
        """
        Clear the ordering
        """
        if self._parent:
            self._parent._setInternalParameter(self._ORDER, None)
        else:
            self._internalOrder = None

    def orderedItems(self, items: Union[List, Tuple], resize=False) -> Optional[Tuple]:
        """
        Return the tuple of items ordered by the stored indexing.
        resize is True/False. If True the stored ordering will shrink to the length of the list,
        otherwise the extra elements are kept so that order of longer lists is remembered.

        :param items: list/tuple of items
        :param resize: True/False
        :return: tuple of spectrumViews/spectra
        """
        _order = self._retrieveOrder()
        if _order is None:
            _order = tuple(ii for ii in range(len(items)))

        # if there are too many items then increase the length of the list, and store
        if len(_order) < len(items):
            _order += tuple(x for x in range(len(_order), len(items)))
        elif resize:
            # resize the order to the exact number of items
            _order = tuple(index for index in _order if index < len(items))

        self._storeOrder(_order)

        # return the reordered items
        return tuple(items[index] for index in _order if index < len(items))

    @property
    def order(self) -> Optional[Tuple]:
        """
        The current indexing list

        :return: tuple of ints
        """
        # return the index list
        return self._retrieveOrder()

    @order.setter
    def order(self, newOrder: Tuple[int]):
        """
        Set the ordering of the items.
        order can be None, tuple of integers.
        Duplicates are not allowed.
        Values must be between 0 and (n-1) in any order

        :param newOrder: tuple of integers, or None
        """
        # parameter checking
        if not isinstance(newOrder, (tuple, type(None))) or (newOrder and any(not isinstance(val, int) for val in newOrder)):
            raise ValueError('order is not tuple of integers, or None')
        if newOrder and ((len(set(newOrder)) != len(newOrder)) or (len(newOrder) != max(newOrder) + 1)):
            raise ValueError('order contains bad/missing elements')

        if self._undoEnabled:
            try:
                # should the undo block be in _storeOrder?
                with undoBlockWithoutSideBar():
                    with undoStackBlocking() as addUndoItem:
                        _oldOrder = self._retrieveOrder()
                        self._storeOrder(newOrder)

                        # set undo/redo operation
                        addUndoItem(undo=partial(self._storeOrder, _oldOrder),
                                    redo=partial(self._storeOrder, newOrder))
            except Exception as es:
                raise RuntimeError(f'Error setting order: {es}')

        else:
            self._storeOrder(newOrder)


class OrderedSpectrumViews(OrderedItemsABC):
    """
    Class handler for ordering of a list of spcetra/spectrumViews

    See OrderedItemsABC for more details
    """
    _ORDER = '_spectrumViewIndex'

    def orderedItems(self, items: Union[List, Tuple], resize=False) -> Optional[Tuple]:
        """
        The spectrumViews/spectra attached to the strip, ordered by the stored indexing
        items is the list of items to be ordered, originally designed for spectra/spectrumViews, but
        any list/tuple can be used.

        resize is True/False. If True the stored ordering will shrink to the length of the list,
        otherwise the extra elements are kept so that order of longer lists is remembered.

        :param items: list/tuple of items
        :param resize: True/False
        :return: tuple of spectrumViews/spectra
        """
        return super().orderedItems(items, resize=resize)


def mainTest():
    """
    A few quick tests for the ordering
    """
    from tabulate import tabulate
    from ccpn.ui.gui.widgets.Application import newTestApplication
    from ccpn.framework.Application import getApplication
    from unittest import TestCase

    newTestApplication()
    application = getApplication()
    project = application.project


    class testing(TestCase):
        def test_stuff(self):

            # create store to hold the ordering - in Project, undoEnabled=True
            _store = OrderedSpectrumViews(project)

            _store.order = None
            _store.order = ()

            # check errors are returned for anything other than None, or list of integers
            for val in ([],
                        12,
                        'help',
                        ('help',),
                        (1, 2, 3, 4.0),
                        (None,),
                        (-1)):
                with self.assertRaisesRegex(ValueError, 'order is not tuple of integers, or None'):
                    print(f'  assertRaisesRegex   ValueError   {val}')
                    _store.order = val

            for val in ((0, 1, 2, 3, 5),
                        (3, 4, 5),
                        (4, 3, 2),
                        (0, 1, 1),
                        (0, 1, -1),
                        (-1, 0, 1),
                        (-1,)):
                with self.assertRaisesRegex(ValueError, 'order contains bad/missing elements'):
                    print(f'  assertRaisesRegex   ValueError   {val}')
                    _store.order = val

            # write out a few examples
            ll = ['zero', 'one', 'two', 'three']
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            _store.order = (3, 1, 0, 2)
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            ll = ['zero', 'one', 'two']
            items = _store.orderedItems(ll, resize=True)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            ll = ['zero', 'one', 'two', 'three', 'four']
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            ll = ['zero', 'one']
            items = _store.orderedItems(ll, resize=True)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            _store._clearOrder()
            ll = ['zero', 'one', 'two', 'three', 'four']
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            _store.order = (3, 1, 4, 0, 2)
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)

            ll = ['zero', 'one']
            items = _store.orderedItems(ll)
            msg = tabulate([ll, _store.order or [], items])
            print(msg)


    # make a simple testCase
    doTest = testing()
    doTest.test_stuff()


if __name__ == '__main__':
    mainTest()
