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
"""
======================COPYRIGHT/LICENSE START==========================

ApiDocGen.py: Code generation for CCPN framework

Copyright (C) 2007 Wayne Boucher (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public
License as published by the Free Software Foundation; either
version 2 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../license/GPL.license
 
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

import os
import string

from ccpncore.memops.metamodel import MetaModel
from ccpncore.memops.metamodel.ModelTraverse import ModelTraverse
from ccpncore.memops.metamodel import OpTypes
from ccpncore.memops.metamodel import Util as metaUtil
from ccpncore.memops.metamodel import Constants as metaConstants
from ccpncore.memops.license import data as licenseData
from ccpncore.util import Path as Path
from ccpncore.memops.license import headers
from ccpncore.memops.metamodel import TextWriter
from ccpncore.memops.scripts.docgen.Documentation import Documentation


infinity = metaConstants.infinity
MemopsError = MetaModel.MemopsError

mandatoryAttributes = ('apiName', 'baseDirName', 'fileSuffix', 'scriptName')

attrOpTypes = ['get', 'set', 'sorted', 'add', 'remove', 'findFirst', 'findAll']
classOpTypes = ['fullDelete', 'fullUnDelete', 'checkValid', 'checkAllValid', 'getByKey',
                'getFullKey', 'getLocalKey', 'getAttr', 'setAttr', 'clone']
newOpTypes = ['new']
otherOpTypes = ['otherQuery', 'otherModify', 'otherCreate', 'otherDelete', 
                'other']
ignoreOpTypes = ['init', 'checkDelete', 'singleDelete', 'singleUnDelete']

# check that not missing something and that do not have any extra
usedOpTypes = list(attrOpTypes + classOpTypes + newOpTypes + otherOpTypes + ignoreOpTypes)
usedOpTypes.sort()
allOpTypes = list(OpTypes.operationData.keys())
allOpTypes.sort()
if usedOpTypes != allOpTypes:
  raise Exception('allOpTypes = %s, usedOpTypes = %s' % (allOpTypes, usedOpTypes))

# pkgGroup* stuff is for diagrams
pkgGroupData = {
 'core':{'htmlClass':'',
  'homeTitle'
  :'Core packages (CCPN)'
 },
 'nmr':{'htmlClass':'nmr',
  'homeTitle':'NMR and related packages (CCPN)'
 },
 'pp':{'htmlClass':'ppdm',
  'homeTitle':'Protein Production packages (EBI/MSD)'
 }
}
pkgGroupOrder = ('pp', 'core', 'nmr')

# Requires other writers also to be implemented in subclass
class ApiDocGen(Documentation, ModelTraverse):
  
  topApiPrefix = 'api'
  classMapPrefix = 'classMap'
  methodMapPrefix = 'methodMap'
  indexPrefix = '_index'
  ###attrRoleDir = 'attributeMap'
  attributeMapPrefix = 'attributeMap'
  imageDir = metaConstants.imageDir
  docDir = metaConstants.docDir
  styleSheetDir = 'doc'
  docSubDirs = ['api','doc']
  modelDocDir = 'model/doc'
  diagImgDir = 'html/diagram'
  diagFileExt = '_Diag.gif'
  detailDiagExt = '-details'
  helpPrefix = 'help'
  licensePrefix = 'license'

  draftDocString = """
