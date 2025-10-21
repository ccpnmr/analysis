"""
Module Documentation here
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-10-20 16:39:53 +0100 (Mon, October 20, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2025-10-10 10:23:20 +0100 (Fri, October 10, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Protocol, TYPE_CHECKING, TypeVar, TypeAlias, cast, Union
from typing_extensions import Self
import numpy as np

from ccpn.core.lib.SpectrumLib import QuantumType
from ccpn.core.lib.WeakRefLib import WeakRefDescriptor
from ccpn.ui.gui.lib.OpenGL import GL
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray, GLRENDERMODE_REBUILD
from ccpn.util.Constants import AxisMatch, MOUSEDICTCURSOR, MOUSEGLPARENT
from ccpn.ui.gui.lib.mouseEvents import PICK


if TYPE_CHECKING:
    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget
    from ccpn.ui.gui.modules.SpectrumDisplay import (SpectrumDisplay1d, SpectrumDisplayNd)
    from ccpn.ui.gui.lib.SpectrumView import (SpectrumView1d, SpectrumViewNd)

_CoreSpectrumDisplay = TypeVar("_CoreSpectrumDisplay", bound="SpectrumDisplay1d | SpectrumDisplayNd")
_CoreSpectrumView = TypeVar("_CoreSpectrumView", bound="SpectrumView1d | SpectrumViewNd")

# The `|` operator doesn't like quoted types here, so MUST use typing.Union (it may be python 3.10 issue)
_COORDS_TYPE: TypeAlias = dict[str | AxisMatch | int, Union[dict[str, list[float]], tuple, "CcpnGLWidget", None]]

#-----------------------------------------------------------------------------------------
# Tuning constants
CURSOR_BOX_SIZE_FACTOR = 8.0  # pick box side = deltaX/deltaY * factor
UNIT_MIN = 0.0  # normalized (ratio) space
UNIT_MAX = 1.0


class CursorProtocol(Protocol):
    """A protocol defining any class that handles cursor objects."""

    def attach(self, host: CcpnGLWidget) -> Self: ...

    def buildCursors(self) -> None: ...

    def initialise(self, context: CcpnGLWidget): ...

    disableCursorUpdate: bool
    crosshairVisible: bool
    doubleCrosshairVisible: bool

    # @property
    # def disableCursorUpdate(self) -> bool: ...
    # @disableCursorUpdate.setter
    # def disableCursorUpdate(self, value: bool): ...
    def drawCursors(self): ...

    def drawLastCursors(self): ...


def _getQuantumOrders(host: CcpnGLWidget) -> tuple[int, int, QuantumType]:
    """
    Return (x_order, y_order, match_type). Defaults to (1, 1, QuantumType.NONE).
    Uses host._firstVisible.spectrum.coherenceOrders and a CoherenceOrder enum.
    """
    from ccpn.core.lib.SpectrumLib import CoherenceOrder

    x_order: int = 1
    y_order: int = 1
    if (fv := host._firstVisible) and not fv.isDeleted:
        x_idx, y_idx = fv.dimensionIndices[:2]
        spec = fv.spectrum
        mTypes = [CoherenceOrder[co].value for co in spec.coherenceOrders]  # type: ignore
        if len(mTypes) > max(x_idx, y_idx):
            x_order = mTypes[x_idx]
            y_order = mTypes[y_idx]

    if x_order == 1 and y_order == 2:
        match_type = QuantumType.Y
    elif x_order == 2 and y_order == 1:
        match_type = QuantumType.X
    else:
        # This includes (1,1), (2,2), (3,1), etc.
        match_type = QuantumType.NONE

    return x_order, y_order, match_type


#=========================================================================================
# CursorRenderer - base renderer for Nd displays
#=========================================================================================

class CursorRenderer:
    """
    Composition class that builds cursor/double-cursor geometry and uploads it
    to the current GL draw list obtained from the host widget.

    -------------------------
    Host requirements (widget)
    -------------------------
    Attributes / fields:
      - _disableCursorUpdate: bool
      - _crosshairVisible: bool
      - _doubleCrosshairVisible: bool
      - _updateHTrace: bool
      - _updateVTrace: bool
      - _matchingIsotopeCodes: bool
      - _orderedAxes: list-like of two objects each with .code
      - spectrumDisplay.isotopeCodes: list[str]
      - spectrumDisplay.phasingFrame.isVisible(): bool
      - current.mouseMovedDict: dict or None
      - deltaX: float
      - deltaY: float
      - mousePickColour: sequence[float]  (r,g,b,a)
      - foreground: sequence[float]       (r,g,b,a)
      - mouseCoordDQ: tuple|None (will be set)
      - _glCursorQueue, _glCursorHead (draw list queue as you already use)
        drawList has: .vertices, .indices, .numVertices, .colors, .defineIndexVBO()

    Methods (host):
      - _advanceGLCursor() -> None
      - _scaleAxisToRatio(values: list[float | None]) -> list[float]
      - getCurrentCursorCoordinate(localPos: Optional[QPointF] = None) -> list[float]
      - underMouse() -> bool
      - etc.

    There are also host attributes that MUST be moved here for correct ownership.

    Optional methods (if present, used; otherwise safe defaults are applied):
      - isPickMode() -> bool
      - isPhasingVisible() -> bool
      - _getActiveCursorDrawList() -> Any              # if queue differs
      - getCurrentMouseMode() -> int                   # alternative to isPickMode

    Optional attributes (for quantum cursors):
      - _firstVisible with: .isDeleted, .dimensionIndices, .spectrum.coherenceOrders
      - CoherenceOrder enum accessible in host module scope
    """

    host: WeakRefDescriptor[CcpnGLWidget] = WeakRefDescriptor()
    disableCursorUpdate = False
    crosshairVisible = True
    doubleCrosshairVisible = False
    _numBuffers = 2

    def __init__(self, host: CcpnGLWidget | None = None,
                 *, box_size_factor: float = CURSOR_BOX_SIZE_FACTOR):
        self.host = host
        self.box_size_factor = float(box_size_factor)

    #-----------------------------------------------------------------------------------------
    # Lifetime/binding

    def attach(self, host: CcpnGLWidget) -> Self:
        """Bind this renderer to a host widget and return self (for chaining)."""
        self.host = host
        return self

    #-----------------------------------------------------------------------------------------
    # Public entry point

    def buildCursors(self) -> None:
        """Build and upload cursor geometry for the current frame."""
        host = self._requireHost
        if self.disableCursorUpdate or not self.crosshairVisible:
            return

        # Advance cursor draw-list and get active buffer
        self._advanceGLCursor()
        drawList = self._glCursorQueue[self._glCursorHead]
        # Reset per-frame quantum info
        host.mouseCoordDQ = None  # nasty - should be in here
        vertices: list[float] = []
        indices: list[int] = []
        color = host.foreground
        coords_dict: _COORDS_TYPE = host.current.mouseMovedDict

        if (coords_dict and (newCoords := cast(tuple[float | None, float | None],
                                               coords_dict.get(MOUSEDICTCURSOR))) and
                None not in newCoords):
            # 1) PICK mode → small selection box - could have different shapes
            if self._isPickMode() and host.underMouse():
                self._addPickBox(host, vertices, indices,
                                 host._scaleAxisToRatio(newCoords),
                                 size_factor=self.box_size_factor)
                color = host.mousePickColour

            # 2) Crosshair / quantum cursors (skip if phasing)
            if (not host.spectrumDisplay.phasingFrame.isVisible()):
                # Resolve which lists to draw + axis types
                xPosList, yPosList, xQuantumOrder, yQuantumOrder = self._resolveAxisLists(host, coords_dict)
                # Build simple vertical/horizontal lines
                foundX: list[float] = []
                foundY: list[float] = []
                self._makeCursor(host, foundX, foundY, indices, newCoords, vertices, xPosList, yPosList)
                # Double-quantum lines when applicable
                self._makeQuantumCursor(host, foundX, foundY, indices, vertices,
                                        xPosList, xQuantumOrder, yPosList, yQuantumOrder)

        # 3) Upload to GL
        drawList.vertices = np.array(vertices, dtype=np.float32)
        drawList.indices = np.array(indices, dtype=np.int32)
        drawList.numVertices = len(vertices) // 2
        drawList.colors = np.array(color * drawList.numVertices, dtype=np.float32)
        drawList.defineIndexVBO()

    #-----------------------------------------------------------------------------------------
    # Geometry builders

    def _makeCursor(self,
                    host: CcpnGLWidget,
                    foundX: list[float],
                    foundY: list[float],
                    indices: list[int],
                    newCoords: tuple[float | None, float | None],
                    vertices: list[float],
                    xPosList: list[float],
                    yPosList: list[float]) -> None:
        """
        Generate single crosshair lines along X and Y.
        - foundX, foundY store normalized positions so we don't overdraw overlapping lines
        - newCoords is [rx, ry] in normalized space (can contain None)
        """
        # Vertical lines (constant X)
        if not host._updateVTrace and newCoords[0] is not None:
            for pos in xPosList:
                x, _ = host._scaleAxisToRatio([pos, 0])
                if all(abs(x - val) > host.deltaX for val in foundX):
                    foundX.append(x)
                    self._appendLine(vertices, indices, x, UNIT_MAX, x, UNIT_MIN)

        # Horizontal lines (constant Y)
        if not host._updateHTrace and newCoords[1] is not None:
            for pos in yPosList:
                _, y = host._scaleAxisToRatio([0, pos])
                if all(abs(y - val) > host.deltaY for val in foundY):
                    foundY.append(y)
                    self._appendLine(vertices, indices, UNIT_MIN, y, UNIT_MAX, y)

    def _makeQuantumCursor(self,
                           host: CcpnGLWidget,
                           foundX: list[float],
                           foundY: list[float],
                           indices: list[int],
                           vertices: list[float],
                           xPosList: list[float],
                           xQuantumOrder: int,
                           yPosList: list[float],
                           yQuantumOrder: int) -> None:
        """Generate double-quantum/zero-quantum auxiliary lines when conditions allow."""
        if not (host._matchingIsotopeCodes and
                host._firstVisible):
            return

        # Case 1: single double quantum on Y (x < y)
        if 0 < xQuantumOrder < yQuantumOrder < 3:
            if len(xPosList) == 1 and len(yPosList) == 1:
                xPosList.append(yPosList[0])
            if len(xPosList) == 2:
                xx = xPosList[1] - xPosList[0]  # (y - x)
                host.mouseCoordDQ = (xx, yPosList[0] if yPosList else None, 0)
                x_norm, _ = host._scaleAxisToRatio([xx, 0])
                if all(abs(x_norm - val) > host.deltaX for val in foundX):
                    foundX.append(x_norm)
                    self._appendLine(vertices, indices, x_norm, UNIT_MAX, x_norm, UNIT_MIN)

        # Case 2: single double quantum on X (y < x)
        elif 0 < yQuantumOrder < xQuantumOrder < 3:
            if len(xPosList) == 1 and len(yPosList) == 1:
                yPosList.insert(0, xPosList[0])
            if len(yPosList) == 2:
                yy = yPosList[0] - yPosList[1]  # (x - y) per your original order
                host.mouseCoordDQ = (xPosList[0] if xPosList else None, yy, 1)
                _, y_norm = host._scaleAxisToRatio([0, yy])
                if all(abs(y_norm - val) > host.deltaY for val in foundY):
                    foundY.append(y_norm)
                    self._appendLine(vertices, indices, UNIT_MIN, y_norm, UNIT_MAX, y_norm)

    #-----------------------------------------------------------------------------------------
    # Domain helpers

    def initialise(self, context: CcpnGLWidget):
        """Initialise the GL lists, hard-coded to 2 swapBuffers."""
        # Sanity check to ensure that host has been set before doing anything else
        _ = self._requireHost
        fmt = context.format()
        self._numBuffers = int(fmt.swapBehavior()) or 2
        self._glCursorQueue: tuple[GLVertexArray, ...] = ()
        for buf in range(self._numBuffers):
            self._glCursorQueue += (GLVertexArray(numLists=1,
                                                  renderMode=GLRENDERMODE_REBUILD,
                                                  blendMode=False,
                                                  drawMode=GL.GL_LINES,
                                                  dimension=2,
                                                  GLContext=context),)
        self._clearGLCursorQueue()
        self._glCursor = GLVertexArray(numLists=1,
                                       renderMode=GLRENDERMODE_REBUILD,
                                       blendMode=False,
                                       drawMode=GL.GL_LINES,
                                       dimension=2,
                                       GLContext=context)

    def _clearGLCursorQueue(self):
        """Clear the cursor glLists."""
        if not self.disableCursorUpdate:
            for glBuf in self._glCursorQueue:
                glBuf.clearArrays()
            self._glCursorHead = 0
            self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers

    def _advanceGLCursor(self):
        """Advance the pointers for the cursor glLists."""
        if not self.disableCursorUpdate:
            self._glCursorHead = (self._glCursorHead + 1) % self._numBuffers
            self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers

    def drawLastCursors(self):
        """Draw the cursors/doubleCursors."""
        cursor = self._glCursorQueue[self._glCursorTail]
        if cursor.indices.size:
            cursor.drawIndexVBO()

    def drawCursors(self):
        """Draw the cursors/doubleCursors."""
        cursor = self._glCursorQueue[self._glCursorHead]
        if cursor.indices.size:
            cursor.drawIndexVBO()

    # @staticmethod
    # def _updateCoordsFromDict(host: CcpnGLWidget,
    #                           coords_dict: _COORDS_TYPE,
    #                           current: list[float | None]) -> list[float | None]:
    #     """Pull single x/y coordinates out of mouseMovedDict using ordered axis codes."""
    #
    #     newCoords = list(current) if current else [None, None]
    #     atCodes = host._orderedAxes
    #     if not atCodes:
    #         return newCoords
    #
    #     chrs = max(1, host._preferences.get("matchNumChars", 0))
    #     full_dict: dict[str, list[float]] = coords_dict.get(AxisMatch.CODE, {})
    #     x_code = atCodes[0].code[:chrs].lower()
    #     y_code = atCodes[1].code[:chrs].lower()
    #     x_list = full_dict.get(x_code, [])
    #     y_list = full_dict.get(y_code, [])
    #
    #     if x_list:
    #         newCoords[0] = x_list[0]
    #     if y_list:
    #         newCoords[1] = y_list[0]
    #     return newCoords

    def _resolveAxisLists(self, host: CcpnGLWidget, coords_dict: _COORDS_TYPE
                          ) -> tuple[list[float], list[float], int, int]:
        """
        Decide which x/y lists to use (full-atom-names vs isotope-types) and return axis-types.
        """
        matchPref = host._preferences.matchAxisCode
        if matchPref == AxisMatch.ISOTOPE.value:
            isoDict = cast(dict[str, list[float]], coords_dict[AxisMatch.ISOTOPE])
            isotopes = host.spectrumDisplay.isotopeCodes
            xPosList = isoDict.get(isotopes[0], [])
            yPosList = isoDict.get(isotopes[1], [])
        else:
            xPosList, yPosList = self._resolveAxisCodes(host, coords_dict)

        x_order, y_order, dq = _getQuantumOrders(host)
        if host._matchingIsotopeCodes:
            # Only disable double-cursors in these displays
            sameSd = host.spectrumDisplay == ((st := coords_dict.get("strip")) and st.spectrumDisplay)

            if sameSd and not self.doubleCrosshairVisible and dq is QuantumType.NONE:
                # Non-double quantum display
                x_coord, y_coord = cast(tuple, coords_dict[MOUSEDICTCURSOR])
                xPosList = [x_coord]
                yPosList = [y_coord]

            elif dq is not QuantumType.NONE:
                _, _, dq_source = _getQuantumOrders(cast("CcpnGLWidget", coords_dict[MOUSEGLPARENT]))

                # SHOULD really test the first isotope-code of the other display :|
                if dq_source is QuantumType.NONE or dq == dq_source:
                    x_slice, y_slice = slice(0, 1), slice(1, 2)
                else:
                    # Flip the co-ordinates
                    x_slice, y_slice = slice(1, 2), slice(0, 1)
                # Always put a value in to, at least, give a cross-hair.
                # When mapping from a non-matching display, one of these may be empty.
                xPosList = xPosList[x_slice] or yPosList[y_slice]
                yPosList = yPosList[y_slice] or xPosList[x_slice]

        return xPosList, yPosList, x_order, y_order

    @staticmethod
    def _resolveAxisCodes(host: CcpnGLWidget, coords_dict: _COORDS_TYPE) -> tuple[list[float], list[float]]:
        atCodes = host._orderedAxes
        assert atCodes and len(atCodes) >= 2, "CursorRenderer: _orderedAxes must provide two axes"

        chrs = host._preferences.matchNumChars
        x_code = atCodes[0].code[:chrs].lower()
        y_code = atCodes[1].code[:chrs].lower()
        codeDict = cast(dict[str, list[float]], coords_dict[AxisMatch.CODE])
        xPosList = codeDict.get(x_code, [])
        yPosList = codeDict.get(y_code, [])
        return xPosList, yPosList

    #-----------------------------------------------------------------------------------------
    # Small geometry utilities

    @staticmethod
    def _appendLine(vertices: list[float], indices: list[int],
                    x1: float, y1: float, x2: float, y2: float) -> None:
        """Append one GL_LINES segment (two vertices) and its indices."""
        base = len(vertices) // 2
        vertices.extend([x1, y1, x2, y2])
        indices.extend([base, base + 1])

    def _addPickBox(self, host: CcpnGLWidget, vertices: list[float], indices: list[int],
                    coords: list[float | None], size_factor: float) -> None:
        """
        Add a rectangular outline centered at coords (in normalized/ratio space),
        sized by deltaX/deltaY * size_factor.
        """
        x, y = coords
        if x is None or y is None:  # coords[0] is None or coords[1] is None:
            return
        dx = host.deltaX * size_factor
        dy = host.deltaY * size_factor

        # Four edges (clockwise)
        self._appendLine(vertices, indices, x - dx, y - dy, x + dx, y - dy)  # bottom
        self._appendLine(vertices, indices, x + dx, y - dy, x + dx, y + dy)  # right
        self._appendLine(vertices, indices, x + dx, y + dy, x - dx, y + dy)  # top
        self._appendLine(vertices, indices, x - dx, y + dy, x - dx, y - dy)  # left

    #-----------------------------------------------------------------------------------------
    # Adapters/defaults

    # def _getActiveCursorDrawList(self, host: CcpnGLWidget) -> GLVertexArray:
    #     """Default adapter to your queue; override if you use a different mechanism."""
    #     try:
    #         return self._glCursorQueue[self._glCursorHead]
    #     except Exception as exc:
    #         raise RuntimeError("CursorRenderer requires host._glCursorQueue/_glCursorHead "
    #                            "or an override of _getActiveCursorDrawList()") from exc

    @staticmethod
    def _isPickMode() -> bool:
        """Return the pick-mode determined from getCurrentMouseMode()."""
        from ccpn.ui.gui.lib.mouseEvents import getCurrentMouseMode

        return getCurrentMouseMode() == PICK

    # def _isPhasingVisible(self, host: CcpnGLWidget) -> bool:
    #     """Prefer host.isPhasingVisible() if available; otherwise read from spectrumDisplay."""
    #     if hasattr(host, "isPhasingVisible"):
    #         try:
    #             return bool(host.isPhasingVisible())
    #         except Exception:
    #             pass
    #     try:
    #         return bool(host.spectrumDisplay.phasingFrame.isVisible())
    #     except Exception:
    #         return False

    # def _resolveCoherenceEnum(self, host: CcpnGLWidget):
    #     """
    #     Locate CoherenceOrder enum in host module. Override if located elsewhere.
    #     The enum must support subscription [key] and .value.
    #     """
    #     # Try host attribute first
    #     if hasattr(host, "CoherenceOrder"):
    #         return getattr(host, "CoherenceOrder")
    #     # Try module-level import path (customize if needed)
    #     try:
    #         from ccpn.core.lib.SpectrumLib import CoherenceOrder
    #
    #         return CoherenceOrder
    #     except Exception as exc:
    #         raise RuntimeError("CursorRenderer: CoherenceOrder enum not found on host. "
    #                            "Provide host.CoherenceOrder or override _resolveCoherenceEnum().") from exc

    #-----------------------------------------------------------------------------------------
    # Internal utilities

    @property
    def _requireHost(self) -> CcpnGLWidget:
        if self.host is None:
            raise RuntimeError("CursorRenderer is not attached to a host. "
                               "Call `cursorHandler.attach(host)` or pass host=... in the constructor.")
        return self.host

    @staticmethod
    def _valueToRatio(val: float, x0: float, x1: float) -> float:
        if abs(x1 - x0) > 1e-9:
            return (val - x0) / (x1 - x0)
        else:
            return 0.0

    @staticmethod
    def _widthsChangedEnough(r1, r2, tol=1e-5):
        if len(r1) != len(r2):
            raise ValueError('WidthsChanged must be the same length')
        return any(abs(a - b) > tol for a, b in zip(r1, r2))

    #-----------------------------------------------------------------------------------------
    # Cursor strings - for later

    _mouseCoords = None
    _mouseCoordsDQ = None
    _mouseString: GLVertexArray | None = None
    _mouseStringDQ: GLVertexArray | None = None

    def _drawMouseCoords(self):
        if self._mouseString is not None:
            # draw the mouse coordinates to the screen
            self._mouseString.drawTextArrayVBO()
        if self._mouseStringDQ is not None:
            self._mouseStringDQ.drawTextArrayVBO()


