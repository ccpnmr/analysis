"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from ccpncore.lib.pid import Pid
from ccpncore.lib.pid import PREFIXSEP
from ccpncore.lib.pid import IDSEP

@functools.total_ordering
class AbstractWrapperObject(abc.MutableMapping):
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

  # NBNB TBD
  # Two objects compare aa dictionaries (because this is a MutableMapping)
  # and this does noto work properly NBNB Reconsider
  
  
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
      _id = IDSEP.join((parent.id, self._key))
    self.id = _id
    
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
    tt = tag.split(PREFIXSEP)
    if len(tt) == 2:
      # String of form '{prefix}:{pid}'
      dd = project._pid2Obj.get(tt[0])
      if dd:
        # prefix matches a known class name. Child or bust!
        key = tt[1] 
        if IDSEP in key:
          # not a direct child
          raise KeyError(tag)
          
        else:
          # this is then a direct child
          if project is not self:
            key = IDSEP.join((self.id,key))
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
    tt = tag.split(PREFIXSEP)
    if len(tt) == 2:
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
    tt = tag.split(PREFIXSEP)
    if len(tt) == 2:
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
    
    prefix = self.id + IDSEP
    childAttrs = (y for x in self._childClasses
                  for y in self._project._pid2Obj[x.shortClassName]
                  if y.startswith(prefix))
    
    dd = self.__dict__
    extraAttrs = (x for x in sorted(dd)
                  if not x.startswith('_') and len(x.split(PREFIXSEP)) != 2)
    
    #
    return itertools.chain(propertyAttrs, childAttrs, extraAttrs)

    
  def __len__(self):
    """Dictionary implementation method: length"""
    return len(list(self))
    
  
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

  def __hash__(self):
    """Python 2 behaviour - objects equal only to themselves.
    Necessary to avoid dictionary-type behaviour"""
    return hash(id(self))
  
  # CCPN properties 
  @property
  def project(self):
    """Project (root) object."""
    # NB return type is Project. Set in Project.py
    return self._project
  
  @property
  def pid(self) -> str:
    """Object project-wide identifier, unique within project.
    Set automatically from short class name, and id of object and parents."""
    return Pid(PREFIXSEP.join((self.shortClassName, self.id)))
  
  @property
  def longPid(self) -> str:
    """Object project-wide identifier, unique within project.
    Set automatically from full class name, and id of object and parents."""
    return Pid(PREFIXSEP.join((type(self).__name__, self.id)))
    
  
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

    tt = identifier.split(PREFIXSEP)
    if len(tt) == 2:
        dd = self._project._pid2Obj.get(tt[0])
        if dd:
            key = tt[1]
            #
            return dd.get(key)
    #
    return None
    
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
                          ("Type: (*%s*,)\* \n\nsorted %s type child objects" %
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
            key = '%s%s%s' % (self._pid,IDSEP, relativeId)
            # key = IDSEP.join((self._pid,relativeId))
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


AbstractWrapperObject.getById.__annotations__['return'] = AbstractWrapperObject