DRAFT - backward compatibility of future versions not guaranteed.<br>
"""

  ###########################################################################

  ###########################################################################

  def __init__(self):
    
    settings = TextWriter.settings['html']
    for (tag, val) in settings.items():
      if not hasattr(self, tag):
        setattr(self, tag, val)

    for tag in mandatoryAttributes:
      if not hasattr(self, tag):
        raise MemopsError("ApiDocGen lacks mandatory %s attribute" % tag)

    #self.codeDirName = uniIo.joinPath(genConstants.apiCodeDir, self.docDir)
    self.codeDirName = metaConstants.apiCodeDir
    self.topDocDir = Path.joinPath(self.baseDirName, self.docDir)
    self.baseDirName = Path.joinPath(self.baseDirName, self.docDir)
    self.topApiFile = '%s.%s' % (self.topApiPrefix, self.fileSuffix)
    self.classMapFile = '%s.%s' % (self.classMapPrefix, self.fileSuffix)
    self.methodMapFile = '%s.%s' % (self.methodMapPrefix, self.fileSuffix)
    self.attributeMapFile = '%s.%s' % (self.attributeMapPrefix, self.fileSuffix)
    self.indexFile = '%s.%s' % (self.indexPrefix, self.fileSuffix)

    self.handCodeKey = self.typeCodeKey = self.modelFlavours['language']
    self.impPackage = None

    # init handling
    #super(ApiDocGen, self).__init__()
    Documentation.__init__(self)
    ModelTraverse.__init__(self)
    
    self.diagramOrderedPackages = self.getDiagramOrderedPackages()
    
    # get dictionary of -to-one links and datatype use
    self.valueTypeUse = valueTypeUse = {}
    for pp in self.modelPortal.leafPackagesByImport():
      for cc in self.modelPortal.classesByInheritance(pp):
        # add one-way roles
        for role in cc.roles:
          if role.otherRole is None and not role.isImplicit:
            # one-way link
            valueType = role.valueType
            ll = valueTypeUse.get(valueType)
            if ll is None:
              valueTypeUse[valueType] = [role]
            else:
              ll.append(role)
        
        # add datatype use
        for attr in cc.attributes:
          if not attr.isImplicit:
            valueType = attr.valueType
            ll = valueTypeUse.get(valueType)
            if ll is None:
              valueTypeUse[valueType] = [attr]
            else:
              ll.append(attr)
      
      for cc in self.modelPortal.dataObjTypesByInheritance(pp):
        # add datatype use
        for attr in cc.attributes:
          if not attr.isImplicit:
            valueType = attr.valueType
            ll = valueTypeUse.get(valueType)
            if ll is None:
              valueTypeUse[valueType] = [attr]
            else:
              ll.append(attr)

    # TBD: relies on separator being /
    self.baseDirNames = self.baseDirName.split('/')

  ###########################################################################

  ###########################################################################
  ###
  ### code overriding ModelTraverse
  ###

  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def processBranchPackage(self, package):
    """ processing actions for branch package
    """
    
    packageDirName = self.getObjDocDirName(package)
    #print 'processBranchPackage', package.qualifiedName(), packageDirName
    
    if package in self.modelPortal.twigPackages():
      self.clearOutDir(packageDirName)
    
    self.createDir(packageDirName)
    
    if package.container:
      directory = self.getObjDocDirName(package)
      fileName = Path.joinPath(directory, self.indexPrefix)
    else:
      fileName = Path.joinPath(self.rootDirName, self.topDocDir, self.topApiPrefix)
      self.impPackage = package.getElement(metaConstants.modellingPackageName).getElement(metaConstants.implementationPackageName)

    self.openFile(fileName)

    self.writeElementComment(package)

    title = 'CCPN %s' % self.apiName
    if package.container:
      title += ' - %s' % self.getImportName(package)
    (prev, foll) = self.getPrevNextPackages(package)
    self.writeElementHeader(package, title, prev=prev, foll=foll)

    if package.container:
      self.writeBranchPackage(package)
    else:
      self.writeRootPackage(package)

    self.writeObjectFooter(package)

    self.closeFile()

    # write class, attribute, method maps (only do once, for root package)
    if not package.container:

      # write class map
      fileName = Path.joinPath(self.rootDirName, self.topDocDir, self.classMapPrefix)
      self.openFile(fileName)
      title = 'CCPN %s - Class Map' % self.apiName
      self.writeElementHeader(package, title, special='Class Map')
      self.writeClassMap(package)
      self.closeFile()

      # write attribute map
      ##self.writeAttrRoleMap(package)
      fileName = Path.joinPath(self.rootDirName, self.topDocDir, self.attributeMapPrefix)
      self.openFile(fileName)
      title = 'CCPN %s - Attribute Map' % self.apiName
      self.writeElementHeader(package, title, special='Attribute Map')
      self.writeAttributeMap(package)
      self.closeFile()


      # write method map
      fileName = Path.joinPath(self.rootDirName, self.topDocDir, self.methodMapPrefix)
      self.openFile(fileName)
      title = 'CCPN %s - Method Map' % self.apiName
      self.writeElementHeader(package, title, special='Method Map')
      self.writeMethodMap(package)
      self.closeFile()

    # write package diagram documentation
    self.writeDiagramDocumentation(package)

  ###########################################################################

  ###########################################################################

  # overrides ModelTraverse
  def processLeafPackage(self, package):
    """ processing actions for leaf package
    """
    
    fileName = self.getObjDocFileName(package)
    packageDirName = Path.splitPath(fileName)[0]
    #print 'processLeafPackage', package.qualifiedName(), packageDirName
    
    self.createDir(packageDirName)
    
    self.openFile(fileName)

    self.writeElementComment(package)

    title = 'CCPN %s - %s' % (self.apiName, self.getImportName(package))
    (prev, foll) = self.getPrevNextPackages(package)
    self.writeElementHeader(package, title, prev=prev, foll=foll)
    self.writeLeafPackage(package)
    self.writeObjectFooter(package)

    self.closeFile()

    # write related files

    elems = package.classes + package.dataObjTypes + package.dataTypes
    elems = metaUtil.sortByAttribute(elems, 'name')
    elems.insert(0, None)
    elems.append(None)

    for ii in range(1, len(elems)-1):
      elem = elems[ii]

      if isinstance(elem,MetaModel.MetaClass):
        self.writeClassDocumentation(elem,elems[ii-1],elems[ii+1])
      elif isinstance(elem,MetaModel.MetaDataObjType):
        self.writeDataObjTypeDocumentation(elem,elems[ii-1],elems[ii+1])
      elif isinstance(elem,MetaModel.MetaDataType):
        self.writeDataTypeDocumentation(elem,elems[ii-1],elems[ii+1])
      else:
        raise MemopsError("Illegal type object found : %s" % elem)

    # write package diagram documentation
    self.writeDiagramDocumentation(package)

  ###########################################################################

  ###########################################################################
  ###
  ### internal code
  ###
  ###########################################################################

  ###########################################################################

  def writeRootPackage(self, root):
    """ write code for Root package
    """

    topPath = self.pathToTop(root)

    self.writeStartSection(cellpadding=5, width='100%')

    self.writeHeading('%s Documentation' % self.apiName, level=1)

    self.writePageDocString(root)

    self.writeBreak()
    self.writeStartTable(cellpadding=2, cellspacing=2)
    self.writeStartRow(valign='top')
    self.writeCell('See Also:')
    self.writeNonBreakingSpaces(4)
    self.writeStartCell()
    self.writeLink('%s/%s/%s' % (topPath, self.modelDocDir, self.indexFile), 'Documentation', target='blank')
    self.write('for Data Model')
    self.writeBreak()
    self.writeLink('%s/doc/quickguide.html' % topPath, 'Quick Guide', target='blank')
    self.write('to CCP software')
    self.writeBreak()
    self.writeLink('%s/doc/api-description.html' % topPath, 'Overview', target='blank')
    self.write('of %s' % self.apiName)
    self.writeEndCell()
    self.writeEndRow()
    self.writeEndTable()
    self.writeBreak()

    self.writeHeading('Directly Contained packages:', level=2)
    self.writeStartTable(_class="elemtable")
    self.writeStartRow()
    self.writeCell('Package', _class='tblhead')
    self.writeCell('Description', _class='tblhead')
    self.writeEndRow()

    directList = metaUtil.sortByAttribute(root.containedPackages, 'name')

    # write directly contained packages
    for pp in directList:
      ss = Path.joinPath(topPath, self.fileFromTop(pp))
      tt = self.getLinkString(ss, pp.name)
      doc = self.getElemDocString(pp)
      self.writeStartRow(valign='top')
      self.writeCell(tt, _class='tblrow')
      self.writeCell(doc, _class='tblrow')
      self.writeEndRow()

    self.writeEndTable()
    self.writeBreak()

    self.writeHorizontalLine()

    # write all contained packages
    self.writeBreak()
    self.writeHeading('All Contained packages:', level=2)

    for package in directList:

      self.writeHeading('%s contains:' % package.name, level=3)
          
      self.writeStartTable(cellpadding=2, cellspacing=2, _class="elemtable")
      self.writeStartRow()
      self.writeCell('Package', _class="tblhead")
      self.writeCell('Description', _class="tblhead")
      self.writeEndRow()
  
      ll = metaUtil.sortByAttribute(package.containedPackages, 'name')

      while ll:

        pp = ll.pop()
        ss = Path.joinPath(topPath, self.fileFromTop(pp))
        tt = self.getLinkString(ss, self.getImportName(pp))
        doc = self.getElemDocString(pp)
        self.writeStartRow(valign='top')
        self.writeCell(tt, _class='tblrow')
        self.writeCell(doc, _class='tblrow')
        self.writeEndRow()

        ll.extend(metaUtil.sortByAttribute(pp.containedPackages, 'name'))

      self.writeEndTable()
      self.writeBreak()
    
    self.writeEndSection()
  
    self.writePackageGuid(root)

  ###########################################################################

  ###########################################################################

  def writeClassMap(self, root):

    # determine what should be listed
    allAbstractDataTypes = []
    self.determineAllAbstractDataTypes(root, allAbstractDataTypes)

    # write content page
    self.writeDoubleColPage('Class Map', root, allAbstractDataTypes)

  ###########################################################################

  ###########################################################################

  def writeDoubleColPage(self, heading, root, elems):

    self.writeStartTable(cellpadding=5, width='100%')

    self.writeStartRow()
    self.writeStartCell(colspan=2)

    self.writeHeading(heading, level=1)
    self.writeEndCell()
    self.writeEndRow()

    self.writeStartRow()
    self.writeStartCell(colspan=2)
    self.writeStartTable()
    self.writeStartRow()

    alphabet = string.ascii_uppercase
    for letter in alphabet:
      self.writeCell('%s%s' % (self.getNonBreakingSpaces(),
                               self.getLinkString('#letter%s' % letter, letter)))
    self.writeEndRow()
    self.writeEndTable()
    self.writeEndCell()
    self.writeEndRow()

    topPath = self.pathToTop(root)
    dd = {}

    for elem in elems:
      key = elem.name + '.' + elem.container.qualifiedName()
      if isinstance(elem, MetaModel.MetaOperation) and not self.methodHasOwnPage(elem):
        ee = elem.target
      else:
        ee = elem

      link = Path.joinPath(topPath, self.fileFromTop(ee))
      dd[key] = (link, self.getImportName(elem), elem.name)
    self.writeStartRow(valign='top')
    self.writeStartCell()
    self.writeStartTable()

    keys = list(dd.keys())
    keys.sort()
    i = 0
    imax = len(keys)
    countLetters = {}

    for letter in alphabet:
      countLetters[letter] = 0
      self.writeStartRow()
      ss = self.getStyleString(letter, style='font-weight: bold; foint-size: 12pt')
      ss = '%s%s' % (self.getNonBreakingSpaces(), self.getAnchorLinkString('letter%s' % letter, ss))
      self.writeCell(ss, _class='tblhead', colspan=3)
      self.writeEndRow()

      for key in keys:
        if key[0].upper() == letter:
          countLetters[letter] += 1
          i += 1
          if i == int (imax/2) + 10:
            self.writeEndTable()
            self.writeEndCell()
            self.writeStartCell()
            self.writeStartTable()

            if countLetters[letter] > 1:
              self.writeStartRow()
              ss = self.getStyleString('%s ' % letter, style='font-weight: bold; font-size: 12pt;')
              ss = '%s%s%s' % (self.getNonBreakingSpaces(), ss, 'continued')
              self.writeCell(ss, _class='tblhead', colspan=3)

          (link, longName, shortName) = dd[key]

          self.writeStartRow()
          self.writeCell(self.getNonBreakingSpaces(2))
          self.writeCell(self.getSmallString(longName[:-len(shortName)]), align='right')
          self.writeCell(self.getStyleString(self.getLinkString(link, shortName), style='font-size: 11pt'))
          self.writeEndRow()
          del dd[key]

      self.writeStartRow()
      self.writeCell(self.getNonBreakingSpaces())
      self.writeEndRow()

    ##self.writeStartRow()
    ##ss = self.getStyleString('...', style='font-weight: bold; foint-size: 12pt')
    ##ss = '%s%s' % (self.getNonBreakingSpaces(), ss)
    ##self.writeCell(ss)
    ##self.writeEndRow()

    keys = list(dd.keys())
    keys.sort()
    for key in keys:
      (link, longName, shortName) = dd[key]
      self.writeStartRow()
      self.writeCell(self.getNonBreakingSpaces(2))
      self.writeCell(self.getSmallString(longName[:-len(shortName)]), align='right')
      self.writeCell(self.getStyleString(self.getLinkString(link, shortName), style='font-size: 11pt;'))
      self.writeEndRow()

    self.writeEndTable()
    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeAttributeMap(self, root):

    # determine what should be listed
    allAttrRoles = []
    self.determineAllAttrRoles(root, allAttrRoles)

    # write content page
    self.writeDoubleColPage('Attribute Map', root, allAttrRoles)

  ###########################################################################

  ###########################################################################

  def writeMethodMap(self, root):

    # determine what should be listed
    allMethods = []
    self.determineAllMethods(root, allMethods)

    # write content page
    self.writeDoubleColPage('Method Map', root, allMethods)

  ###########################################################################

  ###########################################################################

  def writeBranchPackage(self, package):
    """ write code for non-Root branch packages
    """

    topPath = self.pathToTop(package)

    self.writeStartSection(cellpadding=5, width='100%')

    # write page heading
    self.writePageHeading(package, 'Package')

    # write package documentation
    self.writePageDocString(package)

    # write directly contained packages

    self.writeStartTable(cellpadding=2, cellspacing=2, _class="elemtable")
    self.writeStartRow()
    self.writeCell('Package', _class='tblhead')
    self.writeCell('Description', _class='tblhead')
    self.writeEndRow()

    directList = metaUtil.sortByAttribute(package.containedPackages, 'name')
    for pp in directList:
      ss = Path.joinPath(topPath, self.fileFromTop(pp))
      tt = self.getLinkString(ss, pp.name)
      doc = self.getElemDocString(pp)
      self.writeStartRow(valign='top')
      self.writeCell(tt, _class='tblrow')
      self.writeCell(doc, _class='tblrow')
      self.writeEndRow()

    self.writeEndTable()

    self.writeEndSection()

    self.writePackageGuid(package)

  ###########################################################################

  ###########################################################################

  def writeLeafPackage(self, package):
    """ write code for leaf packages
    """

    self.writeStartSection(cellpadding=5, width="100%")

    self.writeStartTable(cellpadding=2, cellspacing=2, width="100%")
    self.writeStartRow(valign='top')
    self.writeStartCell()

    # write page heading
    self.writePageHeading(package, 'Package')

    # write package documentation
    self.writePageDocString(package)

    self.writeEndCell()

    self.writeStartCell(width='20%', valign='top', align='right')
    self.writeLink('#Classes', 'Classes')
    self.writeBreak()
    self.writeLink('#Data Types', 'Data Types')
    self.writeBreak()
    self.writeLink('#Data Obj Types', 'Data Obj Types')
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    for (packages, heading) in ((package.importedPackages, 'Imported Packages'),
                      (package.accessedPackages, 'Packages Importing %s' % self.getImportName(package))):
      ll = [self.getLinkInfo(package,pp) for pp in packages]
      self.writeBreak()
      self.writeHeading('%s:' % heading, level=3)
      if ll:
        ll.sort()
        ll2 = []
        for (name, ref) in ll:
          ss = self.getLinkString('%s/%s' % (ref, self.indexFile), name)
          ll2.append(ss)
        cc = ', %s\n' % self.getNonBreakingSpaces()
        self.write(cc.join(ll2))
      else:
        self.write('None')
      self.writeBreak()

    self.writeEndSection()

    classes = metaUtil.sortByAttribute(package.classes, 'name')
    dataObjTypes = metaUtil.sortByAttribute(package.dataObjTypes, 'name')
    dataTypes = metaUtil.sortByAttribute(package.dataTypes, 'name')

    for (elems, heading) in ((classes, 'Classes'),
                             (dataObjTypes, 'Data Obj Types'),
                             (dataTypes, 'Data Types')):

      self.writeStartSection(cellpadding=5, width="100%")

      self.writeBreak()
      self.writeAnchorLink(heading)
      self.writeHeading('%s:' % heading, level=3)
      self.writeStartTable(cellpadding=2, cellspacing=2, _class="elemtable")
      self.writeStartRow()
      if heading == 'Classes':
        ss = 'Class'
      else:
        ss = 'Type'
      self.writeCell(ss, _class='tblhead')
      self.writeCell('Description', _class='tblhead')
      self.writeEndRow()

      if elems:
        for elem in elems:
          self.writeStartRow(valign='top')
          if self.elemHasOwnDirectory(elem):
            link = self.getLinkString('%s/%s' % (elem.name, self.indexFile), elem.name)
          else:
            link = self.getLinkString('%s.%s' % (elem.name, self.fileSuffix), elem.name)
          self.writeCell(link, _class='tblrow')
          doc = self.getElemDocString(elem)
          self.writeCell(doc, _class='tblrow')
          self.writeEndRow()
      else:
        self.writeStartRow()
        self.writeCell('None', colspan=2, _class='tblrow')
        self.writeEndRow()
      self.writeEndTable()

      self.writeEndSection()

    self.writePackageGuid(package)

  ###########################################################################

  ###########################################################################

  def writeRootPackageDiagram(self, package):
    """ write code for diagram for root package
    """

    # make table lists
    lists = {}
    for pkgGroup in pkgGroupOrder:
      lists[pkgGroup] = []

    for pp in self.diagramOrderedPackages:
      if not pp.containedPackages:
        # leaf package
        pkgGroup = pp.taggedValues.get('packageGroup','core')
        lists[pkgGroup].append(pp)

    fileName = self.getDiagramFileName(package, isAbsolute=True)
    pathList = self.getElementPathList(package)
    pathList = pathList[:-1]
    topPath = self.upDir(len(pathList))

    self.openFile(fileName)

    self.writeElementComment(package)

    self.writeDiagramElementHeader(package)

    self.writeStartTable(width="100%")
    self.writeStartRow()

    self.writeDiagramLeftBar(package, topPath)

    self.writeStartCell(valign='top', align='left', width="100%")
    self.writeHeading('Diagram Home', level=3)
    self.writeStartParagraph()

    self.writeStartTable(align='center')
    self.writeStartRow()
    self.writeStartCell(valign='middle')
    self.writeStartTable()
    self.writeStartRow(valign='top')

    for pkgGroup in pkgGroupOrder:
      ll = lists[pkgGroup]
      if ll:
        dd = pkgGroupData[pkgGroup]
        self.writeStartCell()
        self.writeStartDiv(_class='leftbanner')

        self.writeStartTable(width=130, height=60)
        self.writeStartRow()
        self.writeCell(self.getNonBreakingSpaces(), width=1, _class=dd['htmlClass'])
        self.writeCell(dd['homeTitle'], _class='space')
        self.writeEndRow()
        self.writeEndTable()

        self.writeStartTable(width=150)

        for pp in ll:
          pathList = self.getElementPathList(pp)
          pathList = pathList[:-1]
          if pathList:
            dirName = Path.joinPath(*pathList)
          else:
            dirName = ''
          href = Path.joinPath(dirName, '%s.%s' % (pp.name, self.fileSuffix))

          self.writeStartRow()
          self.writeStartCell(_class=pkgGroupData[pkgGroup]['htmlClass'])
          self.writeLink(href, pp.qualifiedName())
          self.writeEndCell()
          self.writeEndRow()

        self.writeEndTable()
        self.writeEndDiv()
        self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()
    self.writeEndCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeEndParagraph()

    self.writeStartParagraph()
    self.write("""
