"""
class CcpNmrUserError(CcpNmrError):
    This error defines a user error, occuring a public-api calling method and obj
    (optionally None), the reason of the error and the possible remedy.

class CcpNmrParameterValueError(CcpNmrError):
    This error defines a value error of a parameter, required for a public-api calling method
    and obj (optionally None), and possible reason.

class CcpNmrParameterTypeError(CcpNmrError):
    This error defines a type error of a parameter, required for a public-api calling method
    and obj (optionally None), and possible reason.

class CcpNmrWarning(CcpNmrError):
    This error defines a warning for a public-api calling method and obj
    (optionally None).
    To be called at the end on a method; warnings to be logged along the way.


>>>> testing

class Test():

    def raiseError(self):

        raise CcpNmrUserError(Test.raiseError, self, 'just testing', 'try again')

    def method1(self, value:int):

        if not isinstance(value, int):
            raise CcpNmrParameterTypeError(Test.method1, self, ('value', value), 'should be int')

        if value < 0:
            raise CcpNmrParameterValueError(Test.method1, self, ('value', value), 'should be > 0')

    def raiseWarning(self):

        for i in range(3):
            print(f'step {i}')

        raise CcpNmrWarning(Test.raiseWarning, self)

>>>> Calling the different methods:

t = Test()

try:
    t.raiseError()
except CcpNmrError as es:
    print(es)

>> While calling 'Test.raiseError' on <Test>: just testing, try again


try:
    t.method1('bla')
except CcpNmrError as es:
    print(es)

>>While calling 'Test.method1' on <Test>: parameter 'value' ('bla', type:str), should be int


try:
    t.method1(-1)
except CcpNmrError as es:
    print(es)

>> While calling 'Test.method1' on <Test>: parameter 'value' (-1), should be > 0


try:
    t.raiseWarning()
except CcpNmrError as es:
    print(es)

>> step 0
>> step 1
>> step 2
>> While calling 'Test.raiseWarning' on <Test>: encountered one (or more) warnings; see console/log for details

"""
from __future__ import annotations

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2023-02-05 16:57:00 +0000 (Sun, February 05, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2023-02-05 10:28:41 +0000 (Sun, February 05, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

class CcpNmrError(Exception):
    """CCpNmr exception class; to allow for catching each one of them
    """
    pass


class CcpNmrUserError(CcpNmrError):
    """This error defines a user error, occuring a public-api calling method and obj
    (optionally None), the reason of the error and the possible remedy.
    """

    def __init__(self,  method, obj, reason:str, remedy:str = None):
        """
        :param method: the calling method, typically the method of the code executing the
                                  error
        :param obj: object generating the error (can be None)
        :param reason: an explanation of the reason for calling the error
        :param remedy: (optional) a remedy for solving the issue
        """

        if obj is not None:
            _funcName = f'{obj.__class__.__name__}.{method.__name__}'
            _line1 = f"While calling '{_funcName}' on {obj}: "
        else:
            _funcName = f'{method.__name__}'
            _line1 = f"While calling '{_funcName}': "

        if reason:
            _line2 = reason
        else:
            _line2 = ''

        if remedy:
            _line2 += f', {remedy}'

        self._obj = obj
        self._method = method,
        self._reason = reason
        self._remedy = remedy
        self._line1 = _line1
        self._line2 = _line2

        super().__init__(_line1 + _line2)


class CcpNmrParameterValueError(CcpNmrError):
    """This error defines a value error of a parameter, required for a public-api calling method
    and obj (optionally None), and possible reason.
    """

    def __init__(self,  method, obj, parameter:tuple, reason:str = None):
        """
        :param method: the calling method, typically the method of the code executing the
                                  error
        :param obj: object generating the error (can be None)
        :param parameter: a (name, value) tuple of the parameter with invalid value
        :param reason: (optional) an explanation of the reason for calling the error
        """

        if obj is not None:
            _funcName = f'{obj.__class__.__name__}.{method.__name__}'
            _line1 = f"While calling '{_funcName}' on {obj}: "
        else:
            _funcName = f'{method.__name__}'
            _line1 = f"While calling '{_funcName}': "

        _parameterName, _parameterValue = parameter

        _line2 = f"parameter '{_parameterName}' ({_parameterValue!r})"

        if reason:
            _line2 += f', {reason}'

        self._obj = obj
        self._method = method,
        self._reason = reason
        self._parameter = parameter
        self._line1 = _line1
        self._line2 = _line2

        super().__init__(_line1 + _line2)


class CcpNmrParameterTypeError(CcpNmrError):
    """This error defines a type error of a parameter, required for a public-api calling method
    and obj (optionally None), and possible reason.
    """

    def __init__(self,  method, obj, parameter:tuple, reason:str = None):
        """
        :param method: the calling method, typically the method of the code executing the
                                  error
        :param obj: object generating the error (can be None)
        :param parameter: a (name, value) tuple of the parameter with invalid type
        :param reason: (optional) an additional explanation of the reason for calling the error
        """

        if obj is not None:
            _funcName = f'{obj.__class__.__name__}.{method.__name__}'
            _line1 = f"While calling '{_funcName}' on {obj}: "
        else:
            _funcName = f'{method.__name__}'
            _line1 = f"While calling '{_funcName}': "

        _parameterName, _parameterValue = parameter

        _typeString = type(_parameterValue).__name__
        _line2 = f"parameter '{_parameterName}' ({_parameterValue!r}, type:{_typeString})"

        if reason:
            _line2 += f', {reason}'

        self._obj = obj
        self._method = method,
        self._reason = reason
        self._parameter = parameter
        self._line1 = _line1
        self._line2 = _line2

        super().__init__(_line1 + _line2)


class CcpNmrWarning(CcpNmrError):
    """This error defines a warning for a public-api calling method and obj
    (optionally None).
    To be called at the end on a method; warnings to be logged along the way.
    """

    def __init__(self,  method, obj, reason:str = None):
        """
        :param method: the calling method, typically the method of the code executing the
                                  error
        :param obj: object generating the error (can be None)
        :param reason: (optional) an additional explanation of the reason for calling the error
        """

        if obj is not None:
            _funcName = f'{obj.__class__.__name__}.{method.__name__}'
            _line1 = f"While calling '{_funcName}' on {obj}: "
        else:
            _funcName = f'{method.__name__}'
            _line1 = f"While calling '{_funcName}': "

        _line2 = 'encountered one (or more) warnings; see console/log for details'

        if reason:
            _line2 += f'; {reason}'

        self._obj = obj
        self._method = method,
        self._reason = reason
        self._line1 = _line1
        self._line2 = _line2

        super().__init__(_line1 + _line2)


if __name__ == '__main__':

    class Test():

        def raiseError(self):

            raise CcpNmrUserError(Test.raiseError, self, 'just testing', 'try again')

        def method1(self, value:int):

            if not isinstance(value, int):
                raise CcpNmrParameterTypeError(Test.method1, self, ('value', value), 'should be int')

            if value < 0:
                raise CcpNmrParameterValueError(Test.method1, self, ('value', value), 'should be > 0')

        def raiseWarning(self):

            for i in range(3):
                print(f'step {i}')

            raise CcpNmrWarning(Test.raiseWarning, self)


        def __str__(self):
            return '<Test>'


    t = Test()

    try:
        t.raiseError()
    except CcpNmrError as es:
        print(es)

    try:
        t.method1('bla')
    except CcpNmrError as es:
        print(es)

    try:
        t.method1(-1)
    except CcpNmrError as es:
        print(es)

    try:
        t.raiseWarning()
    except CcpNmrError as es:
        print(es)
