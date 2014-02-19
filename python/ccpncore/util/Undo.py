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

  def __init__(self, maxUndoCount=20):
    """Create Undo object with maximum stack length maxUndoCount"""

    self.maxUndoCount = maxUndoCount
    self.haveWaypoint = False
    self.currentIndex = -1
    deque.__init__(self)

  def newWaypoint(self):
    # get rid of oldest waypoint if there are too many
    if self.currentIndex == self.maxUndoCount - 1:
      self.popleft()
      self.currentIndex -= 1

    # clear out redos that are no longer going to be doable
    for n in range(len(self)-self.currentIndex-1):
      self.pop()

    # create new waypoint
    self.append([])
    self.haveWaypoint = True
    self.currentIndex += 1

  def addItem(self, undoMethod, undoData, redoMethod, redoData=None):
    """Add item to the undo stack.
       Note that might not know redoData until after we do undo.
    """
    haveWaypoint = self.haveWaypoint
    if not haveWaypoint:
      self.newWaypoint()

    waypoint = self[-1]
    waypoint.append((undoMethod, undoData, redoMethod, redoData))

    if not haveWaypoint:
      self.haveWaypoint = False

  def undo(self):
    """Undo one waypoint"""

    # TBD: what should we do if undoMethod() throws an exception?

    self.haveWaypoint = False
    if self.currentIndex < 0:
      return # should this instead be an Exception?

    waypoint  = self[self.currentIndex]
    for n, (undoMethod, undoData, redoMethod, redoData) in enumerate(reversed(waypoint)):
      if undoData is None:
        redoData = undoMethod()
      else:
        redoData = undoMethod(undoData)
      if redoData:
        waypoint[n] = (undoMethod, undoData, redoMethod, redoData)

    self.currentIndex -= 1

  def redo(self):
    """Redo one waypoint."""

    # TBD: what should we do if redoMethod() throws an exception?

    self.haveWaypoint = False

    if self.currentIndex >= len(self)-1:
      return # should this instead be an Exception?

    self.currentIndex += 1

    waypoint  = self[self.currentIndex]
    for undoMethod, undoData, redoMethod, redoData in waypoint:
      if redoData is None:
        redoMethod()
      else:
        redoMethod(redoData)
