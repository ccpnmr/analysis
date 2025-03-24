"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-03-21 15:53:16 +0000 (Fri, March 21, 2025) $"
__version__ = "$Revision: 3.3.1 $"
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
import numpy as np
from ccpn.framework import Framework
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpnmodel.ccpncore.testing.CoreTesting import TEST_PROJECTS_PATH

from ccpn.util.Common import Sentinel

#=========================================================================================
# fix checkAlValid
#=========================================================================================

def fixCheckAllValid(project):
    # fix the bad structure for the test
    # new pdb loader does not load the into the data model so there are no atoms defined
    # the corresponding dataMatrices therefore have dimension set to zero which causes a crash :|
    # SHOULD NOT BE USED IN MAIN CODE YET

    for st in project.structureEnsembles:
        stw = st._wrappedData
        getLogger().info(f'fixing {stw}')
        for dm in list(stw.dataMatrices):
            if dm.name in ['bFactors', 'coordinates', 'occupancies']:

                # get the shape - make sure minimum dimension size is 1
                _shape = dm.shape
                _shape = tuple(max(val, 1) for val in _shape)

                # force the shape
                dm.__dict__['shape'] = _shape

                # create empty MolStructure information and insert into matrix
                _matrix = np.zeros(_shape)
                for model in list(st.models):
                    model._wrappedData.setSubmatrixData(dm.name, _matrix.flatten())


#=========================================================================================
# checkGetSetAttr
#=========================================================================================

def checkGetSetAttr(cls, obj, attrib, value, *funcOut):
    """
    Test that the object has a populated attribute.
    Read the attribute using getattr(), if not populated then an error is raised.
    If populated, then test the setter/getter are consistent.

    :param obj:
    :param attrib:
    :param value:
    """
    setattr(obj, attrib, value)
    if not funcOut:
        cls.assertEqual(getattr(obj, attrib), value)
    else:
        cls.assertEqual(getattr(obj, attrib), funcOut[0])


def getProperties(obj) -> dict:
    props = {}
    for k in dir(obj):
        if not k.startswith('_') and isinstance(getattr(type(obj), k), property):
            try:
                val = str(getattr(obj, k))
                props[k] = val
            except Exception:
                # if the property is deleted then some/most properties will be unavailable
                props[k] = ''

    return props


#=========================================================================================
# WrapperTesting
#=========================================================================================

class WrapperTesting(unittest.TestCase):
    """Base class for all testing of wrapper code that requires projects."""

    # Path for project to load - can be overridden in subclasses
    projectPath = None
    noLogging = True
    noDebugLogging = False
    noEchoLogging = True  # block all logging to the terminal - debug<n>|warning|info
    debug = False
    debug2 = False
    debug3 = False

    @contextlib.contextmanager
    def initialSetup(self):
        # if self.projectPath is None:
        #   self.project = core.newProject('default')
        # else:
        #   self.project = core.loadProject(os.path.join(TEST_PROJECTS_PATH, self.projectPath))

        projectPath = self.projectPath
        if projectPath is not None:
            projectPath = aPath(TEST_PROJECTS_PATH) / projectPath
        self.framework = Framework.createFramework(projectPath=projectPath,
                                                   noLogging=self.noLogging,
                                                   noDebugLogging=self.noDebugLogging,
                                                   noEchoLogging=self.noEchoLogging,
                                                   debug=self.debug,
                                                   interface='NoUi',
                                                   debug=self.debug,
                                                   debug2=self.debug2,
                                                   debug3=self.debug3,
                                                   _skipUpdates=True)
        self.project = self.framework.project
        if self.project is None:
            self.tearDown()
            raise RuntimeError(f"No project found for project path {projectPath}")

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
            if self.framework._temporaryDirectory:
                # if not cleaned then second test-case that runs reports a ResourceWarning
                # on the previously opened TemporaryDirectory
                self.framework._temporaryDirectory.cleanup()
        self.framework = self.project = self.undo = None

        from ccpn.util.decorators import singleton

        # delete all the singletons - was causing leakage between running testcases
        singleton._instances = {}


    def loadData(self, dataPath):
        """load data relative to TEST_PROJECTS_PATH (unless dataPath is absolute"""
        if not os.path.isabs(dataPath):
            dataPath = os.path.join(TEST_PROJECTS_PATH, dataPath)
        return self.framework.loadData(dataPath)

    def raiseDelayedError(self, *args, **kwargs):
        """Debugging tool. To raise an error the """
        if hasattr(self, 'delayedError') and self.delayedError:
            self.delayedError -= 1
        else:
            raise RuntimeError('Deliberate delayed error!!')

    def assertEqualForAttribute(self, obj, attribute, value1, value2=Sentinel):
        """Helper routine to test the value of attribute of obj:
        - do val:= getattr(obj, attribute) and
             assert val is equal to value1

        if value2 is not Sentinel:
        - do setattr(obj, attribute, value)
        - do val:= getattr(obj, attribute) and
             assert val is equal to value2

        - undo
        - getattr and assert val is equal to value1
        - redo
        - getattr and assert val is equal to value2

        - undo
        """
        _val = getattr(obj, attribute)
        self.assertEqual(_val, value1, f'>>> Asserting {attribute} of {obj} <<<')

        if value2 != Sentinel:
            setattr(obj, attribute, value2)
            _val = getattr(obj, attribute)
            self.assertEqual(_val, value2, f'>>> After assignment: Asserting {attribute} of {obj} <<<')

            self.undo.undo()
            _val = getattr(obj, attribute)
            self.assertEqual(_val, value1, f'>>> After undo: Asserting {attribute} of {obj} <<<')

            self.undo.redo()
            _val = getattr(obj, attribute)
            self.assertEqual(_val, value2, f'>>> After redo: Asserting {attribute} of {obj} <<<')

            # revert back for the next test
            self.undo.undo()

    def assertEqualForAttributeItem(self, obj, attribute, value1, value2=Sentinel, itemIndex=0):
        """Helper routine to test the item value of attribute of obj:
        - do val:= getattr(obj, attribute) and
             and assert val[itemIndex] is equal to value1[itemIndex]

        if value2 is not Sentinel:
        - do setattr(obj, attribute, value2)
        - do val:= getattr(obj, attribute) and
             assert val[itemIndex] is equal to value2[itemIndex]

        - undo
        - getattr and assert val[itemIndex] is equal to value1[itemIndex]
        - redo
        - getattr and assert val[itemIndex] is equal to value2[itemIndex]

        - undo
        """
        _val = getattr(obj, attribute)
        self.assertEqual(_val[itemIndex], value1[itemIndex], f'>>> Asserting {attribute}[{itemIndex}] of {obj} <<<')

        if value2 != Sentinel:
            setattr(obj, attribute, value2)
            _val = getattr(obj, attribute)
            self.assertEqual(_val[itemIndex], value2[itemIndex], f'>>> After assignment: Asserting {attribute}[{itemIndex}] of {obj} <<<')

            self.undo.undo()
            _val = getattr(obj, attribute)
            self.assertEqual(_val[itemIndex], value1[itemIndex], f'>>> After undo: Asserting {attribute}[{itemIndex}] of {obj} <<<')

            self.undo.redo()
            _val = getattr(obj, attribute)
            self.assertEqual(_val[itemIndex], value2[itemIndex], f'>>> After redo: Asserting {attribute}[{itemIndex}] of {obj} <<<')

            self.undo.undo()
