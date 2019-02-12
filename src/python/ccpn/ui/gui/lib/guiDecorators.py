"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2018-12-20 15:53:11 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager


# @contextmanager
# def suspendSideBarNotifications(project, funcName='suspendSideBarNotifications', *args, quiet=True):
#     """
#     Context manager to wrap the function with a command block and suspend notifications
#     to the sideBar until commandBlock has finished
#     """
#     try:
#         project._startCommandEchoBlock(funcName, *args, quiet=quiet)
#         yield
#
#     finally:
#         project._endCommandEchoBlock()
#
#
# def _suspendSideBarNotifications(project):
#     """
#     decorator to wrap the function with a command block and suspend notifications
#     to the sideBar until commandBlock has finished
#     """
#
#     def funcWrapper(fn):
#         def returnfunc(*args):  # the same arguments as fn
#             # propagate args to the function
#             try:
#                 project._startCommandEchoBlock(fn.__name__, quiet=True)
#                 fn_ret = fn(*args)  # call 'fn' here - don't forget the brackets
#
#             finally:
#                 project._endCommandEchoBlock()
#
#             return fn_ret
#
#         return returnfunc  # and return the outer function
#
#     return funcWrapper
