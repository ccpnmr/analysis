
from contextlib import contextmanager
from ccpn.util.Logging import getLogger


class _SettingsChanged(object):
    '''
    A class that fires registered callbacks when a class property (e.g a setting) has been changed.
    It wraps the getter and setter, so that they are not needed to be defined to fire the notifier.
    it can be used with a contextManager for temporarily disabling callbacks for each change.
    A silentCallback will notify that something has changed.

    '''
    def __init__(self):
        self.callbacks = []
        self.silentCallback = None
        self._enabled = True
        self._blockingLevel = 0
        self._lastEnabledState = True

    def notify(self, *args, **kwargs):
        if self.enabled:
            list(map(lambda f:f(*args, **kwargs), self.callbacks))
        else:
            if callable(self.silentCallback):
                self.silentCallback()

    def register(self, callback):
        self.callbacks += [callback]
        return callback

    def deregister(self):
        self.callbacks = []
        self.silentCallback = None

    def setSilentCallback(self, callback):
        self.silentCallback = callback

    @classmethod
    def watchedProperty(cls, eventName, key):
        actualKey = '_%s' % key
        def getter(obj):
            return getattr(obj, actualKey)

        def setter(obj, value):
            oldValue = getattr(obj, actualKey)
            event = getattr(obj, eventName)
            setattr(obj, actualKey, value)
            event.notify(obj,
                        {
                        'theProperty': key,
                        'theObject'  : obj,
                        'newValue'   : value,
                        'oldValue'   : oldValue
                        })
        return property(fget=getter, fset=setter)

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        if isinstance(value, bool):
            self._enabled = value

    @contextmanager
    def blockChanges(self):
        """Block all changes to the object"""
        self._blockChanges()
        try:
            yield
        except Exception as es:
            getLogger().warn('Object %s. Error executing callbacks %s' %(self, es))
        finally:
            self._unblockChanges()

    def _blockChanges(self):
        """Block all Changes to the object """
        if not hasattr(self, '_blockingLevel'):
            self._blockingLevel = 0
        if self._blockingLevel == 0:
            self._lastEnabledState = self._enabled
            self._enabled = False
        self._blockingLevel += 1

    def _unblockChanges(self):
        """Unblock all changes to the object"""
        if self._blockingLevel > 0:
            self._blockingLevel -= 1
            if self._blockingLevel == 0:
                self._enabled = self._lastEnabledState
        else:
            getLogger().warn('Changes blocking already at 0')

DefaultFoo = 0
SettingsChanged = 'settingsChanged'

class _DataModuleBase(object):
    """
    A base class for a Non-Gui Module.
    It implements a notifier system so that anytime a property is changed, a registered method is called.
    A callable can also be registered externally, e.g. in a GUI module, allowing to update the Gui part indirectly
    decoupling the two parts.

    e.g.
        MyNoUIModule(_DataModuleBase)
            foo = settingsChanged.watchedProperty(SettingsChanged, 'foo')
            def __init__():
                self._foo = 0
            def update():...

        MyDataModule(CcpnModule)
            def __init__():
                self.myDataModule = MyDataModule()
                self.myDataModule.settingsChanged.register(self.updateGui)
                self.myDataModule.settingsChanged.setSilentCallback(self.silentGuiCallBack)
            def updateGui():...
            def silentGuiCallBack()...

        # >>> myGuiModule = MyGuiModule()
        # >>> myGuiModule.myDataModule.foo = 5
        -->  update() is called (in myDataModule)
        -->  updateGui() is called (in myGuiModule)

        To don't automatically notify when a change has occurred:
        # >>> myGuiModule.myDataModule.autoUpdateEnabled = False
        # >>> myGuiModule.myDataModule.foo = 5
        -->  silentGuiCallBack() is called (in myGuiModule)

        or in a loop with a contextManager:
        # >>> myDataModule = MyDataModule()
        # >>> with myDataModule.settingsChanged.blockChanges():
        # >>>    for i in range(10):
        # >>>        myDataModule.foo = i
        --> only the silentCallback is called (once).

    """

    settingsChanged = _SettingsChanged()

    def __init__(self, project, **kwds):

        self.project = project
        self._data = None

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def autoUpdateEnabled(self):
        return self._autoUpdateEnabled

    @autoUpdateEnabled.setter
    def autoUpdateEnabled(self, value:bool):
        self._autoUpdateEnabled = value
        self.settingsChanged.enabled = value

    @settingsChanged.register
    def update(self, *args, **kwargs):
        """ Subclass this """
        pass

