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
__dateModified__ = "$dateModified: 2017-07-07 16:32:42 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2017-04-18 15:19:30 +0100 (Tue, April 18, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from functools import partial
from collections import OrderedDict
from typing import Callable, Any

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.DropBase import DropBase

from ccpn.util.Logging import getLogger


logger = getLogger()


def skip(*args, **kwargs):
    "Do nothing"
    pass


class GuiNotifier(object):
    """
     GuiNotifier class:

    triggers callback function with signature:  callback(callbackDict [, *args] [, **kwargs])

    ____________________________________________________________________________________________________________________

    trigger             targetName           callbackDict keys          Notes
    ____________________________________________________________________________________________________________________

    Notifier.DROPEVENT  [dropTargets]         theObject,targetName      theObject should inherit from QtWidgets.QWidget and
                                                                        be droppable
                                              trigger, notifier,        targetName: optional dropTargets to filter for
                                              event, isCcpnJson,        before callback (None to skip, defined in DropBase)
                                              [dropTargets]


    dropTargets: keywords defining type of dropped objects: currently implemented: 'urls', 'text', 'pids'

    Implemention:

      The callback provides a dict with several key, value pairs and optional arguments and/or keyword arguments if
      defined in the instantiation of the Notifier object. (idea following the Traitlets concept).
      Note that this dict also contains a reference to the GuiNotifier object itself; this way it can be used
      to pass-on additional implementation specfic information to the callback function.

    """
    _currentIndex = 0

    # Trigger keywords
    DROPEVENT = 'dropEvent'
    ENTEREVENT = 'enterEvent'
    DRAGMOVEEVENT = 'dragMoveEvent'
    _triggerKeywords = (DROPEVENT, ENTEREVENT, DRAGMOVEEVENT)

    def __init__(self, theObject: Any, triggers: list, targetName: list, callback: Callable[..., str], *args, **kwargs):
        """
        Create GuiNotifier object;

        :param theObject: valid V3 core object or current object to watch
        :param triggers: list of trigger keywords callback
        :param targetName: optional list of dropTargets or None
        :param callback: callback function with signature: callback(obj, parameter2 [, *args] [, **kwargs])
        :param *args: optional arguments to callback
        :param **kwargs: optional keyword,value arguments to callback
        """

        # some sanity checks
        if not isinstance(theObject, QtWidgets.QWidget):
            raise RuntimeError('Invalid object (%r), expected object of type QWidget' % theObject)

        if triggers is None:
            if not (isinstance(triggers, list) or isinstance(triggers, tuple)) \
                    or len(triggers) == 0:
                raise RuntimeError('Invalid trigger (%r)' % triggers)

        self._index = GuiNotifier._currentIndex
        GuiNotifier._currentIndex += 1

        self._theObject = theObject  # The object we are monitoring

        self._notifiers = []  # list of tuples defining Notifier call signature; used for __str__
        self._unregister = []  # list of tuples needed for unregistering

        self._callback = callback
        self._args = args
        self._kwargs = kwargs

        self._debug = False  # ability to report on individual instances

        # register the callbacks
        for trigger in triggers:

            if trigger not in GuiNotifier._triggerKeywords:
                raise RuntimeError('GuiNotifier.__init__: invalid trigger "%s"' % trigger)

            elif trigger == GuiNotifier.DROPEVENT:

                if not self._theObject.acceptDrops():
                    raise RuntimeError('GuiNotifier.__init__: Widget "%s" does not accept drops' % self._theObject)

                if targetName is not None:
                    for target in targetName:
                        if target not in DropBase._dropTargets:
                            raise RuntimeError('GuiNotifier.__init__: invalid dropTarget "%s"' % (target))

                notifier = (trigger, targetName)
                self._notifiers.append(notifier)
                self._theObject.setDropEventCallback(partial(self, notifier=notifier))
                self._unregister.append((trigger, targetName))  # for now a duplicate, but we may need this late

            elif trigger == GuiNotifier.ENTEREVENT:
                notifier = (trigger, targetName)
                self._notifiers.append(notifier)
                self._theObject.setDragEnterEventCallback(partial(self, notifier=notifier))
                self._unregister.append((trigger, targetName))  # for now a duplicate, but we may need this late

            elif trigger == GuiNotifier.DRAGMOVEEVENT:
                notifier = (trigger, targetName)
                self._notifiers.append(notifier)
                self._theObject.setDragMoveEventCallback(partial(self, notifier=notifier))
                self._unregister.append((trigger, targetName))  # for now a duplicate, but we may need this late

        if len(self._notifiers) == 0:
            raise RuntimeWarning('GuiNotifier.__init__: no notifiers intialised for theObject=%s, targetName=%r, triggers=%s ' % \
                                 (theObject, targetName, triggers))

    def unRegister(self):
        """
        unregister the notifiers
        """
        for trigger, targetName in self._unregister:
            if trigger == GuiNotifier.DROPEVENT:
                self._theObject.setDropEventCallback(None)
        self._notifiers = []
        self._unregister = []

    def setDebug(self, flag: bool):
        "Set debug output on/off"
        self._debug = flag

    def __call__(self, data: dict, notifier: tuple = None):
        """
        wrapper, accommodating the different triggers before firing the callback
        """
        trigger, targetName = notifier

        # DROPEVENT
        if trigger == GuiNotifier.DROPEVENT:
            if self._debug:
                logger.info('>>> GuiNotifier (%d): obj=%s  callback for %s, %s: data=%s' % \
                            (self._index, self._theObject, notifier, self._callback, data)
                            )
            # optionally filter for targetName
            skip = False
            if targetName is not None:
                skip = True
                for target in targetName:
                    if target in data.keys():
                        skip = False
                        break
            if skip: return

            callbackDict = dict(
                    notifier=self,
                    trigger=trigger,
                    theObject=self._theObject,
                    targetName=targetName,
                    )
            callbackDict.update(data)
            self._callback(callbackDict, *self._args, **self._kwargs)

        if trigger == GuiNotifier.DRAGMOVEEVENT:
            callbackDict = dict(
                    notifier=self,
                    trigger=trigger,
                    theObject=self._theObject,
                    targetName=targetName,
                    )
            callbackDict.update(data)
            self._callback(callbackDict, *self._args, **self._kwargs)

        return

    def __str__(self) -> str:
        return '<GuiNotifier (%d): theObject=%s, notifiers=%s>' % \
               (self._index, self._theObject, self._notifiers)


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
