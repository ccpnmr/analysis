"""General undo handle supporting undo/redo stack
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial, update_wrapper
from collections import deque


# def deleteAll(objects):
#   """Delete each object in objects - utility for undoing multi-object creation functions"""
#   for obj in objects:
#     obj.delete()


def _deleteAllApiObjects(objsToBeDeleted):
    """Delete all API objects in collection, together.
    Does NOT look for additional deletes or do any checks. Programmer beware!!!
    Does NOT do undo handling, as it is designed to be used within the Undo machinery"""

    ##CCPNINTERNAL

    # NBNB USee with EXTREME CARE, and make sure you get ALL API objects being created

    for obj in objsToBeDeleted:
        if (obj.__dict__.get('isDeleted')):
            raise ValueError("""%s: _deleteAllApiObjects
       called on deleted object""" % obj.qualifiedName
                             )

    for obj in objsToBeDeleted:
        for notify in obj.__class__._notifies.get('preDelete', ()):
            notify(obj)

    for obj in objsToBeDeleted:
        obj._singleDelete(objsToBeDeleted)

    # doNotifies
    for obj in objsToBeDeleted:
        for notify in obj.__class__._notifies.get('delete', ()):
            notify(obj)


def restoreOriginalLinks(obj2Value, linkName):
    """Set obj values using obj2Value dictionary"""
    for obj, val in obj2Value.items():
        setattr(obj, linkName, val)


def no_op():
    """Does nothing - for special undo situations where only one direction must act"""
    return


def resetUndo(memopsRoot, maxWaypoints=20, maxOperations=10000,
              debug: bool = False, application=None):
    """Set or reset undo stack, using passed-in parameters.
    NB setting either parameter to 0 removes the undo stack."""

    undo = memopsRoot._undo
    if undo is not None:
        undo.clear()

    if maxWaypoints and maxOperations:
        memopsRoot._undo = Undo(maxWaypoints=maxWaypoints, maxOperations=maxOperations,
                                debug=debug, application=application)
    else:
        memopsRoot._undo = None


class Undo(deque):
    """Implementation of an undo and redo stack, with possibility of waypoints.
       A waypoint is the level at which an undo happens, and each of them could
       consist of multiple individual undo operations.

       To create a waypoint use newWaypoint().
    """

    # TODO: get rid of debug and use logging function instead
    def __init__(self, maxWaypoints=20, maxOperations=10000, debug=False, application=None):
        """Create Undo object with maximum stack length maxUndoCount"""

        self.maxWaypoints = maxWaypoints
        self.maxOperations = maxOperations
        self.nextIndex = 0  # points to next free slot (or first slot to redo)
        self.waypoints = []  # array of last item in each waypoint
        self._blocked = False  # Block/unblock switch - internal use only
        self._blockingLevel = 0  # Blocking level - modify with increase/decreaseBlocking only
        self._waypointBlockingLevel = 0  # Waypoint blocking - modify with increase/decreaseWaypointBlocking/ only
        if maxWaypoints:
            self.newWaypoint()  # DO NOT CHANGE THIS ONE
        deque.__init__(self)

        # Reset to True to unblank errors during undo/redo
        self._debug = debug
        self.application = application

    @property
    def blocking(self):
        """Undo blocking. If true (non-zero) undo setting is blocked.
        Allows multiple external functions to set blocking without trampling each other

        Modify with increaseBlocking/decreaseBlocking only"""
        return self._blockingLevel > 0

    def increaseBlocking(self):
        """Set one more level of blocking"""
        self._blockingLevel += 1

    def decreaseBlocking(self):
        """Reduce level of blocking - when level reaches zero, undo is unblocked"""
        if self._blockingLevel > 0:
            self._blockingLevel -= 1

    @property
    def undoList(self):
        try:
            undoState = (self.maxWaypoints,
                         self.maxOperations,
                         self.nextIndex,
                         self.waypoints,
                         self._blocked,
                         self.blocking,
                         len(self),
                         self[-1],
                         [(undoFunc[0].__name__, undoFunc[1].__name__) for undoFunc in self],
                         [undoFunc[0].__name__ for undoFunc in self],
                         [undoFunc[1].__name__ for undoFunc in self])
        except:
            undoState = (self.maxWaypoints,
                         self.maxOperations,
                         self.nextIndex,
                         self.waypoints,
                         self._blocked,
                         self.blocking,
                         len(self),
                         None, None, None, None)
        return undoState

    @property
    def waypointBlocking(self):
        """Undo blocking. If true (non-zero) undo setting is blocked.
        Allows multiple external functions to set blocking without trampling each other

        Modify with increaseBlocking/decreaseBlocking only"""
        return self._waypointBlockingLevel > 0

    def increaseWaypointBlocking(self):
        """Set one more level of blocking"""
        self._waypointBlockingLevel += 1

    def decreaseWaypointBlocking(self):
        """Reduce level of blocking - when level reaches zero, undo is unblocked"""
        if self.waypointBlocking:
            self._waypointBlockingLevel -= 1

    def newWaypoint(self):
        """Start new waypoint"""
        if self.maxWaypoints < 1:
            raise ValueError("Attempt to set waypoint on Undo object that does not allow them ")

        waypoints = self.waypoints

        if self.nextIndex < 1:
            return

        elif self._blocked or self._blockingLevel > 0 or self.waypointBlocking:  # ejb - added self._blocked 9/6/17
            return

        elif waypoints and waypoints[-1] == self.nextIndex - 1:  # don't need to add a new waypoint
            return  # if is the same as the last one

        waypoints.append(self.nextIndex - 1)  # add the new waypoint to the end

        # if the list is too big then cull the first item

        if len(waypoints) > self.maxWaypoints:
            nRemove = waypoints[0]
            self.nextIndex -= nRemove
            for ii in range(nRemove):
                self.popleft()
            del waypoints[0]
            for ii, junk in enumerate(waypoints):
                waypoints[ii] -= nRemove

            # need to remove waypoints from the left that are negative
            # while waypoints and waypoints[0]<0:
            #   del waypoints[0]

        # waypoints.append(self.nextIndex-1)

    def _wrappedPartial(self, func, *args, **kwargs):
        partial_func = partial(func, *args, **kwargs)
        update_wrapper(partial_func, func)
        return partial_func

    def _newItem(self, undoPartial=None, redoPartial=None):
        """Add predefined partial(*) item to the undo stack.
        """
        if self._blocked or self._blockingLevel:
            return

        if self._debug:
            # print('undo.newItem', self.blocking, undoMethod, redoMethod, undoArgs, undoKwargs, redoArgs,
            #       redoKwargs)
            from sandbox.Geerten.Refactored.logger import getLogger

            getLogger().debug('undo._newItem %s %s %s' % (self.blocking, undoPartial,
                                                          redoPartial))

        # clear out redos that are no longer going to be doable
        for n in range(len(self) - self.nextIndex):
            self.pop()

        # add new undo/redo methods
        self.append((undoPartial, redoPartial))

        # fix waypoints:
        ll = self.waypoints
        while ll and ll[-1] >= self.nextIndex:
            ll.pop()

        # correct for maxOperations
        if len(self) > self.maxOperations:
            self.popleft()
            ll = self.waypoints
            if ll:
                for n, val in enumerate(ll):
                    ll[n] = val - 1
                if ll[0] < 0:
                    del ll[0]
        else:
            self.nextIndex += 1

    def newItem(self, undoMethod, redoMethod, undoArgs=None, undoKwargs=None,
                redoArgs=None, redoKwargs=None):
        """Add item to the undo stack.
        """
        if self._blocked or self._blockingLevel:
            return

        if self._debug:
            # print('undo.newItem', self.blocking, undoMethod, redoMethod, undoArgs, undoKwargs, redoArgs,
            #       redoKwargs)
            from ccpn.util.Logging import getLogger

            getLogger().debug('undo.newItem %s %s %s %s %s %s %s' % (self.blocking, undoMethod,
                                                                     redoMethod, undoArgs,
                                                                     undoKwargs, redoArgs,
                                                                     redoKwargs))

        if not undoArgs:
            undoArgs = ()
        if not redoArgs:
            redoArgs = ()

        # clear out redos that are no longer going to be doable
        for n in range(len(self) - self.nextIndex):
            self.pop()

        # add new data
        if undoKwargs is None:
            undoCall = self._wrappedPartial(undoMethod, *undoArgs)
        else:
            undoCall = self._wrappedPartial(undoMethod, *undoArgs, **undoKwargs)
        if redoKwargs is None:
            redoCall = self._wrappedPartial(redoMethod, *redoArgs)
        else:
            redoCall = self._wrappedPartial(redoMethod, *redoArgs, **redoKwargs)
        self.append((undoCall, redoCall))

        # fix waypoints:
        ll = self.waypoints
        while ll and ll[-1] >= self.nextIndex:
            ll.pop()

        # correct for maxOperations
        if len(self) > self.maxOperations:
            self.popleft()
            ll = self.waypoints
            if ll:
                for n, val in enumerate(ll):
                    ll[n] = val - 1
                if ll[0] < 0:
                    del ll[0]
        else:
            self.nextIndex += 1

    # def newItem(self, undoMethod, undoData, redoMethod, redoData=None):
    #   """Add item to the undo stack.
    #      Note that might not know redoData until after we do undo.
    #      NBNB NO, we should know, so resetting facility disabled. Rasmus
    #   """
    #
    #   if self._blocked:
    #     return
    #
    #   # clear out redos that are no longer going to be doable
    #   for n in range(len(self)-self.nextIndex):
    #     self.pop()
    #
    #   # add new data
    #   self.append((undoMethod, undoData, redoMethod, redoData))
    #
    #   # fix waypoints:
    #   ll = self.waypoints
    #   while ll and ll[-1] >= self.nextIndex:
    #     ll.pop()
    #
    #   # correct for maxOperations
    #   if len(self) > self.maxOperations:
    #     self.popleft()
    #     ll = self.waypoints
    #     if ll:
    #       for n,val in enumerate(ll):
    #         ll[n] = val - 1
    #       if ll[0] < 0:
    #         del ll[0]
    #   else:
    #     self.nextIndex += 1

    def undo(self):
        """Undo one operation - or one waypoint if waypoints are set

        For now errors are handled by printing a warning and clearing the undo object"""

        # TBD: what should we do if undoMethod() throws an exception?

        # print('@~@~ Undo.undo', self.nextIndex, self.maxWaypoints, self.waypoints, self._debug)

        if self.nextIndex == 0:
            # print ('>>> NOTHING TO UNDO')
            return

        elif self.maxWaypoints:
            undoTo = -1
            for val in self.waypoints:
                if val < self.nextIndex - 1:
                    undoTo = val
                else:
                    break

        else:
            undoTo = max(self.nextIndex - 2, -1)

        # print('@~@~ undoTo', self.nextIndex-1, undoTo)
        # block addition of items while operating
        self._blocked = True
        from ccpn.core.lib.ContextManagers import undoBlock

        try:
            with undoBlock(self.application):
                undoCall = redoCall = None
                for n in range(self.nextIndex - 1, undoTo, -1):
                    undoCall, redoCall = self[n]
                    # if self._debug:
                    #   print ("undoing", undoCall)

                    if undoCall:
                        undoCall()
                self.nextIndex = undoTo + 1

        except Exception as e:
            from ccpn.util.Logging import getLogger

            getLogger().warning("Error while undoing (%s). Undo stack is cleared." % e)
            if self._debug:
                print("UNDO DEBUG: error in undo. Last undo function was:", undoCall)
                raise
            self.clear()
        finally:
            # Added by Rasmus March 2015. Surely we need to reset self._blocked?
            self._blocked = False

    def redo(self):
        """Redo one waypoint - or one operation if waypoints are not set.

        For now errors are handled by printing a warning and clearing the undo object"""

        # TODO: what should we do if redoMethod() throws an exception?

        if self.nextIndex >= len(self):
            # print ('>>> NOTHING TO REDO')
            return

        elif self.maxWaypoints:
            redoTo = len(self) - 1
            for val in reversed(self.waypoints):
                if val >= self.nextIndex:
                    redoTo = val
                else:
                    break

        else:
            redoTo = min(self.nextIndex, len(self))

        # block addition of items while operating
        self._blocked = True
        from ccpn.core.lib.ContextManagers import undoBlock

        try:
            with undoBlock(self.application):
                for n in range(self.nextIndex, redoTo + 1):
                    # undoMethod, undoData, redoMethod, redoData = self[n]
                    # if redoData is None:
                    #   redoMethod()
                    # else:, axis=1, inplace=True
                    #   redoMethod(redoData)
                    undoCall, redoCall = self[n]
                    # if self._debug:
                    #   print ("@~@~ redoing", redoCall)
                    if redoCall:
                        redoCall()
                self.nextIndex = redoTo + 1

        except Exception as e:
            from ccpn.util.Logging import getLogger

            getLogger().warning("Error while redoing (%s). Undo stack is cleared." % e)
            if self._debug:
                print("REDO DEBUG: error in redo. Last redo call was:", redoCall)
                raise
            self.clear()
        finally:
            # Added by Rasmus March 2015. Surely we need to reset self._blocked?
            self._blocked = False

    def clear(self):
        """Clear and reset undo object """
        # if self._debug:
        #   print ('@~@~ CLEAR undo')
        self.nextIndex = 0
        self.waypoints.clear()
        self._blocked = False
        self._blockingLevel = 0
        deque.clear(self)

    def canUndo(self) -> bool:
        """True if an undo operation can be performed?"""
        return self.nextIndex > 0

    def canRedo(self) -> bool:
        """True if a redo operation can be performed"""
        return self.nextIndex < len(self)

    def numItems(self):
        return len(self)
