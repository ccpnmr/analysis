""""
--------------------------------------------------------------------------------------------
 Testing
--------------------------------------------------------------------------------------------
"""

from ccpn.util.traits.CcpNmrTraits import Dict, Odict, Int, List
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, RecursiveDictHandler, \
    RecursiveListHandler

class TestObj(CcpNmrJson):
    saveAllTraitsToJson = True
    odict = Odict()
    theDict = Dict().tag(jsonHandler=RecursiveDictHandler)
    theList = List().tag(jsonHandler=RecursiveListHandler)
TestObj.register()


class TestObj2(CcpNmrJson):
    saveAllTraitsToJson = True
    value = Int(default_value = 1)

    def __init__(self, value=0):
        self.value = value
TestObj2.register()


if __name__ == '__main__':

    obj1 = TestObj()

    for v in [10, 11, 12]:
        obj2 = TestObj2(v)
        obj1.theDict[str(v)] = obj2

    for v in [20, 21, 22]:
        obj1.odict[str(v)] = v

    for v in [30, 31, 32]:
        obj2 = TestObj2(v)
        obj1.theList.append(obj2)

    js = obj1.toJson()
    print(js)
    obj2 = TestObj().fromJson(js)
    print(obj2)

