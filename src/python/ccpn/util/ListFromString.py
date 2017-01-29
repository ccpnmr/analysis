from typing import Union
from typing import Iterable

ListOrString = Union[int, float, str, Iterable[Union[int, float, str]]]



def listFromString(string:str) -> list:
    '''
    Convenience function to turn a string into a list of items.
    '''
    l = [e.strip() for e in string.split(',')]
    lst = []
    for i in l:
      hyphenated = i.split('-')
      if len(hyphenated) == 1:
        lst += hyphenated
      elif len(hyphenated) == 2:
        lst += range(int(hyphenated[0]), int(hyphenated[1]) + 1)
      else:
        raise ValueError('bad selector specification')
    return lst

