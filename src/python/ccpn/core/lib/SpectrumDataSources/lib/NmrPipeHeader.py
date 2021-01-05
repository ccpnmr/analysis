"""
This file contains the NmrPipe header class
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:14 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2020-11-20 10:28:48 +0000 (Fri, November 20, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from array import array

from ccpn.core.lib.SpectrumDataSources.BinaryHeader import BinaryHeader
from ccpn.core.lib.SpectrumDataSources.lib.NmrPipeFDdict import nmrPipeFDdict


class NmrPipeHeader(BinaryHeader):
    """Class to read from / write to NMRPipe binary header;
    All values are stored as 4 byte floats, except a 'axisLabels' that are stored as 8bytes onto two float-words
    """
    def getInt(self, loc):
        "Convert and return value at loc to int"
        return int(self.floatValues[loc])

    def getFloat(self, loc):
        "Return value at loc as float"
        return self.floatValues[loc]

    def getBool(self, loc):
        "Convert and return value at loc to boolean"
        return bool(self.getInt(loc))

    def toChar8(self, loc):
        "Convert and return values starting at loc, +8-bytes to string"
        bIdx = loc*self.wordSize
        # result = ''.join([c for c in self.bytesToString(bIdx, bIdx+8) if c != '\x00'])
        result = self.bytesToString(bIdx, bIdx+8, strip=True)
        return result

    def fromChar8(self, loc, value):
        "set and convert value at loc"
        bIdx = loc*self.wordSize
        # assure 8 bytes
        value += '\00' * 8
        value = value[0:8]
        b_array = array('B', [ord(c) for c in value])
        self.bytes[bIdx:bIdx+8] = b_array[0:8]

    def setFloat(self, loc, value):
        "set and convert value at loc"
        bIdx = loc*self.wordSize
        self.floatValues[loc] = value

        # create an array to hold the float, so we can convert it to bytes
        typeCode = 'f' if self.wordSize == 4 else 'd'
        f_array= array(typeCode, [value])

        typeCode = 'B'
        b_array = array(typeCode)
        b_array.frombytes( f_array.tobytes() )

        self.bytes[bIdx:bIdx+self.wordSize] = b_array[0:self.wordSize]
        
    def setInt(self, loc, value):
        "set and convert value at loc; int's (and bool) are mapped on floats, so piggyback on the setFloat method"
        self.intValues[loc] = int(value)
        self.setFloat(loc, float(value))

    # Order matters as the proper extraction requires certain info to be present first, to interpret the values appropiately!
    # These parameters will be set in the NmrPipeSpectrumDataSource object
    defs = [
    #     parameter           pipe2header header2pipe  dimensionMapped transpose default FDdefs
        ("dimensionCount",          (getInt,  setInt, False, False, 0,          "FDDIMCOUNT")),
        ("transposed",              (getBool, setInt, False, False, False,     "FDTRANSPOSED")),
        ("nFiles",                  (getInt,  setInt, False, False, 0,        "FDFILECOUNT")),
        ("pipeDimension",           (getInt,  setInt, False, False, 0,        "FDPIPEFLAG")),
        ("sliceCount",              (getInt,  setInt, False, False, 0,        "FDSLICECOUNT")),
        ("nusDimension",            (getInt,  setInt, False, False, 0,        "FDNUSDIM")),
        ("nusType" ,                (getInt,  setInt, False, False, 0,        "FDUSER6")),  # GWV added

        ("dimensionOrder",          (getInt,  setInt, False, True, 0,         ["FDDIMORDER1", "FDDIMORDER2", "FDDIMORDER3", "FDDIMORDER4"])),

        ("axisLabels",              (toChar8, fromChar8, True,  True,  '',      ["FDF2LABEL", "FDF1LABEL", "FDF3LABEL", "FDF4LABEL"])),
        ("dataTypes",               (getInt,  setInt, True, True, 0,          ["FDF2QUADFLAG", "FDF1QUADFLAG", "FDF3QUADFLAG", "FDF4QUADFLAG"])),
        ("domain",                  (getInt,  setInt, True, True, 0,          ["FDF2FTFLAG", "FDF1FTFLAG", "FDF3FTFLAG", "FDF4FTFLAG"])),
        ("pointCounts",             (getInt,  setInt, False, True, 0,         ["FDSIZE", "FDSPECNUM", "FDF3SIZE", "FDF4SIZE"])),
        ("tdSizes",                 (getInt,  setInt, True, True, 0,          ["FDF2TDSIZE", "FDF1TDSIZE", "FDF3TDSIZE", "FDF4TDSIZE"])),

        ("spectralWidthsHz",        (getFloat, setFloat, True, True, 0.0,      ["FDF2SW", "FDF1SW", "FDF3SW", "FDF4SW"])),
        ("spectrometerFrequencies", (getFloat, setFloat, True, True, 0.0,      ["FDF2OBS", "FDF1OBS", "FDF3OBS", "FDF4OBS"])),

        ("referenceValues",         (getFloat, setFloat, True, True, 0.0,      ["FDF2CAR", "FDF1CAR", "FDF3CAR", "FDF4CAR"])),
        ("referencePoints",         (getInt,   setInt, True, True, 0.0,        ["FDF2CENTER", "FDF1CENTER", "FDF3CENTER", "FDF4CENTER"])),
        ("origin",                  (getFloat, setFloat, True, True, 0.0,      ["FDF2ORIG", "FDF1ORIG", "FDF3ORIG", "FDF4ORIG"])),

        ("apodCode",                (getInt,   setInt, True, True, 0,          ["FDF2APODCODE", "FDF1APODCODE", "FDF3APODCODE", "FDF4APODCODE"])),
        ("apodParameter1",          (getFloat, setFloat, True, True, 0.0,      ["FDF2APODQ1", "FDF1APODQ1", "FDF3APODQ1", "FDF4APODQ1"])),
        ("apodParameter2",          (getFloat, setFloat, True, True, 0.0,      ["FDF2APODQ2", "FDF1APODQ2", "FDF3APODQ2", "FDF4APODQ2"])),
        ("apodParameter3",          (getFloat, setFloat, True, True, 0.0,      ["FDF2APODQ3", "FDF1APODQ3", "FDF3APODQ3", "FDF4APODQ3"])),
        ("apodSizes",               (getInt,   setInt, True, True, 0,          ["FDF2APOD", "FDF1APOD", "FDF3APOD", "FDF4APOD"])),
        ("firstPoint",              (getFloat, setFloat, True, True, 1.0,      ["FDF2C1", "FDF1C1", "FDF3C1", "FDF4C1"])),
        ("zeroFill",                (getInt,   setInt, True, True, 0,          ["FDF2ZF", "FDF1ZF", "FDF3ZF", "FDF4ZF"])),
        ("ftSize",                  (getInt,   setInt, True, True, 0,          ["FDF2FTSIZE", "FDF1FTSIZE", "FDF3FTSIZE", "FDF4FTSIZE"])),
        ("phases0",                 (getFloat, setFloat, True, True, 0.0,      ["FDF2P0", "FDF1P0", "FDF3P0", "FDF4P0"])),
        ("phases1",                 (getFloat, setFloat, True, True, 0.0,      ["FDF2P1", "FDF1P1", "FDF3P1", "FDF4P1"])),

        ("userValues",              (getFloat, setFloat, False, False, float('nan'), ["FDUSER1", "FDUSER2", "FDUSER3", "FDUSER4", "FDUSER5"])),
        ("tau" ,                    (getFloat, setFloat, False, False, 0,      "FDTAU")),
        ("temperature" ,            (getFloat, setFloat, False, False, 0.0,    "FDTEMPERATURE")),
    ]

    # Also make a dict of the definitions for convenience
    defsDict = dict(defs)

    _byteOrderFlags = { (0x40, 0x16, 0x14, 0x7b) : 'big',
                        (0x7b, 0x14, 0x16, 0x40) : 'little'
    }


    def __init__(self, headerSize, wordSize=4):
        """Create the various arrays
        """
        super().__init__(headerSize=headerSize, wordSize=wordSize)

        # Always initialise the bytes, intValues and floatValues arrays, but these will be
        # re-intialised upon reading the header
        self.fromBytes(bytearray(headerSize*wordSize))
        self.setDefaultValues()
        
    def setDefaultValues(self):
        """Setting the magic numbers and default values
        """
        self.setFloat(0, 0.0)
        self.setFloat(2, 2.345)
        for parameterName in self.defsDict.keys():
            self.setParameterValue(parameterName, value=None)
        
    def _byDimensionOrder(self, values) -> list:
        """Return values orders accounting for dimensionOrder
        """
        # pipeDimMapDict: nmrPipe dimensions are 2,1,3,4 or 1,2,3,4 (when transposed) as defined by dimensionOrder;
        #                 CcpNmr axes are always 0,1,2,3, parameters are parsed in the 2,1,3,4 order of the
        #                 non-transposed data: i.e. the map is (2,1,3,4) --> (0,1,2,3)
        pipeDims = (2,1,3,4)
        ccpnAxes = (0,1,2,3)
        pipeDimMap = dict([t for t in zip(pipeDims,ccpnAxes)])
        dimOrder = self.getParameterValue('dimensionOrder')
        for dim in dimOrder:
            if dim not in pipeDims:
                raise RuntimeError('invalid pipe-dimension "%s"; should be one of %s' % (dim, pipeDims))
        return [values[pipeDimMap[dim]] for dim in dimOrder]

    @property
    def parameterNames(self) -> list:
        "Return parameter names as a list"
        return [k for k, v in self.defs]

    def getParameterValue(self, parameterName):
        """Get the value(s) for parameterName;
        """
        _defs = self.defsDict.get(parameterName)
        if _defs is None:
            raise ValueError('Invalid parameter name "%s"' % parameterName)

        func1, _func2, dimensionMapped, transpose, default, fdDefs = _defs
        # get the locations using fdDict to map the FDname to loc (an idx)
        if isinstance(fdDefs, list):
            locations = [nmrPipeFDdict[par] for par in fdDefs]
            # get the values using the function and loc
            result = [func1(self, loc) for loc in locations]
            # Optional change the order
            if dimensionMapped:
                result = self._byDimensionOrder(result)

        elif isinstance(fdDefs, str):
            loc = nmrPipeFDdict[fdDefs]
            result = func1(self, loc)

        else:
            raise RuntimeError('getParameterValue: Invalid definition "%s" for "%s"' % (fdDefs, parameterName))

        return result

    def setParameterValue(self, parameterName, value=None):
        """Set the value(s) for parameterName; use default if Value is None
        """
        _defs = self.defsDict.get(parameterName)
        if _defs is None:
            raise ValueError('Invalid parameter name "%s"' % parameterName)

        func1, _func2, dimensionMapped, transpose, defaultValue, fdDefs = _defs
        # get the locations using fdDict to map the FDname to loc (an idx)
        if isinstance(fdDefs, list):
            locations = [nmrPipeFDdict[par] for par in fdDefs]
            # set the values using the function and locations
            for idx, loc in enumerate(locations):
                if value is not None:
                    val = value[idx]
                else:
                    val = defaultValue
                _func2(self, loc, val)

        elif isinstance(fdDefs, str):
            if value is not None:
                val = value
            else:
                val = defaultValue
            loc = nmrPipeFDdict[fdDefs]
            _func2(self, loc, val)

        else:
            raise RuntimeError('setParameterValue: Invalid definition "%s" for "%s"' % (fdDefs, parameterName))

        return
