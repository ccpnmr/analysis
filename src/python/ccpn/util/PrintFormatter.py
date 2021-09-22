"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-09-22 11:47:47 +0100 (Wed, September 22, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-06-28 18:39:46 +0100 (Mon, June 28, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import OrderedDict
from functools import partial
from ccpn.util.FrozenDict import FrozenDict
from ccpn.util.OrderedSet import OrderedSet, FrozenOrderedSet


class PrintFormatter(object):
    """
    Class to produce formatted strings from python objects.

    Includes standard python objects: list, tuple, dict, set, bytes, str, int, float, complex, bool, type(None)
    and additional objects: OrderedDict, OrderedSet, frozenset, FrozenOrderedSet, FrozenDict

    Objects not added to formatter will return a pickled object if ALLOWPICKLE is True, otherwise None

    * The original basis for this came from stackOverflow somewhere, but I can't seem to find it now
    """
    TAB = '    '
    CRLF = '\n'
    ALLOWPICKLE = False

    def __init__(self):
        """Initialise the class
        """
        self.registeredFormats = {}
        self.literalEvals = {}
        self.indent = 0

        # list of default registered objects
        _registrations = {object          : PrintFormatter.formatObject,
                          dict            : PrintFormatter.formatDict,
                          list            : PrintFormatter.formatList,
                          tuple           : PrintFormatter.formatTuple,
                          set             : PrintFormatter.formatSet,
                          OrderedSet      : partial(PrintFormatter.formatListType, klassName=OrderedSet.__name__),
                          FrozenOrderedSet: partial(PrintFormatter.formatListType, klassName=FrozenOrderedSet.__name__),
                          frozenset       : partial(PrintFormatter.formatSetType, klassName=frozenset.__name__),
                          OrderedDict     : PrintFormatter.formatOrderedDict,
                          FrozenDict      : PrintFormatter.formatFrozenDict,
                          }

        # add objects to the formatter
        for obj, func in _registrations.items():
            self.registerFormat(obj, func)

        # add objects to the literal_eval list
        for klass in (OrderedDict, OrderedSet, frozenset, FrozenOrderedSet, FrozenDict, self.PythonObject):
            self.registerLiteralEval(klass)

    def registerFormat(self, obj, callback):
        """Register an object class to formatter
        """
        self.registeredFormats[obj] = callback

    def registerLiteralEval(self, obj):
        """Register a literalEval object class to formatter
        """
        self.literalEvals[obj.__name__] = obj

    def __call__(self, value, **args):
        """Call method to produce output string
        """
        for key in args:
            setattr(self, key, args[key])
        formatter = self.registeredFormats[type(value) if type(value) in self.registeredFormats else object]
        return formatter(self, value, self.indent)

    def formatObject(self, value, indent):
        """Fallback method for objects not registered with formatter
        Returns 'None' if allowPickle is False
        """
        from base64 import b64encode
        import pickle

        if isinstance(value, (list, dict, str, bytes, int, float, bool, complex, type(None))):
            # return python recognised objects if not already processed
            return repr(value)
        elif self.ALLOWPICKLE:
            # and finally catch any non-recognised object
            return "PythonObject('{0}')".format(b64encode(pickle.dumps(value, pickle.HIGHEST_PROTOCOL)).decode('utf-8'))
        return repr(None)

    def formatDictBase(self, value, indent, formatString=''):
        """Output format for dict/FrozenDict
        """
        items = [
            self.CRLF + self.TAB * (indent + 1) + repr(key) + ': ' +
            (self.registeredFormats[type(value[key]) if type(value[key]) in self.registeredFormats else object])(self, value[key], indent + 1)
            for key in value
            ]
        return formatString.format(','.join(items) + self.CRLF + self.TAB * indent)

    formatDict = partial(formatDictBase, formatString='{{{0}}}')
    formatFrozenDict = partial(formatDictBase, formatString='FrozenDict({{{0}}})')

    def formatBase(self, value, indent, formatString=''):
        """Output format for list
        """
        items = [
            self.CRLF + self.TAB * (indent + 1) +
            (self.registeredFormats[type(item) if type(item) in self.registeredFormats else object])(self, item, indent + 1)
            for item in value
            ]
        return formatString.format(','.join(items) + self.CRLF + self.TAB * indent)

    formatList = partial(formatBase, formatString='[{0}]')
    formatTuple = partial(formatBase, formatString='({0})')
    formatSet = partial(formatBase, formatString='{{{0}}}')

    def formatKlassBase(self, value, indent, klassName=None, formatString=''):
        """Output format for set of type klass
        currently   ccpn.util.OrderedSet.OrderedSet
                    frozenset
                    ccpn.util.OrderedSet.FrozenOrderedSet
        """
        items = [
            self.CRLF + self.TAB * (indent + 1) +
            (self.registeredFormats[type(item) if type(item) in self.registeredFormats else object])(self, item, indent + 1)
            for item in value
            ]
        return formatString.format(klassName, ','.join(items) + self.CRLF + self.TAB * indent)

    formatListType = partial(formatKlassBase, formatString='{0}([{1}])')
    formatSetType = partial(formatKlassBase, formatString='{0}({{{1}}})')

    def formatOrderedDict(self, value, indent):
        """Output format for OrderedDict (collections.OrderedDict)
        """
        items = [
            self.CRLF + self.TAB * (indent + 1) +
            "(" + repr(key) + ', ' + (self.registeredFormats[
                type(value[key]) if type(value[key]) in self.registeredFormats else object
            ])(self, value[key], indent + 1) + ")"
            for key in value
            ]
        return 'OrderedDict([{0}])'.format(','.join(items) + self.CRLF + self.TAB * indent)

    def PythonObject(self, value):
        """Call method to produce object from pickled string
        Returns None if allowPickle is False
        """
        from base64 import b64decode
        import pickle

        if type(value) in (str,) and self.ALLOWPICKLE:
            return pickle.loads(b64decode(value.encode('utf-8')))

    def literal_eval(self, node_or_string):
        """
        Safely evaluate an expression node or a string containing a Python
        expression.  The string or node provided may only consist of the following
        Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
        sets, booleans, and None.
        """
        from ast import parse, Expression, Constant, UnaryOp, UAdd, USub, Tuple, \
            List, Set, Dict, Call, Add, Sub, BinOp

        if isinstance(node_or_string, str):
            node_or_string = parse(node_or_string, mode='eval')
        if isinstance(node_or_string, Expression):
            node_or_string = node_or_string.body

        def _convert_num(node):
            if isinstance(node, Constant):
                if type(node.value) in (int, float, complex):
                    return node.value
            raise ValueError('malformed node or string: ' + repr(node))

        def _convert_signed_num(node):
            if isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
                operand = _convert_num(node.operand)
                if isinstance(node.op, UAdd):
                    return + operand
                else:
                    return - operand
            return _convert_num(node)

        def _convert_LiteralEval(node, klass):
            if isinstance(node, Call) and node.func.id == klass.__name__:
                mapList = list(map(_convert, node.args))
                if mapList:
                    return klass(mapList[0])

        def _convert(node):
            if isinstance(node, Constant):
                return node.value
            elif isinstance(node, Tuple):
                return tuple(map(_convert, node.elts))
            elif isinstance(node, List):
                return list(map(_convert, node.elts))
            elif isinstance(node, Set):
                return set(map(_convert, node.elts))
            elif isinstance(node, Dict):
                return dict(zip(map(_convert, node.keys),
                                map(_convert, node.values)))
            elif isinstance(node, Call):
                if node.func.id in self.literalEvals:
                    return _convert_LiteralEval(node, self.literalEvals[node.func.id])

            elif isinstance(node, BinOp) and isinstance(node.op, (Add, Sub)):
                left = _convert_signed_num(node.left)
                right = _convert_num(node.right)
                if isinstance(left, (int, float)) and isinstance(right, complex):
                    if isinstance(node.op, Add):
                        return left + right
                    else:
                        return left - right
            return _convert_signed_num(node)

        return _convert(node_or_string)


