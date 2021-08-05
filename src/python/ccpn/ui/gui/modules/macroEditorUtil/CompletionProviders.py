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

def _getCcpnNamespace():
    """
    This function is called several times from external scrips, therefore it init the imports Only Once with global.
    Namespace are (unfortunately) done with imports.
    NOTE:
    Ideally Namespace should be inserted from the initialised objects. However the PyQode implementation of using
    sockets/processes to run external scripts means you need to give them in a Json-Serialisable format.
    The alternative way of not using sockets, seems to create odd behaviours on the QCompleter. For using that you need
    to add a subclassed CodeCompletionMode (see src/python/ccpn/ui/gui/widgets/QPythonEditor.py:49)
    and remove the native CodeCompletionMode.
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


class CcpnNameSpacesProvider:
    """
    Provides code completion for the Ccpn Name space...
    """

    def complete(self, code, line, column, path, encoding, prefix):
        """
        Completes python code using `jedi`_.

        :returns: a list of completion.
        """

        ret_val = []
        _namespaceAtts = []
        pids = []
        try:
            # namespaceDict = self.namespace
            # ccpnNamespaces = list(namespaceDict)
            # namespaces = [{k: namespaceDict[k]} for k in ccpnNamespaces]
            # pids = _getAvailablePids()
            # pidNameSpaces = [{pid: pid} for pid in pids]
            # namespaces += pidNameSpaces
            namespaces = _getCcpnNamespace()
            _namespaceAtts = [k for dd in namespaces for k in dd.keys()]
            script = jedi.Interpreter(code, namespaces=list(namespaces))
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
        sys.stderr.write(f'==> completions code:{code}, line:{line}, column:{column}, prefix:{prefix}, path:{path}.')
        ret_val = []
        try:
            script = jedi.Script(code, line + 1, column, path, encoding)
            completions = script.completions()
        except RuntimeError:
            completions = []
        for completion in completions:
            ret_val.append({
                            'name': completion.name,
                            'tooltip': completion.description,
                            'icon': iDef.iconFromTypename(completion.name, completion.type),
                            })
            sys.stderr.write(
                f'ITEMS => Name:{ completion.name}, type:{completion.type}.')
        return ret_val