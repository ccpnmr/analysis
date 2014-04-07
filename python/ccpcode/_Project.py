
from ccpcode._AbstractWrapperClass import AbstractWrapperClass
from ccp.api.nmr.Nmr import NmrProject as Ccpn_NmrProject
from memops.general import Implementation as genImpl
from ccp.lib import DataConvertLib


class Project(AbstractWrapperClass):
  """Project (root) object. Corresponds to CCPN: NmrProject"""
  
  # Short class name, for PID.
  shortClassName = 'PR'
  
  # List of child classes. 
  _childClasses = []
  
  # Top level maoing dictionaries:
  # pid to object and ccpnData tp pbject
  #__slots__ = ['_pid2Obj', '_data2Obj']
  
  
  # Implementation methods
  def __init__(self, wrappedData: Ccpn_NmrProject):
    """ Special init for root (Project) object
    """
    
    # set up attributes
    self._project = self
    self._wrappedData = wrappedData
    self._pid = pid = ''
    
    # Notifier tracking dict, {(fullClassname,funcname):func)} 
    # They must be stored to enable us to remove them afterwards
    self._activeNotifiers = {}
    
    # setup object handling dictionaries
    self._data2Obj = {wrappedData:self}
    self._pid2Obj = {}
    
    self._pid2Obj[self.__class__.__name__] =  dd = {}
    self._pid2Obj[self.shortClassName] = dd
    dd[pid] = self
    
    # general residue name to ChemCompIDs tuple Map.
    self.residueName2chemCompIds = DataConvertLib.getStdResNameMap(
      wrappedData.root.sortedChemComps()
    )
    
    self._registerAllNotify()
    
    self._initializeAll()
  
  def _registerAllNotify(self):
    """Register or remove notifiers"""
    classes = [self.__class__]
    for cls in classes:
      # breadth-firts traversal of child class tree
      classes.extend(cls._childClasses)
      
      # get and process notifiers
      for className, funcName, notify in cls._getNotifiers(self):
        
        tt = (className, funcName)
        previousNotify = self._activeNotifiers.get(tt)
        if previousNotify:
          # remove previously set notifier
          genImpl.unregisterNotify(previousNotify, className, funcName)
        
        # set new notifier in list for later removal
        self._activeNotifiers[tt] = notify
        
        # register notifier
        genImpl.unregisterNotify(notify, className, funcName)
  
  def _unregisterAllNotify(self):
    """Register already prepared notifiers"""
    while self._activeNotifiers:
      tt,func = self._activeNotifiers.pop()
      genImpl.unregisterNotify(func, tt[0], tt[1])
  
  def _initializeAll(self):
    """Initialize children, using existing objects in data model"""
 
    project = self._project
    data2Obj = project._data2Obj
 
    for childClass in self._childClasses:
      
      # recursively create chldren
      for wrappedObj in childClass._getAllWrappedData(self):
        newObj = data2Obj.get(wrappedObj)
        if newObj is None:
          newObj = childClass(project, wrappedObj)
        newObj.initializeAll()

  # CCPN properties  
  @property
  def id(self) -> str:
    """Project id: Globally unique identifier (guid)"""
    return self._wrappedData.guid
    
  @property
  def parent(self) -> AbstractWrapperClass:
    """Parent (containing) object."""
    return None
  
  @property
  def name(self) -> str:
    """name of Project"""
    return self._wrappedData.name
  
  @property
  def nmrProject(self) -> Ccpn_NmrProject:
    """CCPN equivalen to object: Nmrproject"""
    return self._wrappedData
    
  @classmethod
  def _getNotifiers(cls, dummy) -> list:
    """Get list of (className,funcName,notifier) tuples"""
    #
    return [(Ccpn_NmrProject.qualifiedName, 'delete', self.delete)]
  
  # Implementation functions
  ##classmethod
  #d#ef _getAllWrappedData(cls, parent: AbstractWrapperClass)-> list:
  #  raise NotImplementedError("Code error: function not implemented")
  #
  #  Not relevant for Project, which has no parent. DELIBERATELY not implemented


# NBNB set function parameter annotations for AbstractBaseClass functions
# MUST be done here to avoid circular import problems
AbstractWrapperClass.__init__.__annotations__['project'] = Project
AbstractWrapperClass.project.fget.__annotations__['return'] = Project