#=========================================================================================
# CursorRenderer1d - simpler for 1d displays that do not have double-quantum axes
#=========================================================================================

class CursorRenderer1d(CursorRenderer):

    #-----------------------------------------------------------------------------------------
    # Geometry builders

    def _makeQuantumCursor(self,
                           host: CcpnGLWidget,
                           foundX: list[float],
                           foundY: list[float],
                           indices: list[int],
                           vertices: list[float],
                           xPosList: list[float],
                           xQuantumOrder: int,
                           yPosList: list[float],
                           yQuantumOrder: int) -> None:
        # No action required
        ...

    #-----------------------------------------------------------------------------------------
    # Domain helpers

    def _resolveAxisLists(self, host: CcpnGLWidget, coords_dict: _COORDS_TYPE
                          ) -> tuple[list[float], list[float], int, int]:
        """
        Decide which x/y lists to use (full-atom-names vs isotope-types) and return axis-types.
        """
        matchPref = host._preferences.matchAxisCode
        if matchPref == AxisMatch.ISOTOPE.value:
            # add extra 'isotopeCode' so that 1D appears correctly
            if host.strip.spectrumDisplay._flipped:
                atomTypes = ('intensity',) + host.spectrumDisplay.isotopeCodes
            else:
                atomTypes = host.spectrumDisplay.isotopeCodes + ('intensity',)
            isoDict = cast(dict[str, list[float]], coords_dict[AxisMatch.ISOTOPE])
            xPosList = isoDict.get(atomTypes[0], [])
            yPosList = isoDict.get(atomTypes[1], [])
        else:
            xPosList, yPosList = self._resolveAxisCodes(host, coords_dict)

        # No quantum checking required
        return xPosList, yPosList, 1, 1
