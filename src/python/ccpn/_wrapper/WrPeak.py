"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import operator
from typing import Union, List, Optional, Sequence

from ccpn.core.lib import _Implementation
from ccpncore.api.ccp.nmr.Nmr import PeakDim


class WrAbstractWrapperObject:
  """These are functions that should be in the Implementation AbstractWrapperObject.
   I put them here for demo purposes to keep things compact"""

  # Attribute remapping - Must be overridden in subclass
  _attributeNameMap = 'MustBeOverriddenInSubclass'


  @classmethod
  def _ccpnProperty(cls, name, dataType, doc, optional=False, settable=False):
    """Function to make wrapper properties, dispatching exceptions to specific cases.
    Override in subclasses to handle special cases"""

    # When finished with special cases - use the general function
    cls._ccpnSimpleProperty(name, dataType, doc, optional=False, settable=False)

  @classmethod
  def _ccpnKeyProperty(cls, attributeExpression:Union[str,tuple], doc=None) -> property:
    """Make property for _key attribute. Can be overridden in subclasses"""
    ff = operator.attrgetter(attributeExpression)
    if isinstance(attributeExpression, str):
      def getter(self):
        return str(ff(self))
    else:
      def getter(self):
        return '.'.join(str(x) for x in ff(self))
    if not doc:
      doc =  "Key string, distinguishing the %s from its siblings" % cls.className

    return property(getter, None, None, doc)

  @classmethod
  def _ccpnSimpleProperty(cls, name, dataType, doc, optional=False, settable=False):
    """Make simple property, using a known type,
    or the name with or without a class-specific mapping"""

    if name == '_parent':
      # _parent property
      # Parent properties are never optional or settable
      def getter(self) -> dataType:
        return  self.project._data2Obj[self._wrappedData.parent]
      if not doc:
        doc = "%s containing %s" % (dataType.__class__.__name__, cls.__name__)
      return property(getter, None, None, doc)

    elif name == 'comment':
      # Comment properties are always optional and settable
      def getter(self) -> str:
        return  self._wrappedData.details
      def setter(self, value):
        self._wrappedData.details = value
      if not doc:
        doc = "Free-form text comment"
      return property(getter, setter, None, doc)


    else:
      # Standard property
      if optional:
        dataType = Optional[dataType]

      # Find attribute getter expression - remapped if necessary
      attributeExpression = cls._attributeNameMap.get(name, name)
      ff = operator.attrgetter(attributeExpression)
      def getter(self) -> dataType:
        return ff(self._wrappedData)

      if settable:
        if isinstance(attributeExpression, str):
          ll = attributeExpression.rsplit('.',1)
          if len(ll) == 1:
            def setter(self, value):
              setattr(self._wrappedData, ll[0], value)
          else:
            ff = operator.attrgetter(ll[0])
            def setter(self, value):
              setattr(ff(self._wrappedData), ll[1], value)
        else:
          raise ValueError(
            "Invalid attribute expression %s for settable attribute" % attributeExpression)
      else:
        setter = None

      return property(getter, setter, None, doc)

class _PeakPropertyView(_Implementation.AbstractPropertyView):
  """View on per-dimension attributes of the Peak class,
  behaving like a namedtuple with settable items

  Values are in dimension order. The field names are the spectrum axisCodes
  (or '_ii' for axes where the axisCode is None), and are updated if the axisCodes change."""

  @property
  def _fields(self) -> List[Optional[str]]:
    """Field names for List view property"""
    ll = [x.expDim.findFirstExpDimRef(serial=1)
          for x in self._wrappedData.peakList.dataSource.sortedDataDims()]
    return ['_%s' % ii if x is None else x for ii,x in enumerate(ll)]

  @property
  def _dataObjects(self) -> List[PeakDim]:
    """Data-holding implementation objects for List view property"""
    return self._wrappedData.sortedPeakDims()



class WrPeak(WrAbstractWrapperObject):
  """Implementation-level class for Peak"""

  # Map from wrapper-level attributes to API level attributeExpressions
  # The key is the wrapper-level attribute name.
  # The value is an expression that is passed unchanged as input to operator.attrgetter
  # which is then called on self._wrappedData (for simple properties)
  # or the data-holding object (for ListView properties)
  # Specific for the Peak class
  _attributeNameMap = {
    'figureOfMerit':'figOfMerit',
    'position':'value',
    'positionError':'valueError',
    'pointPosition':'position',
    'boxWidths':'boxWidth',
    'lineWidths':'lineWidth',
  }

  @classmethod
  def _ccpnSimpleProperty(cls, name, dataType, doc, optional=False, settable=False):
    """Special case simple properties for the Peak class"""


    if name == 'assignedNmrAtoms':
      # This should return a ListView of tuples of NmrAtoms
      # so that assignments can be modified.
      raise NotImplementedError("Special case - not implemented yet")

    else:
      result = super(WrPeak, cls)._ccpnSimpleProperty(name, dataType, doc,
                                                      optional=optional, settable=settable)

  @classmethod
  def _listViewProperty(cls, name, dataType, doc, optional=False, settable=False) -> property:
    """Make property For list views."""

    if name == 'dimensionNmrAtoms':
      # This should return a ListViewProperty where each element is a ListView
      print('''NotImplementedError("Special case - not implemented yet")''')

    else:
      # Simplest case - handle with generic mechanism

      if settable:
        superclasses = (_PeakPropertyView, _Implementation.MutablePropertyView)
      else:
        superclasses = (_PeakPropertyView,)

      typeName = '%s_%s' % (cls.__name__, name)

      dataTag = cls._attributeNameMap.get(name, name)
      typeDict = {'_dataTag':dataTag, '__slots__':[]}

      ViewClass = type(typeName, superclasses, typeDict)

      if optional:
        dataType = Optional[dataType]

      def getter(self) -> List[dataType]:
        # Lazy evaluation of the property
        result = self.__dict__.get(name)
        if result is None:
          result = ViewClass(self)
          self.__dict__[name] = result
        return result

      def setter(self, value):
        getter(self)[:] = value

      return property(getter, setter, None, doc)

def _newPeak(self:'PeakList',height:Optional[float]=None, volume:Union[float, None]=None,
            figureOfMerit:float=1.0, annotation:str=None, comment:str=None,
            position:Sequence[float]=(), pointPosition:Sequence[float]=(),
            dimensionAssignments:Sequence[Sequence['NmrAtom']]=(),
            assignments:Sequence[Sequence[Optional['NmrAtom']]]=()) -> 'Peak':
  """Create new ccpn.Peak within ccpn.peakList"""
  def __init__(self):
    raise NotImplementedError("Not implemented yet")
