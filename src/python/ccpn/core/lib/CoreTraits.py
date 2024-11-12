#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-11-08 11:02:22 +0000 (Fri, November 08, 2024) $"
__version__ = "$Revision: 3.2.10.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2023-10-10 10:10:10 +0000 (Tue, October 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.util.traits.CcpNmrTraits import \
    Instance, OWTraits, TList, List, Int, Float, Unicode, \
    TraitError, TraitType, _CcpNmrTrait, _TypedList, Bunch
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase

from ccpn.framework.Application import getApplication, getProject
from ccpn.util.Common import classType, Sentinel
from ccpn.util.Logging import getLogger

from ccpn.core.lib.Notifiers import NotifierABC, NotifierBase
from ccpn.core.lib.ContextManagers import notificationBlanking


from ccpn.core.lib.PeakPickers import PeakPickerABC
class PeakPickerTrait(OWTraits):
    """Specific trait for a PeakPicker instance.
    """
    klass = PeakPickerABC


from ccpn.core.lib.DataStore import DataStore
class DataStoreTrait(OWTraits):
    """Specific trait for a Datastore instance encoding the path and dataFormat of the (binary) spectrum data.
    None indicates no spectrum data file path has been defined
    """
    klass = DataStore


from ccpn.core.lib.SpectrumDataSources.SpectrumDataSourceABC import SpectrumDataSourceABC
class DataSourceTrait(OWTraits):
    """Specific trait for a Datasource instance encoding access to the (binary) spectrum data.
    None indicates no spectrumDataSource has been defined
    """
    klass = SpectrumDataSourceABC


from ccpn.framework.Version import VersionString
class VersionTrait(Unicode):
    """A trait to encode a version
    """
    def validate(self, obj, value):
        return VersionString(value)


from ccpn.core.lib.Pid import Pid
class PidTrait(Unicode):
    """A trait to encode/decode a pid
    """
    def validate(self, obj, value):
        if value is None and self.allow_none:
            return None
        if isinstance(value, str):
            return Pid(value)
        elif hasattr(value, 'pid'):
            value = getattr(value, 'pid')
            return Pid(value)
        else:
            raise ValueError(f'{self._fullName(obj)}: expected pid or object with pid, got {value}')


class CoreObjectTrait(TraitType, _CcpNmrTrait):
    """A trait that defines a core-object, json serialisable through its Pid
    """
    default_value = Sentinel
    info_text = "A Core-Object"

    _overrideClassCheck = False  # flag for ccpnv4 testing

    def __init__(self, klass=None, default_value=Sentinel, allow_pid=False, **kwargs):
        """
        Initialise the trait
        :param klass: only allow objects of type klass (V3object or className str);
                      ignored when None
        :param default_value: value set by default (Sentinel)
        :param allow_pid: allow conversion from Pid/str to V3object
        :param kwargs: optional kwds to the TraitType invocation
        """
        from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass

        if klass is None:
            self._klass = None
            self._klassName = None

        elif self._overrideClassCheck:
            self._klass = klass
            self._klassName = None

        else:

            if _isV3coreClass(klass):
                self._klass = klass
                self._klassName = None

            elif isinstance(klass, str) :
               # postphone this check until later, as we otherwise run into
               # trouble with not-yet registered classes
               # (_klass := _getV3coreClass(klass)) is not None:
                self._klass = None
                self._klassName = klass

            else:
                raise ValueError(f'parameter klass: expected a valid V3 class; got {klass!r}')

        TraitType.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)

        if default_value is not None:
            self.default_value = default_value

        self.allow_pid = allow_pid

    def validate(self, obj, value):
        """Assure a Core-class instance
        :raises TypeError, ValueError
        """
        # Local import to avoid cycles
        from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass

        if value is None and self.allow_none:
            return None

        if isinstance(value, (Pid, str)) and self.allow_pid:
            _app = getApplication()
            if (value := _app.get(value)) is None:
                raise ValueError(f'Unable to get a V3object from {value}')

        if self._overrideClassCheck:
            pass

        elif self._klass is not None and not isinstance(value, self._klass):
            raise TypeError(f'Expected an instance of {classType(self._klass)}; got {value} {classType(value)}')

        elif (self._klass is None and self._klassName is not None):
            if (_klass := _getV3coreClass(self._klassName)) is None:
                raise RuntimeError(f'CoreObjectTrait: invalid className {self._klassName!r}')
            if not isinstance(value, _klass):
                raise TypeError(f'Expected an instance of {classType(_klass)}; got {value} {classType(value)}')

        elif not _isV3coreClassInstance(value):
            raise TypeError(f'Expected an instance of a V3 class; got {value} {classType(value)}')

        return value

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """json compatible;
        """
        def encode(self, value):
            "returns a json serialisable object"
            if value is None:
                return None
            else:
                return str(value.pid)

        def decode(self, value):
            "uses value to generate and set the new (or modified) obj"
            if value is None:
                return None
            else:
                _app = getApplication()
                if (result := _app.get(value)) is None:
                    getLogger().warning(f'Error decoding {value!r}; set to None')
                return result
# end class

