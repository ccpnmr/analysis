"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-02 18:40:28 +0000 (Tue, November 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
import datetime
import numpy
import pandas as pd
from ccpn.util.Tensor import Tensor

from ccpn.core.testing.WrapperTesting import WrapperTesting


class DataSetTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    def test_complex_creation(self):
        undo = self.project._undo
        self.project.newUndoPoint()
        dd = {
            'programName'   : 'aaa.aaa',
            'programVersion': 'bbb.bbb',
            'title'         : 'TryMe!',
            'creationDate'  : datetime.datetime.now(),
            'dataPath'      : 'abc/de/f.g',
            'uuid'          : 'blah',
            'comment'       : 'why?'
            }
        dataSet = self.project.newStructureData(**dd)
        undo.undo()
        undo.redo()
        for key, val in sorted(dd.items()):
            self.assertEqual(getattr(dataSet, key), val)


class CalculationStepTest(WrapperTesting):
    # Path of project to load (None for new project
    projectPath = None

    def test_simple_creation(self):
        dataSet = self.project.newStructureData()
        step1 = dataSet.newCalculationStep(programName='CcpNmr')
        self.assertEqual(step1.programName, 'CcpNmr')

    def test_complex_creation(self):
        undo = self.project._undo
        self.project.newUndoPoint()
        dataSet = self.project.newStructureData()
        dataSet2 = self.project.newStructureData(uuid='dataSet2-12345')
        dataSet3 = self.project.newStructureData(uuid='dataSet3-67890')
        dd = {
            'programName'   : 'aaa.aaa',
            'programVersion': 'bbb.bbb',
            'scriptName'    : 'ccc ccc',
            'script'        : 'dd\nee\n',
            'inputDataUuid' : dataSet2.uuid,
            'outputDataUuid': dataSet3.uuid,
            }
        step1 = dataSet.newCalculationStep(**dd)
        for key, val in sorted(dd.items()):
            self.assertEqual(getattr(step1, key), val)
        self.assertEqual(step1.inputStructureData, dataSet2)
        self.assertEqual(step1.outputStructureData, dataSet3)
        self.assertEqual(dataSet2.outputCalculationSteps, [step1])
        self.assertEqual(dataSet3.inputCalculationSteps, [])
        undo.undo()
        undo.redo()
        for key, val in sorted(dd.items()):
            self.assertEqual(getattr(step1, key), val)
        self.assertEqual(step1.inputStructureData, dataSet2)
        self.assertEqual(step1.outputStructureData, dataSet3)
        self.assertEqual(dataSet2.outputCalculationSteps, [step1])
        # NB inputCalculationSteps MUST be part of the data set itself, hence this shoudl be empty
        self.assertEqual(dataSet3.inputCalculationSteps, [])

    def test_link_setting(self):
        undo = self.project._undo
        self.project.newUndoPoint()
        dataSet = self.project.newStructureData(uuid='dataSet-1')
        dataSet2 = self.project.newStructureData(uuid='dataSet-2')
        dataSet3 = self.project.newStructureData(uuid='dataSet-3')
        step1 = dataSet.newCalculationStep()
        step1.inputStructureData = dataSet2
        self.assertEqual(step1.inputDataUuid, dataSet2.uuid)
        step1.inputStructureData = dataSet3
        self.assertEqual(step1.inputDataUuid, dataSet3.uuid)
        step1.inputStructureData = None
        undo.undo()
        undo.redo()
        self.assertEqual(step1.inputDataUuid, None)

    def test_uuid_error(self):
        dataSet = self.project.newStructureData(uuid='dataSet-13579')
        dataSet2 = self.project.newStructureData(uuid='daytaSet2-24680')
        with self.assertRaises(ValueError):
            dataSet.newCalculationStep(inputDataUuid=dataSet2.uuid, inputStructureData=dataSet2)


