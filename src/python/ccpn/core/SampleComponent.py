"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:30 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import typing

from ccpn.core.Project import Project
from ccpn.core.Sample import Sample
from ccpn.core.SpectrumHit import SpectrumHit
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.util import Constants
from ccpn.util.Constants import DEFAULT_LABELLING
from ccpnmodel.ccpncore.api.ccp.lims.Sample import Sample as ApiSample
from ccpnmodel.ccpncore.api.ccp.lims.Sample import SampleComponent as ApiSampleComponent
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, deleteObject, ccpNmrV3CoreSetter, logCommandBlock
from ccpn.util.Logging import getLogger


class SampleComponent(AbstractWrapperObject):
    """ A Samplecomponent indicates a Substance contained in a specific Sample,
    (e.g. protein, buffer, salt), and its  concentrations.

    The Substance referred to is defined by the 'name' and 'labelling' attributes.
    For this reason the SampleComponent cannot be renamed. See Substance."""

    #: Short class name, for PID.
    shortClassName = 'SC'
    # Attribute it necessary as subclasses must use superclass className
    className = 'SampleComponent'

    _parentClass = Sample

    #: Name of plural link to instances of class
    _pluralLinkName = 'sampleComponents'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiSampleComponent._metaclass.qualifiedName()

    # CCPN properties
    @property
    def _apiSampleComponent(self) -> ApiSampleComponent:
        """ API sampleComponent matching SampleComponent"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - name.labelling"""
        obj = self._wrappedData

        name = obj.name
        labelling = obj.labeling
        if labelling == DEFAULT_LABELLING:
            labelling = ''
        return Pid.createId(name, labelling)

    @property
    def _localCcpnSortKey(self) -> typing.Tuple:
        """Local sorting key, in context of parent."""
        obj = self._wrappedData
        labelling = obj.labeling
        return (obj.name, '' if labelling == DEFAULT_LABELLING else labelling)

    @property
    def name(self) -> str:
        """name of SampleComponent and corresponding substance"""
        return self._wrappedData.name

    @property
    def labelling(self) -> str:
        """labelling descriptor of SampleComponent and corresponding substance """
        result = self._wrappedData.labeling
        if result == DEFAULT_LABELLING:
            result = None
        #
        return result

    @property
    def _parent(self) -> Sample:
        """Sample containing SampleComponent."""
        return self._project._data2Obj[self._wrappedData.parent]

    sample = _parent

    @property
    def role(self) -> str:
        """Role of SampleComponent in solvent, e.g. 'solvent', 'buffer', 'target', ..."""
        return self._wrappedData.role

    @role.setter
    def role(self, value: str):
        self._wrappedData.role = value

    @property
    def concentration(self) -> float:
        """SampleComponent.concentration"""
        return self._wrappedData.concentration

    @concentration.setter
    def concentration(self, value: float):
        self._wrappedData.concentration = value

    @property
    def concentrationError(self) -> float:
        """Estimated Standard error of SampleComponent.concentration"""
        return self._wrappedData.concentrationError

    @concentrationError.setter
    def concentrationError(self, value: float):
        self._wrappedData.concentrationError = value

    @property
    def concentrationUnit(self) -> str:
        """Unit of SampleComponent.concentration, one of: 'Molar', 'g/L', 'L/L', 'mol/mol', 'g/g' , 'eq' """

        result = self._wrappedData.concentrationUnit
        # if result is not None and result not in Constants.concentrationUnits:
        #   self._project._logger.warning(
        #     "Unsupported stored value %s for SampleComponent.concentrationUnit"
        #     % result)
        #
        return result

    @concentrationUnit.setter
    def concentrationUnit(self, value: str):
        # if value not in Constants.concentrationUnits:
        #   self._project._logger.warning(
        #     "Setting unsupported value %s for SampleComponent.concentrationUnit."
        #     % value)
        self._wrappedData.concentrationUnit = value

    @property
    def purity(self) -> float:
        """SampleComponent.purity on a scale between 0 and 1"""
        return self._wrappedData.purity

    @purity.setter
    def purity(self, value: float):
        self._wrappedData.purity = value

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

    @property
    def spectrumHits(self) -> typing.Tuple[SpectrumHit, ...]:
        """ccpn.SpectrumHits found for SampleComponent"""
        ff = self._project._data2Obj.get
        return tuple(sorted(ff(x) for x in self._apiSampleComponent.spectrumHits))

    @property
    def isotopeCode2Fraction(self) -> typing.Dict[str, float]:
        """{isotopeCode:fraction} dictionary giving uniform isotope percentages

        isotopeCodes are of the form '12C', '13C', and all relevant isotopes for a given
        nucleus must be entered. Fractions must add up to 1.0 for each element.

        Example value:
        {'12C':0.289, '13C':0.711, '1H':0.99985, '2H':0.00015}

        NBNB the internal dictionary is returned directly without checks or encapsulation"""

        result = self._ccpnInternalData.get('isotopeCode2Fraction')
        #
        return result

    @isotopeCode2Fraction.setter
    def isotopeCode2Fraction(self, value):
        if not isinstance(value, dict):
            raise ValueError("SampleComponent.isotopeCode2Fraction must be a dictionary")
        self._ccpnInternalData['isotopeCode2Fraction'] = value

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: Sample) -> list:
        """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
        return parent._wrappedData.sortedSampleComponents()

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================


def getter(self: SpectrumHit) -> SampleComponent:
    return self._project._data2Obj.get(self._apiSpectrumHit.sampleComponent)


SpectrumHit.sampleComponent = property(getter, None, None,
                                       "ccpn.SampleComponent in which ccpn.SpectrumHit is found")
del getter


@newObject(SampleComponent)
def _newSampleComponent(self: Sample, name: str = None, labelling: str = None, role: str = None,  # ejb
                        concentration: float = None, concentrationError: float = None,
                        concentrationUnit: str = None, purity: float = None, comment: str = None,
                        serial: int = None) -> SampleComponent:
    """Create new SampleComponent within Sample.

    Automatically creates the corresponding Substance if the name is not already taken.

    See the SampleComponent class for details.

    :param name:
    :param labelling:
    :param role:
    :param concentration:
    :param concentrationError:
    :param concentrationUnit:
    :param purity:
    :param comment:
    :param serial: optional serial number.
    :return: a new SampleComponent instance.
    """

    # Default values for 'new' function, as used for echoing to console
    defaults = collections.OrderedDict(
            (('name', None), ('labelling', None), ('role', None),
             ('concentration', None), ('concentrationError', None), ('concentrationUnit', None),
             ('purity', None), ('comment', None),
             )
            )

    if not isinstance(name, str):
        raise TypeError("ccpn.SampleComponent name must be a string")
    elif not name:
        raise ValueError("ccpn.SampleComponent name must be set")
    elif Pid.altCharacter in name:
        raise ValueError("Character %s not allowed in ccpn.SampleComponent id: %s.%s" %
                         (Pid.altCharacter, name, labelling))

    if labelling is not None:  # 'None' caught by below as default
        if not isinstance(labelling, str):
            raise TypeError("ccpn.SampleComponent 'labelling' name must be a string")
        elif not labelling:
            raise ValueError("ccpn.SampleComponent 'labelling' name must be set")
        elif Pid.altCharacter in labelling:
            raise ValueError("Character %s not allowed in ccpn.SampleComponent labelling, id: %s.%s" %
                             (Pid.altCharacter, name, labelling))

    if concentrationUnit is not None and concentrationUnit not in Constants.concentrationUnits:
        self._project._logger.warning(
                "Unsupported value %s for SampleComponent.concentrationUnit"
                % concentrationUnit)
        raise ValueError("SampleComponent.concentrationUnit must be in the list: %s" % Constants.concentrationUnits)  # ejb

    apiSample = self._wrappedData
    substance = self._project.fetchSubstance(name=name, labelling=labelling)

    # NB - using substance._wrappedData.labelling because we need the API labelling value,
    # which is different for the default case
    obj = apiSample.newSampleComponent(name=name, labeling=substance._wrappedData.labeling,
                                       concentration=concentration,
                                       concentrationError=concentrationError,
                                       concentrationUnit=concentrationUnit, details=comment,
                                       purity=purity)
    result = self._project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new SampleComponent item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            getLogger().warning("Could not reset serial of %s to %s - keeping original value"
                                % (result, serial))

    return result


#EJB 20181204: moved to Sample
# Sample.newSampleComponent = _newSampleComponent
# del _newSampleComponent

# Notifiers - to notify SampleComponent - SpectrumHit link:
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.append(
        ('_modifiedLink', {'classNames': ('SampleComponent', 'SpectrumHit')}, className, 'setSample'),
        )
className = ApiSample._metaclass.qualifiedName()
Project._apiNotifiers.extend(
        (('_modifiedLink', {'classNames': ('SampleComponent', 'SpectrumHit')}, className,
          'addNmrExperiment'),
         ('_modifiedLink', {'classNames': ('SampleComponent', 'SpectrumHit')}, className,
          'removeNmrExperiment'),
         ('_modifiedLink', {'classNames': ('SampleComponent', 'SpectrumHit')}, className,
          'setNmrExperiments'),
         )
        )
