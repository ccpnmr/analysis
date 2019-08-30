"""Module Documentation here

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
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import unittest
import contextlib
# from ccpn import core
from ccpn.framework import Framework
from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH


#=========================================================================================
# checkGetSetAttr
#=========================================================================================

def checkGetSetAttr(cls, obj, attrib, value, *funcOut):
    """
    Test that the object has a populated attribute.
    Read the attribute using getattr(), if it not populated then an error is raised.
    If populated, then test the setter/getter are consistent.

    :param obj:
    :param attrib:
    :param value:
    """
    thisParam = getattr(obj, attrib)
    setattr(obj, attrib, value)
    if not funcOut:
        cls.assertEqual(getattr(obj, attrib), value)
    else:
        cls.assertEqual(getattr(obj, attrib), funcOut[0])


#=========================================================================================
# WrapperTesting
#=========================================================================================

class WrapperTesting(unittest.TestCase):
    """Base class for all testing of wrapper code that requires projects."""

    # Path for project to load - can be overridden in subclasses
    projectPath = None

    @contextlib.contextmanager
    def initialSetup(self):
        # if self.projectPath is None:
        #   self.project = core.newProject('default')
        # else:
        #   self.project = core.loadProject(os.path.join(TEST_PROJECTS_PATH, self.projectPath))

        projectPath = self.projectPath
        if projectPath is not None:
            projectPath = os.path.join(TEST_PROJECTS_PATH, projectPath)
        self.framework = Framework.createFramework(projectPath=projectPath, nologging=False)
        self.project = self.framework.project
        if self.project is None:
            self.tearDown()
            raise RuntimeError("No project found for project path %s" % projectPath)

        self.project._resetUndo(debug=True, application=self.framework)
        self.undo = self.project._undo
        self.undo.debug = True
        try:
            yield
        except:
            self.tearDown()
            raise

    def setUp(self):
        with self.initialSetup():
            pass

    def tearDown(self):
        if self.framework:
            self.framework._closeProject()
        self.framework = self.project = self.undo = None

    def loadData(self, dataPath):
        """load data relative to TEST_PROJECTS_PATH (unless dataPath is absolute"""
        if not os.path.isabs(dataPath):
            dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
        dataList = self.project.loadData(dataPath)
        #
        return dataList

    def raiseDelayedError(self, *args, **kwargs):
        """Debugging tool. To raise an error the """
        if hasattr(self, 'delayedError') and self.delayedError:
            self.delayedError -= 1
        else:
            raise Exception('Deliberate delayed error!!')
