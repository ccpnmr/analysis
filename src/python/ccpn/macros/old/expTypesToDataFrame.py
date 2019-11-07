



def _experimentTypesToDataFrame(project, dimensionCount):
  '''
  
  :param project: 
  :param dimensionCount: int 1 to 6
  :return: dataFrame containing the experiment types available in CcpNmr V3 for the given Dimension
  '''
  import pandas as pd
  axisCodes = []
  stdExpType = []
  ccpnExpType = []
  for ac, expTypes in project._experimentTypeMap[dimensionCount].items():
    for std, ccpn in expTypes.items():
      axisCodes.append(''.join(ac))
      stdExpType.append(std)
      ccpnExpType.append(ccpn)

  return pd.DataFrame({'Codes': axisCodes, 'STD': stdExpType, 'CCPN': ccpnExpType})

## save in excel
# df.to_excel(path, sheet_name=str(dimensionCount)+'D', index=False)


