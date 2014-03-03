"""
======================COPYRIGHT/LICENSE START==========================

Undo.py: Utility code for CCPN code generation framework

Copyright (C) 2014  (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

A copy of this license can be found in ../../../license/LGPL.license

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================
"""

from collections import deque

class Undo(deque):
  """Implementation of an undo and redo stack, with possibility of waypoints.
     A waypoint is the level at which an undo happens, and each of them could
     consist of multiple individual undo operations.

     To create a waypoint use newWaypoint().  If you don't want to use waypoints
     then just don't use this method and then every item is in its own waypoint.
  """

  def __init__(self, maxWaypoints=20, maxOperations=10000):
    """Create Undo object with maximum stack length maxUndoCount"""

    self.maxWaypoints = maxWaypoints
    self.maxOperations = maxOperations
    self.nextIndex = 0   # points to next free slot (or first slot to redo)
    self.waypoints = []  # array of last item in each waypoint
    self.blocked = False
    deque.__init__(self)

  def newWaypoint(self):
    """Start new waypoint"""
    waypoints = self.waypoints
    waypoints.append(self.nextIndex-1)

    if len(waypoints) > self.maxWaypoints:
      del self[:waypoints[0]+1]
      del waypoints[0]

  def addItem(self, undoMethod, undoData, redoMethod, redoData=None):
    """Add item to the undo stack.
       Note that might not know redoData until after we do undo.
       NBNB NO, we should know, so resetting facility disabled. Rasmus
    """

    if self.blocked:
      return

    # clear out redos that are no longer going to be doable
    for n in range(len(self)-self.nextIndex):
      self.pop()

    # add new data
    self.append((undoMethod, undoData, redoMethod, redoData))

    # fix waypoints:
    ll = self.waypoints
    while ll and ll[-1] >= self.nextIndex:
      ll.pop()

    # correct for maxOperations
    if len(self) > self.maxOperations:
      self.popleft()
      ll = self.waypoints
      if ll:
        for n,val in enumerate(ll):
          ll[n] = val - 1
        if ll[0] < 0:
          del ll[0]
    else:
      self.nextIndex += 1


  def undo(self):
    """Undo one operation - or one waypoinit if waypoints are not set

    For now errors are handled by printing a warning and clearing the undo object"""

    # TBD: what should we do if undoMethod() throws an exception?

    if self.nextIndex == 0:
      return

    elif self.maxWaypoints:
      undoTo = -1
      for val in self.waypoints:
        if val < self.nextIndex:
          undoTo = val
        else:
          break
    else:
      undoTo = max(self.nextIndex - 2, -1)

    # block addition of items while operating
    self.blocked = True
    try:
      for n in range(self.nextIndex-1,undoTo,-1):
        undoMethod, undoData, redoMethod, redoData = self[n]
        if undoData is None:
          undoMethod()
        else:
          undoMethod(undoData)
      self.nextIndex = undoTo + 1
      self.blocked = False
    except:
      print ("WARNING, error while undoing. Undo is cleared")
      self.clear()

  def redo(self):
    """Redo one waypoint - or one operation if waypoints are not set.

    For now errors are handled by printing a warning and clearing the undo object"""

    # TBD: what should we do if redoMethod() throws an exception?

    if self.nextIndex > len(self):
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
    self.blocked = True
    try:
      for n in range(self.nextIndex,redoTo+1):
        undoMethod, undoData, redoMethod, redoData = self[n]
        if redoData is None:
          redoMethod()
        else:
          redoMethod(redoData)
      self.nextIndex = redoTo + 1
    except:
      print ("WARNING, error while redoing. Undo is cleared")
      self.clear()

  def clear(self):
    """Clear and reset undo object """
    self.nextIndex = 0
    self.waypoints.clear()
    self.blocked = False
    deque.clear(self)

  def canUndo(self) -> bool:
    """Can an undo operation be performed?"""
    return self.nextIndex > 0

  def canRedo(self) -> bool:
    """can a redo operation be performed"""
    return self.nextIndex <= len(self)
