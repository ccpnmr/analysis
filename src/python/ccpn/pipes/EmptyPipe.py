__author__ = 'TJ Ragan'

from ccpn.framework.lib.Pipe import PandasPipe
import pandas as pd

class EmptyExtension(PandasPipe):
  METHODNAME = 'Empty Extension'

  def run(self, dataframe:pd.DataFrame) -> pd.DataFrame:
    print('empty')
    return dataframe
