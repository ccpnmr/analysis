"""Generation of Sphinx automatic documentation

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-07-05 14:23:16 +0100 (Tue, July 05, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhf22 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
"""Scrips to (re)create project sphinx documentation"""

import typing

import subprocess
import os
import re
import shutil
from sphinx.ext import apidoc
from ccpn.framework import Version
from ccpn.framework.credits import authors
from ccpn.util import Path as corePath


joinPath = corePath.joinPath

# Relative path to documentation directory
documentationPath = 'doc'

ll = ('__pycache__', 'testing', 'api', 'xml', 'data', 'macros', 'chemBuild', 'Bmrb',
      'v_\d+_\d+_.*')
skipSubDirectories = re.compile('|'.join(ll))


def refreshSphinxDocumentation():
    """(Re)create sphinx documentation. Locations are hardwired"""

    pythonDirectory = corePath.getPythonDirectory()
    topDirectory = corePath.getTopDirectory()
    docDirectory = joinPath(topDirectory, documentationPath)

    # Direwcteories that should not be documented
    excludeTopDirs = ('chemBuild', '__pycache__')

    inputDirectories = list(x for x in os.scandir(pythonDirectory)
                            if x.is_dir() and x.name not in excludeTopDirs)

    # Remove sphinx-apidoc files
    outputDirs = {}
    for dirEntry in inputDirectories:
        inDirectory = joinPath(docDirectory, 'source', dirEntry.name)
        outputDirs[dirEntry.name] = inDirectory
        if os.path.exists(inDirectory):
            print("Removing %s" % inDirectory)
            shutil.rmtree(inDirectory)
            os.mkdir(inDirectory)

    # clean builds
    subprocess.call(['make', '-C', docDirectory, 'clean'])

    # # Recreate apidoc
    # precommand = ['sphinx-apidoc']
    # # documentation target - filled in below
    # precommand.extend(('-o', 'output TBD'))
    # # Put module documentation before submodule documentation:
    # precommand.append('--module-first')
    # # Project name header:
    # precommand.extend(('-A', Version.authors))
    # # Project name header:
    # precommand.extend(('-V', Version.applicationVersion))
    # # Project name header:
    # precommand.extend(('-R', Version.revision))
    #
    # # Generate documentation - ccpn:
    # for dirEntry in inputDirectories:
    #     module = dirEntry.name
    #     target = dirEntry.path
    #     skipDirs = getNamedSubdirectories(target, skipSubDirectories)
    #     command = precommand + ['-H', 'CCPN', target] + skipDirs
    #     if module == 'ccpnmodel':
    #         # Skip an additional directory
    #         command.append(os.path.join(target, 'ccpncore', 'memops', 'scripts', 'model'))
    #     command[2] = outputDirs[module]
    #     apidoc.main(command)

    # NOTE:ED - ordering is incorrect

    # Recreate apidoc
    # precommand = ['sphinx-apidoc']
    precommand = []
    # Put module documentation before submodule documentation:
    precommand.append('--module-first')
    # Project name header:
    precommand.extend(('-A', authors))
    # Project name header:
    precommand.extend(('-V', Version.applicationVersion))
    # Project name header:
    precommand.extend(('-R', Version.revision))

    # # documentation target - filled in below
    # precommand.extend(('-o', 'output TBD'))

    # Generate documentation - ccpn:
    for dirEntry in inputDirectories:
        module = dirEntry.name
        target = dirEntry.path
        skipDirs = getNamedSubdirectories(target, skipSubDirectories)

        # command = precommand + ['-H', 'CCPN', target] + skipDirs
        command = precommand + ['-H', 'CCPN'] + ['-o', outputDirs[module], target] + skipDirs

        if module == 'ccpnmodel':
            # Skip an additional directory
            command.append(os.path.join(target, 'ccpncore', 'memops', 'scripts', 'model'))

        # command[2] = outputDirs[module]
        apidoc.main(command)

    # rebuild docs
    subprocess.call(['make', '-C', docDirectory, 'html'])


def getNamedSubdirectories(path, matchExpression=None) -> typing.List[str]:
    """Get a list of all subdirectories of path whose basename starts with one of the prefixes

    Does not look inside the selected subdirectories"""

    result = []

    if matchExpression is not None:
        for root, dirs, files in os.walk(path):
            if matchExpression.fullmatch(os.path.basename(root)) is not None:
                result.append(root)
                del dirs[:]
    #
    return result


if __name__ == '__main__':
    refreshSphinxDocumentation()
