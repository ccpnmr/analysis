#  NBNB TBD FIXME. OBSOLETE. moved. remove

import os

moduleDoc = '''"""Module Documentation here

"""
'''

template='''#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
'''

excludeFiles = {'__init__.py'}
excludeDirs = {'api', 'apiDoc', 'xml'}
suffixMatch = '.py'

startMatchCount = 3
endMatchCount = 3

templateLines = template.split('\n')
startMatch = '\n'.join(templateLines[:startMatchCount])
endMatch = '\n'.join(templateLines[-endMatchCount:])

curDir = os.getcwd()
thisFile = os.path.join(curDir, __file__)

def updateFile(fileName):

  fp = open(fileName, 'rU')
  data = fp.read()
  fp.close()
  n1 = data.find(startMatch)
  n2 = data.find(endMatch)
  if n1 >= 0 and n2 > n1: # have a match
    data = data[:n1] + template + data[n2+len(endMatch):]
  else:
    data = moduleDoc + template + data
  fp = open(fileName, 'w')
  data = fp.write(data)
  fp.close()

def visitDirectory(directory):

  relFiles = os.listdir(directory)
  for relFile in relFiles:
    absFile = os.path.join(directory, relFile)
    if os.path.isfile(absFile) and absFile != thisFile:
      if relFile.endswith(suffixMatch) and relFile not in excludeFiles:
        updateFile(absFile)
    elif os.path.isdir(absFile):
      if relFile not in excludeDirs:
        visitDirectory(absFile)
      
if __name__ == '__main__':

  visitDirectory(curDir)
