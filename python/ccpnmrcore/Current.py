__author__ = 'simon'

_fields = ['spectrum','spectra','peak','peaks','pane','region','position']

class Current:

  def __init__(self):
    for field in _fields:
      setattr(self,field,None)