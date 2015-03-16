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
""" Create list of handcode
All data are read from and written to a file tree of the structure given by
the code repository.
Default is to use the same file tree as the code is loaded from,
determined as the tree that contains memops.universal.constants.

======================COPYRIGHT/LICENSE START==========================

makeHandCodeList.py: Code generation for CCPN framework

Copyright (C) 2007 Wayne Boucher (CCPN Project)

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

# Utility script for analysing model, getting handcode.

# new machinery imports
from ccpncore.memops.metamodel import XmlModelIo
from ccpncore.memops.metamodel import Util as metaUtil
from ccpncore.memops.metamodel.ModelPortal import ModelPortal

codeStubKeys = ('python', 'java')

stubSeparator = '\n**%s**\n'
constraintSeparator = '\n' + 80 * '*' + '\n\n'

# set qualified names of package to generate from (None means default)
# these seem to work by listing explicitly leaf packages
includePackageNames = None
excludePackageNames = None

# this works by seeing if package starts with these
#excludedPackages = ('ccpnmr', 'molsim', 'utrecht')
excludedPackages = ('molsim', 'utrecht')

dataModelVersion = None    # data model version object (default: current)

outputFile = 'handcodeList.txt'

def outputCodeStubs(fp, elem, codeStubs, name):

  if not codeStubs:
    return

  if name:
    name = '.' + name

  fp.write('%s%s (%s)\n' % (elem.qualifiedName(), name, elem.__class__.__name__))
  for key in codeStubKeys:
    fp.write(stubSeparator % key)
    code = codeStubs.get(key, 'NO CODE SPECIFIED')
    if code[-1] != '\n':
      code += '\n'
    fp.write(code)

  fp.write(constraintSeparator)

def outputConstraints(fp, elem):

  for constraint in elem.constraints:
    outputCodeStubs(fp, elem, constraint.codeStubs, constraint.name)

def main():

  # load model
  topPackage = XmlModelIo.readModel(includePackageNames=includePackageNames,
                                    excludePackageNames=excludePackageNames)

  modelPortal = ModelPortal(topPackage, dataModelVersion=dataModelVersion)

  fp = open(outputFile, 'w')

  packages = modelPortal.leafPackagesAlphabetic()
  for package in packages:
    name = package.qualifiedName()
    for ss in excludedPackages:
      if name == ss or name.startswith(ss+'.'):
        break
    else:
      dataTypes = modelPortal.dataTypesAlphabetic(package)
      for dataType in dataTypes:
        outputConstraints(fp, dataType)

      dataObjTypes = modelPortal.dataObjTypesAlphabetic(package)
      for dataObjType in dataObjTypes:
        outputCodeStubs(fp, dataObjType, dataObjType.constructorCodeStubs, 'constructor')
        outputConstraints(fp, dataObjType)
  
        attributes = metaUtil.sortByMethodCall(dataObjType.attributes, 'qualifiedName')
        for attribute in attributes:
          outputConstraints(fp, attribute)

        operations = metaUtil.sortByMethodCall(dataObjType.operations, 'qualifiedName')
        for operation in operations:
          outputCodeStubs(fp, operation, operation.codeStubs, name='')

      classes = modelPortal.classesAlphabetic(package)
      for clazz in classes:
        outputCodeStubs(fp, clazz, clazz.constructorCodeStubs, 'constructor')
        outputCodeStubs(fp, clazz, clazz.destructorCodeStubs, 'destructor')
        outputConstraints(fp, clazz)

        attributes = metaUtil.sortByMethodCall(clazz.attributes, 'qualifiedName')
        for attribute in attributes:
          outputConstraints(fp, attribute)

        roles = metaUtil.sortByMethodCall(clazz.roles, 'qualifiedName')
        for role in roles:
          outputConstraints(fp, role)

        operations = metaUtil.sortByMethodCall(clazz.operations, 'qualifiedName')
        for operation in operations:
          outputCodeStubs(fp, operation, operation.codeStubs, name='')

  fp.close()

if __name__ == '__main__':

  main()

