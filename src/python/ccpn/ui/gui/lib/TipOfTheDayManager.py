"""
Code to mange the Tip of the day; adapted from Gary's code initially in FrameWork
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-09-18 16:32:46 +0100 (Wed, September 18, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2024-09-18 10:28:48 +0000 (Wed, September 18, 2024) $"

#=========================================================================================
# Start of code
#=========================================================================================


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from ccpn.framework.PathsAndUrls import \
    ccpnConfigPath, \
    ccpnCodePath



from ccpn.ui.gui.widgets.TipOfTheDay import TipOfTheDayWindow, MODE_KEY_CONCEPTS, loadTipsSetup
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup


DEFAULT_CONFIG_PATH = 'tipConfig.hjson'
tipOfTheDayConfigPath  = ccpnConfigPath / DEFAULT_CONFIG_PATH

# how frequently to check if license dialog has closed when waiting to show the tip of the day
WAIT_EVENT_LOOP_EMPTY = 0
WAIT_LICENSE_DIALOG_CLOSE_TIME = 100


class TipOfTheDayManager():
    """Class to manage Tip of the day code
    """

    #-----------------------------------------------------------------------------------------

    def __init__(self, gui, preferences):

        self.gui = gui

        # GST slightly complicated as we have to wait for any license or other
        # startup dialogs to close before we display tip of the day
        loadTipsSetup(tipOfTheDayConfigPath, [ccpnCodePath])
        self._tip_of_the_day_wait_dialogs = (RegisterPopup,)

        # info from preferences
        self.show_tips = preferences['general'].setdefault('showTipOfTheDay', True)
        self.is_first_time_tip_of_the_day = preferences['general'].setdefault('firstTimeShowKeyConcepts', True)
        # retain access to preferences for buttons callback
        self.preferences = preferences

        # Popups populated later
        self._tip_of_the_day = None
        self._key_concepts = None

        self._initial_show_timer = None
        # self._startupShowTipofTheDay()

    def start(self):
        if self.show_tips:
            self._initial_show_timer = QTimer(parent=self.gui.mainWindow._widget)
            self._initial_show_timer.timeout.connect(self._startupDisplayTipOfTheDayCallback)
            self._initial_show_timer.setInterval(0)
            self._initial_show_timer.start()

    def _canTipOfTheDayShow(self):
        result = True
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, self._tip_of_the_day_wait_dialogs) and widget.isVisible():
                result = False
                break
        return result

    def _startupDisplayTipOfTheDayCallback(self):

        # GST this waits till any inhibiting dialogs aren't show and then awaits till the event loop is empty
        # effectively it swaps between waiting for WAIT_LICENSE_DIALOG_CLOSE_TIME or until the event loop is empty
        if not self._canTipOfTheDayShow() or self._initial_show_timer.interval() == WAIT_LICENSE_DIALOG_CLOSE_TIME:
            if self._initial_show_timer.interval() == WAIT_EVENT_LOOP_EMPTY:
                self._initial_show_timer.setInterval(WAIT_LICENSE_DIALOG_CLOSE_TIME)
            else:
                self._initial_show_timer.setInterval(WAIT_EVENT_LOOP_EMPTY)

            self._initial_show_timer.start()
        else:
            # this should only happen when the event loop is empty...
            if self.is_first_time_tip_of_the_day:
                self._displayKeyConcepts()
                self.is_first_time_tip_of_the_day = False
            else:
                try:
                    self._displayTipOfTheDay()
                except Exception as e:
                    self._initial_show_timer.stop()
                    self._initial_show_timer.deleteLater()
                    self._initial_show_timer = None
                    raise e

            if self._initial_show_timer:
                self._initial_show_timer.stop()
                self._initial_show_timer.deleteLater()
                self._initial_show_timer = None

    def _displayKeyConcepts(self):
        if not self._key_concepts:
            self._key_concepts = TipOfTheDayWindow(mode=MODE_KEY_CONCEPTS)
        self._key_concepts.show()
        self._key_concepts.raise_()

    def _displayTipOfTheDay(self, standalone=False):

        # tip of the day allocated standalone already
        if self._tip_of_the_day and standalone and self._tip_of_the_day.isStandalone():
            self._tip_of_the_day.show()
            self._tip_of_the_day.raise_()

        # tip of the day hanging around from startup
        elif self._tip_of_the_day and standalone and not self._tip_of_the_day.isStandalone():

            self._tip_of_the_day.hide()
            self._tip_of_the_day.deleteLater()
            self._tip_of_the_day = None

        if not self._tip_of_the_day:

            seen_tip_list = []
            # if not standalone:
            seen_tip_list = self.preferences['general']['seenTipsOfTheDay']

            self._tip_of_the_day = TipOfTheDayWindow(dont_show_tips=not self.show_tips,
                                                     seen_perma_ids=seen_tip_list, standalone=standalone)
            self._tip_of_the_day.dont_show.connect(self._tip_of_the_day_dont_show_callback)
            # if not standalone:
            self._tip_of_the_day.seen_tips.connect(self._tip_of_the_day_seen_tips_callback)

            self._tip_of_the_day.show()
            self._tip_of_the_day.raise_()

    def _tip_of_the_day_dont_show_callback(self, dont_show):
        self.preferences['general']['showTipOfTheDay'] = not dont_show

    def _tip_of_the_day_seen_tips_callback(self, seen_tips):
        seen_tip_list = self.preferences['general']['seenTipsOfTheDay']
        previous_seen_tips = set(seen_tip_list)
        previous_seen_tips.update(seen_tips)
        seen_tip_list.clear()
        seen_tip_list.extend(previous_seen_tips)


