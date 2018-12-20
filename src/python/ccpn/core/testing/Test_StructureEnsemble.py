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
__dateModified__ = "$dateModified: 2017-07-07 16:32:35 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2017-03-30 15:03:06 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy
from ccpn.core.testing.WrapperTesting import WrapperTesting, checkGetSetAttr
from ccpn.framework import Framework
import unittest


#=========================================================================================
# StructureEnsembleTesting    No loaded project
#=========================================================================================

class StructureEnsembleTesting_None(WrapperTesting):

    #=========================================================================================
    # setUp       initialise a newStructureEnsemble
    #=========================================================================================

    def _test_load_structure(self):
        self.loadData('../structures/2CPP.pdb')
        ensemble = self.project.structureEnsembles[0]
        self.assertEqual(len(ensemble.models), 1)
        self.assertEqual(len(ensemble.data), 3462)
        self.assertEqual(ensemble.data.shape, (3462, 17))
        self.assertTrue(self.project.save())
        loadedProject = Framework.createFramework(projectPath=self.project.path).project
        try:
            ensemble = loadedProject.structureEnsembles[0]
            data = ensemble.data
            self.assertEqual(len(ensemble.models), 1)
            self.assertEqual(len(data), 3462)
            self.assertEqual(data.shape, (3462, 17))
            self.assertTrue(all(x == 'A' for x in data['chainCode']))
            tags = [
                'modelNumber', 'chainCode', 'sequenceId', 'insertionCode',
                'residueName', 'atomName', 'altLocationCode', 'element',
                'occupancy', 'bFactor',
                'nmrChainCode', 'nmrSequenceCode', 'nmrResidueName', 'nmrAtomName',
                ]
        finally:
            loadedProject.delete()


#=========================================================================================
# StructureEnsembleTesting    Loaded project
#=========================================================================================

class StructureEnsembleTesting_Project(WrapperTesting):

    #=========================================================================================
    # setUp       initialise a newStructureEnsemble
    #=========================================================================================

    def setUp(self):
        """
        Test StructureEnsemble with a pre-loaded valid project
        """
        self.projectPath = 'CcpnCourse3e'
        super().setUp()  # ejb - call WrapperTesting setup to load project

    def test_haveEnsemble(self):
        # assert len(self.project.structureEnsembles) > 0
        #
        self.assertGreater(len(self.project.structureEnsembles), 0)

        self.project._wrappedData.root.checkAllValid(complete=True)

        models = self.project.structureEnsembles[0].models
        # assert len(models) > 0
        # assert len(models) == 20
        #
        self.assertGreater(len(models), 0)
        self.assertEquals(len(models), 20)

        data = self.project.structureEnsembles[0].data
        self.assertEquals(data.shape, (29680, 17))

    def test_getModels(self):
        models = self.project.structureEnsembles[0].models
        # assert len(models) > 0
        # assert len(models) == 20
        #
        self.assertGreater(len(models), 0)
        self.assertEquals(len(models), 20)

    def test_coords(self):
        data = self.project.structureEnsembles[0].data
        self.assertEquals(data.shape, (29680, 17))


#=========================================================================================
# StructureEnsembleTesting      Properties
#=========================================================================================