This documentation may not cover all known model packages. Some diagrams may contain
classes from model packages that are not covered in the present documentation. If
so, you should assume that these classes are not relevant to your purpose.
""")
    self.writeEndParagraph()

    self.writeEndCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeObjectFooter(package)

    self.closeFile()

    # extra files
    self.writeDiagramHelp()
    self.writeDiagramLicense()

  ###########################################################################

  ###########################################################################

  def writeBranchPackageDiagram(self, package):
    """ write code for diagram for non-root branch packages
    """

    fileName = self.getDiagramFileName(package, isAbsolute=True)
    pathList = self.getElementPathList(package)
    topPath = self.upDir(len(pathList))
    docDirName = Path.joinPath(self.rootDirName, self.modelDocDir)

    self.openFile(fileName)

    self.writeElementComment(package)

    self.writeDiagramElementHeader(package)

    self.writeStartTable(width="100%")
    self.writeStartRow()

    self.writeDiagramLeftBar(package, topPath)

    self.writeStartCell(valign='top', align='left', width="100%")
    self.writeHeading('Package: %s' % package.qualifiedName(), level=3)
    self.write(self.getElemDocString(package))
    self.writeStartCenter()

    ss = package.taggedValues.get('docDiagramNames')
    if ss:
      diagNames = ss.split()
      for diagName in diagNames:
        diagFile = Path.joinPath(self.diagImgDir, package.qualifiedName().replace('.', '_') + '_' + diagName + self.diagFileExt)
        file = Path.joinPath(docDirName, diagFile)
        if not os.path.isfile(file):
          print("WARNING1: File %s does not exist" % file)
        diagFile = Path.joinPath(topPath, diagFile)
        diagAlt  = package.qualifiedName()
        if diagName[0] == '_':
          diagLegend = diagName[1:]
        else:
          diagLegend = diagName
        self.writeBreak(2)
        self.write(diagLegend)
        self.writeBreak()
        self.write(self.getImageString(src=diagFile, alt=diagAlt, border=0))
        self.writeBreak(2)

    self.writeEndCenter()
    self.writeEndCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeObjectFooter(package)

    self.closeFile()

  ###########################################################################

  ###########################################################################

  def writeLeafPackageDiagram(self, package):
    """ write code for diagram for leaf branch packages
    """

    # get diagram names to generate files from
    diagNameDict = set()
    dd = set([package.name])
    ss = package.taggedValues.get('docDiagramNames')
    n = len(self.detailDiagExt)
    if ss:
      for ss in ss.split():
        diagNameDict.add(ss)
        # strip leading underscore
        ss = ss[1:]
        if ss[-n:] == self.detailDiagExt:
          ss = ss[:-n]
        dd.add(ss)
    diagramTags = list(dd)
    diagramTags.sort()

    # make files
    for tag in diagramTags:
      self.writeLeafPackageTagDiagram(package, tag, diagramTags)

  ###########################################################################

  ###########################################################################

  def writeLeafPackageTagDiagram(self, package, tag, diagramTags):

    pathList = self.getElementPathList(package)
    pathList = pathList[:-1]
    topPath = self.upDir(len(pathList))
    docDirName = Path.joinPath(self.rootDirName, self.modelDocDir)
    dirName = Path.joinPath(docDirName, *pathList)
    pkgName = package.name

    if not os.path.exists(dirName):
      raise MemopsError('Directory "%s" does not exist' % dirName)

    if tag == pkgName:
      name = tag
    else:
      name = pkgName + '_' + tag
    fileName = Path.joinPath(dirName, name)

    self.openFile(fileName)
    self.writeElementComment(package)

    self.writeDiagramElementHeader(package)

    self.writeStartTable(width="100%")
    self.writeStartRow()

    self.writeDiagramLeftBar(package, topPath)

    self.writeStartCell(valign='top', align='left', width="100%")
    self.writeHeading('Package: %s' % package.qualifiedName(), level=3)
    self.write(self.getElemDocString(package))

    # add menu for other diagrams
    if len(diagramTags) > 1:
      self.writeStartParagraph()
      self.writeStartDiv(_class = 'topbanner')
      self.writeStartTable(width='100%', border=0)
      self.writeStartRow(valign='top')
      self.writeStartCell(align='left', valign='bottom')
      self.write('Class diagrams: { ')

      tt = None
      for ss in diagramTags:
        if ss == pkgName:
          name2 = ss
        else:
          name2 = pkgName + '_' + ss
        href = '%s.%s' % (name2, self.fileSuffix)
        if tt:
          self.write(' | ')
        if ss == tag:
          tt = self.getStyleString(ss, _class='underover')
        else:
          tt = ss
        self.writeLink(href, tt)

      self.write('}')
      self.writeEndCell()
      self.writeEndRow()
      self.writeEndTable()
      self.writeEndDiv()
      self.writeEndParagraph()

    self.writeStartCenter()

    # details diagram:
    dDiagFile = Path.joinPath(self.diagImgDir,
     package.qualifiedName().replace('.', '_') + '__' + tag + self.detailDiagExt + self.diagFileExt)
   
    file = Path.joinPath(docDirName, dDiagFile)

    if os.path.isfile(file):
      path = Path.joinPath(topPath, dDiagFile)
      self.writeLink("javascript:wopn('%s')" % path, self.getItalicString('click here to see the detailed diagram'))
    else:
      print('WARNING2: File "%s" does not exist' % file)
   
    # normal diagram
    dDiagFile = Path.joinPath(self.diagImgDir,
     package.qualifiedName().replace('.', '_') + '__' + tag + self.diagFileExt)

    file = Path.joinPath(docDirName, dDiagFile)
    if os.path.isfile(file):
      src = Path.joinPath(topPath, dDiagFile)
      alt = package.qualifiedName() + tag + ' class diagram'
      self.writeBreak()
      self.write(self.getImageString(src=src, alt=alt, border=0))
    else:
      print('WARNING3: File "%s" does not exist' % file)

    self.writeEndCenter()

    self.writeEndCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeObjectFooter(package)

    self.closeFile()
    
  ###########################################################################

  ###########################################################################

  def writeDiagramHelp(self):

    docDirName = Path.joinPath(self.rootDirName, self.modelDocDir)
    fileName = Path.joinPath(docDirName, self.helpPrefix)

    self.openFile(fileName)

    self.writeComment('Help')

    self.writeDiagramElementHeader(special='Help')

    self.writeStartTable(width="100%")
    self.writeStartRow()

    topPath = self.upDir(0)  # HACK for Help and License
    self.writeDiagramLeftBar(topPath=topPath)

    self.writeStartCell(valign='top', align='left', width='100%')
    self.writeDiagramHelpContent()
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    self.writeObjectFooter()

    self.closeFile()

  ###########################################################################

  ###########################################################################

  def writeDiagramLicense(self):

    docDirName = Path.joinPath(self.rootDirName, self.modelDocDir)
    fileName = Path.joinPath(docDirName, self.licensePrefix)

    self.openFile(fileName)

    self.writeComment('License')

    self.writeDiagramElementHeader(special='License')

    self.writeStartTable(width="100%")
    self.writeStartRow()

    topPath = self.upDir(0)  # HACK for Help and License
    self.writeDiagramLeftBar(topPath=topPath)

    self.writeStartCell(valign='top', align='left', width='100%')
    self.writeGnuLicense()
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    self.writeObjectFooter()

    self.closeFile()

  ###########################################################################

  ###########################################################################

  def writeDiagramLeftBar(self, package = None, topPath = ''):
    """ write bar at left for diagram pages
    """

    self.writeStartCell(valign='top')
    self.writeStartDiv(_class='leftbanner')
    self.writeStartTable(width=130)

    firstTime = True
    for pp in self.diagramOrderedPackages:

      if pp.container:
        label = pp.name
      else:
        label = 'Diagram Home'

      if pp is package:
        label = self.getStyleString(label, _class='underover')

      if pp.containedPackages:
        # branch package

        if not firstTime:
          self.writeStartRow(height=10)
          self.writeCell(_class='space')
          self.writeEndRow()

        pathList = self.getElementPathList(pp)
        if not pp.container:
          pathList = pathList[:-1]
        dirname = Path.joinPath(topPath, *pathList)
        href = Path.joinPath(dirname,  self.indexFile)
        self.writeStartRow()
        self.writeCell(self.getLinkString(href, label), colspan=2)
        self.writeEndRow()

      else:
        # leaf package

        pathList = self.getElementPathList(pp)
        pathList = pathList[:-1]
        dirname = Path.joinPath(topPath, *pathList)
        href = Path.joinPath(dirname,  '%s.%s' % (pp.name, self.fileSuffix))

        pkgGroup = pp.taggedValues.get('packageGroup','core')
        ss = pkgGroupData[pkgGroup]['htmlClass']

        self.writeStartRow()
        self.writeCell(self.getNonBreakingSpaces(), _class=ss, width=1)
        self.writeCell(self.getLinkString(href, label))
        self.writeEndRow()

      firstTime = False

    self.writeEndTable()
    self.writeEndDiv()
    self.writeEndCell()
 
  ###########################################################################

  ###########################################################################

  def writePackageGuid(self, package):

    self.writeHorizontalLine()
    self.writeStartSection(cellpadding=5, width="100%")
    self.writeStartTable(cellpadding=2, cellspacing=2)

    self.writeStartRow(valign='top')
    self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Package guid:')))
    self.writeCell('%s%s' % (self.getBreakString(), package.guid))
    self.writeEndRow()

    self.writeEndTable()
    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeClassDocumentation(self, clazz, prev, foll):

    fileName = self.getObjDocFileName(clazz)
    directory = Path.splitPath(fileName)[0]
    self.createDir(directory)

    self.openFile(fileName)

    title = 'CCPN %s Class: %s' % (self.apiName, clazz.name)

    self.writeElementHeader(clazz, title, prev, foll)
    self.writeClass(clazz)
    self.writeObjectFooter(clazz)

    self.closeFile()

    # write related files
    ll = clazz.attributes + clazz.roles
    ll = metaUtil.sortByAttribute(ll, 'name')

    ll.insert(0,None)
    ll.append(None)
    for ii in range(1,len(ll)-1):
      self.writeAttrDocumentation(ll[ii], ll[ii-1], ll[ii+1])

    ll = [ op for op in clazz.operations if self.methodHasOwnPage(op) ]
    ll = metaUtil.sortByAttribute(ll, 'name')

    ll.insert(0,None)
    ll.append(None)
    for ii in range(1,len(ll)-1):
      self.writeMethodDocumentation(ll[ii], ll[ii-1], ll[ii+1])

  ###########################################################################

  ###########################################################################

  def writeDataObjTypeDocumentation(self, dataObjType, prev, foll):

    fileName = self.getObjDocFileName(dataObjType)
    directory = Path.splitPath(fileName)[0]
    self.createDir(directory)

    self.openFile(fileName)

    title = 'CCPN %s Data ObjType: %s' % (self.apiName, dataObjType.name)

    self.writeElementHeader(dataObjType, title, prev, foll)
    self.writeDataObjType(dataObjType)
    self.writeObjectFooter(dataObjType)

    self.closeFile()

    # write related files
    ll = dataObjType.attributes
    ll = metaUtil.sortByAttribute(ll, 'name')

    ll.insert(0,None)
    ll.append(None)
    for ii in range(1,len(ll)-1):
      self.writeAttrDocumentation(ll[ii], ll[ii-1], ll[ii+1])

    ll = [ op for op in dataObjType.operations if self.methodHasOwnPage(op) ]
    ll = metaUtil.sortByAttribute(ll, 'name')

    ll.insert(0,None)
    ll.append(None)
    for ii in range(1,len(ll)-1):
      self.writeMethodDocumentation(ll[ii], ll[ii-1], ll[ii+1])

  ###########################################################################

  ###########################################################################

  def writeDataTypeDocumentation(self, dataType, prev, foll):

    fileName = self.getObjDocFileName(dataType)
    directory = Path.splitPath(fileName)[0]
    self.createDir(directory)

    self.openFile(fileName)

    title = 'CCPN %s Data Type: %s' % (self.apiName, dataType.name)

    self.writeElementHeader(dataType, title, prev, foll)
    self.writeDataType(dataType)
    self.writeObjectFooter(dataType)

    self.closeFile()

  ###########################################################################

  ###########################################################################

  # previously called writeElemDocumentation
  def writeAttrDocumentation(self, elem, prev, foll):

    fileName = self.getObjDocFileName(elem)
    #print 'writeElemDocumentation', elem.qualifiedName(), fileName

    self.openFile(fileName)

    title = 'CCPN %s Attribute: %s' % (self.apiName, self.getImportName(elem))

    ##self.writeElementHeader(elem, title, prev, foll, attributeLetter=elem.name[0].upper())
    self.writeElementHeader(elem, title, prev, foll)
    self.writeAttributePage(elem)
    self.writeObjectFooter(elem.container)

    self.closeFile()

  ###########################################################################

  ###########################################################################

  # previously called writeOpDocumentation
  def writeMethodDocumentation(self, elem, prev, foll):

    fileName = self.getObjDocFileName(elem)
    #print 'writeElemDocumentation', elem.qualifiedName(), fileName

    self.openFile(fileName)

    title = 'CCPN %s Method: %s' % (self.apiName, self.getImportName(elem))

    self.writeElementHeader(elem, title, prev, foll)
    self.writeMethodPage(elem)
    self.writeObjectFooter(elem.container)

    self.closeFile()

  ###########################################################################

  ###########################################################################

  def writeClass(self, clazz):

    self.writeStartSection(cellpadding=5, width="100%")

    self.writeStartTable(cellpadding=2, cellspacing=2, width='100%')
    self.writeStartRow(valign='top')
    self.writeStartCell()

    # write page heading
    self.writePageHeading(clazz, 'Class')

    if clazz.isAbstract:
      self.writeBreak()
      self.writeEmphasisString('Abstract Class')
      self.writeBreak()

    if (self.handCodeKey in clazz.constructorCodeStubs or
       self.handCodeKey in clazz.postConstructorCodeStubs):
      self.writeEmphasisString('The %s constructor includes non-standard actions.' % clazz.name)

    if (self.handCodeKey in clazz.destructorCodeStubs or
       self.handCodeKey in clazz.postDestructorCodeStubs):
      self.writeEmphasisString('The %s destructor includes non-standard actions.' % clazz.name)

    # write class documentation
    self.writePageDocString(clazz)

    self.writeEndCell()

    self.writeStartCell(width='20%', valign='top', align='right')
    self.writeLink('#Attributes', 'Attributes')
    self.writeBreak()
    self.writeLink('#Link Attributes', 'Link Attributes')
    self.writeBreak()
    self.writeLink('#Attribute Methods', 'Attribute Methods')
    self.writeBreak()
    self.writeLink('#Link Attribute Methods', 'Link Attribute Methods')
    self.writeBreak()
    self.writeLink('#Class Methods', 'Class Methods')
    self.writeBreak()
    self.writeLink('#Factory Methods', 'Factory Methods')
    self.writeBreak()
    self.writeLink('#Other Methods', 'Other Methods')
    self.writeBreak()
    self.writeLink('#Appendix', 'Appendix')
    self.writeBreak()
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    self.writeEndSection()
    
    self.writeStartSection(cellpadding=5, width="100%")

    # Inheritance
    self.writeInheritanceDiagram(clazz)

    # Details
    self.writeBreak()
    self.writeHeading('Details:', level=3)
    self.writeStartTable(cellpadding=2, cellspacing=2)

    # Parent
    self.writeStartRow()
    self.writeCell('Parent:')
    self.writeCell(self.getParentString(clazz))
    self.writeEndRow()

    # Main key
    if clazz.keyNames:
      ss = self.getEmphasisString(', '.join(clazz.keyNames))
    else:
      ss = 'n/a'
    self.writeStartRow()
    self.writeCell('Main key:')
    self.writeCell(ss)
    self.writeEndRow()

    # Mandatory Attributes
    mandatoryElements, hasOptionals = self.getMandatoryElements(clazz)
    if mandatoryElements:
      ss = self.getEmphasisString(', '.join(mandatoryElements))
    else:
      ss = 'None'
    self.writeStartRow()
    self.writeCell('Mandatory Attributes:')
    self.writeCell(ss)
    self.writeEndRow()

    # Partitions children
    # for now only if true
    if clazz.partitionsChildren:
      self.writeStartRow()
      self.writeCell('Partitions Children:')
      self.writeCell(str(clazz.partitionsChildren))
      self.writeEndRow()

    # Known Subclasses
    subtypes = clazz.subtypes
    if subtypes:
      ll = [self.getLinkInfo(clazz, x) for x in subtypes]
      ll.sort()
      links = [ self.getLinkString(Path.joinPath(ref, self.indexFile), name) for (name, ref) in ll ]
      ss = ', '.join(links)
    else:
      ss = 'None'
    self.writeStartRow()
    self.writeCell('Known Subclasses:')
    self.writeCell(ss)
    self.writeEndRow()

    # Children
    childRoles = [ role for role in clazz.getAllRoles() if role.hierarchy == metaConstants.child_hierarchy ]
    if childRoles:
      childRoles = metaUtil.sortByAttribute(childRoles, 'name')
      self.writeStartRow(valign='top')
      self.writeCell('Children:')
      self.writeStartCell()
      self.writeStartTable(cellpadding=2, cellspacing=2)
      for childRole in childRoles:
        child = childRole.valueType
        self.writeStartRow()
        self.writeCell('link')
        self.writeCell(self.getEmphasisString(childRole.name))
        (name, ref) = self.getLinkInfo(clazz, child)
        self.writeCell('to%sclass' % self.getNonBreakingSpaces())
        self.writeCell(self.getLinkString(Path.joinPath(ref, self.indexFile), name))
        self.writeEndRow()
      self.writeEndTable()
      self.writeEndCell()
      self.writeEndRow()
    else:
      self.writeStartRow()
      self.writeCell('Children:')
      self.writeCell('None', colspan=4)
      self.writeEndRow()

    # Constructor
    if not clazz.isAbstract:
      self.writeConstructorRows(clazz, mandatoryElements)

    self.writeEndTable()
    self.writeEndSection()

    # Attributes
    self.writeAttributeTable(clazz, 'attrs')

    # Link attributes
    self.writeAttributeTable(clazz, 'links')

    # Methods
    self.writeMethodTables(clazz)

    # Appendix
    self.writeAppendix(clazz)

  ###########################################################################

  ###########################################################################

  def writeDataObjType(self, dataObjType):

    self.writeStartSection(cellpadding=5, width="100%")

    self.writeStartTable(cellpadding=2, cellspacing=2, width='100%')
    self.writeStartRow(valign='top')
    self.writeStartCell()

    # write page heading
    self.writePageHeading(dataObjType, 'Data Obj Type')

    if dataObjType.isAbstract:
      self.writeBreak()
      self.writeEmphasisString('Abstract Data Obj Type')
      self.writeBreak()

    # write data obj type documentation
    self.writePageDocString(dataObjType)

    self.writeEndCell()

    self.writeStartCell(width='20%', valign='top', align='right')
    self.writeLink('#Attributes', 'Attributes')
    self.writeBreak()
    self.writeLink('#Attribute Methods', 'Attribute Methods')
    self.writeBreak()
    self.writeLink('#Class Methods', 'Class Methods')
    self.writeBreak()
    self.writeLink('#Other Methods', 'Other Methods')
    self.writeBreak()
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    self.writeEndSection()

    self.writeStartSection(cellpadding=5, width="100%")

    # Inheritance
    self.writeInheritanceDiagram(dataObjType)

    # Details
    self.writeBreak()
    self.writeHeading('Details:', level=3)
    self.writeStartTable(cellpadding=2, cellspacing=2)

    # isChangeable
    self.writeStartRow()
    self.writeCell('isChangeable:')
    self.writeCell(str(dataObjType.isChangeable))
    self.writeEndRow()

    # Mandatory Attributes
    mandatoryElements, hasOptionals = self.getMandatoryElements(dataObjType)
    if mandatoryElements:
      ss = self.getEmphasisString(', '.join(mandatoryElements))
    else:
      ss = 'None'
    self.writeStartRow()
    self.writeCell('Mandatory Attributes:')
    self.writeCell(ss)
    self.writeEndRow()

    # Known Subtypes
    subtypes = dataObjType.subtypes
    if subtypes:
      ll = [self.getLinkInfo(dataObjType, x) for x in subtypes]
      ll.sort()
      links = [ self.getLinkString(Path.joinPath(ref, self.indexFile), name) for (name, ref) in ll ]
      ss = ', '.join(links)
    else:
      ss = 'None'
    self.writeStartRow()
    self.writeCell('Known Subtypes:')
    self.writeCell(ss)
    self.writeEndRow()

    # Constructor
    if not dataObjType.isAbstract:
      self.writeConstructorRows(dataObjType, mandatoryElements)

    self.writeEndTable()
    self.writeEndSection()

    # Attributes
    self.writeAttributeTable(dataObjType, 'attrs')

    # Methods
    self.writeMethodTables(dataObjType)

    # Appendix
    self.writeAppendix(dataObjType)

    self.writeBreak()
    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeDataType(self, dataType):

    self.writeStartSection(cellpadding=5, width="100%")

    # write page heading
    self.writePageHeading(dataType, 'Data Type')

    typeCode = dataType.typeCodes[self.typeCodeKey]

    self.writeStartTable(cellpadding=2, cellspacing=2)

    self.writeStartRow()
    self.writeCell('Implementation%sType:' % self.getNonBreakingSpaces())
    self.writeCell(typeCode)
    self.writeEndRow()

    package = dataType.container
    supertypes = dataType.supertypes
    if supertypes:
      topPath = self.pathToTop(package)
      ll = []
      for supertype in supertypes:
        if supertype.container is package:
          ss = '%s.%s' % (supertype.name, self.fileSuffix)
        else:
          ss = Path.joinPath(topPath, self.fileFromTop(supertype))
        tt = self.getBreakString() + self.getLinkString(ss, supertype.qualifiedName())
        ll.append(tt)
      if len(ll) == 1:
        ss = ''
      else:
        ss = 's'
      self.writeStartRow()
      self.writeCell('%sSupertype%s:' % (self.getBreakString(), ss))
      self.writeCell('%s%s' % (self.getBreakString(), ', '.join(ll)))
      self.writeEndRow()

    if typeCode == metaConstants.string_code:
      maxlength = dataType.length
      if maxlength is None or maxlength == metaConstants.infinity:
        maxlength = 'unlimited'
      self.writeStartRow()
      self.writeCell('%sMaximum%slength:' % (self.getBreakString(), self.getNonBreakingSpaces()))
      self.writeCell('%s%s' % (self.getBreakString(), maxlength))
      self.writeEndRow()

    if dataType.enumeration:
      if dataType.isOpen:
        ss = 'Open'
        tt = 'Preset'
      else:
        ss = 'Closed'
        tt = 'Permitted'

      self.writeStartRow()
      self.writeCell('%s%s%sEnumeration:' % (self.getBreakString(), ss, self.getNonBreakingSpaces()))
      self.writeCell('%s%s%sValues: %s' % (self.getBreakString(), tt, self.getNonBreakingSpaces(), dataType.enumeration))
      self.writeEndRow()

    constraints = dataType.getAllConstraints()
    if constraints:
      constraints = metaUtil.sortByAttribute(constraints, 'name')
      for constraint in constraints:
        self.writeStartRow(valign='top')
        self.writeCell('%sConstraint%sname:' % (self.getBreakString(), self.getNonBreakingSpaces()))
        self.writeCell('%s%s' % (self.getBreakString(), constraint.name))
        self.writeEndRow()
        self.writeStartRow(valign='top')
        self.writeCell('%s code' % self.handCodeKey, align='right')
        self.writeCell(constraint.codeStubs.get(self.handCodeKey))
        self.writeEndRow()
    else:
      self.writeStartRow()
      self.writeCell('%sConstraints:' % self.getBreakString())
      self.writeCell('%sNone' % self.getBreakString())
      self.writeEndRow()

    self.writeEndTable()

    self.writeBreak()
    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeAttributePage(self, elem):

    self.writeStartSection(cellpadding=5, width="100%")

    if isinstance(elem,MetaModel.MetaAttribute):
      elemType = 'Attribute'
    else:
      elemType = 'Link Attribute'

    self.writePageHeading(elem, elemType)

    if isinstance(elem,MetaModel.MetaRole):
      ll = []
      if elem.isAbstract:
        ll.append('Abstract')

      if elem.hierarchy == metaConstants.parent_hierarchy:
        ll.append("Parent")
      elif elem.hierarchy == metaConstants.child_hierarchy:
        ll.append("Child")

      if ll:
        ll.append('Link')
        self.writeEmphasisString(' '.join(ll))
        self.writeBreak()
        self.writeBreak()

    # write attribute documentation
    self.writePageDocString(elem)

    # write details

    self.writeBreak()
    self.writeStartTable(cellpadding=2, cellspacing=2)

    # guid
    self.writeStartRow()
    self.writeCell('guid:')
    self.writeCell(elem.guid)
    self.writeEndRow()

    valueType = elem.valueType
    haveImplType = False
    if isinstance(valueType, MetaModel.MetaDataType):
      typeCode = valueType.typeCodes[self.typeCodeKey]
      if valueType.name != typeCode:
        haveImplType = True

    # Model Type (or just Type)
    self.writeStartRow()
    if haveImplType:
      tt = 'Model '
    else:
      tt = ''
    self.writeCell('%sType:' % tt)
    self.writeCell(self.getElemTypeString(elem))
    self.writeEndRow()

    # Implementation Type
    if haveImplType:
      self.writeStartRow()
      self.writeCell('Implementation Type:')
      self.writeCell(typeCode)
      self.writeEndRow()

    # multiplicity, changeability, isDerived, isAutomatic, isImplementation, isImplicit, isAbstract, scope
    for (ss, tt) in (('Multiplicity', self.getMultiplicity(elem)),
                     ('Changeability', elem.changeability),
                     ('isDerived', elem.isDerived),
                     ('isAutomatic', elem.isAutomatic),
                     ('isImplementation', elem.isImplementation),
                     ('isImplicit', elem.isImplicit),
                     ('isAbstract', elem.isAbstract),
                     ('Scope', elem.scope)):
      self.writeStartRow()
      self.writeCell('%s:' % ss)
      self.writeCell(str(tt))
      self.writeEndRow()

    # isOrdered, isUnique
    if elem.hicard != 1:
      for (ss, tt) in (('isOrdered', elem.isOrdered),
                       ('isUnique', elem.isUnique)):
        tt = str(tt)
        self.writeStartRow()
        self.writeCell('%s:' % ss)
        self.writeCell(str(tt))
        self.writeEndRow()

    # default value
    if isinstance(elem,MetaModel.MetaAttribute):
      self.writeStartRow()
      self.writeCell('Default Value:')
      if elem.hicard == 1:
        if elem.defaultValue:
          dd = elem.defaultValue[0]
        else:
          dd = 'None'
      else:
        dd = elem.defaultValue
      self.writeCell(self.normaliseString(str(dd)))
      self.writeEndRow()

      constraints = elem.getAllConstraints()
      if constraints:
        constraints = metaUtil.sortByAttribute(constraints, 'name')
        for constraint in constraints:
          self.writeStartRow(valign='top')
          self.writeCell('%sConstraint name:' % self.getBreakString())
          self.writeCell('%s%s' % (self.getBreakString(), constraint.name))
          self.writeEndRow()
          self.writeStartRow(valign='top')
          self.writeCell('%s code' % self.handCodeKey, align='right')
          ss = constraint.codeStubs.get(self.handCodeKey)
          ss = self.normaliseString(ss)
          self.writeCell(ss)
          self.writeEndRow()
      else:
        self.writeStartRow()
        self.writeCell('Constraints:')
        self.writeCell('None')
        self.writeEndRow()

    else: # isinstance(elem,MetaModel.MetaRole)
      if elem.hierarchy != metaConstants.no_hierarchy:
        self.writeStartRow()
        self.writeCell('Object hierarchy:')
        self.writeCell(elem.hierarchy)
        self.writeEndRow()

      otherRole = elem.otherRole
      if otherRole is None:
        self.writeStartRow()
        self.writeCell('Inverse role:')
        self.writeCell('None')
        self.writeEndRow()
      else:
        (name, ref) = self.getLinkInfo(elem.container, otherRole)
        self.writeStartRow()
        self.writeCell('Inverse role:')
        self.writeCell(self.getLinkString('%s.%s' % (ref, self.fileSuffix), name))
        self.writeEndRow()

      constraints = elem.getAllConstraints()
      if constraints:
        constraints = metaUtil.sortByAttribute(constraints, 'name')
        for constraint in constraints:
          self.writeStartRow(valign='top')
          self.writeCell('%sConstraint name:' % self.getBreakString())
          self.writeCell('%s%s' % (self.getBreakString(), constraint.name))
          self.writeEndRow()
          self.writeStartRow(valign='top')
          self.writeCell('%s code' % self.handCodeKey, align='right')
          ss = constraint.codeStubs.get(self.handCodeKey)
          ss = self.normaliseString(ss)
          self.writeCell(ss)
          self.writeEndRow()

        if otherRole is not None and otherRole.getAllConstraints():
          self.writeStartRow()
          self.writeCell('Constraints:')
          self.writeCell('See also Inverse Role')
          self.writeEndRow()

      elif otherRole is not None and otherRole.getAllConstraints():
        self.writeStartRow()
        self.writeCell('Constraints:')
        self.writeCell('See Inverse Role')
        self.writeEndRow()

      else:
        self.writeStartRow()
        self.writeCell('Constraints:')
        self.writeCell('None')
        self.writeEndRow()

    self.writeEndTable()
    self.writeBreak()

    # add tagged values
    items = list(elem.taggedValues.items())
    if items:
      items.sort()
      self.writeStartTable(cellpadding=2, cellspacing=2)
      self.writeStartRow()
      self.writeCell('Tag')
      self.writeCell('Value')
      self.writeEndRow()

      for item in items:
        (tag, value) = item
        self.writeStartRow(valign='top')
        self.writeCell(tag)
        self.writeCell(value)
        self.writeEndRow()

      self.writeEndTable()
      self.writeBreak()

    self.writeEndSection()

    self.writeHorizontalLine()
    self.writeStartSection(cellpadding=5, width="100%")
    self.writeHeading('Methods', level=3)

    self.writeStartTable(cellpadding=2, cellspacing=2, _class='elemtable')

    self.writeStartRow()
    self.writeCell('Method', align='left', _class='tblhead')
    self.writeCell('Return', align='left', _class='tblhead')
    self.writeCell('Parameters', align='left', _class='tblhead')
    self.writeCell('Comment', align='left', _class='tblhead')
    self.writeEndRow()

    nonStdString = self.getStrongString('Non-std.')
    # TBD: below should maybe be Java specific but in current
    # data model no methods end up using this in any case
    classString = self.getStrongString('Static')

    methods = self.getElemMethods(elem)
    for method in methods:
      self.writeStartRow()
      if self.methodHasOwnPage(method):
        (name, ref) = self.getLinkInfo(elem.container, method)
        ss = self.getLinkString('%s.%s' % (ref, self.fileSuffix), self.getFuncname(method))
      else:
        ss = self.getFuncname(method)
      self.writeCell(ss, _class='tblrow')

      # Return
      self.writeCell(self.getMethodReturn(method), _class='tblrow')

      # Parameters
      self.writeCell(self.getMethodParameters(method), _class='tblrow')

      # Comment
      ll = []
      if method.scope == metaConstants.classifier_level:
        ll.append(classString)
      if not method.isImplicit:
        ll.append(nonStdString)

      ss = self.getNonBreakingSpaces()
      ss = ss.join(ll)
      self.writeCell(ss, _class='tblrow')

      self.writeEndRow()

    self.writeEndTable()

    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeMethodPage(self, elem):

    self.writeStartSection(cellpadding=5, width="100%")

    self.writePageHeading(elem, 'Method')

    if elem.isAbstract:
      self.writeBreak()
      self.writeEmphasisString('Abstract Method')
      self.writeBreak()
      self.writeBreak()

    # write operation documentation
    self.writePageDocString(elem)

    # guid, isQuery, isAbstract, scope
    self.writeBreak()
    self.writeStartTable(cellpadding=2, cellspacing=2)
    for ss in ('guid', 'OpType', 'OpSubType', 'isQuery', 'isAbstract', 'Scope'):
      self.writeStartRow()
      self.writeCell('%s:' % ss)
      self.writeCell(str(getattr(elem, metaUtil.lowerFirst(ss))))
      self.writeEndRow()

    # Code
    ss = elem.codeStubs.get(self.handCodeKey)
    ss = self.normaliseString(ss)
    self.writeStartRow()
    self.writeCell('Code:', valign='top')
    self.writeCell(ss, valign='top')
    self.writeEndRow()

    self.writeEndTable()

    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  # previously called writeModellerInfo
  def writeAppendix(self, complexDataType):

    toplinkString = 'Go%sto%sTop' % (self.getNonBreakingSpaces(), self.getNonBreakingSpaces())
    toplinkString = self.getLinkString('#toplink', self.getStyleString(toplinkString, style='font-size:9pt'))

    self.writeHorizontalLine()
    self.writeStartSection(cellpadding=5, width="100%")

    self.writeAnchorLink('Appendix')
    self.writeHeading('Appendix', level=3)

    self.writeStartTable(cellpadding=2, cellspacing=2, width='100%')
    self.writeStartRow(valign='center')
    self.writeCell(toplinkString, align='right')
    self.writeEndRow()
    self.writeEndTable()
 
    self.writeStartTable(cellpadding=2, cellspacing=2)

    # isImplicit, guid
    for ss in ('guid', 'isImplicit'):
      self.writeStartRow(valign='top')
      self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('%s:' % ss)))
      self.writeCell('%s%s' % (self.getBreakString(), getattr(complexDataType, ss)))
      self.writeEndRow()

    # Tagged Values
    taggedValues = complexDataType.taggedValues
    if taggedValues:
      #print 'TAGGED VALUES', complexDataType.qualifiedName()
      keys = list(taggedValues.keys())
      keys.sort()
      for key in keys:
        self.writeStartRow(valign='top')
        self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Tag')))
        self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Value')))
        self.writeEndRow()
        self.writeStartRow(valign='top')
        self.writeCell(key)
        self.writeCell(taggedValues[key])
        self.writeEndRow()
    else:
      self.writeStartRow(valign='top')
      self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Tagged Values:')))
      self.writeCell('%sNone' % self.getBreakString())
      self.writeEndRow()

    # Special constructor code
    ss = (complexDataType.constructorCodeStubs.get(self.handCodeKey, ''))
    if isinstance(complexDataType, MetaModel.MetaClass):
      ss +=  complexDataType.postConstructorCodeStubs.get(self.handCodeKey, '')

    if ss:
      #print 'CONSTRUCTOR', complexDataType.qualifiedName()
      ss = self.normaliseString(ss)
    else:
      ss = 'None'
    self.writeStartRow(valign='top')
    self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Special constructor code:')), valign='top')
    self.writeCell('%s%s' % (self.getBreakString(), ss), valign='top')
    self.writeEndRow()

    # Special destructor code
    if isinstance(complexDataType, MetaModel.MetaClass):
      for tag in ('destructor','postDestructor'):
        ss = getattr(complexDataType, tag + 'CodeStubs').get(self.handCodeKey)
        if ss:
          #print 'DESTRUCTOR', tag, complexDataType.qualifiedName()
          ss = self.normaliseString(ss)
        else:
          ss = 'None'
        self.writeStartRow(valign='top')
        self.writeCell('%s%s' % (self.getBreakString(),
                       self.getStrongString('Special %s code:' % tag)), valign='top')
        self.writeCell('%s%s' % (self.getBreakString(), ss), valign='top')
        self.writeEndRow()

    # Constraints
    constraints = complexDataType.getAllConstraints()
    if constraints:
      #print 'CONSTRAINTS', complexDataType.qualifiedName(), len(constraints)
      constraints = metaUtil.sortByAttribute(constraints, 'name')
      for constraint in constraints:
        self.writeStartRow(valign='top')
        self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Constraint name:')), valign='top')
        self.writeCell('%s%s' % (self.getBreakString(), constraint.name), valign='top')
        self.writeEndRow()
        self.writeStartRow(valign='top')
        self.writeCell(self.getStrongString('Constraint code:'), valign='top')
        ss = constraint.codeStubs.get(self.handCodeKey)
        ss = self.normaliseString(ss)
        self.writeCell(ss, valign='top')
        self.writeEndRow()
    else:
      self.writeStartRow()
      self.writeCell('%s%s' % (self.getBreakString(), self.getStrongString('Constraints:')), valign='top')
      self.writeCell('%sNone' % self.getBreakString(), valign='top')
      self.writeEndRow()
    
    # Added dataType use and inward one-way links
    self.writeStartRow(valign='top')
    if isinstance(complexDataType, MetaModel.MetaClass):
      self.writeCell(self.getStrongString('Known inward one-way links:'), 
                     valign='top')
    else:
      self.writeCell(self.getStrongString('Attributes using DataObjType:'), 
                     valign='top')
    valueTypeUse = self.valueTypeUse.get(complexDataType)
    if valueTypeUse:
      valueTypeUse.sort(key=MetaModel.MetaModelElement.qualifiedName)
      ll = []
      for ee in valueTypeUse:
        (name, ref) = self.getLinkInfo(complexDataType, ee)
        ll.append(self.getLinkString('%s.%s' % (ref, self.fileSuffix), name))
      tt = ',' + self.getNonBreakingSpaces() + '\n'
      self.writeCell(tt.join(ll), valign='top')
    else:
      self.writeCell('None', valign='top')
      self.writeEndRow()
    
    self.writeEndTable()

    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writePageDocString(self, elem):

    doc = self.getElemDocString(elem)
    if doc:
      self.writeBreak()
      self.writeStartIndent()
      self.write(doc)
      self.writeEndIndent()
    #elif isinstance(elem, MetaModel.MetaPackage) or isinstance(elem, MetaModel.MetaClass):
    elif elem.container and elem.container.documentation:
      print("WARNING, %s has no documentation" % elem.qualifiedName())

  ###########################################################################

  ###########################################################################

  def getDiagramFileName(self, elem, isAbsolute):
    """ Get the path for the diagram documentation for given element
    """

    if isAbsolute:
      topPath = self.rootDirName
    else:
      topPath = self.pathToTop(elem)

    # diapackage is needed to establish the ink to Diagram
    diapackage = elem
    while not isinstance(diapackage,MetaModel.MetaPackage):
      diapackage = diapackage.container
  
    if elem.container is None:
      # root package
      diapath = Path.joinPath(topPath,'%s/%s' % (self.modelDocDir, self.indexPrefix))
    elif isinstance(elem,MetaModel.MetaPackage) and elem.containedPackages:
      # branch package
      ll = diapackage.qualifiedName().split('.')
      ll.append(self.indexPrefix)
      diapath = Path.joinPath(topPath,self.modelDocDir,*ll)
    else:
      # leaf package or package content
      ll = diapackage.qualifiedName().split('.')
      diapath = Path.joinPath(topPath,self.modelDocDir, *ll)
  
    return diapath

  ###########################################################################

  ###########################################################################

  ###def writeNavigatorBar(self, elem, prev = None, foll = None, special = None, upDir = 0, attributeLetter = 'A'):
  def writeNavigatorBar(self, elem, prev = None, foll = None, special = None):

    """write javastyle navigator bar
  
    The exact look is adjusted depending on the type of elem.
    prev and foll are objects pointed to by the 'previous' and 'foll'
    links, and should be of appropriate type.
    """
    
    ## upDir is hack to get Attribute Map pages to work
    ##self.writeCommonNavigatorBar(elem, upDir=upDir)
    self.writeCommonNavigatorBar(elem)

    ##topPath = self.pathToTop(elem, upDir=upDir)
    topPath = self.pathToTop(elem)
    diapath = self.getDiagramFileName(elem, isAbsolute=False)
    tt = Path.joinPath(topPath, self.docDir)

    self.writeStartRow()
    self.writeStartCell(align='center')
    self.writeLink('%s.%s' % (diapath, self.fileSuffix), 'Diagram')

    self.writeVerticalBar()

    if special == 'Class Map':
      self.writeStyleString('Class Map', _class='underover')
    else:
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.classMapFile), 'Class Map')

    self.writeVerticalBar()

    if special == 'Attribute Map':
      self.writeStyleString('Attribute Map', _class='underover')
    else:
      ## bit of a hack, assumes that will have something on A page
      ##ff = '%s.%s' % (attributeLetter, self.fileSuffix)
      ##self.writeLink(uniIo.joinPath(topPath, self.topDocDir, self.attrRoleDir, ff), 'Attribute Map')
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.attributeMapFile), 'Attribute Map')

    self.writeVerticalBar()

    if special == 'Method Map':
      self.writeStyleString('Method Map', _class='underover')
    else:
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.methodMapFile), 'Method Map')

    self.writeVerticalBar()

    self.writeLink("javascript:wopn('%s/%s.%s')" % (tt, self.helpPrefix, self.fileSuffix), 'Help')

    self.writeVerticalBar()

    if special == 'License':
      self.writeStyleString('License', _class='underover')
    else:
      self.writeLink("javascript:wopn('%s/%s.%s')" % (tt, self.licensePrefix, self.fileSuffix), 'License')
    self.writeEndCell()
    self.writeEndRow()

    self.writeStartRow(valign='top')
    self.writeStartCell(align='center', valign='bottom')
  
    if elem.container is None:
      # root package
      if special in ('Class Map', 'Attribute Map'):
        self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'Home')
      else:
        self.writeStyleString('Home', _class='underover')
      self.writeVerticalBar()
      self.write('Package')
      self.writeVerticalBar()
      self.write('Class')
      self.writeVerticalBar()
      self.write('Attribute')
      self.writeVerticalBar()
      self.write('Method')
    
    elif isinstance(elem,MetaModel.MetaPackage):
        
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'Home')
      self.writeVerticalBar()
      self.writeStyleString('Package:', _class='underover')
      self.writePrevNextLinks(topPath, prev, foll)
      self.writeVerticalBar()
      self.write('Class')
      self.writeVerticalBar()
      self.write('Attribute')
      self.writeVerticalBar()
      self.write('Method')

    elif isinstance(elem,MetaModel.AbstractDataType):

      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'Home')
      self.writeVerticalBar()
      self.writeLink(Path.joinPath(topPath,self.fileFromTop(elem.container)), 'Package')
      self.writeVerticalBar()
      self.writeStyleString('Class:', _class='underover')
      self.writePrevNextLinks(topPath, prev, foll)
      self.writeVerticalBar()
      self.write('Attribute')
      self.writeVerticalBar()
      self.write('Method')

    elif isinstance(elem,MetaModel.MetaOperation):
        
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'Home')
      self.writeVerticalBar()
      self.writeLink(Path.joinPath(topPath,self.fileFromTop(elem.container.container)), 'Package')
      self.writeVerticalBar()
      self.writeLink(Path.joinPath(topPath,self.fileFromTop(elem.container)), 'Class')
      self.writeVerticalBar()
      self.write('Attribute')
      self.writeVerticalBar()
      self.writeStyleString('Method:', _class='underover')
      self.writePrevNextLinks(topPath, prev, foll)

    else:
      # attribute or role
      self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'Home')
      self.writeVerticalBar()
      self.writeLink(Path.joinPath(topPath,self.fileFromTop(elem.container.container)), 'Package')
      self.writeVerticalBar()
      self.writeLink(Path.joinPath(topPath,self.fileFromTop(elem.container)), 'Class')
      self.writeVerticalBar()
      self.writeStyleString('Attribute:', _class='underover')
      self.writePrevNextLinks(topPath, prev, foll)
      self.writeVerticalBar()
      self.write('Method')
  
    self.writeEndCell()
    self.writeEndRow()

    self.writeStartRow()
    self.writeCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeEndDiv()
    self.writeComment('TOP BANNER END')
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()
  
  ###########################################################################

  ###########################################################################

  def writeDiagramNavigatorBar(self, package = None, special = None):

    """write javastyle navigator bar for diagrams
    """
    
    self.writeCommonNavigatorBar(package, isDiagram=True)

    if package:
      topPath = self.pathToTop(package, isDiagram=True)
    else:
      topPath = self.upDir(2)  # HACK for Help and License

    self.writeStartRow()
    self.writeStartCell(align='center')
    self.writeLink(Path.joinPath(topPath, self.topDocDir, self.topApiFile), 'API Home')
    self.writeVerticalBar()
    self.writeLink(Path.joinPath(topPath, self.topDocDir, self.classMapFile), 'Class Map')

    self.writeVerticalBar()
    tt = Path.joinPath(topPath, self.modelDocDir)
    if special == 'Help':
      self.writeStyleString('Help', _class='underover')
    else:
      self.writeLink('%s/%s.%s' % (tt, self.helpPrefix, self.fileSuffix), 'Help')

    self.writeVerticalBar()
    if special == 'License':
      self.writeStyleString('License', _class='underover')
    else:
      self.writeLink('%s/%s.%s' % (tt, self.licensePrefix, self.fileSuffix), 'License')

    self.writeEndCell()
    self.writeEndRow()

    self.writeStartRow()
    self.writeCell()
    self.writeEndRow()
    self.writeEndTable()

    self.writeEndDiv()
    self.writeComment('TOP BANNER END')
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()
  
  ###########################################################################

  ###########################################################################

  ###def writeCommonNavigatorBar(self, elem = None, isDiagram = False, upDir = 0):
  def writeCommonNavigatorBar(self, elem = None, isDiagram = False):

    ## upDir is hack to get Attribute Map pages to work

    if elem:
      ##topPath = self.pathToTop(elem, isDiagram=isDiagram, upDir=upDir)
      topPath = self.pathToTop(elem, isDiagram=isDiagram)
    else:
      topPath = self.upDir(2)  # HACK for Help and License
  
    dataModelVersion = self.modelPortal.dataModelVersion
    
    self.writeStartTable(height=100, width='100%', bgcolor=self.color1, border=0)
    self.writeStartRow()
    self.writeStartCell()
    src = '%s/CCPN_Logo_200_x.gif'% Path.joinPath(topPath,self.imageDir)
    ss = self.getImageString(src=src, id='toplink', border=0, alt='CCPN')
    self.writeLink('http://www.ccpn.ac.uk/', ss, _class='mainlogo')
    self.writeBreak()
    self.writeNonBreakingSpaces(3)
    self.write('Data Model version %s' % dataModelVersion)
    self.writeEndCell()

    tt = Path.joinPath(topPath, self.docDir)

    self.writeStartCell(width='80%', valign='center')
    self.writeComment('TOP BANNER BEGIN')
    self.writeStartDiv(_class='topbanner')

    self.writeStartTable(width='100%', border=0)
    self.writeStartRow(valign='top')
    self.writeStartCell(width='80%', align='right')
    self.writeLink("javascript:wopn('%s/acknowledgements.html')" % tt, 'Acknowledgements')
    self.writeEndCell()
    self.writeEndRow()

  ###########################################################################

  ###########################################################################

  def writeAttributeTable(self, clazz, kind):

    if kind == 'attrs':
      anchor = 'Attributes'
      elems = clazz.getAllAttributes()
    else:
      anchor = 'Link Attributes'
      elems = clazz.getAllRoles()

    if clazz.container == self.impPackage:
      # only list details for those in same class
      title = anchor
      oneelems = [ e for e in elems if e.container == clazz ]
      inhelems = [ e for e in elems if e.container != clazz ]
    else:
      # only list details for those in same package
      title = anchor + ' (in package)'
      # note: these names not appropriate in this context
      oneelems = [ e for e in elems if e.container.container == clazz.container ]
      inhelems = [ e for e in elems if e.container.container != clazz.container ]

    oneelems = metaUtil.sortByAttribute(oneelems, 'name')
    inhelems = metaUtil.sortByAttribute(inhelems, 'name')

    self.writeHorizontalLine()
    self.writeStartSection(cellpadding=5, width="100%")

    # title

    self.writeStartTable(cellpadding=2, cellspacing=2, width='100%')
    self.writeStartRow(valign='center')

    self.writeStartCell()
    self.writeAnchorLink(anchor)
    self.writeHeading(title, level=3)
    self.writeEndCell()

    tt = 'Go%sto%sTop' % (self.getNonBreakingSpaces(), self.getNonBreakingSpaces())
    self.writeStartCell(align='right')
    self.writeLink('#toplink', self.getStyleString(tt, style='font-size:9pt'))
    self.writeEndCell()

    self.writeEndRow()
    self.writeEndTable()

    # direct attributes

    if oneelems:
      self.writeStartTable(cellpadding=2, cellspacing=2, _class='elemtable')

      self.writeStartRow()
      self.writeCell('Attribute', align='left', _class='tblhead')
      self.writeCell('Type', align='left', _class='tblhead')
      self.writeCell('Multiplicity', align='left', _class='tblhead')
      self.writeCell('Description', align='left', _class='tblhead')
      self.writeEndRow()

      for ee in oneelems:
        if ee.isDerived:
          ss = self.getEmphasisString('Derived.%s' % self.getNonBreakingSpaces())
        elif (isinstance(ee,MetaModel.MetaRole)
            and ee.hierarchy == metaConstants.parent_hierarchy):
          ss = self.getEmphasisString('(Parent link).%s' % self.getNonBreakingSpaces())
        elif (isinstance(ee,MetaModel.MetaRole)
              and ee.hierarchy == metaConstants.child_hierarchy):
          ss = self.getEmphasisString('(Child link).%s' % self.getNonBreakingSpaces())
        else:
          ss = ''
        ss = ss + ee.documentation + ' ' + self.getNonBreakingSpaces()

        (name, ref) = self.getLinkInfo(clazz, ee)
        self.writeStartRow(valign='top')
        self.writeCell(self.getLinkString('%s.%s' % (ref, self.fileSuffix), ee.name), _class='tblrow')
        self.writeCell(self.getElemTypeString(ee), _class='tblrow')
        self.writeCell(self.getMultiplicity(ee), _class='tblrow', align='center')
        self.writeCell(ss, _class='tblrow')
        self.writeEndRow()

      self.writeEndTable()

    else:
      # no own elements. Make empty table
      self.writeStartTable()
      self.writeStartRow()
      self.writeCell('None', valign='top')
      self.writeEndRow()
      self.writeEndTable()

    # handle inherited elements
    self.writeBreak()
    if clazz.container == self.impPackage:
      ss = ''
    else:
      ss = ' (not in package)'
    self.writeStrongString('Inherited Attributes%s: ' % ss)

    if inhelems:
      ll = []
      for ee in inhelems:
        (name, ref) = self.getLinkInfo(clazz, ee)
        ll.append(self.getLinkString('%s.%s' % (ref, self.fileSuffix), ee.name))
      tt = ',' + self.getNonBreakingSpaces() + '\n'
      self.write(tt.join(ll))
    else:
      self.write('None')
    self.writeBreak()

    self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def getClassAttrMethods(self, complexDataType, methods):

    attrMethods = [ method for method in methods if method.opType in attrOpTypes \
                    and isinstance(method.target, MetaModel.MetaAttribute) ]
    self.sortAttrMethods(attrMethods)

    return attrMethods

  ###########################################################################

  ###########################################################################

  def getClassLinkAttrMethods(self, complexDataType, methods):

    if isinstance(complexDataType, MetaModel.MetaClass):
      linkAttrMethods = [ method for method in methods if method.opType in attrOpTypes \
                          and isinstance(method.target, MetaModel.MetaRole) ]
      self.sortAttrMethods(linkAttrMethods)
    else:
      linkAttrMethods = []

    return linkAttrMethods

  ###########################################################################

  ###########################################################################

  def getClassClassMethods(self, complexDataType, methods):

    classMethods = [ method for method in methods if method.opType in classOpTypes ]
    self.sortClassMethods(classMethods)

    return classMethods

  ###########################################################################

  ###########################################################################

  def getClassNewMethods(self, complexDataType, methods):

    if isinstance(complexDataType, MetaModel.MetaClass):
      newMethods = [ method for method in methods if method.opType in newOpTypes ]
      newMethods = metaUtil.sortByAttribute(newMethods, 'name')
    else:
      newMethods = []

    return newMethods

  ###########################################################################

  ###########################################################################

  def getClassOtherMethods(self, complexDataType, methods):

    otherMethods = [ method for method in methods if method.opType in otherOpTypes ]
    otherMethods = metaUtil.sortByAttribute(otherMethods, 'name')

    return otherMethods

  ###########################################################################

  ###########################################################################

  def writeMethodTables(self, complexDataType):

    package = complexDataType.container
 
    if package == self.impPackage:
      methods = complexDataType.operations
      methodString = 'class'
    else:
      methods = complexDataType.getAllOperations()
      methods = [ method for method in methods if method.container.container == package ]
      methodString = 'package'

    toplinkString = 'Go%sto%sTop' % (self.getNonBreakingSpaces(), self.getNonBreakingSpaces())
    toplinkString = self.getLinkString('#toplink', self.getStyleString(toplinkString, style='font-size:9pt'))

    nonStdString = self.getStrongString('non-std.')
    classString = self.getStrongString('static')

    ll = self.getClassPageMethods(complexDataType, methods)

    ncols = 2
    for (kind, methods) in ll:
      haveAttrCol = kind.endswith('Attribute')
      haveCommCol = (kind != 'Factory')

      if haveAttrCol:
        ncols += 2
      if haveCommCol:
        ncols += 1

      self.writeHorizontalLine()
      self.writeStartSection(cellpadding=5, width="100%")

      self.writeAnchorLink('%s Methods' % kind)
      self.writeHeading('%s Methods (in %s)' % (kind, methodString), level=3)

      self.writeStartTable(cellpadding=2, cellspacing=2, width='100%')
      self.writeStartRow(valign='center')
      self.writeCell(toplinkString, align='right')
      self.writeEndRow()
      self.writeEndTable()

      self.writeStartTable(cellpadding=2, cellspacing=2, _class='elemtable')

      self.writeStartRow()
      if haveAttrCol:
        self.writeCell('Attribute', align='left', _class='tblhead')
      self.writeCell('Method', align='left', _class='tblhead')
      self.writeCell('Return', align='left', _class='tblhead')
      self.writeCell('Parameters', align='left', _class='tblhead')
      if haveCommCol:
        self.writeCell('Comment', align='left', _class='tblhead')
      self.writeEndRow()

      if methods:
        target = None
        for n in range(len(methods)):
          method = methods[n]
          self.writeStartRow(valign='top')

          # Attribute
          if haveAttrCol:
            if method.target != target:
              attr = method.target
              (name, ref) = self.getLinkInfo(attr.container, attr)
              ss = self.getLinkString('%s.%s' % (ref, self.fileSuffix), attr.name)
              self.writeCell(ss, _class='tblspecialrow', colspan=ncols)
              self.writeEndRow()
              self.writeStartRow(valign='top')

          # Method
          if haveAttrCol:
            colspan = 2
            align = 'right'
          else:
            colspan = 1
            align = 'left'
          if self.methodHasOwnPage(method):
            (name, ref) = self.getLinkInfo(complexDataType, method)
            ###ss = self.getLinkString('%s.%s' % (ref, self.fileSuffix), method.name)
            ss = self.getLinkString('%s.%s' % (ref, self.fileSuffix), self.getFuncname(method))
          else:
            ###ss = method.name
            ss = self.getFuncname(method)
          self.writeCell(ss, _class='tblrow', align=align, colspan=colspan)

          # Return
          self.writeCell(self.getMethodReturn(method), _class='tblrow')

          # Parameters
          self.writeCell(self.getMethodParameters(method), _class='tblrow')

          # Comment
          if haveCommCol:
            ll = []
            if method.scope == metaConstants.classifier_level:
              ll.append(classString)
            if not method.isImplicit:
              ll.append(nonStdString)
            if kind == 'Other':
              ll.append(self.getElemDocString(method))

            ss = self.getNonBreakingSpaces()
            ss = ss.join(ll)
            self.writeCell(ss, _class='tblrow')

          target = method.target

          self.writeEndRow()

      else:
        self.writeStartRow(valign='top')
        self.writeCell('None')
        self.writeEndRow()
        
      self.writeEndTable()

      self.writeEndSection()

  ###########################################################################

  ###########################################################################

  def writeDiagramDocumentation(self, package):

    if not package.container:
      self.writeRootPackageDiagram(package)
    elif package.containedPackages:
      self.writeBranchPackageDiagram(package)
    else:
      self.writeLeafPackageDiagram(package)

  ###########################################################################

  ###########################################################################

  def writeInheritanceDiagram(self, complexDataType):

    spaceImage = 'whiteBlank.gif'
    vertLine = 'vertLine.gif'
    horizLine = 'horizLine.gif'
    cornerLine = 'cornerLine.gif'

    # get superclasses
    supers = [[complexDataType]]
    supertypes = complexDataType.supertypes
    while supertypes:
      supers.append(supertypes)
      supertypes = supertypes[0].supertypes

    # image dir
    imgPath = Path.joinPath(self.pathToTop(complexDataType), self.imageDir)
    src = '%s/%s' % (imgPath, spaceImage)
    space = self.getImageString(src=src, align='top', border=0)

    # build diagram
    self.writeHeading('Inheritance:', level=3)
    self.writeStartIndent()
    indent = ''

    supertypes = supers.pop()
    while True:
      ll = []
      for supertype in supertypes:
        (name, ref) = self.getLinkInfo (complexDataType, supertype)
        link = Path.joinPath(ref, self.indexFile)
        ss = self.getLinkString(link, self.getImportName(supertype))
        ll.append(ss)
      cc = ' ' + self.getNonBreakingSpaces()
      self.write(cc.join(ll))
      self.writeBreak()

      if not supers:
        break

      tt = indent
      for xx in (vertLine, cornerLine, horizLine, horizLine):
        tt = tt + self.getImageString(src='%s/%s' % (imgPath, xx), align='top', border=0)
        if xx == vertLine:
          tt = tt + self.getBreakString() + indent
      self.write(tt)

      indent += space * 3
      supertypes = supers.pop()

    self.writeEndIndent()

  ###########################################################################

  ###########################################################################

  def writePrevNextLinks(self, topPath, prev, foll):

    strs = []
    for tag,xx in (('prev',prev), ('foll',foll)):
      if xx is None:
        strs.append(tag)
      else:
        link = Path.joinPath(topPath, self.fileFromTop(xx))
        strs.append(self.getLinkString(link, tag))
        
    self.write('{')
    self.write(strs[0])
    self.writeVerticalBar()
    self.write(strs[1])
    self.write('}')

  ###########################################################################

  ###########################################################################

  def writeElementComment(self, elem):

    self.writeComment(self.getVersionString(
      metaobj=elem,
      scriptName=self.scriptName)
    )

  ###########################################################################

  ###########################################################################

  ###def writeElementHeader(self, elem, title, prev=None, foll=None, special = None, upDir = 0, attributeLetter = 'A'):
  def writeElementHeader(self, elem, title, prev=None, foll=None, special = None):

    # upDir is hack to get Attribute Map pages to work

    ##self.writeBasicHeader(elem, title, isDiagram=False, upDir=upDir)
    self.writeBasicHeader(elem, title, isDiagram=False)

    # write navigator bar
    ##self.writeNavigatorBar(elem, prev=prev, foll=foll, special=special, upDir=upDir, attributeLetter=attributeLetter)
    self.writeNavigatorBar(elem, prev=prev, foll=foll, special=special)

  ###########################################################################

  ###########################################################################

  def writeDiagramElementHeader(self, package = None, special = None):

    if special:
      ss = special
    elif package.container:
      ss = package.qualifiedName()
    else:
      ss = 'Home'
    title = 'UML Diagram Doc - %s' % ss

    self.writeBasicHeader(package, title, isDiagram=True)

    # write navigator bar
    self.writeDiagramNavigatorBar(package, special=special)

  ###########################################################################

  ###########################################################################

  def writeBasicHeader(self, elem, title, isDiagram, upDir = 0):

    # upDir is hack to get Attribute Map pages to work

    # TBD: this is now producing the wrong formula so look at again
    if elem:
      # TBD: can dirDepth be done otherwise now?
      dirDepth = 0
      package = elem
      while not isinstance(package, MetaModel.MetaPackage):
        dirDepth += 1
        package = package.container
      dirDepth = dirDepth + len(package.qualifiedName().split('.')) + 3
      if isDiagram:
        dirDepth -= 1
      dirDepth += upDir

      packageGroup = package.taggedValues['packageGroup']
      ss = package.qualifiedName()
    else:
      dirDepth = 2  # HACK for Help and License
      packageGroup = 'core'
      ss = 'n/a'

    dict = licenseData.licenseInfo[packageGroup].copy()
    dict['fileName'] = self.indexFile
    dict['licenseLocation'] = self.upDir(dirDepth) + 'license'
    dict['programType'] = 'API documentation'
    dict['programFunction'] = (
      "%s documentation for CCPN data model, package %s"
      % (self.apiName, ss)
    )
    dict['licenseFileName'] = dict['useLicense']
    if not elem or elem != package:
      dict['useLicense'] = 'brief'
      dict['references'] = ()
      dict['credits'] = None

    # TBD: this affects how many ..'s you get to find stylesheet, so can be seen to be correct or not via that
    if not elem:
      #topPath = self.upDir(2)  # HACK for Help and License
      topPath = self.upDir(1)  # HACK for Help and License
    elif self.elemHasOwnDirectory(elem):
      topPath = self.pathToTop(elem, isDiagram=isDiagram, upDir=upDir)
    else:
      topPath = self.pathToTop(elem.container, isDiagram=isDiagram)

    self.writeHeader(scriptName=self.scriptName,
      headerComment=headers.getHeader(**dict),
      title=title,
      styleSheetDir=Path.joinPath(topPath, self.styleSheetDir))

  ###########################################################################

  ###########################################################################

  def writeObjectFooter(self, obj = None):

    if not obj:
      objName = 'n/a'
    elif obj.container:
      objName = self.getImportName(obj)
    else:
      objName = 'Root'

    self.writeFooter(
      dataModelVersion=self.modelPortal.dataModelVersion,
      releaseVersion=self.releaseVersion, 
      objName=objName, scriptName=self.scriptName,)

  ###########################################################################

  ###########################################################################

  def writePageHeading(self, elem, title):

    name = elem.name
    self.writeHeading('%s: %s' % (title, name), level=2)

    qname = self.getImportName(elem)
    ss = qname[:-(len(name)+1)]
    if isinstance(elem.container, MetaModel.MetaPackage):
      fromstr = 'Package'
      if elem.container is elem.topPackage():
        ss = 'Root'
        # TBD: not sure this works for all implementations
        addr = '../../../%s/%s' % (self.docDir, self.topApiFile)
      elif self.elemHasOwnDirectory(elem):
        addr = '../%s' % self.indexFile
      else:
        addr = self.indexFile
    else:
      fromstr = 'Class'
      addr = self.indexFile

    self.writeStartIndent()
    heading = 'from %s %s' % (fromstr, self.getLinkString(addr, ss))
    self.writeHeading(heading, level=3)
    self.writeEndIndent()

  ###########################################################################

  ###########################################################################

  def sortAttrMethods(self, methods):

    methods.sort(key=lambda method:(method.target.name, method.opType))

  ###########################################################################

  ###########################################################################

  def sortClassMethods(self, methods):

    methods.sort(key=lambda method:method.opType)

  ###########################################################################

  ###########################################################################

  def methodHasOwnPage(self, method):

    return method.codeStubs.get(self.handCodeKey)

  ###########################################################################

  ###########################################################################

  def getMethodReturn(self, method):

    returnPars = [ parameter for parameter in method.parameters if parameter.direction == metaConstants.return_direction ]

    n = len(returnPars)
    assert n in (0, 1), 'method %s has %d return parameters, should be 0 or 1' % (method.qualifiedName(), n)

    if n == 0:
      returnString = ''
    else:
      param = returnPars[0]
      returnString = self.getParamString(param)

    return returnString

  ###########################################################################

  ###########################################################################

  def getMethodParameters(self, method):

    if method.opType == 'new' and not method.opSubType:
      paramsString = self.getNewParamString(method)

    elif method.opType in ('findFirst', 'findAll') and not method.opSubType:
      paramsString = self.getKeywordValueString(method)

    else:
      params = [parameter for parameter in method.parameters
                if parameter.direction != metaConstants.return_direction]
      ll = []
      for param in params:
        paramString = self.getParamString(param)
        ll.append(paramString)
      if ll:
        paramsString = ', '.join(ll)
      else:
        paramsString = '-'

    return paramsString

  ###########################################################################

  ###########################################################################

  def determineAllAbstractDataTypes(self, package, allAbstractDataTypes):

    if package.containedPackages:
      for pp in package.containedPackages:
        self.determineAllAbstractDataTypes(pp, allAbstractDataTypes)
    else:
      allAbstractDataTypes.extend(package.classes)
      allAbstractDataTypes.extend(package.dataTypes)
      allAbstractDataTypes.extend(package.dataObjTypes)

  ###########################################################################

  ###########################################################################

  def determineAllAttrRoles(self, package, allAttrRoles):

    if package.containedPackages:
      for pp in package.containedPackages:
        self.determineAllAttrRoles(pp, allAttrRoles)
    else:
      for clazz in package.classes:
        allAttrRoles.extend(clazz.attributes)
        allAttrRoles.extend(clazz.roles)
      for dataObjType in package.dataObjTypes:
        allAttrRoles.extend(dataObjType.attributes)

  ###########################################################################

  ###########################################################################

  def determineAllMethods(self, package, allMethods):

    if package.containedPackages:
      for pp in package.containedPackages:
        self.determineAllMethods(pp, allMethods)
    else:
      for clazz in package.classes:
        for op in clazz.operations:
          if not op.opSubType and not op.name.startswith('_'):
            allMethods.append(op)

  ###########################################################################

  ###########################################################################

  def getPrevNextPackages(self, package):

    if package.container:
      containedPackages = metaUtil.sortByAttribute(package.container.containedPackages, 'name')
      m = containedPackages.index(package)
      if m > 0:
        prev = containedPackages[m-1]
      else:
        prev = None
      if m < len(containedPackages)-1:
        foll = containedPackages[m+1]
      else:
        foll = None
    else:
      prev = foll = None

    return (prev, foll)

  ###########################################################################

  ###########################################################################

  def getElemDocString(self, elem):

    doc = self.normaliseString(elem.documentation)
    if elem.taggedValues.get('isDraft'):
      doc = self.draftDocString + doc

    return doc

  ###########################################################################

  ###########################################################################

  def getLinkInfo(self, fromElem, toElem):
    """return tuple of relName, relDirectory.
       see code for details
    """
    if toElem.container is None:
      raise MemopsError('getLinkInfo callled with containerless element %s' % toElem)

    # logic moved to bottom because path was not always coming out correctly
    ###elif (fromElem.container is toElem.container and toElem.container.container is not None):
    ###  # elements with the same container are in the same directory,
    ###  # unless they are packages contained in RootPackage
    ###  return (toElem.name, '../%s' % toElem.name)

    else:
      path = Path.joinPath(self.pathToTop(fromElem), self.directoryFromTop(toElem, ignoreElemType=True))

    if isinstance(toElem,MetaModel.MetaDataType) or isinstance(toElem, MetaModel.MetaDataObjType):

      pp = toElem.container

      if pp == self.impPackage:
        return toElem.name, path

    if fromElem.container is toElem.container and toElem.container.container is not None:
      name = toElem.name
    else:
      name = self.getImportName(toElem, fromElem)
    
    return name, path

  ###########################################################################

  ###########################################################################

  def pathToTop(self, element, isDiagram=False, upDir=0):
    """ return relative directory path from a given element to the top directory
    """
  
    # upDir is hack to get Attribute Map pages to work

    if isDiagram:
      n = 2  # it's always in model/doc directory, not in language-specific api directory
    else:
      n = len(self.baseDirNames)

    if element.container is None:
      if hasattr(element, 'topPackage') and element is element.topPackage():
        # this is the root package
        #return Path.joinPath(*(['..']*(n+1+upDir)))
        return Path.joinPath(*(['..']*(n+upDir)))
    
      raise MemopsError("path from root element not implemented for %s" 
       % element
      )
  
    length = len(self.getElementPathList(element))
    if isDiagram:
      if element.containedPackages:
        length = length + n + 1
      else:
        length += n
    elif self.elemHasOwnDirectory(element):
      length = length + n + 2
    else:
      length = length + n + 1
  
    #return self.upDir(length)
    return self.upDir(length-2) # truing to adjust to new locations. TODO experiment

  ###########################################################################

  ###########################################################################

  def getElementPathList(self, element):

    return element.qualifiedName().split('.')

  ###########################################################################

  ###########################################################################

  def upDir(self, n = 1):

    if n == 0:
      return ''
    else:
      return Path.joinPath(*(n * ['..']))

  ###########################################################################

  ###########################################################################

  # TBD: not sure why ignoreElemType comes into use in one case
  # something probably wrong with that use, look at again
  def directoryFromTop(self, element, ignoreElemType = False):
    """ Generate directory name relative to top directory of an element
    """
  
    #n = len(self.baseDirNames)
    ll = self.baseDirNames + element.qualifiedName().split('.')
    #ll[n+1:n+1] = self.docSubDirs
    if not ignoreElemType and not self.elemHasOwnDirectory(element):
      del ll[-1]

    return Path.joinPath(*ll)

  ###########################################################################

  ###########################################################################

  def fileFromTop(self, element):

    directory = self.directoryFromTop(element)
    if self.elemHasOwnDirectory(element):
      fileName = Path.joinPath(directory, self.indexFile)
    else:
      fileName = '%s.%s' % (Path.joinPath(directory, element.name), self.fileSuffix)

    return fileName

  ###########################################################################

  ###########################################################################

  def getObjDocDirName(self, metaObj):

    fileName = self.getObjDocFileName(metaObj)
    dirName = Path.splitPath(fileName)[0]
 
    return dirName

  ###########################################################################

  ###########################################################################

  def getObjDocFileName(self, metaObj, absoluteName=True, addSuffix=False):

    """ Get filename for metaObj
    If absoluteName is True the file name is absolute
    otherwise it is relative to the relevant baseDir
    """
   
    # absolute or relative path
    if absoluteName:
      #pathList = [self.rootDirName] + self.baseDirNames
      pathList = [self.rootDirName] + self.baseDirNames
    else:
      pathList = []
   
    if metaObj.container is None:
      # Root package only
      pathList.append(metaConstants.modellingPackageName)
      #pathList.append(self.codeDirName)
      #pathList.append(self.docDir)
      pathList.append(self.rootFileName)

    else:
      # any other object
      ll = metaObj.qualifiedName().split('.')
      #ll[1:1] = [self.codeDirName, self.docDir]
      pathList.extend(ll)
      if self.elemHasOwnDirectory(metaObj):
        # gets own directory
        pathList.append(self.indexPrefix)

    # add suffix
    if addSuffix and self.fileSuffix:
      pathList[-1] = '%s.%s' % (pathList[-1], self.fileSuffix)

    #
    return Path.joinPath(*pathList)

  ###########################################################################

  ###########################################################################

  def getParentString(self, clazz):
    """ get string with parent class name
    """

    parentRole = clazz.parentRole
    if parentRole:
      otherClass = parentRole.valueType
      return 'link %s to class %s' % (parentRole.name,
                    self.getEmphasisString(self.getElemTypeString(parentRole)))
    else:
      return 'None'

  ###########################################################################

  ###########################################################################

  def getElemTypeString(self, elem):
    """ get attribute type string (string or link) for HTML
    """

    if isinstance(elem,MetaModel.MetaParameter):
      target = elem.valueType
      (name, ref) = self.getLinkInfo(elem.container.container,target)
    elif isinstance(elem,MetaModel.MetaAttribute):
      target = elem.valueType
      (name, ref) = self.getLinkInfo(elem.container,target)
      # TBD: is below correct (first clause added, second was there)???
      if isinstance(target, MetaModel.MetaDataType) and target.name == target.typeCodes[self.typeCodeKey]:
        name = target.name
    elif isinstance(elem,MetaModel.MetaRole):
      target = elem.valueType
      (name, ref) = self.getLinkInfo(elem.container,target)
    else:
      raise MemopsError('getElemTypeString called with object of class %s' % elem.__class__.__name__)

    if self.elemHasOwnDirectory(target):
      return '<a href ="%s/%s.html">%s</a>' % (ref, ApiDocGen.indexPrefix, name)
    else:
      return '<a href ="%s.html">%s</a>' % (ref, name)

  ###########################################################################

  ###########################################################################

  def getMultiplicity(self, obj):
    """ get multiplicity string from object with a locard and hicard
    """

    hicard = obj.hicard
    if hicard == metaConstants.infinity:
      hicard = '*'

    return '%s..%s' % (obj.locard,hicard)

  ###########################################################################

  ###########################################################################

  def getMandatoryElements(self, elem):
    """ get list of mandatory element names
    All elements with locard == hicard are mandatory
    """

    hasOptionals = False
    mandatories = []

    for ee in elem.getAllAttributes():
      if not ee.isDerived and not ee.isAutomatic and not ee.isImplementation:
        if ee.locard > 0:
          if not ee.defaultValue:
            mandatories.append(ee.name)
        else:
          hasOptionals = True

    if isinstance(elem, MetaModel.MetaClass):
      for ee in elem.getAllRoles():
        if (ee.hierarchy == metaConstants.no_hierarchy
              and not ee.isDerived and not ee.isAutomatic and not ee.isImplementation):
          if ee.locard > 0:
            mandatories.append(ee.name)
          else:
            hasOptionals = True

    return mandatories, hasOptionals

  ###########################################################################

  ###########################################################################

  def elemHasOwnDirectory(self, elem):
    """ whether element's HTML page is in own directory or in container's directory
    """

    if isinstance(elem, MetaModel.MetaPackage) or isinstance(elem, MetaModel.MetaClass) or isinstance(elem, MetaModel.MetaDataObjType):
      return True
    else:
      return False

  ###########################################################################

  ###########################################################################

  def getDiagramOrderedPackages(self):
    """ return packages ordered depth-first for use in left bar of diagram pages
    """

    mp = self.modelPortal
    topPackage = mp.topPackage
    usePackages = mp.branchPackages() + mp.leafPackagesAlphabetic()

    # traverse packages in depth-first order, adding to list if in usePackages
    result = []
    #stack = [metaUtil.sortByAttribute(topPackage.containedPackages, 'name')]
    #stack.reverse()
    stack = [[topPackage]]
 
    while stack:
      current = stack[-1].pop()
      if not stack[-1]:
        del stack[-1]
    
      if current in usePackages:
        result.append(current)
        ll = metaUtil.sortByAttribute(current.containedPackages, 'name')
        if ll:
          ll.reverse()
          stack.append(ll)

    return result

  ###########################################################################

  ###########################################################################

  def getElemMethods(self, elem):
    """ return methods listed on attribute page
    """

    opTypes = ('get', 'sorted', 'set', 'add', 'remove', 'new', 'findFirst', 'findAll')
    ops = {}
    for opType in opTypes:
      ops[opType] = []
    for op in elem.container.operations:
      if op.name.startswith('__'):
        pass
      elif (op.target == elem or (isinstance(elem, MetaModel.MetaRole) and
           elem.hierarchy == metaConstants.child_hierarchy and
           op.target in elem.valueType.getNonAbstractSubtypes())):
        ops[op.opType].append((op.name, op))

    methods = []
    for opType in opTypes:
      ops[opType].sort()
      methods.extend([op for (name, op) in ops[opType]])

    return methods

  ###########################################################################

  ###########################################################################

  def getClassPageMethods(self, complexDataType, method):

    raise MemopsError('must be overridden in subclass')

  ###########################################################################

  ###########################################################################

  def getParamString(self, parameter):

    raise MemopsError('must be overridden in subclass')

  ###########################################################################

  ###########################################################################

  def getKeywordValueString(self, method):

    raise MemopsError('must be overridden in subclass')

  ###########################################################################

  ###########################################################################

  def getNewParamString(self, method):

    raise MemopsError('must be overridden in subclass')

  ###########################################################################

  ###########################################################################

  def writeConstructorRows(self, clazz, mandatoryElements):

    raise MemopsError('must be overridden in subclass')

