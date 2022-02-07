"""
This file contains AutoBackup class
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
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-02-07 17:13:52 +0000 (Mon, February 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2022-02-05 10:28:48 +0000 (Saturday, February 5, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from threading import Thread
from time import time, sleep

from ccpn.util.Logging import getLogger


class AutoBackup(Thread):

    def __init__(self, q, backupFunction, sleepTime=1):
        super().__init__()
        self.sleepTime = sleepTime
        self.q = q
        self.backupFunction = backupFunction
        self.startTime = None

    def run(self):
        self.startTime = time()
        while True:
            waitTime = None
            if not self.q.empty():
                waitTime = self.q.get()
            if waitTime is None:
                sleep(self.sleepTime)
            elif waitTime == 'kill':
                return
            elif (time() - self.startTime) < waitTime:
                sleep(self.sleepTime)
            else:
                self.startTime = time()
                try:
                    self.backupFunction()
                except Exception as es:
                    getLogger().warning('Project backup failed with error %s' % es)
