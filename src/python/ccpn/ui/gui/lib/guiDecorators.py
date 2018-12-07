"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
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
