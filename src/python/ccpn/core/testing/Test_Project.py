"""Module Documentation here

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
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: VickyAH $"
__dateModified__ = "$dateModified: 2021-01-08 11:49:57 +0000 (Fri, January 08, 2021) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os

from ccpn.core.testing.WrapperTesting import WrapperTesting
from ccpnmodel.ccpncore.lib.Io import Api as apiIo


class ProjectTestRename(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_name_and_rename(self):
        apiNmrProject = self.project._apiNmrProject
        self.assertEqual(self.project.name, 'default')
        self.assertEqual(apiNmrProject.root.name, 'default')
        oldLocation = apiNmrProject.root.findFirstRepository(name='userData').url.getDataLocation()
        self.assertTrue(os.path.isdir(oldLocation))


class ProjectTestExperimentTypeMap(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_experimentTypeMap(self):
        experimentTypeMap = self.project._experimentTypeMap
        self.assertEqual(list(sorted(experimentTypeMap.keys())), [1, 2, 3, 4, 5, 6])

        experimentTypeMap2 = self.project._experimentTypeMap
        # Undo and redo all operations
        self.undo.undo()
        self.undo.redo()
        self.assertIs(experimentTypeMap, experimentTypeMap2)


class ProjectTestIo(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = 'CcpnCourse2b.ccpn'

    def test_name(self):
        project = self.project
        self.assertTrue(project.name.startswith('CcpnCourse2b'))
        baseDir, projDir = os.path.split(project.path)
        self.assertEquals(projDir[-5:], '.ccpn')
        self.assertTrue(projDir.startswith('CcpnCourse2b'))

        self.assertTrue(project.save(newPath=os.path.join(baseDir, '_SAVED_TO_NAME.ccpn'),
                                     overwriteExisting=True))
        self.assertTrue(project.name.startswith('_SAVED_TO_NAME'))
        self.assertTrue(project.name == '_SAVED_TO_NAME' or project.name[14] == '_')
