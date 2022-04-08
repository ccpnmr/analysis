"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2022-04-08 11:25:43 +0100 (Fri, April 08, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-07 15:46:23 +0100 (Thu, April 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial


class UpdateQueue:
    PRIORITY_RUN = 'RUN'
    PRIORITY_WAIT = 'WAIT'
    PRIORITIES = (PRIORITY_RUN, PRIORITY_WAIT)

    def __init__(self):
        self._queue = {UpdateQueue.PRIORITY_RUN : [],
                       UpdateQueue.PRIORITY_WAIT: []}  # ordered sets?

    def put(self, newItem, priority=PRIORITY_WAIT):
        """Add a new task to the specified queue
        """
        self._checkPriority(priority)

        queue = self._queue[priority]
        if isinstance(newItem, partial):
            # for speed this could be an ordered dict of (func,args,keywords) keying the partial?
            # each partial is a new object... compare with the last item in the queue
            # note partials don't nest after 3.5 [python issue 3780]
            if queue and (queuedItem := queue[-1]):
                if newItem.func == queuedItem.func and newItem.args == queuedItem.args and newItem.keywords == queuedItem.keywords:
                    return

        else:
            if queue and (queuedItem := queue[-1]) and queuedItem == newItem:
                return

        # append the new task
        self._queue[priority].append(newItem)

    def get(self):
        """Get the next task from the queues in priority order
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.get not implemented')

    def hasItems(self):
        """Return True of there are still items in the queues
        """
        for priority in self.PRIORITIES:
            if len(self._queue[priority]) != 0:
                return True

        return False

    def items(self):
        """Return a generator of the items in the queues
        """
        for priority in self.PRIORITIES:
            for itm in self._queue[priority]:
                yield itm

    def clearItems(self):
        """Clear the queues
        """
        self._queue = {UpdateQueue.PRIORITY_RUN : [],
                       UpdateQueue.PRIORITY_WAIT: []}  # ordered sets?

    def __len__(self):
        """Return the number of items in the queues
        """
        return sum(len(qq) for qq in self._queue.values())

    @property
    def empty(self):
        """Return True if there are no items
        """
        return len(self) == 0

    def _checkPriority(self, priority):
        if priority not in self.PRIORITIES:
            raise Exception(f'got priority {priority} expected one of {",".join(self.PRIORITIES)}')
