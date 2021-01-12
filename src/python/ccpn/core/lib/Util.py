"""CCPN-level utility code independent of model content

"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import inspect
import os
from typing import Optional
from ccpn.core.lib import Pid
from ccpn.core import _coreClassMap
from ccpn.core._implementation import AbstractWrapperObject
from ccpn.util.Path import joinPath


def pid2PluralName(pid: str) -> str:
    """Get plural class name, (e.g. 'peaks', 'spectra' from short-form or long-form, Pid string
    Unrecognised strings are returned unchanged"""
    from ccpn.core.Project import Project

    tag = pid.split(Pid.PREFIXSEP, 1)[0]
    cls = Project._className2Class.get(tag)
    if cls is None:
        return tag
    else:
        return cls._pluralLinkName


def getParentPid(childPid) -> Pid.Pid:
    """Get the pid of parent of childPid; only uses Pid definitions (i.e. does not involve the actual objects)
    :returns Pid instance defining parent
    """
    if not isinstance(childPid, (str, Pid.Pid)):
        raise ValueError('Invalid pid "%s"' % childPid)
    childPid = Pid.Pid(childPid)
    if childPid.type not in _coreClassMap:
        raise ValueError('Invalid pid "%s"' % childPid)

    klass = _coreClassMap[childPid.type]
    parentClass = klass._parentClass
    offset = klass._numberOfIdFields
    fields = [parentClass.shortClassName] + list(childPid.fields[:-offset])
    parentPid = Pid.Pid.new(*fields)
    return parentPid


def getParentObjectFromPid(project, pid):
    """Get a parent object from a pid, which may represent a deleted object.

    :returns: Parent object or None on error/non-existence

    Example:
        pid = 'NA:A.40.ALA.CB'
        getParentObjectFromPid(pid) -> 'NR:A.40.ALA'
    """
    if not isinstance(pid, (str, Pid.Pid)):
        raise ValueError('Invalid pid "%s"' % pid)

    obj = None
    # First try if the object defined by pid still exists
    try:
        obj = project.getByPid(pid)
        if obj is not None:
            return obj._parent
    except:
        pass

    if obj is None:
        parentPid = getParentPid(pid)
        obj = project.getByPid(parentPid)
    return obj


# Atom ID
AtomIdTuple = collections.namedtuple('AtomIdTuple', ['chainCode', 'sequenceCode',
                                                     'residueType', 'atomName', ])


# def _fetchDataUrl(memopsRoot, nameStore, filePath):
#     """Get or create DataUrl that matches fullPath, prioritising insideData, alongsideDta, remoteData
#     and existing dataUrls"""
#     from memops.api.Implementation import Url
#     from memops.universal import Io as uniIo
#     import os
#
#     standardStore = memopsRoot.findFirstDataLocationStore(name='standard')
#
#     # standardStore = (memopsRoot.findFirstDataLocationStore(name='standard')
#     #                  or memopsRoot.newDataLocationStore(name='standard'))
#
#     # [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
#     # [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
#
#     if standardStore is None:
#         raise TypeError("Coding error - standard DataLocationStore has not been set")
#
#     stores = set([(store, store.dataUrl) for store in standardStore.sortedDataStores() if store.path == filePath])
#
#     if stores and len(stores) > 1:
#         raise ValueError("Too many stores")
#
#     for store, dataUrl in stores:
#         directoryPath = os.path.join(dataUrl.url.path, '')
#
#         # print('>>>_fetchDataUrl', filePath, directoryPath)
#
#         if filePath.startswith(directoryPath):
#             return store.fullPath
#         else:
#             return store.fullPath
#
#
#     # # for dataUrl in standardStore.sortedDataUrls():
#     # #     if dataUrl.name is nameStore:
#     #
#     #
#     # # fullPath = uniIo.normalisePath(fullPath, makeAbsolute=True)
#     # standardTags = ('insideData', 'alongsideData', 'remoteData')
#     # # Check standard DataUrls first
#     # checkUrls = [standardStore.findFirstDataUrl(name=tag) for tag in standardTags]
#     # # Then check other existing DataUrls
#     # checkUrls += [x for x in standardStore.sortedDataUrls() if x.name not in standardTags]
#     # for dataUrl in checkUrls:
#     #     if dataUrl is not None and dataUrl.name is nameStore:
#     #
#     #         directoryPath = os.path.join(dataUrl.url.path, '')
#     #         if filePath.startswith(directoryPath):
#     #             break
#     # else:
#     #     # No matches found, make a new one
#     #     dirName, path = os.path.split(filePath)
#     #     dataUrl = standardStore.newDataUrl(url=Url(path=dirName))
#     # #
#     # return dataUrl

# def expandDollarFilePath(project: 'Project', spectrum, filePath: str) -> str:
#     """Expand paths that start with $REPOSITORY to full path.
#
#     NBNB Should be moved to ccpnmodel.ccpncore.lib.ccp.general.DataLocation.DataLocationstore"""
#
#     # Convert from custom repository names to full names
#     stdRepositoryNames = {
#         '$INSIDE/'   : 'insideData',
#         '$ALONGSIDE/': 'alongsideData',
#         '$DATA/'     : 'remoteData',
#         }
#
#     if not filePath.startswith('$'):
#         # Nothing to expand
#         return filePath
#
#     dataLocationStore = project._wrappedData.root.findFirstDataLocationStore(name='standard')
#
#     if dataLocationStore is None:
#         raise TypeError("Coding error - standard DataLocationStore has not been set")
#
#     for prefix, dataUrlName in stdRepositoryNames.items():
#         if filePath.startswith(prefix):
#
#             apiDataStore = spectrum._apiDataSource.dataStore
#             if not apiDataStore:
#                 return filePath
#
#             elif apiDataStore.dataLocationStore.name == 'standard':
#
#                 # this fails on the first loading of V2 projects - ordering issue?
#                 spectrumDataUrlName = apiDataStore.dataUrl.name
#
#                 if spectrumDataUrlName == dataUrlName:
#                     return os.path.join(apiDataStore.dataUrl.url.dataLocation, filePath[len(prefix):])
#
#                 # if dataUrlName == 'insideData':
#                 #     pathData.setText('$INSIDE/%s' % apiDataStore.path)
#                 # elif dataUrlName == 'alongsideData':
#                 #     pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
#                 # elif dataUrlName == 'remoteData':
#                 #     pathData.setText('$DATA/%s' % apiDataStore.path)
#             else:
#                 # pathData.setText(apiDataStore.fullPath)
#                 return filePath
#
#             # dataUrl = dataLocationStore.findFirstDataUrl(name=dataUrlName)
#             # if dataUrl is not None:
#             #     return os.path.join(dataUrl.url.dataLocation, filePath[len(prefix):])
#
#     return filePath


def commandParameterString(*params, values: dict = None, defaults: dict = None):
    """Make  parameter string to insert into function call string.

    params are positional parameters in order, values are keyword parameters.
    If the defaults dictionary is passed in,
    only parameters in defaults are added to the string, and only if the value differs from the
    default. This allows you to pass in values=locals(). The order of keyword parameters
    follows defaults if given, else values, so you can get ordered parameters by passing in
    ordered dictionaries.

    Wrapper object values are replaced with their Pids

    Example:

    commandParameterString(11, values={a:1, b:<Note NO:notename>, c:2, d:3, e:4},
                            defaults=OrderedDict(d=8, b=None, c=2))

      will return

      "11, d=3, b='NO:notename'"
      """

    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

    ll = []
    for val in params:
        if isinstance(val, AbstractWrapperObject):
            val = val.pid
        ll.append(repr(val))

    if values:
        if defaults:
            for tag, default in defaults.items():
                val = values[tag]
                if val != default:
                    if isinstance(val, AbstractWrapperObject):
                        val = val.pid
                    ll.append('%s=%s' % (tag, repr(val)))

        else:
            for tag, val in values.items():
                if isinstance(val, AbstractWrapperObject):
                    val = val.pid
                ll.append('%s=%s' % (tag, repr(val)))
    #
    return ', '.join(ll)


def commandParameterStringValues(*params, values: dict = None, defaults: dict = None):
    """Make  parameter string to insert into function call string.

    params are positional parameters in order, values are keyword parameters.
    If the defaults dictionary is passed in,
    only parameters in defaults are added to the string, and only if the value differs from the
    default. This allows you to pass in values=locals(). The order of keyword parameters
    follows defaults if given, else values, so you can get ordered parameters by passing in
    ordered dictionaries.

    Wrapper object values are replaced with their Pids

    Example:

    commandParameterString(11, values={a:1, b:<Note NO:notename>, c:2, d:3, e:4},
                            defaults=OrderedDict(d=8, b=None, c=2))

      will return

      "11, d=3, b='NO:notename'"
      """

    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

    ll = []
    for val in params:
        if isinstance(val, AbstractWrapperObject):
            val = val.pid
        ll.append(repr(val))

    if values:
        if defaults:
            for tag, default in defaults.items():
                val = values[tag]
                if val != default:
                    if isinstance(val, AbstractWrapperObject):
                        val = val.pid
                    ll.append('%s=%s' % (tag, repr(val)))

        else:
            for tag, val in values.items():
                if isinstance(val, AbstractWrapperObject):
                    val = val.pid
                ll.append('%s=%s' % (tag, repr(val)))
    #
    return ', '.join(ll)


def funcCaller() -> Optional[str]:
    """
    return the name of the current function
    (actually the parent caller to this function, hence the index of '1')
    :return: string name
    """
    try:
        return inspect.stack()[1][3]
    except:
        return None


def callList(fn):
    """
    Wrapper to give the call stack for then current function
    Add callList=None, callStr=None to the parameter list for the function
    """

    def inner(*args, **kwargs):
        stack = inspect.stack()
        minStack = len(stack)  # min(stack_size, len(stack))
        modules = [(index, inspect.getmodule(stack[index][0]))
                   for index in range(1, minStack)]
        callers = [(0, fn.__module__, fn.__name__)]
        for index, module in modules:
            try:
                name = module.__name__
            except:
                name = '<NOT_FOUND>'
            callers.append((index, name, stack[index][3]))

        s = '{index:>5} : {module:^%i} : {name}' % 20
        printStr = []
        for i in range(0, len(callers)):
            printStr.append(s.format(index=callers[i][0], module=callers[i][1], name=callers[i][2]))

        kwargs['callList'] = callers
        kwargs['callStr'] = '\n'.join(printStr)

        fn(*args, **kwargs)

    return inner
