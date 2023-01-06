"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-01-06 13:28:38 +0000 (Fri, January 06, 2023) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-04-07 15:46:23 +0100 (Thu, April 07, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

class UpdateQueue:
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_NORMAL = 'NORMAL'
    PRIORITY_LOW = 'LOW'
    PRIORITIES = (PRIORITY_HIGH, PRIORITY_NORMAL, PRIORITY_LOW)

    def __init__(self):
        self._initQueue()

    def _initQueue(self):
        self._queue = {UpdateQueue.PRIORITY_HIGH  : [],
                       UpdateQueue.PRIORITY_NORMAL: [],
                       UpdateQueue.PRIORITY_LOW   : []
                       }

    def put(self, newItem, priority=PRIORITY_NORMAL):
        """Add a new task to the specified queue
        """
        self._checkPriority(priority)

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
        return any(len(self._queue[priority]) != 0 for priority in self.PRIORITIES)

    def items(self, reverse=False):
        """Return a generator of the items in the queues
        """
        if reverse:
            for priority in reversed(self.PRIORITIES):
                yield from reversed(self._queue[priority])
        else:
            for priority in self.PRIORITIES:
                yield from self._queue[priority]

    def clearItems(self):
        """Clear the queues
        """
        self._initQueue()

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
            raise ValueError(f'got priority {priority} expected one of {",".join(self.PRIORITIES)}')
