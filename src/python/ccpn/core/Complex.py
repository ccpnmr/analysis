"""

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid

class Complex(AbstractWrapperObject):
  """A group of Chains, which can be used as a single object to describe a
  molecular complex.

  NB NOT YET IMPLEMENTED"""

  def __init__(self):
    raise NotImplementedError("The Complex class has not been implemented yet.")

  #: Class name and Short class name, for PID.
  shortClassName = 'MX'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Complex'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'complexes'

  #: List of child classes.
  _childClasses = []

  # # Qualified name of matching API class
  # _apiClassQualifiedName = ApiAtom._metaclass.qualifiedName()
