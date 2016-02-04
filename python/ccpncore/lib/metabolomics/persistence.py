__author__ = 'TJ Ragan'

from collections import OrderedDict

class Borg:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state


class MetabolomicsPersistenceDict(OrderedDict):
  class __Inner(OrderedDict):
    pass
  instance = None

  def __new__(cls, *args, **kwargs):
    if cls.instance is None:
      cls.instance = cls.__Inner(*args, **kwargs)
    return cls.instance
