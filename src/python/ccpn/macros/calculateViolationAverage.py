"""
Calculate statistics for violations found in dataSets
"""

import pandas as pd
import numpy as np
from ccpn.core.Restraint import Restraint
from ccpn.core.lib import Pid

print('Calculate statistics for violations found in dataSets')

requiredColumns = ['model_id', 'restraint_id', 'atoms', 'violation']
printAverage = True

_results = {}

# get the dataSets that contain data with a matching name - should be violations
violationDataItems = [(restraintList, data) for restraintList in project.restraintLists 
                                  for data in restraintList.dataSet.data
                                  if restraintList.name == data.name]

print(f'Available data containing violationLists:')
for (restraintList, violationDataItem) in violationDataItems:
    
    print(f'  {violationDataItem}')
    for k, violationRun in violationDataItem.parameters.items():
        
        if k == 'results':
            # skip results
            continue

        invalidColumns = [col for col in requiredColumns if col not in  violationRun.columns]
        if invalidColumns:
            print(f'    {k} missing required columns {invalidColumns}')
            continue

        print(f'    violationItem: {k}')
        
        # grab the models defined for the violations
        models = [v for k, v in violationRun.groupby(['model_id'], as_index=False)]

        if models:
            print(f'    MODELS {len(models)}')
            print(f'{models[0].columns}')

            restraintsFromModel = []
            
            # use the serial to get the restraint from the peak
            for serial in models[0]['restraint_id']:
                restraintId = Pid.IDSEP.join(('' if x is None else str(x)) for x in (restraintList.dataSet.name, restraintList.name, serial))
                modelRestraint = project.getObjectsByPartialId(className='Restraint', idStartsWith=restraintId)
                restraintsFromModel.append(modelRestraint[0].pid if modelRestraint else None)
            
            # calculate statistics for the violations
            average = pd.concat([v.reset_index()['violation'] for v in models], axis=1).agg(['min', 
                                                                                            'max', 
                                                                                            'mean',
                                                                                            'std', 
                                                                                            lambda x : int(sum(x > 0.3)), 
                                                                                            lambda x : int(sum(x > 0.5)),], axis=1)
            
            # # merge the atom columns - done in nef loader?
            # atoms = models[0]['atom1'].map(str) + ' - ' + models[0]['atom2'].map(str)
            atoms = models[0].reset_index()['atoms']
            pids = pd.DataFrame(restraintsFromModel, columns=['pid'])
            ids = models[0].reset_index()['restraint_id']
            subIds = models[0].reset_index()['restraint_sub_id']
            
            # build the result dataFrame
            result = pd.concat([pids, atoms, average], ignore_index=True, axis=1)
    
            # rename the columns (lambda just gives the name 'lambda')
            result.columns = ('RestraintPid', 'Atoms', 'Min', 'Max', 'Mean', 'STD', 'Count>0.3', 'Count>0.5')

            if printAverage:
                val = result[['RestraintPid', 'Atoms', 'Mean']]
                # print generated dataFrame (selected columns)
                print(f'\n{val}')
                
            # insert results into the parameters as 'results'
            violationDataItem.setParameter('results', result)

    #         # build the result dataFrame
    #         result = pd.concat([ids, subIds, atoms, average], ignore_index=True, axis=1)
    # 
    #         # rename the columns (lambda just gives the name 'lambda')
    #         result.columns = ('Id', 'SubId', 'Atoms', 'Min', 'Max', 'Mean', 'STD', 'Count>0.3', 'Count>0.5')

    #         if printAverage:
    #             val = result[['Id', 'SubId', 'Mean']]
    #             # print generated dataFrame (selected columns)
    #             print(f'\n{val}')
    #             
    #         # insert results into the parameters as 'results'
    #         violationDataItem.setParameter('results', result)

            if restraintList in _results:
                print('   Already found')
            _results[restraintList] = result
