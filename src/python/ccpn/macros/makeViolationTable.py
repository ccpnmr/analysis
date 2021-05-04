"""
Create violation dataFrames
"""

import pandas as pd
import numpy as np
from ccpn.core.Restraint import Restraint
from ccpn.core.lib import Pid

print('Create violation dataFrames')

def _getContributions(restraint):
    return [' - '.join(sorted(ri)) for rc in restraint.restraintContributions 
            for ri in rc.restraintItems]

# get the target peakLists
pkList = project.peakLists[0]
pks = pkList.peaks

# check the first 2 restraintLists
resLists = project.restraintLists
print(f' restraintLists   {resLists}')

ids = pd.DataFrame({'#': [pk.serial for pk in pks], 
                    'Peak': [pk.pid for pk in pks], 
                    '_object': [pk for pk in pks], 
                    'Expand': [None for pk in pks]})

# make a reference for quicker access later
contribs = {res: _getContributions(res) for rList in resLists for res in rList.restraints}

# get the maximum number of restraintItems from each restraint list
counts = [np.array([sum([
              len(contribs[res]) for res in pk.restraints if res and res.restraintList == rList
              ])
              for pk in pks])
                for rList in resLists]
maxCount = np.max(counts, axis=0)

# allPks = pd.DataFrame([(pk.pid, pk, None)  for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['Peak', '_object', 'Expand'])
allPkPids = pd.DataFrame([pk.pid  for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['PeakPid', ])
index = pd.DataFrame([ii for ii in range(1, len(allPkPids)+1)], columns=['index'])
allPks = pd.DataFrame([(pk.pid, pk, None)  for pk, count in zip(pks, maxCount) for rr in range(count)], columns=['PeakPid', '_object', 'Expand'])

dfs = {}
ll = [(None, None)] * sum(maxCount)
# aa = [(None, None)] * sum(maxCount)

for lCount, rl in enumerate(resLists):
    head = 0

    for pk, cc, maxcc in zip(pks, counts[lCount], maxCount):
        _res = [(res.pid, _atom) for res in pk.restraints if res.restraintList == rl
                    for _atom in contribs[res]]
        if _res:
            ll[head:head+len(_res)] = _res

        head += maxcc
            
    # put the pid and atoms into another table to be concatenated to the right - lCount = index in resLists
    dfs[rl] = pd.concat([allPkPids, 
                          pd.DataFrame(ll, columns=[f'RestraintPid_{lCount+1}', 
                                                                        f'Atoms_{lCount+1}'])], axis=1)

    # now need to add the results to the right with merge on pid/atom
    
# dfs = [pd.DataFrame([(pk, res) for pk, cc, maxcc in zip(pks, count[lCount], maxCount) 
#                                              for res in pk.restraints if res.restraintList == rl], 
#                     columns=['Peak', f'Pid_{cc+1}']) for lCount, rl in enumerate(resLists)]
# # rl1 = pd.merge(ids['Peak'], df1, how='right')

# print(f'  {dfs[0]}')

                # ids = pd.DataFrame({'#': [pk.serial for pk in buildList], 'Peak': [pk.pid for pk in buildList], '_object': [pk for pk in buildList], 'Expand': [None for pk in buildList]})
                # df1 = pd.DataFrame([(pk, res) for pk in buildList for res in pk.restraints if res.restraintList == rl], columns=['Peak', 'Pid_1'])
                # rl1 = pd.merge(ids['Peak'], df1, how='right')

# get the dataSets that contain data with a matching 'result' name - should be violations
violationResults = {resList: viols.copy() if viols is not None else None
                                  for resList in project.restraintLists 
                                  for data in resList.dataSet.data if resList.name == data.name
                                  for k, viols in data.parameters.items() if k == 'results'}

# rename the columns to match the order in visible list
for ii, (k, resViol) in enumerate(violationResults.items()):
    resViol.columns = [vv+f'_{ii+1}' for vv in resViol.columns]
    
# check - results maybe None if not found
#                                                                             res.pid
# pd.merge(dfs[0], violationResults[resLists[0]], on=['Pid_1', 'Atoms_1'], how='left').fillna(0.0)
# pd.merge(dfs[1], violationResults[resLists[1]], on=['Pid_2', 'Atoms_2'], how='left').fillna(0.0)

_out = {}
for ii, resList in enumerate(resLists):
    if resList in violationResults:

        _left = dfs[resList]
        _right = violationResults[resList]
        if (f'RestraintPid_{ii+1}' in _left.columns and f'Atoms_{ii+1}' in _left.columns) and \
            (f'RestraintPid_{ii+1}' in _right.columns and f'Atoms_{ii+1}' in _right.columns):
             
            print(f'     generating _out[{resList}] for ({ii+1})')
            _out[resList] = pd.merge(_left, _right, on=[f'RestraintPid_{ii+1}', f'Atoms_{ii+1}'], how='left').drop(columns=['PeakPid']).fillna(0.0)

_table = pd.concat([index, allPkPids, *_out.values()], axis=1)
