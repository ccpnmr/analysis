"""
Notifier extensions for Gui objects, wrapping it into a class that also acts as the called 
function, displatching the 'user' callback if required.
The Notifier can be defined relative to any valid V3 Widget
object as it first checks if the triggered signature is valid.

The callback function is passed a callback dictionary with relevant info (see
docstring of Notifier class. This idea was copied from the Traitlets package.

Very similar (and if fact based upon) the Notifier Class for core objects,
but separate to keep graphics code isolated

April 2017: First design by Geerten Vuister

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-09-11 18:57:16 +0100 (Wed, September 11, 2024) $"
__version__ = "$Revision: 3.2.7 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys

from functools import partial
from collections import OrderedDict
from typing import Callable, Any, Optional

from PyQt5 import QtGui, QtWidgets

from ccpn.core.lib.Notifiers import NotifierABC, _NotifierList
from ccpn.util.Logging import getLogger


class GuiNotifier(NotifierABC):
    """
     GuiNotifier class:

    triggers callback function with signature:  callback(callbackDict)

    ____________________________________________________________________________________________________________________

    trigger             targetName           callbackDict keys          Notes
    ____________________________________________________________________________________________________________________

    Notifier.DROPEVENT  [dropTargets]         theObject,                theObject should inherit from QtWidgets.QWidget
                                                                        and be droppable
                                              targetName                targetName: optional dropTargets to filter for
                                                                        before callback (None to skip), as defined in
                                                                        DropBase
                                              trigger,
                                              notifier,
                                              event, isCcpnJson,
                                              [dropTargets]


    dropTargets: keywords defining type of dropped objects: currently implemented: 'urls', 'text', 'pids' (see DropBase)

    Implementation:

      The callback provides a dict with several key, value pairs (idea following the Traitlets concept).
      Note that this dict also contains a reference to the GuiNotifier object itself; this way it can be used
      to pass-on additional implementation specfic information to the callback function.

      On Intialisation, the GuiNotifier instance sets the appropriate callback functions of the widget,
      as defined in DropBase, from which each Ccpn-Widget derives.

    """

    # Trigger keywords
    DROPEVENT = 'dropEvent'
    ENTEREVENT = 'enterEvent'
    DRAGMOVEEVENT = 'dragMoveEvent'
    _triggerKeywords = (DROPEVENT, ENTEREVENT, DRAGMOVEEVENT)

    def __init__(self, theObject: QtWidgets.QWidget, trigger, targetName,
                 callback: Callable, setterObject=None, debug=False, **kwds):
        """
        Create GuiNotifier object;

        :param theObject: Widget to watch
        :param trigger: one of trigger keywords; i.e. (DROPEVENT, ENTEREVENT, DRAGMOVEEVENT)
        :param targetName: optional dropTarget; i.e. URLS, TEXT, PIDS, IDS
        :param callback: callback function with signature: callback(callbackDict[, **kwargs])
        :param setterObject: Object that was setting the Notifier
        :param debug: set debug
        :param **kwds: optional keywords arguments passed to callback
        """
        # local import to avoid cycles
        from ccpn.ui.gui.widgets.DropBase import DropBase

        # some sanity checks
        if not isinstance(theObject, QtWidgets.QWidget):
            raise ValueError('Invalid object (%r), expected object of type QWidget' % theObject)

        if isinstance(targetName, (list, tuple)):
            raise ValueError(f'Invalid targetName {targetName}; remove list or tuple')

        # super() will also check for trigger against self._triggerKeywords
        super().__init__(theObject=theObject, trigger=trigger, targetName=targetName,
                         callback=callback, setterObject=setterObject,
                         debug=debug, **kwds
                         )

        # register the callback
        if trigger == GuiNotifier.DROPEVENT:

            # if not theObject.acceptDrops():
            #     raise RuntimeError(f'GuiNotifier.__init__: Widget {theObject} does not accept drops')

            if targetName is not None:
                if targetName not in DropBase._dropTargets:
                    raise RuntimeError(f'GuiNotifier.__init__(): invalid dropTarget "{targetName}"')


        if trigger == GuiNotifier.DRAGMOVEEVENT:
            raise RuntimeError(f'GuiNotifier for "{trigger}" currently not implemented')

        self.registerNotifier()

    # def unRegisterNotifier(self):
    #     """
    #     unregister the notifiers
    #     """
    #     if not self.isRegistered:
    #         return
    #
    #     if self._trigger == GuiNotifier.DROPEVENT:
    #         # self._theObject.setDropEventCallback(None)
    #         pass
    #
    #     elif self._trigger == GuiNotifier.ENTEREVENT:
    #         # self._theObject.setDragEnterEventCallback(None)
    #         pass
    #
    #     elif self._trigger == GuiNotifier.DRAGMOVEEVENT:
    #         self._theObject.setDragMoveEventCallback(None)
    #
    #     super().unRegisterNotifier()  # the end as it clears all attributes

    def __call__(self, data: dict):
        """
        wrapper, accommodating the different triggers before firing the callback
        """
        if not self.isRegistered:
            getLogger().warning('Triggering unregistered guiNotifier %s' % self)
            return

        if self._debug:
            sys.stderr.write(f'>>> {self}.__call__(): {data = } {self._isBlanked = }\n' )

        if self._isBlanked:
            return

        # DROPEVENT
        if self._trigger == GuiNotifier.DROPEVENT and \
           self._targetName is not None and \
           self._targetName not in data:
            return

        callbackDict = self.newCallbackDict()
        callbackDict.update(data)
        result = self._callback(callbackDict, **self._kwds)
        return result


