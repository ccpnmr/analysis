"""
Various Project related routines
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-10-09 15:40:46 +0100 (Thu, October 09, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Geerten Vuister $"
__date__ = "$Date: 2023-01-19 11:47:50 +0000 (Thu, January 19, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
import sys

from ccpn.util import Logging
from ccpn.util.Path import aPath

from ccpn.framework.Application import getApplication
from ccpn.framework.PathsAndUrls import CCPN_API_DIRECTORY, CCPN_DIRECTORY_SUFFIX, CCPN_LOGS_DIRECTORY

from ccpnmodel.ccpncore.memops.metamodel import Constants as metaConstants


MEMOPS = metaConstants.modellingPackageName
IMPLEMENTATION = metaConstants.implementationPackageName


def checkProjectName(name, correctName=False) -> str | None:
    """Checks name

    :param name: name to be checked
    :param correctName: flag to correct
    :return: name (optionally corrected) or None
    """
    from ccpn.core.Project import Project

    newName = re.sub('[^0-9a-zA-Z]+', '_', name)
    if name != newName and not correctName:
        return None

    if len(newName) > Project._MAX_PROJECT_NAME_LENGTH:
        if not correctName:
            return None
        newName = newName[:32]

    return newName


def isV3project(path) -> bool:
    """Convenience method:
    :return True is path is (appears to be?) a V3 project"""
    path = aPath(path)
    if not path.is_dir(): return False
    if path.suffix != CCPN_DIRECTORY_SUFFIX: return False
    if path.name == CCPN_API_DIRECTORY: return False
    if not (path / CCPN_API_DIRECTORY / MEMOPS / IMPLEMENTATION).exists(): return False
    # it is a directory with .ccpn suffix, not named ccpnv3, that has ccpnv3/memops/implementation subdirectory,
    # so we assume it to be a V3 project directory.
    return True


def isV2project(path) -> bool:
    """Convenience method:
    :return True is path is (appears to be?) a V2 project"""
    path = aPath(path)
    if not path.is_dir(): return False
    if isV3project(path): return False
    if not (path / MEMOPS / IMPLEMENTATION).exists(): return False
    # it is a directory which is not a V3-project directory , that has memops/implementation subdirectory,
    # so we assume it to be a V2 project directory.
    return True


def createLogger(project, now=''):
    """Create a logger for project
    Adapted from Api.py
    """

    # Cannot use the back linkage to application, as this routine is called during Project initialisation
    _app = getApplication()

    logger = Logging.createLogger(_app.applicationName,
                                  project.projectPath / CCPN_LOGS_DIRECTORY,
                                  stream=sys.stderr,
                                  level=_app._loggingLevel,
                                  now=now
                                  )

    return logger


def _finaliseV2Upgrade(project):
    """Final step of upgrading from v2 to v3 projects.
    Copy all the internal validationStores to v3-dataTables
    """
    import pandas as pd
    from collections import OrderedDict
    from xml.sax.saxutils import escape

    Logging.getLogger().debug(f'Finalise upgrade v2-v3')
    fields = ['_ID', 'className', 'createdBy', 'guid', 'name',
              'packageName', 'packageShortName',
              'qualifiedName', 'structureEnsemble'
    ]
    columns = ['serial', 'context', 'keyword', 'keywordDefinition',
               'figOfMerit', 'textValue', 'intValue', 'floatValue',
               'booleanValue', 'details'
    ]
    wrp = project._wrappedData

    # loop over the validationStores
    vStores = list(wrp.validationStores)
    for vs in vStores:
        out = []
        for vr in vs.validationResults:
            out.append([str(val) if not hasattr(val, '_ID') else val.name
                        for col in columns
                        for val in [getattr(vr, col, '')]])
        df = pd.DataFrame(out, columns=columns)

        # create the new DataTable
        dTable = project.newDataTable(name=vs.name, data=df)

        # think that internally is using a dict and losing order :|
        meta = [(k, str(val)) if not hasattr(val, '_ID') else (k, val.name)
                for k in fields
                for val in [getattr(vs, k, '')]
        ]
        if sft := getattr(vs, 'software', ''):
            # try and convert the software information to something serializable
            meta.append(('software',
                         ':'.join(map(lambda _ss: escape(str(_ss)),
                                      filter(None, [sft.name, sft.version, sft.details, sft.tasks,
                                                    sft.vendorName, sft.vendorAddress,
                                                    sft.vendorWebAddress])))))
        dTable.updateMetadata(OrderedDict(meta))
        Logging.getLogger().debug(f'Extracted V2-{vs.className} into {dTable}')
        vs.delete()

    # Extract V2 structureGenerations info
    columns = ['serial', 'name',
               'generationType', 'nmrConstraintStore',
               'details'
    ]

    out = []
    for sg in wrp.structureGenerations:
        out.append([str(val) if not hasattr(val, '_ID') else val.name
                    for col in columns
                    for val in [getattr(sg, col, '')]])
        sg.delete()

    df = pd.DataFrame(out, columns=columns)
    dTable = project.newDataTable(name='structureGenerations', data=df)
    dTable.updateMetadata({'name': 'structureGenerations'})
    Logging.getLogger().debug(f'Extracted V2-structureGenerations into {dTable}')