if __name__ == '__main__':
    """Test the output from the printFormatter and recover as the python object
    """

    testDict = {
        "Boolean2"  : True,
        "DictOuter" : {
            "ListSet"    : [[0, {1, 2, 3, 4, 5.00000000001, 'more strings'}],
                            [0, 1000000.0],
                            ['Another string', 0.0]],
            "String1"    : 'this is a string',
            "nestedLists": [[0, 0],
                            [0, 1 + 2.00000001j],
                            [0, (1, 2, 3, 4, 5, 6), OrderedDict((
                                ("ListSetInner", [[0, OrderedSet([1, 2, 3, 4, 5.00000001, 'more inner strings'])],
                                                  [0, 1000000.0],
                                                  {'Another inner string', 0.0}]),
                                ("String1Inner", b'this is an inner byte string'),
                                ("String2Inner", b'this is an inner\xe2\x80\x9d byte string'),
                                ("nestedListsInner", [[0, 0],
                                                      [0, 1 + 2.00000001j],
                                                      [0, (1, 2, 3, 4, 5, 6)]])
                                ))
                             ]]
            },
        "nestedDict": {
            "nestedDictItems": FrozenDict({
                "floatItem": 1.23000001,
                "frozen"   : frozenset([67, 78]),
                "frOrdered": FrozenOrderedSet([34, 45])
                })
            },
        "Boolean1"  : (True, None, False),
        }

    pretty = PrintFormatter()
    dd = pretty(testDict)
    print('dataDict string: \n{}'.format(dd))
    recover = pretty.literal_eval(dd)
    print('Recovered python object: {} '.format(recover))