def _makeGuiNotifiers(theObject,
                      triggers: list|tuple,
                      targetNames: list|tuple,
                      callback: Callable,
                      setterObject=None,
                      ) -> _NotifierList:
    """Backward compatibility to make a NotifierList from multiple triggers

    :param theObject: the object to set the Notifier for
    :param triggers: a list of trigger keywords; i.e. (DROPEVENT, ENTEREVENT, DRAGMOVEEVENT)
    :param targetNames: list of dropTargets (URLS, TEXT, PIDS, IDS) or None
    :param callback: callback function with signature: callback(callBackDict)
    :param setterObject: reference to the object setting the notifier

    :return: a _NotifierList instance

    """
    if not isinstance(triggers, (list,tuple)) or len(triggers) == 0:
        raise ValueError(f'Invalid triggers {triggers}; expected list, tuple with at least one item')

    result = _NotifierList()
    for _trigger in triggers:
        for _target in targetNames:
            _notifier = GuiNotifier(theObject=theObject,
                                    trigger=_trigger,
                                    targetName=_target,
                                    callback=callback,
                                    setterObject=setterObject,
                                    )
            result.append(_notifier)

            # bit of a hack to set add _notifier to setterObject if it is not there yet.
            # This adds some backward compatibility to GuiNotifiers not initialised through the
            # setNotifier() method of NotifierBase.
            if setterObject is not None \
                and hasattr(setterObject, '_addNotifier') \
                and hasattr(setterObject, '_hasNotifier') \
                and not setterObject._hasNotifier(_notifier):
                setterObject._addNotifier(_notifier)

    return result


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.BasePopup import BasePopup
    from ccpn.ui.gui.widgets.Label import Label
    from ccpn.ui.gui.widgets.Widget import Widget
    from ccpn.ui.gui.widgets.Button import Button

    from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


    class MyWidget(Widget):
        buttonPressed1 = pyqtSignal(str)
        buttonPressed2 = pyqtSignal(dict)

        def __init__(self, parent, name, **kwds):
            super(MyWidget, self).__init__(parent=parent, setLayout=True, **kwds)
            self.name = name
            self.label = Label(parent=self, grid=(0, 0), text=name, bold=True, textColour='black', textSize='18')
            self.button = Button(parent=self, grid=(1, 0), text='Button-' + name, callback=self._pressed)

        def _pressed(self):
            bText = self.button.getText()
            print(bText + ' was pressed')
            # str signal
            self.buttonPressed1.emit(bText)
            # dict signal
            bDict = {'text': bText}
            self.buttonPressed2.emit(bDict)

        @pyqtSlot(str)
        def _receivedSignal1(self, text):
            print(self.name + ' received signal1:', text)

        @pyqtSlot(dict)
        def _receivedSignal2(self, aDict):
            print(self.name + ' received signal2:', aDict)


    class TestPopup(BasePopup):
        def body(self, parent):
            mainWidget = Widget(parent, setLayout=True)
            widget1 = MyWidget(parent=mainWidget, name='Widget-1', grid=(0, 0), bgColor=(255, 255, 0))
            widget2 = MyWidget(parent=mainWidget, name='Widget-2', grid=(1, 0), bgColor=(255, 0, 0))
            # connect the signals to the str variant
            widget1.buttonPressed1.connect(widget2._receivedSignal1)  # widget2 listens to widget1.buttonPressed1 signal
            widget2.buttonPressed1.connect(widget1._receivedSignal1)  # widget1 listens to widget1.buttonPressed1 signal
            # connect the signals to the dict variant
            widget1.buttonPressed2.connect(widget2._receivedSignal2)  # widget2 listens to widget1.buttonPressed2 signal
            widget2.buttonPressed2.connect(widget1._receivedSignal2)  # widget1 listens to widget1.buttonPressed2 signal


    app = TestApplication()
    popup = TestPopup(title='Testing slots and signals', setLayout=True)
    popup.resize(200, 400)
    app.start()
