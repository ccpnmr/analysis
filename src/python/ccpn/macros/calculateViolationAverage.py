"""
Calculate statistics for violations found in dataSets
"""

import pandas as pd
import numpy as np
from ccpn.core.Restraint import Restraint
from ccpn.core.lib import Pid


_RESTRAINTTABLE = 'restraintTable'
_VIOLATIONTABLE = 'violationTable'
_VIOLATIONRESULT = 'violationResult'
_RUNNAME = 'runName'
DEFAULT_RUNNAME = 'output'

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 7)

print('Calculate statistics for violations found in dataSets')

requiredColumns = ['model_id', 'restraint_id', 'atoms', 'violation']
printAverage = True

_results = {}

# # get the dataSets that contain data with a matching name - should be violations
# violationDataItems = [(restraintTable, data) for restraintTable in project.restraintTables
#                                   for data in restraintTable.structureData.data
#                                   if restraintTable.name == data.name]

violationDataItems = [(restraintTable, vTable.data) for restraintTable in project.restraintTables
                      for vTable in project.violationTables
                      if restraintTable.pid == vTable.getMetadata(_RESTRAINTTABLE)]

print(f'Available data containing violationLists:')
for (restraintTable, _df) in violationDataItems:

    print(f'*********************************************************')
    print(f'  {_df.columns}')

    invalidColumns = [col for col in requiredColumns if col not in _df.columns]
    if invalidColumns:
        print(f'    missing required columns {invalidColumns}')
        continue

    print(f'    violationItem:')

    # get the models defined for the violations
    models = [v for k, v in _df.groupby(['model_id'], as_index=False)]

    if models:
        print(f'    MODELS {len(models)}')
        print(f'{models[0].columns}')

        restraintsFromModels = []

        # use the serial to get the restraint from the peak - make list for each model just to check is actually working
        for mm, _mod in enumerate(models):
            restraintsFromModel = []
            restraintsFromModels.append(restraintsFromModel)
            for serial in _mod['restraint_id']:
                restraintId = Pid.IDSEP.join(('' if x is None else str(x)) for x in (restraintTable.structureData.name, restraintTable.name, serial))
                modelRestraint = project.getObjectsByPartialId(className='Restraint', idStartsWith=restraintId)
                restraintsFromModel.append(modelRestraint[0].pid if modelRestraint else None)

        # check all the same
        print(all(restraintsFromModels[0] == resMod for resMod in restraintsFromModels))

        # calculate statistics for the violations and concatenate into a single dataFrame
        average = pd.concat([v['violation'].reset_index(drop=True) for v in models],
                            ignore_index=True,
                            axis=1).agg(['min',
                                         'max',
                                         'mean',
                                         'std',
                                         lambda x: int(sum(x > 0.3)),
                                         lambda x: int(sum(x > 0.5)), ], axis=1)

        print('**** average *****')
        print(average)

        # # merge the atom columns - done in nef loader?
        # atoms = models[0]['atom1'].map(str) + ' - ' + models[0]['atom2'].map(str)

        # remove the indexing for the next concat
        atoms = models[0]['atoms'].reset_index(drop=True)
        average.reset_index(drop=True)

        print('**** atoms *****')
        print(atoms)
        pids = pd.DataFrame(restraintsFromModels[0], columns=['pid'])
        # ids = models[0]['restraint_id']
        # subIds = models[0]['restraint_sub_id']

        # build the result dataFrame
        result = pd.concat([pids, atoms, average], ignore_index=True, axis=1)

        # rename the columns (lambda just gives the name 'lambda')
        result.columns = ('RestraintPid', 'Atoms', 'Min', 'Max', 'Mean', 'STD', 'Count>0.3', 'Count>0.5')

        # put into a new dataTable
        output = restraintTable.structureData.newDataTable(name=DEFAULT_RUNNAME)
        output.setMetadata(_RESTRAINTTABLE, restraintTable.pid)
        output.setMetadata(_VIOLATIONRESULT, True)
        output.data = result

        if restraintTable in _results:
            print('   Already found')
        _results[restraintTable] = result
