


# the code below is from PyQtGraph
# Not fully working!!! To be fixed



from ccpn.ui.gui.exporters1D.Exporter import Exporter
from pyqtgraph.parametertree import Parameter
from pyqtgraph  import PlotItem
import pyqtgraph as pg
import pandas as pd
from numpy import nan as Nan


__all__ = ['CSVExporter']


class TextExporter(Exporter):
  Name = "Csv from 1D plot data"
  windows = []

  def __init__(self, item):
    Exporter.__init__(self, item)
    self.params = Parameter(name='params', type='group', children=[
      {'name': 'separator', 'type': 'list', 'value': 'comma', 'values': ['comma']},

      # {'name': 'precision', 'type': 'int', 'value': 10, 'limits': [0, None]},
      # {'name': 'columnMode', 'type': 'list', 'values': ['(x,y) per plot', '(x,y,y,y) for all plots']}
    ])

  def parameters(self):
    return self.params

  def getPlottedData(self):

    data = []
    ci = self.item.allChildItems()
    for i in ci:
      if isinstance(i, pg.PlotDataItem):
        x, y = i.getData()
        if x is not None:
          if len(x) > 0:
            data.append((x,y))
    return data

  def export(self, fileName=None):

    if not isinstance(self.item, PlotItem):
      raise Exception("Must have a PlotItem selected for CSV export.")

    if fileName is None:
      self.fileSaveDialog(filter=["*.csv"])#, "*.tsv"])
      return

    self.fileDialog.selectNameFilter('*.tsv')

    data = self.getPlottedData()
    df = []
    if data:

      for i in data:
        x,y = i

        d = pd.DataFrame([x,y])
        d = d.transpose()
        d.columns = ['x', 'y']
        df.append(d)
    df = pd.concat(df, keys=[str(i) for i in range(len(df))])
    df.to_csv(fileName)
    # print(d)

    # if self.params['separator'] == 'comma':
    # d.to_csv(fileName)
    # else:
    #   d.to_table(fileName)



TextExporter.register()


