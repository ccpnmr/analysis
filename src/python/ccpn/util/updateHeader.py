#  NBNB TBD FIXME. OBSOLETE. moved. remove

import os


moduleDoc = '''"""Module Documentation here

"""
'''

template = '''#=========================================================================================
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
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
    with open(fileName, 'rU') as fp:
        data = fp.read()

    n1 = data.find(startMatch)
    n2 = data.find(endMatch)
    if n1 >= 0 and n2 > n1:  # have a match
        data = data[:n1] + template + data[n2 + len(endMatch):]
    else:
        data = moduleDoc + template + data

    with open(fileName, 'w') as fp:
        fp.write(data)

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
