import pandas as pd


def createPeakListDF(peakList, paramName, value):
  '''
  :param peakList: ccpnPeakList obj
  :param paramName: str.  EG. Temperature, Concentration
  :param value: parameter value
  :return: dataframe of 'residueNumber', 'Nh', 'Hn', 'Hpos', 'Npos', 'height', 'paramValue'
  '''

  items = []
  columns = ['residueNumber','Hn', 'Nh', 'Hpos', 'Npos', 'height', str(paramName)]
  if peakList.peaks is not None:
    for peak in peakList.peaks:
      if peak.assignedNmrAtoms is not None:
        if len(peak.assignedNmrAtoms)>0:

          residueNumber = peak.assignedNmrAtoms[0][0].nmrResidue.sequenceCode
          Hn = peak.assignedNmrAtoms[0][0].pid
          Nh = peak.assignedNmrAtoms[0][1].pid
          HnPos =  str(peak.position[0])
          NhPos = str(peak.position[1])
          height = str(peak.height)
          param = value

          items.append([residueNumber, Hn, Nh, HnPos, NhPos, height, param])

  dataFrame =  pd.DataFrame(items, columns=columns)
  dataFrame['residue number'] = dataFrame.index.astype('int')

  dataFrame.index = dataFrame['residueNumber']

  return dataFrame



def calculateChemicalShift(data):

  sel = data['Hn'].str.endswith('H')
  sel = sel & data['Nh'].str.endswith('N')
  data = data[sel]

  data['Hpos'] = data['Hpos'].astype('float64')
  data['Npos'] = data['Npos'].astype('float64')

  shifts = {}
  for r, pid in zip(data['residueNumber'].unique(), data['Hn']) :
    d = data[data['residueNumber']==r]
    d.index=d.temp
    min_temp = d['temp'].min()

    start_H = float(d.loc[min_temp, 'Hpos'])
    start_N = float(d.loc[min_temp, 'Npos'])

    delta = (((d['Hpos']- start_H)*7)**2 + (d['Npos'] - start_N)**2)**0.5
    delta.name = pid
    shifts[int(r)] = delta.sort_index()

  max_shift = 0
  for shift in shifts.values():
    if shift.max() > max_shift:
      max_shift = shift.max()

  return shifts

def getChemicalShifts(shifts):
  for n, i in sorted(shifts.items()):
    max_index = shifts[n].index.max()
    print(i.name, str(shifts[n].loc[max_index]))
    return i.name, str(shifts[n].loc[max_index])


pl1 = project.getByPid('PL:GV04_2899.2')
pl2 = project.getByPid('PL:GV04_2950.2')
pls = {pl1:'16.75', pl2:'21.87'}

dfs = []
for pl, t in pls.items():
    print(pl, 'peakList', t, 'params')
    d = createPeakListDF(pl, 'temp', t)
    dfs.append(d)
dataFrame = pd.concat(dfs)
print(dataFrame)

shifts = calculateChemicalShift(dataFrame)
# getChemicalShifts(shifts)

ds = project.newDataSet(title='name')
ds.newData(ds.title)

for n, i in sorted(shifts.items()):
  max_index = shifts[n].index.max()
  ds.data[0].setParameter(i.name,(str(n), str(shifts[n].loc[max_index])) )
  print(
    {i.name : (str(n), str(shifts[n].loc[max_index]))}
    )

