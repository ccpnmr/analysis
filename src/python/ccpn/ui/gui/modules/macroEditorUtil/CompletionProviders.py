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



def iconFromTypename(name, iconType):
    """
    Returns the icon resource filename that corresponds to the given typename.

    :param name: name of the completion. Use to make the distinction between
        public and private completions (using the count of starting '_')
    :pram typename: the typename reported by jedi

    :returns: The associate icon resource filename or None.
    """
    import pyqode.python.backend.workers as workers

    ICONS = {
        'CLASS': workers.ICON_CLASS,
        'IMPORT': workers.ICON_NAMESPACE,
        'STATEMENT': workers.ICON_VAR,
        'FORFLOW': workers.ICON_VAR,
        'FORSTMT': workers.ICON_VAR,
        'WITHSTMT': workers.ICON_VAR,
        'GLOBALSTMT': workers.ICON_VAR,
        'MODULE': workers.ICON_NAMESPACE,
        'KEYWORD': workers.ICON_KEYWORD,
        'PARAM': workers.ICON_VAR,
        'ARRAY': workers.ICON_VAR,
        'INSTANCEELEMENT': workers.ICON_VAR,
        'INSTANCE': workers.ICON_VAR,
        'PARAM-PRIV': workers.ICON_VAR,
        'PARAM-PROT': workers.ICON_VAR,
        'FUNCTION': workers.ICON_FUNC,
        'DEF': workers.ICON_FUNC,
        'FUNCTION-PRIV': workers.ICON_FUNC_PRIVATE,
        'FUNCTION-PROT': workers.ICON_FUNC_PROTECTED
    }
    ret_val = None
    iconType = iconType.upper()
    if hasattr(name, "string"):
        name = name.string
    if iconType == "FORFLOW" or iconType == "STATEMENT":
        iconType = "PARAM"
    if iconType == "PARAM" or iconType == "FUNCTION":
        if name.startswith("__"):
            iconType += "-PRIV"
        elif name.startswith("_"):
            iconType += "-PROT"
    if iconType in ICONS:
        ret_val = ICONS[iconType]
    return ret_val


class CcpnJediCompletionProvider:
    """
    Provides code completion using the awesome `jedi`_  library

    .. _`jedi`: https://github.com/davidhalter/jedi
    """

    @staticmethod
    def complete(code, line, column, path, encoding, prefix):
        """
        Completes python code using `jedi`_.

        :returns: a list of completion.
        """
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
                            'icon': iconFromTypename(completion.name, completion.type),
                            })

        return ret_val


class CcpnNameSpacesProvider:
    """
    Provides code completion for the Ccpn Name space...
    """
    application = None

    @staticmethod
    def _getAvailablePids() -> list:
        """
        Get all the pids available in the current project
        """
        from ccpn.framework.Application import getApplication
        import itertools
        result = None
        application = getApplication()
        if application:
            project  = application.project
            ll = [i.keys() for i in project._pid2Obj.values()]
            result = list(set(itertools.chain(*ll)))
        return result or []

    @staticmethod
    def complete(self, code, line, column, path, encoding, prefix):
        """
        Under implementation
        :returns: a list of completion.
        """
        ret_val = []

        return ret_val
