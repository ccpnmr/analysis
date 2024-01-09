#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-11-29 12:08:46 +0000 (Wed, November 29, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2023-10-10 10:10:10 +0000 (Tue, October 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.traits.CcpNmrTraits import \
    Instance, OWTraits, List, Int, Float, Unicode, \
    TraitError, TraitType, _CcpNmrTrait
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase
from ccpn.util.Common import classType
from ccpn.framework.Application import getApplication
from ccpn.util.Logging import getLogger


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

class V3Object(TraitType, _CcpNmrTrait):
    """A trait that defines a V3-object, json serialisable through its Pid
    """
    default_value = None
    info_text = "A V3-Object"

    _overrideClassCheck = False  # flag for v3mimic testing

    def __init__(self, klass=None, default_value=None, **kwargs):
        """
        Initialise the trait
        :param klass: only allow objects of type klass (V3object or className str);
                      ignored when None
        :param default_value: value set by default (None)
        :param kwargs: optional
        """
        from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass

        if klass is None:
            self._klass = None

        else:

            if _isV3coreClass(klass):
                self._klass = klass

            elif isinstance(klass, str) and \
               (_klass := _getV3coreClass(klass)) is not None:
                self._klass = _klass

            else:
                raise ValueError(f'parameter klass: expected a valid V3 class; got {klass}')

        TraitType.__init__(self, default_value=default_value, **kwargs)
        _CcpNmrTrait.__init__(self)

        if default_value is not None:
            self.default_value = default_value

    def validate(self, obj, value):
        """Assure a Core-class instance
        :raises TypeError, ValueError
        """
        from ccpn.core._implementation.CoreModel import _isV3coreClass, _isV3coreClassInstance, _getV3coreClass

        if value is None and not self.allow_none:
            raise ValueError(f'Expected an instance of a V3 class; got None')

        elif self._overrideClassCheck:
            pass

        elif self._klass is not None and not isinstance(value, self._klass):
            raise TypeError(f'Expected an instance of {classType(self._klass)}; got {value} {classType(value)}')

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
                    getLogger().warning('Error decoding %r; set to None' % value)
                return result
# end class

#===========================================================================================================
# GWV testing only
#===========================================================================================================

class SpectrumDimensionTrait(List):
    """
    A trait to implement a Spectrum dimensional attribute; e.g. like spectrumFrequencies
    """
    # GWV test
    # _spectrometerFrequencies = SpectrumDimensionTrait(trait=Float(min=0.0)).tag(
    #                            attributeName='spectrometerFrequency',
    #                            doCopy = True
    # )

    isDimensional = True

    def validate(self, obj, value):
        """Validate the value
        """
        if len(value) != obj.dimensionCount:
            raise TraitError('Setting "%s", invalid value "%s"' % (self.name, value))
        value = self.validate_elements(obj, value)
        return value

    def _getValue(self, obj):
        """Get the value of trait, obtained from the obj (i.e.spectrum) dimensions
        """
        if (dimensionAttributeName := self.get_metadata('attributeName', None)) is None:
            raise RuntimeError('Undefined dimensional attributeName for trait %r' % self.name)
        value = [getattr(specDim, dimensionAttributeName) for specDim in obj.spectrumReferences]
        return value

    def get(self, obj, cls=None):
        try:
            value = self._getValue(obj)

        except (AttributeError, ValueError, RuntimeError):
            # Check for a dynamic initializer.
            dynamic_default = self._dynamic_default_callable(obj)
            if dynamic_default is None:
                raise TraitError("No default value found for %s trait of %r"
                                 % (self.name, obj))
            value = self._validate(obj, dynamic_default())
            obj._trait_values[self.name] = value
            return value

        except Exception:
            # This should never be reached.
            raise TraitError('Unexpected error in DimensionTrait')

        else:
            self._obj = obj  # last obj used for get
            return value

    def _setValue(self, obj, value):
        """Set the value of trait, stored in the obj (i.e.spectrum) dimensions
        """
        if (dimensionAttributeName := self.get_metadata('attributeName', None)) is None:
            raise RuntimeError('Undefined dimensional attributeName for trait %r' % self.name)

        for axis, val in enumerate(value):
            setattr(obj.spectrumReferences[axis], dimensionAttributeName, val)

    def set(self, obj, value):

        new_value = self._validate(obj, value)
        try:
            old_value = self._getValue(obj)
        except (AttributeError, ValueError, RuntimeError):
            old_value = self.default_value

        # obj._trait_values[self.name] = new_value
        self._setValue(obj, new_value)

        try:
            silent = bool(old_value == new_value)
        except:
            # if there is an error in comparing, default to notify
            silent = False
        if silent is not True:
            # we explicitly compare silent to True just in case the equality
            # comparison above returns something other than True/False
            obj._notify_trait(self.name, old_value, new_value)
