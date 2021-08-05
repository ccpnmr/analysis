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
__dateModified__ = "$Date: 2021-08-04 22:28:23 +0000 (,  04, 2021) $"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2021-08-04 22:28:23 +0000 (,  04, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import ccpn.ui.gui.modules.macroEditorUtil.editorIcons as _icons
from ccpn.util.Path import aPath

CCPN = 'CCPN'
PID = 'PID'

editorIconsPath = aPath(_icons.__path__[-1])
# General tag
ICON_CLASS              = editorIconsPath / 'class.png'
ICON_NAMESPACE          = editorIconsPath / 'namespace.png'
ICON_VAR                = editorIconsPath / 'variable.png'
ICON_FUNC               = editorIconsPath / 'function.png'
ICON_METHOD             = editorIconsPath / 'method.png'
ICON_KEYWORD            = editorIconsPath / 'keyword.png'
ICON_GENERAL            = editorIconsPath / 'python.png'
ICON_PID                = editorIconsPath / 'ccpPID.png'
ICON_IMPORT             = editorIconsPath / 'import.png'
ICON_PACKAGE            = editorIconsPath / 'package.png'
ICON_MODULE             = editorIconsPath / 'module.png'
# Private tag
ICON_VAR_PROTECTED      = editorIconsPath / 'priv-variable.png'
ICON_FUNC_PRIVATE       = editorIconsPath / 'priv-function.png'
ICON_FUNC_PROTECTED     = editorIconsPath / 'priv-function.png'
ICON_METHOD_PRIVATE     = editorIconsPath / 'priv-method.png'
ICON_METHOD_PROTECTED   = editorIconsPath / 'priv-method.png'
# ccpn tag
ICON_CLASS_CCPN         = editorIconsPath / 'class_ccpn.png'
ICON_KEYWORD_CCPN       = editorIconsPath / 'keyword_ccpn.png'
ICON_VAR_CCPN           = editorIconsPath / 'variable_ccpn.png'
ICON_FUNC_CCPN          = editorIconsPath / 'function_ccpn.png'
ICON_METHOD_CCPN        = editorIconsPath / 'method_ccpn.png'



def _getCcpnIconsDefs():
    """
    A dict of definitions as needed by PyQode
    """

    CCPNICONS = {
        'CLASS'          : ('code-class'    , str(ICON_CLASS)),
        'IMPORT'         : ('code-context'  , str(ICON_IMPORT)),
        'STATEMENT'      : ('code-variable' , str(ICON_VAR)),
        'FORFLOW'        : ('code-variable' , str(ICON_VAR)),
        'FORSTMT'        : ('code-variable' , str(ICON_VAR)),
        'WITHSTMT'       : ('code-variable' , str(ICON_VAR)),
        'GLOBALSTMT'     : ('code-variable' , str(ICON_VAR)),
        'MODULE'         : ('code-context'  , str(ICON_MODULE)),
        'KEYWORD'        : ('code-quickopen', str(ICON_KEYWORD)),
        'PARAM'          : ('code-variable' , str(ICON_VAR)),
        'ARRAY'          : ('code-variable' , str(ICON_VAR)),
        'INSTANCEELEMENT': ('code-variable' , str(ICON_VAR)),
        'INSTANCE'       : ('code-variable' , str(ICON_VAR)),
        'FUNCTION'       : ('code-function' , str(ICON_FUNC)),
        'DEF'            : ('code-function' , str(ICON_FUNC)),
        'FUNCTION-PRIV'  : ('code-function' , str(ICON_FUNC_PRIVATE)),
        'FUNCTION-PROT'  : ('code-function' , str(ICON_FUNC_PROTECTED)),
        'PARAM-PRIV'     : ('code-variable' , str(ICON_VAR_PROTECTED)),
        'PARAM-PROT'     : ('code-variable' , str(ICON_VAR_PROTECTED)),
        'CLASS-CCPN'     : ('code-class'    , str(ICON_CLASS_CCPN)),
        'FUNCTION-CCPN'  : ('code-class'    , str(ICON_FUNC_CCPN)),
        'PARAM-CCPN'     : ('code-class'    , str(ICON_VAR_CCPN)),
        PID              : ('code-variable' , str(ICON_PID))
        }
    return CCPNICONS


def iconFromTypename(name, iconType, ccpnTag=False):
    """

    Returns the icon resource filename that corresponds to the given typename.

    :param name: name of the completion. Use to make the distinction between
                 public and private completions (using the count of starting '_')
    :pram typename: the typename reported by jedi

    :returns: The associate icon resource filename or None.
    """

    icons = _getCcpnIconsDefs()
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
    if ccpnTag:
        iconType += "-"+CCPN
    if iconType in icons:
        ret_val = icons[iconType]
    return ret_val