class StructureEnsembleTesting_Properties(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    #=========================================================================================
    # setUp       initialise a newStructureEnsemble
    #=========================================================================================

    def setUp(self):
        """
        Create a valid empty structureEnsemble
        """
        # Path of project to load (None for new project)
        self.projectPath = None

        with self.initialSetup():
            self.ensemble = self.project.newStructureEnsemble()

    #=========================================================================================
    # test_properties_structuresEnsemble
    #=========================================================================================

    def test_properties_structuresEnsemble_Serial(self):
        """
        Test that structureEnsemble attribute .serial is populated.
        Read the attribute, if it not populated then an error is raised.
        """
        self.assertEqual(self.project.structureEnsembles[0].serial, 1)

    def test_properties_structuresEnsemble_name(self):
        """
        Test that structureEnsemble attribute .label is populated.
        Read the attribute, if it not populated then an error is raised.
        If no error, then test the setter by setting and then getting to check consistent.
        """
        # checkGetSetAttr(self, self.project.structureEnsembles[0], 'name', 'ValidName')

        self.assertEquals(self.project.structureEnsembles[0].name, 'Structure')
        self.project.structureEnsembles[0].rename('validName')
        self.assertEquals(self.project.structureEnsembles[0].name, 'validName')

    def test_properties_structuresEnsemble_Comment(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        checkGetSetAttr(self, self.project.structureEnsembles[0], 'comment', 'ValidComment')


class StructureEnsembleTesting_Data(WrapperTesting):

    #=========================================================================================
    # setUp       initialise a newStructureEnsemble
    #=========================================================================================

    def setUp(self):
        """
        Create a valid empty structureEnsemble
        """
        # Path of project to load (None for new project)
        self.projectPath = None

        with self.initialSetup():
            self.ensemble = self.project.newStructureEnsemble()

    #=========================================================================================
    # test_properties_structuresEnsemble
    #=========================================================================================

    def test_properties_structuresEnsemble_setGoodData(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        self.data = self.ensemble.data
        self.ensemble.data = self.data

    def test_properties_structuresEnsemble_setBadData(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        self.data = self.ensemble.data
        with self.assertRaisesRegexp(TypeError, 'Value is not of type EnsembleData'):  # should raise ValueError
            self.ensemble.data = 'badValue'


class StructureEnsembleTesting_resetModels(WrapperTesting):

    #=========================================================================================
    # setUp       initialise a newStructureEnsemble
    #=========================================================================================

    def setUp(self):
        """
        Create a valid empty structureEnsemble
        """
        # Path of project to load (None for new project)
        self.projectPath = None

        with self.initialSetup():
            self.testAtomName = ['CA', 'C', 'N', 'O', 'H',
                                 'CB', 'HB1', ' HB2', 'HB3',
                                 'CD1', 'HD11', 'HD12', 'HD13', 'CD2', 'HD21', 'HD22', 'HD23',
                                 'CE', 'HE1', 'HE2', 'HE3',
                                 'CG', 'HG1', 'HG2', 'HG3',
                                 'CG1', 'HG11', 'HG12', 'HG13', 'CG2', 'HG21', 'HG22', 'HG23']
            self.testResidueName = ['ALA'] * 5 + ['ALA'] * 4 + ['LEU'] * 8 + ['MET'] * 4 + ['THR'] * 4 + ['VAL'] * 8
            self.testChainCode = ['A'] * 5 + ['B'] * 4 + ['C'] * 8 + ['D'] * 4 + ['E'] * 4 + ['F'] * 8
            self.testSequenceId = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
            self.testModelNumber = [1] * 5 + [2] * 4 + [3] * 8 + [4] * 4 + [5] * 4 + [6] * 8
            self.testModelNumberNew = [6] * 5 + [5] * 4 + [4] * 8 + [3] * 4 + [2] * 4 + [1] * 8
            self.testElement = ['H'] * 4 + ['O'] * 4 + ['C'] * 4 + ['N'] * 21
            self.testFuncName = ['H',
                                 'HB1', ' HB2', 'HB3',
                                 'HD11', 'HD12', 'HD13', 'HD21', 'HD22', 'HD23',
                                 'HE1', 'HE2', 'HE3',
                                 'HG1', 'HG2', 'HG3',
                                 'HG11', 'HG12', 'HG13', 'HG21', 'HG22', 'HG23']

            self.ensemble = self.project.newStructureEnsemble()
            self.data = self.ensemble.data
            self.data['atomName'] = self.testAtomName
            self.data['residueName'] = self.testResidueName
            self.data['chainCode'] = self.testChainCode
            self.data['sequenceId'] = self.testSequenceId
            self.data['modelNumber'] = self.testModelNumber

    #=========================================================================================
    # test_properties_structuresEnsemble_newSE
    #=========================================================================================

    def test_properties_structuresEnsemble_newSE(self):
        """
        Test that new structureEnsemble can be instantiated
        """
        self.newEnsemble = self.project.newStructureEnsemble(data=self.data)
        namedTuples = self.newEnsemble.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEquals(namedTuples[9], (AtomRecord(Index=10,
                                                      atomName='CD1',
                                                      residueName='LEU',
                                                      chainCode='C',
                                                      sequenceId=3,
                                                      modelNumber=3)))  # check initial values

    #=========================================================================================
    # test_properties_structuresEnsemble_resetModels
    #=========================================================================================

    def test_properties_structuresEnsemble_resetModels(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        self.assertEquals(list(self.data['atomName']), self.testAtomName)

        self.assertEqual(list(self.project.models[0].data['atomName']), self.testAtomName[0:5])
        self.assertEqual(list(self.project.models[1].data['atomName']), self.testAtomName[5:9])
        self.assertEqual(list(self.project.models[2].data['atomName']), self.testAtomName[9:17])
        self.assertEqual(list(self.project.models[3].data['atomName']), self.testAtomName[17:21])
        self.assertEqual(list(self.project.models[4].data['atomName']), self.testAtomName[21:25])
        self.assertEqual(list(self.project.models[5].data['atomName']), self.testAtomName[25:33])

    #=========================================================================================
    # test_properties_structuresEnsemble_resetModels
    #=========================================================================================

    def test_properties_structuresEnsemble_clearData(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        undo = self.project._undo

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEquals(namedTuples[9:17], (
            AtomRecord(Index=10, atomName='CD1', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=11, atomName='HD11', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=12, atomName='HD12', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=13, atomName='HD13', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=14, atomName='CD2', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=15, atomName='HD21', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=16, atomName='HD22', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=17, atomName='HD23', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3)
            ))
        self.project.models[2].delete()

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEquals(namedTuples[9:17], (
            AtomRecord(Index=10, atomName='CE', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=11, atomName='HE1', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=12, atomName='HE2', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=13, atomName='HE3', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=14, atomName='CG', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=15, atomName='HG1', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=16, atomName='HG2', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=17, atomName='HG3', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5)
            ))
        undo.undo()  # ejb - this now does a group undo

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEquals(namedTuples[9:17], (
            AtomRecord(Index=10, atomName='CD1', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=11, atomName='HD11', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=12, atomName='HD12', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=13, atomName='HD13', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=14, atomName='CD2', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=15, atomName='HD21', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=16, atomName='HD22', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3),
            AtomRecord(Index=17, atomName='HD23', residueName='LEU', chainCode='C', sequenceId=3,
                       modelNumber=3)
            ))
        undo.redo()

        namedTuples = self.data.as_namedtuples()
        AtomRecord = namedTuples[0].__class__
        self.assertEquals(namedTuples[9:17], (
            AtomRecord(Index=10, atomName='CE', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=11, atomName='HE1', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=12, atomName='HE2', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=13, atomName='HE3', residueName='MET', chainCode='D', sequenceId=4,
                       modelNumber=4),
            AtomRecord(Index=14, atomName='CG', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=15, atomName='HG1', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=16, atomName='HG2', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5),
            AtomRecord(Index=17, atomName='HG3', residueName='THR', chainCode='E', sequenceId=5,
                       modelNumber=5)
            ))

    #=========================================================================================
    # test_properties_Model
    #=========================================================================================

    def test_properties_Model_Serial(self):
        """
        Test that model attribute .serial is populated.
        Requires valid modelNumber to be assigned to atoms.
        Read the attribute, if it not populated then an error is raised.
        """
        self.assertEqual(self.project.models[0].serial, 1)

    def test_properties_Model_Label(self):
        """
        Test that structureEnsemble attribute .label is populated.
        Read the attribute, if it not populated then an error is raised.
        If no error, then test the setter by setting and then getting to check consistent.
        """
        checkGetSetAttr(self, self.project.models[0], 'label', 'ValidName')

    def test_properties_Model_Comment(self):
        """
        Test that structureEnsemble attribute .comment is populated.
        """
        checkGetSetAttr(self, self.project.models[0], 'comment', 'ValidComment')
