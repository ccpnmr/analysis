"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from collections import abc
import itertools
import functools

from ccpncore.util import pid
from ccpncore.util import Common as commonUtil


# PROBLEM:
# The Mutable<MAp[p[ing superclass changes the MetaCLass, which causes
# trouble with multiple inheritance with GUI classes.
# To avoid it, we would need to explicitly implement:
# __contains__, keys, items, values, get, __eq__, and __ne__
# pop, popitem, clear, update, and setdefault
# We should already have __getitem__, __setitem__, __delitem__, __iter__, __len__

@functools.total_ordering
class AbstractWrapperObject():
  """Abstract class containing common functionality for wrapper classes.

  ADVANCED. Core programmers only.


  **Rules for subclasses:**
  
  All collection attributes are tuples. For objects these are sorted by pid;
  for simple values they are ordered. 
  
  Non-child collection attributes must have addElement() and removeElement 
  functions as appropriate.
  
  For each child class there will be a newChild factory function, wrapping the
  normal class creator. There will be a collection attribute for each child, 
  grandchild, and generally descendant. We may decide that the relevant
  attribute can be defined as an abstract class, e.g. to have a single 
  restraintLists attribute that includes different classes for distance 
  restraint lists, dihedral restraint lists etc. subclassing an 
  AbstractRestraintList class.
  
  The object id is given as NM:key1.key2.key3 ... where NM is the shortClassName,
  and key1, key2, etc. are the keys of the parent classes starting at the top. 
  The pid is the object id relative to the project; keys relative to objects lower
  in the hierarchy will omit successively more keys.

  Classes behave as dictionaries containing their child objects (NOT grandchildren
  or other descendants), using the relative object id as key. 
  The ID will use the form with full length class names as prefix.
  
  **Example:**

  There will be a link to the Atom class from both the Residue class, the Chain class,
  the Molecule class, and the Project. The relative keys for each object might be:
  
  ===============  =================
  From object:      relative id:
  ===============  =================
  Project           'MA.A.127.N'
  Chain             'MA:127.N'
  Residue           'MA:N'
  ===============  =================


  **Code organisation:**
  
  All code related to a given class lives in the file for the class. 
  On importing it, it will insert relevant functions in the parent class.
  All import must be through the ccpn module, where it is guaranteed that
  all modules are imported in the right order. 
  
  This is organised as a wrapper API, which means that all actual data live 
  in the wrapped data and are derived where needed. All data storage is done
  at the wrapped data, not at the wrapper level, and there is no mechanism for
  storing attributes that have been added at the wrapper level. Key and uniqueness
  checking, type checking etc.  is also done in the wrapped data, not at the 
  wrapper level.
  
  Initialising happens by passing in an NmrProject instance to the Project __init__;
  all wrapper instances are created automatically starting from there. Unless we change this,
  this means we assume that all data can be found by navigating from an
  NmrProject.
  
  New classes can be added, provided they match the requirements. All classes 
  must form a parent-child tree with the root at Project. All classes must
  must have class-level attributes shortClassName, _childClasses, and _pluralLinkName.
  Each class must implement the properties id and _parent, and the methods 
  _getAllWrappedData,  and rename. Note that the
  properties and the _getAllWrappedData function
  must work from the underlying data, as they will be called before the pid
  and object dictionary data are set up. New classes must also set the _apiNotifiers
  data to ensure that objetcs are created adn deleted according to teh wrapped (CCPN API)
  objects
  """

  #: Short class name, for PID. Must be overridden for each subclass
  shortClassName = None


  #: Name of plural link to instances of class
  _pluralLinkName = 'abstractWrapperClasses'

  #: List of child classes. Must be overridden for each subclass.
  _childClasses = []
  
  # limits attributes to those declared.
  # The __dict__ slot allows setting of new attributes, but is instantiated
  # only when necessary.
  #__slots__ = ['_project', '_wrappedData', 'id', '__dict__']

  
  # Implementation methods
  
  def __init__(self, project, wrappedData:object):
   
    # NB project parameter type is Project. Set in Project.py
    
    # NB wrappedData must be globally unique. CCPN objects all are, 
    # but for non-CCPN objects this must be ensured.
    
    # Check if object is already wrapped
    data2Obj = project._data2Obj
    if wrappedData in data2Obj:
      raise ValueError("Cannot create new object for underlying %s: One  already exists"
                       % wrappedData)

    # initialise
    self._project = project
    self._wrappedData = wrappedData
    data2Obj[wrappedData] = self
      
    # set _pid
    parent = self._parent
    if parent is project:
      _id = self._key
    else:
      _id = '%s%s%s'% (parent._id, pid.IDSEP, self._key)
    self._id = _id
    
    # update pid:object mapping dictionary
    className = self.__class__.__name__
    dd = project._pid2Obj.get(className)
    if dd is None:
      dd = {}
      project._pid2Obj[className] = dd 
      project._pid2Obj[self.shortClassName] = dd
    dd[_id] = self
  
  # NBNB TBD we have a loophole
  # Code like setattr(obj, 'Atom:N', value) would still work. 
  # NBNB consider __setattr__ function ???

  # Classes needed to complement abc.MutableMapping mixin abstract class

  def __getitem__(self, tag:str):
    """Dictionary implementation method: get item"""
    
    if not isinstance(tag, str):
      raise KeyError(tag)   
      
    elif tag.startswith('_'):
      # Attributes starting with '_' are not included in the dictionary representation
      raise KeyError(tag)   
    
    elif isinstance(getattr(self.__class__, tag), property):
      # get attribute defined by property
      return getattr(self, tag)
    
    # getting children
    project = self._project
    tt = tag.split(pid.PREFIXSEP, 1)
    if len(tt) == 2:
      # String of form '{prefix}:{pid}'
      dd = project._pid2Obj.get(tt[0])
      if dd:
        # prefix matches a known class name. Child or bust!
        key = tt[1] 
        if pid.IDSEP in key:
          # not a direct child
          raise KeyError(tag)
          
        else:
          # this is then a direct child
          if project is not self:
            key = pid.IDSEP.join((self._id,key))
          #    
          return dd[key]
      else:
        # prefix is not a child type. Treat as error
          raise KeyError("No child named " + tag)
          
    else:
      # get normal attribute
      return self.__dict__[tag]
      
  def __setitem__(self, tag:str, value):
    """Dictionary implementation method: set item"""
    
    if not isinstance(tag, str):
      raise AttributeError(
        "{} can't set non-string attribute: {}".format(
        self.__class__.__name__, tag))
      
    elif tag.startswith('_'):
      # check for implementation attribute
      raise AttributeError(
        "{} can't set attribute starting with '_': {}".format(
        self.__class__.__name__, tag))
    
    # check for child wrapperclass type attribute
    if pid.PREFIXSEP in tag:
      # String of form '{prefix}:{pid}'. Unsettable
      raise AttributeError(
         "{} can't set attribute with name of form 'xy:abcd': {}".
        format(self.__class__.__name__, tag)
      )
    
    else:
      # No exception encountered. Try to set attribute
      setattr(self, tag, value)
      
  def __delitem__(self, tag:str):
    """Dictionary implementation method: delete item"""
    
    if not isinstance(tag, str):
      raise AttributeError(
        "{} can't delete non-string attribute: {}".format(
        self.__class__.__name__, tag))
    
    elif tag.startswith('_'):
      # check for implementation attribute
      raise AttributeError(
        "{} can't delete attribute starting with '_': {}".format(
        self.__class__.__name__, tag))
    
    # check for child wrapperclass type attribute
    if pid.PREFIXSEP in tag:
      # String of form '{prefix}:{pid}' undeletable
      raise AttributeError(
        "{} can't delete attribute of form 'xy:abcd: {}".
        format(self.__class__.__name__, tag)
      )
    
    # No exception encountered. Try to delete attribute
    delattr(self, tag)
  
  def __iter__(self):
    """Dictionary implementation method: iteration"""
    
    cls = self.__class__
    propertyAttrs = (x for x in sorted(dir(cls))
                     if (not x.startswith('_') and  isinstance(getattr(cls,x), property)))
    
    prefix = self._id + pid.IDSEP
    childAttrs = (y for x in self._childClasses
                  for y in self._project._pid2Obj[x.shortClassName]
                  if y.startswith(prefix))
    
    dd = self.__dict__
    extraAttrs = (x for x in sorted(dd)
                  if not x.startswith('_') and pid.PREFIXSEP not in x)
    
    #
    return itertools.chain(propertyAttrs, childAttrs, extraAttrs)

    
  def __len__(self):
    """Dictionary implementation method: length"""
    # return len(list(self))

    # Calling list(self) seems to give an infinite loop, so let us try sounting elements directly

    cls = self.__class__
    prefix = self._id + pid.IDSEP
    dd = self.__dict__
    return (
      len(list(x for x in sorted(dir(cls))
          if (not x.startswith('_') and  isinstance(getattr(cls,x), property))))
      + len(list((y for x in cls._childClasses for y in self._project._pid2Obj[x.shortClassName]
             if y.startswith(prefix))))
      + len(list(x for x in sorted(dd) if not x.startswith('_')
                 and pid.PREFIXSEP not in x)))


  def __bool__(self):
    """Truth value: true - wrapper classes are never empty"""
    return True


  # Classes lifted from collections.abc.MutableMapping inheriting from it causes metaclass clash

  # sentinel
  __marker = object()

  def pop(self, key, default=__marker):
    """D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
      If key is not found, d is returned if given, otherwise KeyError is raised.
    """
    try:
        value = self[key]
    except KeyError:
        if default is self.__marker:
            raise
        return default
    else:
        del self[key]
        return value

  def popitem(self):
    """D.popitem() -> (k, v), remove and return some (key, value) pair
       as a 2-tuple; but raise KeyError if D is empty.
    """
    try:
        key = next(iter(self))
    except StopIteration:
        raise KeyError
    value = self[key]
    del self[key]
    return key, value

  def clear(self):
    """D.clear() -> None.  Remove all items from D."""
    try:
        while True:
            self.popitem()
    except KeyError:
        pass

  def update(*args, **kwds):
    """ D.update([E, ]**F) -> None.  Update D from mapping/iterable E and F.
        If E present and has a .keys() method, does:     for k in E: D[k] = E[k]
        If E present and lacks .keys() method, does:     for (k, v) in E: D[k] = v
        In either case, this is followed by: for k, v in F.items(): D[k] = v
    """
    if len(args) > 2:
        raise TypeError("update() takes at most 2 positional "
                        "arguments ({} given)".format(len(args)))
    elif not args:
        raise TypeError("update() takes at least 1 argument (0 given)")
    self = args[0]
    other = args[1] if len(args) >= 2 else ()

    if isinstance(other, abc.Mapping):
        for key in other:
            self[key] = other[key]
    elif hasattr(other, "keys"):
        for key in other.keys():
            self[key] = other[key]
    else:
        for key, value in other:
            self[key] = value
    for key, value in kwds.items():
        self[key] = value

  def setdefault(self, key, default=None):
    """D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D"""
    try:
        return self[key]
    except KeyError:
        self[key] = default
    return default


  # Functions lifted from collections.abc.MApping

  def get(self, key, default=None):
      """D.get(k[,d]) -> D[k] if k in D, else d.  d defaults to None."""
      try:
          return self[key]
      except KeyError:
          return default

  def __contains__(self, key):
      try:
          self[key]
      except KeyError:
          return False
      else:
          return True

  def keys(self):
      """D.keys() -> a set-like object providing a view on D's keys"""
      return abc.KeysView(self)

  def items(self):
      """D.items() -> a set-like object providing a view on D's items"""
      return abc.ItemsView(self)

  def values(self):
      """D.values() -> an object providing a view on D's values"""
      return abc.ValuesView(self)

  
  # equality: We use the default Python behavior, 
  #           which is that an object is equal only to itself.
  
  # hashing: We use the default Python behavior, 
  
  
  def __lt__(self, other):
    """Ordering implementation function, necessary for making lists sortable.
    """

    selfPid = self.longPid
    otherPid = other.longPid
    if selfPid == otherPid:
      return id(self._project) < id(other._project)
    else:
      return self._project._pidSortKey(selfPid) < other._project._pidSortKey(otherPid)

  def __repr__(self):
    """String representation"""
    return "<ccpn.%s>" % self.longPid

  def __eq__(self, other):
    """Python 2 behaviour - objects equal only to themselves.
    Necessary to avoid dictionary-type behaviour"""
    return self is other

  def __ne__(self, other):
    """Python 2 behaviour - objects equal only to themselves.
    Necessary to avoid dictionary-type behaviour"""
    return self is not other

  def __hash__(self):
    """Python 2 behaviour - objects equal only to themselves.
    Necessary to avoid dictionary-type behaviour"""
    return hash(id(self))
  
  # CCPN properties 
  @property
  def project(self):
    """Project (root) containing object."""
    # NB return type is Project. Set in Project.py
    return self._project
  
  @property
  def pid(self) -> str:
    """Object project-wide identifier, unique within project.
    Set automatically from short class name, and id of object and parents."""
    return pid.Pid(pid.PREFIXSEP.join((self.shortClassName, self._id)))
  
  @property
  def longPid(self) -> str:
    """Object project-wide identifier, unique within project.
    Set automatically from full class name, and id of object and parents."""
    return pid.Pid(pid.PREFIXSEP.join((type(self).__name__, self._id)))
    
  
  # CCPN abstract properties
  
  @property
  def _key(self) -> str:
    """Object local identifier, unique for a given type with a given parent.
    Set automatically from other (immutable) object attributes."""
    raise NotImplementedError("Code error: function not implemented")
  
  @property
  def _parent(self):
    """Parent (containing) object."""
    raise NotImplementedError("Code error: function not implemented")

  @property
  def id(self):
    """Full ID of object."""
    return self._id
  
  # Abstract methods
  @classmethod
  def _getAllWrappedData(cls, parent)-> list:
    """get list of wrapped data objects for each class that is a child of parent
    """
    if cls not in parent._childClasses:
      raise Exception
    raise NotImplementedError("Code error: function not implemented")

  def rename(self, value:str):
    """Change object id, modifying entire project to maintain consistency"""
    raise NotImplementedError("Code error: function not implemented")
  
  # In addition each class (except for Project) must define a  newClass method
  # The function (e.g. Project.newMolecule), ... must create a new child object
  # AND ALL UNDERLYING DATA, taking in all parameters necessary to do so. 
  # This can be done by defining a function (not a method)
  # def newMolecule( self, *args, **kw):
  # and then doing Project.newMolecule = newMolecule

  # CCPN functions

  def delete(self):
    """Delete object, with all children and underlying data.
    
    # NBNB clean-up of wrapper structure is done via notifiers.
    # NBNB some child classes must override this function"""
    
    self._wrappedData.delete()


  def getById(self, identifier: str):
    """Get  object by absolute ID#
    in either long form ('Residue:MS1.A.127') or short form ('MR:MS1.A.127')"""

    tt = identifier.split(pid.PREFIXSEP,1)
    if len(tt) == 2:
      dd = self._project._pid2Obj.get(tt[0])
      if dd:
        return dd.get(tt[1])
    #
    return None

  def getWrapperObject(self, apiObject:object):
    """get wrapper object wrapping apiObject or None"""
    return self._project._data2Obj.get(apiObject)
    
  # CCPN Implementation methods


  @classmethod
  def _linkWrapperClasses(cls, ancestors:list=None):
    """Recursively set up links and functions involving children for wrapper classes"""

    if ancestors:
      # add getCls in all ancestors
      funcName = 'get' + cls.__name__
      for ancestor in ancestors:
        # Add getDescendant function
        def func(self,  relativeId: str) -> cls:
          return cls._getDescendant(self, relativeId)
        func.__doc__= "Get child %s object by relative ID" % cls.__name__
        setattr(ancestor, funcName, func)

      # Add descendant links
      linkName = cls._pluralLinkName
      newAncestors = ancestors + [cls]
      for ii in range(len(newAncestors)-1):
        ancestor = newAncestors[ii]
        prop = property(functools.partial(AbstractWrapperObject._allDescendants,
                                          descendantClasses=newAncestors[ii+1:]),
                          None, None,
                          ("Type: (*%s*,)\*  - sorted %s type child objects" %
                            (cls.__name__, cls.__name__)
                          )
                        )
        setattr(ancestor, linkName, prop)
    else:
      # Project class. Start generation here
      newAncestors = [cls]

    # recursively call next level down the tree
    for cc in cls._childClasses:
      cc._linkWrapperClasses(newAncestors)

  @classmethod
  def _getDescendant(cls, self,  relativeId: str):
    """Get descendant of class cls with relative key relativeId
     Implementation function, used to generate getCls functions"""

    dd = self._project._pid2Obj.get(cls.__name__)
    if dd:
        if self is self._project:
            key = relativeId
        else:
            key = '%s%s%s' % (self._pid,pid.IDSEP, relativeId)
        return dd.get(key)
    else:
      return None

  def _allDescendants(self, descendantClasses):
    """get all descendants of a given class , following descendantClasses down the data tree
    Implementation function, used to generate child and descendant links
    descendantClasses is a list of classes going down from the class of self down the data tree.
    E.g. if called on a chain with descendantClass == [Residue,Atom] the function returns
    a sorted list of all Atoms in a Chain"""
    data2Obj = self._project._data2Obj
    objects = [self]

    for cls in descendantClasses:

      # function gets wrapped data for all children starting from parent
      func = cls._getAllWrappedData
      # data is iterator of wrapped data for children starting from all parents
      data = itertools.chain(*(func(x) for x in objects))
      # objects is all wrapper objects for next child level down
      objects = [data2Obj[x] for x in data]
    #
    return objects

  def _initializeAll(self):
    """Initialize children, using existing objects in data model"""

    project = self._project
    data2Obj = project._data2Obj

    for childClass in self._childClasses:

      # recursively create children
      for apiObj in childClass._getAllWrappedData(self):
        obj = data2Obj.get(apiObj)
        if obj is None:
          if hasattr(childClass, '_factoryFunction'):
            obj = childClass._factoryFunction(project, apiObj)
          else:
            obj = childClass(project, apiObj)
        obj._initializeAll()

  def _unwrapAll(self):
    """remove wrapper from object and child objects
    For special case where wrapper objects are removed without deleting wrappedData"""
    project = self._project
    data2Obj = project._data2Obj

    for childClass in self._childClasses:

      # recursively unwrap children
      for apiObj in childClass._getAllWrappedData(self):
        obj = data2Obj.get(apiObj)
        if obj is not None:
          obj._unwrapAll()
          del self._pid2Obj[obj.shortClassName][obj._pid]
        del data2Obj[apiObj]

  def _setUniqueStringKey(self, apiObj:object, defaultValue:str, keyTag:str='name') -> str:
    """(re)set obj.keyAttr to make it a unique key, using defaultValue if not set
    NB - is called BEFORE data2obj etc. dictionaries are set"""

    wrappedData = self._wrappedData
    if not hasattr (wrappedData,keyTag):
      raise ValueError("Cannot set unique %s for %s: %s object has no attribute %s"
                       % (keyTag, self, wrappedData.__class__, keyTag))

    # Set default value if present value is None
    value = getattr(wrappedData, keyTag)
    if value is None:
      value = defaultValue
      setattr(wrappedData, keyTag, value)

    # Set to new, unique value if present value is a duplicate
    apiObjects = self._getAllWrappedData(self._parent)
    for apiSibling in apiObjects:
      if apiSibling is wrappedData:
        # We have reached the object itself in the list. Enough
        break
      elif getattr(apiSibling, keyTag) == value:
        # Object name is duplicate of earlier object name - make unique name
        print ("@~@~ &s %s %s %s" % (apiObj, apiSibling, value, apiObj.serial))

        # First try appending serial, if possible
        if hasattr(apiObj, 'serial'):
          value = '%s-%s' % (value, apiObj.serial)
        else:
          value = commonUtil.incrementName(value)
        while any(x for x in apiSibling if getattr(x, keyTag) == value):
          value = commonUtil.incrementName(value)
        setattr(self, keyTag, value)
        break

AbstractWrapperObject.getById.__annotations__['return'] = AbstractWrapperObject