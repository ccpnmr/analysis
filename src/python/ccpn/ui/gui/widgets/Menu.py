"""Module Documentation here
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
__dateModified__ = "$dateModified: 2025-10-02 14:32:05 +0100 (Thu, October 02, 2025) $"
__version__ = "$Revision: 3.3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

__all__ = ['Menu', 'MenuBar']

from typing import TYPE_CHECKING
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.Base import Base
from ccpn.framework.Translation import translator
from ccpn.ui.gui.guiSettings import PALETTE_ROLE_TO_STYLESHEET_NAME


if TYPE_CHECKING:
    from ccpn.ui.gui.lib.MenuLib import MenuEventFilter

SHOWMODULESMENU = 'Show/hide Modules'
MACROSMENU = 'User Macros'
CCPNMACROSMENU = 'Run CCPN Macros'
USERMACROSMENU = 'Run User Macros'
TUTORIALSMENU = 'Tutorials'
HOWTOSMENU = 'How-Tos'
PLUGINSMENU = 'User Plugins'
CCPNPLUGINSMENU = 'CCPN Plugins'

_FOREGROUND = '_foregroundColour'
_BACKGROUND = '_backgroundColour'
_COLOUR_ENABLED = '_colourEnabled'
_SEPARATOR = '_separator'
_PADDING = 3
_MARGIN = 2

# Gradient geometry to unify stylesheet and drawControl
_GRADIENT_START_POINT = QtCore.QPointF(0, -1)
_GRADIENT_END_POINT = QtCore.QPointF(0, 8)
# Gradient colors
_GRADIENT_START_COLOR = QtGui.QPalette.Base  # emphasis is towards the start
_GRADIENT_END_COLOR = QtGui.QPalette.Text


class _MenuProxyStyle(QtWidgets.QProxyStyle):
    """Class to handle foreground/background colours in menuItems.

    This proxy style overrides the default drawing of menu items to apply
    custom colours defined as properties on the associated QAction.

    # NOTE: the menu stylesheets and menu-proxy are not applied to native MacOS menus :|
    """

    def drawControl(self, element: QtWidgets.QStyle.ControlElement,
                    option: QtWidgets.QStyleOption,
                    painter: QtGui.QPainter,
                    widget: QtWidgets.QWidget | None = None) -> None:
        """Draws a custom menu item control with optional foreground and background colours.

        :param element: The control element to draw, e.g., ``QtWidgets.QStyle.CE_MenuItem``.
        :type element: QtWidgets.QStyle.ControlElement
        :param option: The style options to use for drawing.
        :type option: QtWidgets.QStyleOption
        :param painter: The painter device to use for drawing.
        :type painter: QtGui.QPainter
        :param widget: The widget on which to draw. This should be a ``QtWidgets.QMenu``.
        :type widget: QtWidgets.QWidget | None
        :rtype: None
        """
        # A complex guard clause to ensure we are drawing a menu item with a valid widget
        if (element in {QtWidgets.QStyle.CE_MenuItem} and
                isinstance(option, QtWidgets.QStyleOptionMenuItem) and
                isinstance(widget, QtWidgets.QMenu) and
                # Check for the colour enabled flag on the menu widget
                (_colourEnabled := getattr(widget, _COLOUR_ENABLED, False))):

            # Find the QAction corresponding to the current menu item's drawing rectangle.
            action = next((act for act in widget.actions()
                           if not act.isSeparator() and
                           act.isVisible() and
                           # Check if the action's geometry contains the center of the option's rect
                           widget.actionGeometry(act).contains(option.rect.center())), None)
            if action is not None:
                # Check for and apply custom foreground colour from QAction property
                if colour := action.property(_FOREGROUND):
                    # Menu items do not have their own palette, so override the option's
                    # palette color for the text element.
                    option.palette.setColor(option.palette.Text, colour)
                # Check for and apply custom background colour
                if colour := action.property(_BACKGROUND):
                    self._paint_background(painter, widget, colour)
                if getattr(action, _SEPARATOR, None):
                    # If defined as a separator-with-text then draw specialised control
                    self._DrawControlWithSeparator(element, option, painter, widget)
                    return
        # Call the base class's drawControl to ensure default drawing is handled
        super().drawControl(element, option, painter, widget)

    def _DrawControlWithSeparator(self, element: QtWidgets.QStyle.ControlElement,
                                  option: QtWidgets.QStyleOptionMenuItem,
                                  painter: QtGui.QPainter,
                                  widget: QtWidgets.QMenu):
        """Draws a custom menu item control with separator bars either side of text.

        :param element: The control element to draw; this should be ``QtWidgets.QStyle.CE_MenuItem``.
        :type element: QtWidgets.QStyle.ControlElement
        :param option: The style options to use for drawing.
        :type option: QtWidgets.QStyleOptionMenuItem
        :param painter: The painter device to use for drawing.
        :type painter: QtGui.QPainter
        :param widget: The widget on which to draw. This should be a ``QtWidgets.QMenu``.
        :type widget: QtWidgets.QWidget
        :rtype: None
        """
        # Cast option to QStyleOptionMenuItem for text-specific details below
        original_text = option.text.strip(' \u2014\u2015\u2500-')  # strip leading/trailing spaces and dash types
        option.text = ''  # temporarily remove the text for base drawing
        # Call the base class's drawControl to draw without text
        super().drawControl(element, option, painter, widget)

        painter.save()
        # Create gradient to match the qlineargradient in the Menu stylesheet
        gradient = QtGui.QLinearGradient(_GRADIENT_START_POINT, _GRADIENT_END_POINT)
        gradient.setCoordinateMode(QtGui.QGradient.ObjectMode)
        gradient.setColorAt(0, QtWidgets.QApplication.palette().color(_GRADIENT_START_COLOR))
        gradient.setColorAt(1, QtWidgets.QApplication.palette().color(_GRADIENT_END_COLOR))
        # Create brush and pen
        brush = QtGui.QBrush(gradient)
        # Calculate text and separator positions
        text_width = option.fontMetrics.width(original_text)
        x_centre = option.rect.center().x()
        y_centre = option.rect.center().y()
        separator_width = (option.rect.width() - text_width) // 2 - _MARGIN - _PADDING
        # Draw separator lines to the left and right
        painter.fillRect(option.rect.left() + _MARGIN, y_centre, separator_width, 1, brush)
        painter.fillRect(x_centre + (text_width // 2) + _PADDING, y_centre, separator_width, 1, brush)

        # Draw the text if present
        if original_text:
            # Determine appropriate text color role
            enabled = bool(option.state & QtWidgets.QStyle.State_Enabled)
            if option.state & QtWidgets.QStyle.State_Selected:
                role = QtGui.QPalette.HighlightedText
            else:
                role = QtGui.QPalette.Text
            # Draw the original text
            self.drawItemText(painter, option.rect, QtCore.Qt.AlignCenter,
                              option.palette, enabled, original_text, role)
        painter.restore()

    @staticmethod
    def _paint_background(painter: QtGui.QPainter,
                          widget: QtWidgets.QWidget | None,
                          colour: QtGui.QColor | bool = True) -> None:
        """Paints the background of a menu item with a given colour.

        If colour is True, applies a semi-transparent, theme-agnostic gray
        to lighten/darken the current background.

        :param painter: The painter device to use.
        :type painter: QtGui.QPainter
        :param widget: The widget on which to paint.
        :type widget: QtWidgets.QWidget | None
        :param colour: The color to use, or True to use a default semi-transparent grey.
        :type colour: QtGui.QColor | bool
        :rtype: None
        """
        if not widget or colour is False:
            return
        # Save and restore the painter's state to prevent unwanted side effects
        painter.save()
        try:
            wind = widget.rect()
            # Paint a new background
            if colour is True:
                # Apply a semi-transparent, theme-agnostic gray
                # The alpha value is a float between 0.0 and 1.0, currently 9%
                colour = QtGui.QColor('#808080')
                colour.setAlphaF(0.09)
            painter.fillRect(wind, colour)
        except Exception:
            # Handle potential exceptions during painting gracefully
            ...
        finally:
            # Restore the painter's state
            painter.restore()


#=========================================================================================
# Menu
#=========================================================================================

class Menu(QtWidgets.QMenu, Base):
    _colourEnabled = False
    _filter: MenuEventFilter | None = None

    def __init__(self, title, parent, isFloatWidget=False, **kwds):
        super().__init__(parent)
        Base._init(self, isFloatWidget=isFloatWidget, **kwds)

        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        title = translator.translate(title)
        self.setTitle(title)
        self.isFloatWidget = isFloatWidget
        self.setToolTipsVisible(True)
        # patch for icon sizes in menus, etc.
        styles = QtWidgets.QStyleFactory()
        self.setStyle(_MenuProxyStyle(styles.create('fusion')))
        col_start_name = PALETTE_ROLE_TO_STYLESHEET_NAME.get(_GRADIENT_START_COLOR)
        col_end_name = PALETTE_ROLE_TO_STYLESHEET_NAME.get(_GRADIENT_END_COLOR)
        # This is dynamic method to get a theme-agnostic colour into a palette
        self.setStyleSheet(f"""
                            QMenu::item:disabled {{ color: palette(dark); }}
                            QMenu::separator {{
                                height: 1px;
                                background: qlineargradient(
                                    x1: {_GRADIENT_START_POINT.x()}, y1: {_GRADIENT_START_POINT.y()},
                                    x2: {_GRADIENT_END_POINT.x()}, y2: {_GRADIENT_END_POINT.y()},
                                    stop: 0 palette({col_start_name}),
                                    stop: 1 palette({col_end_name})
                                );
                                margin-left: {_MARGIN}px;
                                margin-right: {_MARGIN}px;
                            }}
                            QMenuBar {{ color: palette(text); }}
                            QMenuBar::item:disabled {{ color: palette(dark); }}
                            """
                           )

    def addItem(self, text, shortcut=None, callback=None,
                checked=True, checkable=False, enabled=True,
                icon=None, toolTip=None,
                **kwargs
                ):
        action = Action(self.getParent(), text, callback=callback, shortcut=shortcut,
                        checked=checked, checkable=checkable, enabled=enabled,
                        icon=icon, toolTip=toolTip,
                        isFloatWidget=self.isFloatWidget, **kwargs)
        self.addAction(action)
        return action

    def _addSeparator(self, *args, **kwargs):
        # a method to catch the args of the generic call from _createMenu, and _addMenuItems
        # could be moved to the top of GuiStripContextMenus.py for clarity
        separator = self.addSeparator()
        return separator

    def addMenu(self, title, **kwargs):
        menu = Menu(title, self)
        QtWidgets.QMenu.addMenu(self, menu)
        return menu

    def _addQMenu(self, menu):
        """This adds a normal QMenu.
        """
        QtWidgets.QMenu.addMenu(self, menu)
        return menu

    def getItems(self):
        dd = {i.text(): i for i in self.actions()}
        return dd

    def getActionByName(self, name):
        """Return the named menu action.
        """
        return self.getItems().get(name, None)

    def moveActionBelowName(self, action, targetActionName):
        """Move an action below a pre-existing name.
        """
        targetAction = self.getActionByName(targetActionName)
        if targetAction:
            self.insertAction(action, targetAction)

    def moveActionAboveName(self, action, targetActionName):
        """Move an action above a pre-existing name.
        """
        targetAction = self.getActionByName(targetActionName)
        if targetAction:
            self.insertAction(targetAction, action)

    # NOTE:ED - not required now - delete soon
    # def showEvent(self, event: QtGui.QShowEvent) -> None:
    #     super().showEvent(event)
    #     if self._colourEnabled:
    #         # if _colourEnabled defined for this menu then build a dict of the actionGeometry's
    #         # these can be used in the QProxyStyle to provide access the QAction
    #         self._actionGeometries = {str(self.actionGeometry(action)): action
    #                                   for action in self.actions()}

    def setColourEnabled(self, value):
        if not isinstance(value, bool):
            raise TypeError(f'{self.__class__.__name__}.setColourEnabled: value is not a bool')
        self._colourEnabled = value

    def isColourEnabled(self) -> bool:
        return self._colourEnabled


class MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent):
        QtWidgets.QMenuBar.__init__(self, parent)
