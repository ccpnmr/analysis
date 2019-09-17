""""
--------------------------------------------------------------------------------------------
 Testing
--------------------------------------------------------------------------------------------
"""

from ccpn.util.traits.CcpNmrTraits import Dict, Odict, Int, List, CPath, Adict
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, RecursiveDictHandler, RecursiveListHandler

class TestObj(CcpNmrJson):

    saveAllTraitsToJson = True
    odict = Odict()
    adict = Adict()

    theDict = Dict().tag(jsonHandler=RecursiveDictHandler)
    theList = List().tag(jsonHandler=RecursiveListHandler)
    thePath = CPath(default_value='bla.dat')

TestObj.register()


class TestObj2(CcpNmrJson):
    saveAllTraitsToJson = True
    value = Int(default_value = 1)

    def __init__(self, value=0):
        self.value = value

    def __str__(self):
        return '<TestObj2: value=%s>' % self.value

    def __repr__(self):
        return str(self)

TestObj2.register()


def test():
    "Test it; returns two objects"

    obj1 = TestObj()

    for v in [10, 11, 12]:
        obj2 = TestObj2(v)
        obj1.theDict[str(v)] = obj2
    obj1.theDict['aap'] = 'noot'

    for v in [20, 21, 22]:
        obj1.odict[str(v)] = v

    for v in [30, 31, 32]:
        obj1.adict[str(v)] = v*10

    obj1.theList.append('mies')
    for v in [40, 41, 42]:
        obj2 = TestObj2(v)
        obj1.theList.append(obj2)

    js = obj1.toJson(ident=None)
    print(js)
    obj2 = TestObj().fromJson(js)
    print(obj2)

    return (obj1, obj2)



if __name__ == '__main__':

    test()
