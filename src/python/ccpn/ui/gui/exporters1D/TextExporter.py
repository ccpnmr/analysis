from ccpn.ui.gui.exporters1D.Exporter import Exporter
from pyqtgraph.parametertree import Parameter
from pyqtgraph import PlotItem
import pyqtgraph as pg
import pandas as pd
from numpy import nan as Nan
from pyqtgraph.widgets.FileDialog import FileDialog
from PyQt5 import QtGui, QtWidgets, QtCore


__all__ = ['CSVExporter']


class TextExporter(Exporter):
    Name = "Text"
    windows = []

    def __init__(self, item):
        Exporter.__init__(self, item)
        self.params = Parameter(name='params', type='group', children=[
            {'name': 'separator', 'type': 'list', 'value': 'separator,', 'values': ['*.csv', '*.tsv']},

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
                        data.append((x, y))
            if isinstance(i, pg.BarGraphItem):
                data.append((i.xValues, i.yValues))
        return data

    def _createDataframe(self, data):
        df = []
        for i in data:
            x, y = i
            d = pd.DataFrame([x, y])
            d = d.transpose()
            d.columns = ['x', 'y']
            df.append(d)
        df = pd.concat(df, keys=[str(i) for i in range(len(df))])
        return df

    def export(self, fileName=None):

        if not isinstance(self.item, PlotItem):
            raise Exception("Must have a PlotItem selected for CSV export.")

        if fileName is None:
            filter = self.params['separator']
            self.fileSaveDialog(filter=filter)  #["*.csv", "*.tsv"])
            return

        data = self.getPlottedData()
        if data:
            df = self._createDataframe(data)
            if self.params['separator'] == '*.csv':
                df.to_csv(fileName)
            else:
                df.to_csv(fileName, sep='\t')


TextExporter.register()
