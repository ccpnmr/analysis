"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$Author: Luca Mureddu $"
__dateModified__ = "$Date: 2021-07-31 19:34:45 +0000 (,  31, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-07-31 19:34:45 +0000 (,  31, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import jedi
import sys
from ccpn.ui.gui.modules.macroEditorUtil import IconDefinitions as iDef


_namespace = []


import gc

def _getObjectsById(_id):
    for obj in gc.get_objects():
        if id(obj) == _id:
            return obj

def _getCcpnNamespaceFromApplication():
    """
    Get the namespaces as a list of dicts. Used to complete the Editor on key-pressed.
    """
    from ccpn.framework.Application import getApplication
    application = getApplication()
    namespaceList = []
    if application:
        namespace = application.mainWindow.namespace
        namespaceList = [{i: namespace[i]} for i in list(namespace.keys())]
    return namespaceList

def _getCcpnNamespaceFromImports():
    """
    This function is called several times from external scrips, therefore it init the imports Only Once with global.
    Namespace are done with imports to get Call-Signatures and documentation string.
    Namespaces for completion on the Editor are currently taken from imports too, This because the PyQode mechanism uses
    threads of json-serialisable items only. Therefore cannot send directly the application namespace as the
    IPython-console module.
    The alternative way of not using threads seems to break the GUI.
    """
    global _namespace
    if _namespace:
        return _namespace

    from ccpn.core.Project import Project
    from ccpn.framework.Framework import Framework, getPreferences
    from ccpn.ui.gui.lib.GuiMainWindow import GuiMainWindow
    from ccpn.framework.Current import Current
    from ccpn.ui.Ui import Ui
    from ccpn.util.Logging import getLogger

    _namespace = [
                 {'application'     : Framework},
                 {'current'         : Current},
                 {'mainWindow'      : GuiMainWindow},
                 {'ui'              : Ui},
                 {'project'         : Project},
                 {'preferences'     : getPreferences()},
                 {'redo'            : GuiMainWindow.redo},
                 {'undo'            : GuiMainWindow.undo},
                 {'get'             : Framework.getByPid},
                 {'loadProject'     : Framework.loadProject},
                 {'loadData'        : Framework.loadData},
                 {'warning'         : getLogger().warning},
                 {'info'            : getLogger().info},
                 ]
    return _namespace

def getJediInterpreter(text, namespaces=None, **kwds):
    """
    :type text: str. the  text to parse and get the completions
    :type namespaces: list of dict. a list of namespaces dictionaries such as the one
                      returned by :func:"locals".
    Other optional arguments are same as the ones for :class:"Script".
    If "line" and "column" are None, they are assumed be at the end of
    "text".
    """

    if not namespaces:
        namespaces = list(_getCcpnNamespaceFromImports())
    try:
        interpreter = jedi.Interpreter(text, namespaces=namespaces, **kwds)
        return interpreter
    except ValueError:
        return None

def _getAvailablePids() -> list:
    """
    Get all the pids available in the current project
    """
    from ccpn.framework.Application import getApplication
    result = None
    try:
        application = getApplication()
        if application:
            project  = application.project
            ll = [i.values() for i in project._pid2Obj.values()]
            ids = [j.id for i in ll for j in i]
            result = list(set(ids))
    except:
        sys.stderr.write('==> Completion warning. Pids not found!')

    return result or []


class CcpnCodeCompletionWorker(object):
    """
    This is the worker associated with the code completion mode.

    The worker does not actually do anything smart, the real work of collecting
    code completions is accomplished by the completion providers (see the
    :class:`pyqode.core.backend.workers.CodeCompletionWorker.Provider`
    interface) listed in
    :attr:`pyqode.core.backend.workers.CompletionWorker.providers`.

    Completion providers must be installed on the CodeCompletionWorker
    at the beginning of the main server script, e.g.::

        from pyqode.core.backend import CodeCompletionWorker
        CodeCompletionWorker.providers.insert(0, MyProvider())
    """
    #: The list of code completion provider to run on each completion request.
    providers = []
    namespaces = [{'ajo':111}]
    _application = None
    # namespaces = _getCcpnNamespaceFromApplication()


    def __call__(self, data):
        """
        Do the work (this will be called in the child process by the
        SubprocessServer).
        """
        code = data['code']
        line = data['line']
        column = data['column']
        path = data['path']
        encoding = data['encoding']
        prefix = data['prefix']
        req_id = data['request_id']
        completions = []

        for prov in CcpnCodeCompletionWorker.providers:
            try:
                results = prov.complete(
                    code, line, column, path, encoding, prefix)
                completions.append(results)
                if len(completions):
                    break
            except:
                sys.stderr.write('Failed to get completions from provider %r' % prov)
                exc1, exc2, exc3 = sys.exc_info()
        return [(line, column, req_id)] + completions

    def registerProvider(cls, provider):
        cls.providers.append(provider)

class CcpnNameSpacesProvider:
    """
    Provides code completion for the Ccpn Name space...
    """
    namespaces = []

    def complete(self, code, line, column, path, encoding, prefix):
        """
        Completes python code using `jedi`_.
        :returns: a list of completion.
        """

        ret_val = []
        _namespaceAtts = []
        try:
            namespaces = _getCcpnNamespaceFromImports()
            _namespaceAtts = [k for dd in namespaces for k in dd.keys()]
            script = getJediInterpreter(text=code, namespaces=namespaces, encoding=encoding)
            completions = script.completions()
        except Exception as ex:
            completions = []
            sys.stderr.write('==> Completion warning. ! %s' %ex)

        for completion in completions:
            iconType = ''
            ccpnTag = False
            if completion.type:
                if len(completion.type.split('.'))>0:
                        iconType = completion.type.split('.')[0]
                if completion.name in _namespaceAtts:
                    ccpnTag = True
            else:
                iconType = completion.type
            ret_val.append({
                 'name': completion.name,
                 'tooltip': completion.description,
                 'icon': iDef.iconFromTypename(completion.name, iconType, ccpnTag=ccpnTag),
                })

        return ret_val


class CcpnJediCompletionProvider:
    """
    Provides code completion using the original Jedi library. https://github.com/davidhalter/jedi
    """
    @staticmethod
    def complete(code, line, column, path, encoding, prefix):
        """
        Completes python code using `jedi`_.

        :returns: a list of completion.
        """
        ret_val = []
        try:
            script = getJediInterpreter(text=code, encoding=encoding)
            completions = script.completions()
        except RuntimeError:
            completions = []
        for completion in completions:
            ret_val.append({
                            'name': completion.name,
                            'tooltip': completion.description,
                            'icon': iDef.iconFromTypename(completion.name, completion.type),
                            })
        return ret_val

# setup completion providers
from pyqode.core.modes.code_completion import backend as _backend
_backend.CodeCompletionWorker = CcpnCodeCompletionWorker
# _backend.CodeCompletionWorker.namespaces = _getCcpnNamespaceFromApplication()
ccpnNameSpacesProvider = CcpnNameSpacesProvider()
ccpnNameSpacesProvider.worker = _backend.CodeCompletionWorker
_backend.CodeCompletionWorker.registerProvider(CcpnCodeCompletionWorker, ccpnNameSpacesProvider)
_backend.CodeCompletionWorker.registerProvider(CcpnCodeCompletionWorker, _backend.DocumentWordsProvider())