class DataTest(WrapperTesting):
    # Path of project to load (None for new project)
    projectPath = None

    def test_create_data(self):
        undo = self.project._undo
        self.project.newUndoPoint()
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='try1', attachedObjectPid='blah')
        undo.undo()
        undo.redo()
        self.assertEqual(data1.name, 'try1')
        self.assertEqual(data1.attachedObjectPid, 'blah')
        self.assertIsNone(data1.attachedObject)

    def test_data_object_link(self):
        undo = self.project._undo
        self.project.newUndoPoint()
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='try1', attachedObjectPid=dataSet.pid)
        self.assertEqual(data1.attachedObject, dataSet)

        note = self.project.newNote(name='nn')
        data1.attachedObject = note
        self.assertEqual(data1.attachedObject, note)
        self.assertEqual(data1.attachedObjectPid, note.pid)
        note.rename('different')
        undo.undo()
        undo.redo()
        self.assertIsNone(data1.attachedObject)

    def test_data_parameters(self):
        testpars = collections.OrderedDict()
        for key, val in [
            ('bbb', 1), ('ccc', [1, 2, 3]), ('ddd', True), ('aaa', ()), ('xxx', 'xxx'), ('dict', {1: 1}),
            ('odict', collections.OrderedDict(((2, 100), (1, 10))))
            ]:
            testpars[key] = val

        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='try1', attachedObjectPid=dataSet.pid)
        undo = self.project._undo
        self.project.newUndoPoint()
        self.assertEqual(data1.parameters, {})
        data1.setParameter('aaa', 1)
        self.assertEqual(data1.parameters, {'aaa': 1})
        data1.updateParameters(testpars)
        self.assertEqual(data1.parameters, testpars)
        data1.deleteParameter('ccc')
        del testpars['ccc']
        self.assertEqual(data1.parameters, testpars)
        data1.setParameter('ddd', 11)
        testpars['ddd'] = 11
        self.assertEqual(data1.parameters, testpars)
        undo.undo()
        undo.redo()
        self.assertEqual(data1.parameters, testpars)
        data1.clearParameters()
        self.assertEqual(data1.parameters, {})

        self.assertEqual(data1.pid, 'DA:myStructureData.try1')
        data1.rename('different')
        undo.undo()
        undo.redo()
        self.assertEqual(data1.pid, 'DA:myStructureData.different')

    def test_numpy_parameter(self):
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='try1', attachedObjectPid=dataSet.pid)
        undo = self.project._undo
        self.project.newUndoPoint()
        data1.setParameter('ndarray', numpy.ndarray((5, 3, 1)))
        undo.undo()
        undo.redo()
        self.assertTrue(isinstance(data1.parameters['ndarray'], numpy.ndarray))

    def test_tensor_parameter(self):
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='try1', attachedObjectPid=dataSet.pid)
        undo = self.project._undo
        self.project.newUndoPoint()
        data1.setParameter('tensor', Tensor._fromDict({'orientationMatrix': numpy.identity(3),
                                                       'isotropic'        : 2.1, 'axial': -3.0, 'rhombic': 0.9}))
        undo.undo()
        undo.redo()
        tensor = data1.parameters['tensor']
        self.assertTrue(isinstance(tensor, Tensor))
        self.assertAlmostEquals(tensor.isotropic, 2.1)
        self.assertAlmostEquals(tensor.axial, -3.0)
        self.assertAlmostEquals(tensor.rhombic, 0.9)

    def test_Pandas_parameter(self):
        """
        Test that a Pandas Dataframe can be stored as a Dataset parameter
        """
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='Pandas', attachedObjectPid=dataSet.pid)
        self.assertEqual(data1.attachedObject, dataSet)
        undo = self.project._undo
        self.project.newUndoPoint()

        # generate Pandas Dataframe
        self.Panda = pd.DataFrame(numpy.random.randint(0, 100, size=(100, 4)), columns=list('ABCD'))

        data1.setParameter('pandasDataframe', self.Panda)
        undo.undo()
        undo.redo()
        self.assertTrue(isinstance(data1.parameters['pandasDataframe'], self.Panda.__class__))

    def test_EnsembleData_parameter(self):
        """
        Test that an EnsembleData can be stored as a Dataset parameter
        """
        dataSet = self.project.newStructureData()
        data1 = dataSet.newData(name='EnsembleData', attachedObjectPid=dataSet.pid)
        self.assertEqual(data1.attachedObject, dataSet)
        undo = self.project._undo
        self.project.newUndoPoint()

        # generate simplew EnsembleData
        self.ensemble = self.project.newStructureEnsemble()
        self.data = self.ensemble.data
        self.data['y'] = [2, 1, 2, 1, 2, 1, 2, 1] * 2
        self.data['z'] = None
        self.data['modelNumber'] = [2, 2, 2, 2, 1, 1, 1, 1] * 2
        undo.undo()
        undo.redo()

        data1.setParameter('EnsembleData', self.data)
        undo.undo()  # needs to undo the setParameter
        undo.redo()
        self.assertTrue(isinstance(data1.parameters['EnsembleData'], self.data.__class__))
