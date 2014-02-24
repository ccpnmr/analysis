"""
======================COPYRIGHT/LICENSE START==========================

PyUtil.py: Utility code for CCPN code generation framework

Copyright (C) 2005  (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../license/GPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.
 
You should have received a copy of the GNU General Public
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

import os, time

#from memops.general import Implementation

#from memops.general import Util as genUtil

#from memops.metamodel import MetaModel
#MemopsError = MetaModel.MemopsError

#from memops.metamodel import ImpConstants


from ccpncore.memops import Constants as memopsConstants
from ccpncore.memops import Version

from ccpncore.util import Path

apiSubDirs = [memopsConstants.apiCodeDir,]
infinity = memopsConstants.infinity
#apiImpPackageName = '.'.join( [ImpConstants.modellingPackageName] + 
# apiSubDirs + [ImpConstants.implementationPackageName]
#)
#basicDataTypes = genConstants.baseDataTypeModule
# special metaClasses and metaPackages 
#from memops.model.Implementation import package as impPackage
#dataRoot = impPackage.elementDict[ImpConstants.dataRootName]
#normalStorage = impPackage.elementDict[ImpConstants.normalStorageName]
#contentStorage = impPackage.elementDict[ImpConstants.contentStorageName]
#contentStored = impPackage.elementDict[ImpConstants.contentStoredName]
#url = impPackage.elementDict[ImpConstants.urlClassName]


def getImportName(oo, pp=None, subDirs = None):
  """ get name to refer to an object oo from package pp
  If pp is not None the routine will return a short form of the name whenever
  oo is contained within pp.
  Otherwise the routine returns the full  import name.
  NB the function is used also to generate names for documentation.
  Unless oo is an object contained within a package, the result will
  not be valid for the purpose of importing oo.
  """
    
  if ( pp is not None and
   (oo.container is pp)
  ):
    # pp passed in and oo directly available from pp. Return short name
    return oo.name
  
  else:
  
    if subDirs is None:
      subDirs = apiSubDirs

    # no shortcuts - return fully qualified import name
    qname = oo.qualifiedName()
    pathStr = qname.split('.')
    pathStr[1:1] = subDirs
    #
    return '.'.join(pathStr)
    

def recursiveImport(dirname, modname=None, ignoreModules = None, force=False):
  """ recursively import all .py files 
  (not starting with '__' and not containing internal '.' in their name)
  from directory dirname and all its subdirectories, provided they 
  contain '__init__.py'
  Serves to check that files compile without error
  
  modname is the module name (dot-separated) corresponding to the directory
  dirName.
  If modname is None, dirname must be on the pythonPath
  
  Note that there are potential problems if the files we want are not
  the ones encountered first on the pythonPath
  """
  
  listdir = os.listdir(dirname)
  try:
    listdir.remove('__init__.py')
  except:
    if not force:
      return

  files = []
  
  if ignoreModules is None: 
    ignoreModules = []
  
  if modname is None:
    prefix = ''
  else:
    prefix = modname + '.'
  
  listdir2 = []
  for name in listdir:
    head,ext = os.path.splitext(name)
    if (prefix + head) in ignoreModules:
      pass
    elif ext == '.py' and head.find('.') == -1:
      files.append(head)
    else:
      listdir2.append(name)
  
  # import directory and underlying directories
  if modname:
    # Note that files is never empty, so module is lowest level not toplevel
    for ff in files:
      try:
        __import__(modname, {}, {}, [ff])
      except:
        print("WARNING, Import failed for %s.%s" % (modname,ff))
    
  for name in listdir2:
    newdirname = Path.joinPath(dirname,name)
    if os.path.isdir(newdirname) and name.find('.') == -1:
      recursiveImport(newdirname, prefix + name,ignoreModules)


def getVersionString( dataModelVersion=None, releaseVersion=None, 
   scriptName=None, scriptRevision=None, pkgName=None, pkgRevision=None,
   commentStart='', commentEnd=''
  ):

  """
  Function that returns the version header that should be inserted in
  each generated file. Parameters are:
  dataModelVersion - the data model version used 
                    (defaults to memops.general.Constansts.currentModelVersion).
  the name and version number of the current release,
  the name and cvs tag of the generating script,
  the name and revision of the package used as generation source,
  and the starCommentLine and endCommentLine strings.
  """

  versionHeader = """
%(commentStart)s ---------------------------------------------------------------------- %(commentEnd)s
%(commentStart)s %(commentEnd)s%(releaseLine)s
%(commentStart)s CCPN Data Model version %(dataModelVersion)s %(commentEnd)s
%(commentStart)s %(commentEnd)s
%(commentStart)s Autogenerated by %(scriptName)s revision %(scriptRevision)s on %(date)s %(commentEnd)s
%(commentStart)s %(pkgLine)s%(commentEnd)s
%(commentStart)s %(commentEnd)s
%(commentStart)s ---------------------------------------------------------------------- %(commentEnd)s
"""
  
  dd = {
    'scriptName'        : scriptName or '?',
    'scriptRevision'    : scriptRevision or '?',
    'commentStart'      : commentStart,
    'commentEnd'        : commentEnd,
    'date'              : time.ctime(time.time()),
    }
  
  if not dataModelVersion:
    dataModelVersion = Version.currentModelVersion
  dd['dataModelVersion'] = dataModelVersion
  
  if releaseVersion:
    rname = releaseVersion.name or '?'
    dd['releaseLine'] = ("""
%s Release %s version %s%s
%s %s""" %
     (commentStart, rname, releaseVersion, commentEnd, commentStart, commentEnd)
    )
  else:
    dd['releaseLine'] = ''

  if pkgName:
    pkgRevision = pkgRevision or '?'
    dd['pkgLine'] = '              from data model package %s revision %s ' % (pkgName, pkgRevision)
  
  else:
    dd['pkgLine'] = ''
  
  #
  return versionHeader % dd
