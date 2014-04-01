"""Constants for versioning
======================COPYRIGHT/LICENSE START==========================

Version.py: code for CCPN data model and code generation framework

Copyright (C) 2005  (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../license/LGPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
 
You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================

"""

import os
# import functools

# Maps ccpncore.lmemops.Version modelVersion to repository location
# Used with function getRepositoryDir below - see there for usage.
#
# 'modelVersion': (repositoryCode', (repository location list)
versionMap = {
 # history versions
 '1.1.a3': ('cvs', ('branch4',) ),
 '2.0.a0': ('cvs', ('branch_2_0_3',) ),
 '2.0.a1': ('cvs', ('stable_2_0_4',) ),
 '2.0.a2': ('cvs', ('stable_2_0_5',) ),
 '2.0.a3': ('cvs', ('stable_2_0_6',) ),
 '2.0.b1': ('cvs', ('stable_2_0_7',) ),
 '2.0.b2': ('cvs', ('stable_2_0_8',) ),
 
 '2.0.4' : ('cvs', ('stable_2_2_0',) ),
 '2.0.b3': ('svn', ('tags', 'test2.2.2_stable_A') ),
 '2.0.5' : ('svn', ('branches', 'model_2_0_5')),  # NB NOT the same as branch model2_0_5 (obsolete)
 '2.0.6' : ('svn', ('branches', 'stable_20131212')),
 '2.1.0' : ('svn', ('tags', 'model_2_1_0') ),
 '2.1.1' : ('svn', ('tags', 'model_2_1_1') ),  # NBNB present only on rhf22 computer. FIXNE!
 #'jmci' : ('svn', ('tags', 'jmci') ),   # Temporary - JMCI python versions
 'merge' : ('svn', ('branches', 'merge_2_1_2')),  # Temporary location for 2.1.2 stable/trunk merge
 
 # Current stable/trunk versions
 's'     : ('svn', ('branches', 'stable',) ),       # stable
 't'     : ('svn', ('trunk',) ),                    # trunk
 #'marc'     : ('svn', ('branches', 'FEmarcvDijk',) ),       # Marc new xml model version
}
# Synonyms for stable/trunk, used by backwards compatibility code
versionMap['2.1.2'] = versionMap['s']
#versionMap['2.1.2'] = versionMap['t']

cvsWorkingDir = 'ccpn'

svnWorkingDir = 'work'

# @functools.total_ordering
class Version(str):

  def __lt__(self, other):

    ll1 = [self.major, self.minor, self.level, self.release]
    try:
      ll2 = self.versionAsList(other)
    except ValueError:
      return str.__lt__(self, other)
    for ll in ll1,ll2:
      # hack to make sure empty leverl comapare last
      ll[2] = ll[2] or '~~~'

    return ll1 < ll2

  def __gt__(self, other):

    return not (self == other or self < other)

  @staticmethod
  def versionAsList(self) -> list:
    """Decompose version string in major,minor,level,release, raise ValueError if incorrect"""

    if ''.join(self.split()) != self:
      raise ValueError("Version string contains whitespace: '%s'" % self)

    ll = self.split('.')
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
    raise ValueError("Version string : %s - format must be e.g. 2.0.5; 31.27.aa33" % self)

  def __ge__(self, other):
    return not self < other


  def __le__(self, other):
    return self == other or self < other


  def __cmp__(self, other):
    return (self > other) - (self < other)

  def getMajor(self) -> int:
    return self.versionAsList()[0]

  major = property(getMajor, None, None,"major version number")

  def getMinor(self) -> int:
    return self.versionAsList()[1]

  minor = property(getMinor, None, None,"minor version number")

  def getLevel(self) -> str:
    return self.versionAsList()[2]

  level = property(getLevel, None, None,"version level (None, 'a', 'b', ...)")


  def getRelease(self) -> int:
    return self.versionAsList()[0]

  relesae = property(getRelease, None, None,"version release number")

  def getDirName(self):
    ll = ['v']
    ll.extend(self.split('.'))
    return '_'.join(ll)

# Current version of data model.
# Used by generation scripts to mark generated code.
# Main way of tracking IO code and IO mappings for compatibility.
# Incremented by hand when model (or I/O generators) changes
currentModelVersion = Version('3.0.a1')





def getRepositoryDir(versionTag, repoTag=None):
  """ Get repository directory. Used for compatibility code generation scripts
  (CompatibilityGen) and optionally for repository navigation scripts.
  Should *NOT* be used in released code, as it makes assumptions about the
  code repository structure.

  Assumes that code trees are rooted in
  for CVS:
   $CVSROOT/extraDirs/ccpn (for model only)
  for SVN:
   $CCPN_SVNROOT/work/extraDirs/ccpn

  extraDirs is one or more directories as given in the versionMap
  """

  progCode, extraDirs = versionMap[versionTag]

  if not repoTag:
    if progCode == 'cvs':
      repoTag = cvsWorkingDir
    else:
      repoTag = svnWorkingDir

  if progCode == 'cvs':
    # get cvs directory
    ll = [os.environ.get('CVSROOT')]
    ll.extend(extraDirs)
    ll.append(repoTag)

  else:
    # get svn directory
    ll = [os.environ.get('CCPN_SVNROOT'), repoTag]
    ll.extend(extraDirs)
    ll.append('ccpn')
  #
  return os.path.join(*ll)



#versionDict = {}
#for key in versionTupleDict.keys():
#  versionDict[key] = Version(name=key, *versionTupleDict[key])
#
#def findVersion(key):
#  """Find version given key."""
#'2.0.6' : ('svn', ('branches', 'stable_20131212')),

#  return versionDict.get(key)

def getVersion(s=None, timestamp = None, name = None):
  """Get version given string representation in form '1.0.b3'.
  Amplified to handle strings of form 1.0b3, 
  for backwards compatibility. Rasmus Fogh 3May04"""
  
  if s:
    (major, minor, level, release) = parseVersionString(s)
    return Version(major, minor, level, release, timestamp=timestamp, name=name)
    
  else:
    # special case - get default version
    result = Version()
    result.timestamp = timestamp
    result.name = name
    #
    return result
