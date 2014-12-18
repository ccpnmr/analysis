"""Functions and constants for data version handling and current data version.

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

# Unfortunately this file must be Python 2.1 compliant


def versionAsList(tag):
  """Decompose version string in major,minor,level,release, raise ValueError if incorrect"""

  if ''.join(tag.split()) != tag:
    raise ValueError("Version string contains whitespace: '%s'" % tag)

  ll = tag.split('.')
  if len(ll) == 3:
    ss = ll[2]
    for startat in range(len(ss)):
      try:
        release = int(ss[startat:])
        level = ss[:startat] or None
        return [int(ll[0]), int(ll[1]), level, release]
      except ValueError:
        continue
  #
  raise ValueError("Invalid version string : %s - format must be e.g. 2.0.5; 31.27.aa33" % tag)


class Version:

  def __init__(self, value):

    # in case a veersion was passed in:
    value = str(value)

    self._value = value

    # Serves as validity check:
    versionAsList(value)

  def __str__(self):
    return str(self._value)

  def __repr__(self):
    return repr(self._value)

  def __lt__(self, other):

    v1 = self._value
    v2 = str(other)

    ll1 = versionAsList(v1)
    try:
      ll2 = versionAsList(v2)
    except ValueError:
      return str.__lt__(v1, v2)
    for ll in ll1,ll2:
      # hack to make sure empty leverl comapare last
      ll[2] = ll[2] or '~~~'

    return ll1 < ll2

  def __gt__(self, other):

    return not (self == other or self < other)

  def __eq__(self, other):
    return self._value == str(other)


  def __ge__(self, other):
    return not self < other


  def __le__(self, other):
    return self == other or self < other


  def __cmp__(self, other):
    return (self > other) - (self < other)

  def getMajor(self):
    return versionAsList(self)[0]


  def getMinor(self):
    return versionAsList(self)[1]


  def getLevel(self):
    return versionAsList(self)[2]


  def getRelease(self):
    return versionAsList(self)[0]

  try:
    major = property(getMajor, None, None,"major version number")
    minor = property(getMinor, None, None,"minor version number")
    level = property(getLevel, None, None,"version level (None, 'a', 'b', ...)")
    release = property(getRelease, None, None,"version release number")
  except:
    # Ignore this if imorted into Python 2.1 (e.g. ObjectDomain)
    pass

  def getDirName(self):
    ll = ['v']
    ll.extend(self._value.split('.'))
    return '_'.join(ll)

# Current version of data model.
# Used by generation scripts to mark generated code.
# Main way of tracking IO code and IO mappings for compatibility.
# Incremented by hand when model (or I/O generators) changes
currentModelVersion = Version('3.0.2')

Version.versionAsList = versionAsList
