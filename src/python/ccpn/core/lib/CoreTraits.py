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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-10-11 08:37:28 +0100 (Wed, October 11, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2023-10-10 10:10:10 +0000 (Tue, October 10, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.traits.CcpNmrTraits import Instance, OWTraits, List, Int, Float, Unicode, TraitError


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
