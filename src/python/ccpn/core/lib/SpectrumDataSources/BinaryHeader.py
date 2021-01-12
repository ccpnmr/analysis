"""
This file the BinaryHeader data access class

it serves as int/float/char translator of the actual spectral header data

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

class BinaryHeader(object):
    """A class to convert binary header data into ints, float or char-strings
    Used for formats like NmrPipe and Felix, that contain mixed binary header data
    intValues and floatValues defined in words
    """

    def __init__(self, headerSize, wordSize=4):
        "Define the object's header size and word size (4 or 8 bytes)"

        self.headerSize = headerSize
        self.wordSize = wordSize

        self.bytes = None
        self.swappedBytes = False
        self.intValues = None
        self.floatValues = None

    def read(self, fp, doSeek=True):
        """Read and initialise the header from binary file pointed to by fp; return self
        :param doSeek: seek to start of file if True
        """

        if doSeek:
            fp.seek(0,0)  # rewind the file as header should be at the start

        # bytes = array('B')
        # bytes.fromfile(fp, self.headerSize * self.wordSize)
        bytes = fp.read(self.headerSize * self.wordSize)
        if len(bytes) < self.headerSize*self.wordSize:
            raise RuntimeError('%s appears truncated' % self)
        self.fromBytes(bytes)
        return self

    def fromBytes(self, bytes):
        "Intialise the header from bytes; return self"

        typeCode = 'B'
        self.bytes = array(typeCode)
        self.bytes.frombytes(bytes)

        typeCode = 'i' if self.wordSize == 4 else 'l'
        self.intValues = array(typeCode)
        self.intValues.frombytes(self.bytes)

        typeCode = 'f' if self.wordSize == 4 else 'd'
        self.floatValues = array(typeCode)
        self.floatValues.frombytes(self.bytes)

        return self

    @property
    def bytesAsHexTuple(self):
        "Return all bytes as a tuple of hexadecimal strings"
        return tuple(["%02X" % byte for byte in self.bytes])

    def swapBytes(self):
        "Swap the bytes of intValues and floatValues"
        self.intValues.byteswap()
        self.floatValues.byteswap()
        self.swappedBytes = not self.swappedBytes

    def bytesToString(self, start, stop, strip=False):
        """Return bytes within range(start,stop) (eg. (10,14) converts bytes 10,11,12,13 to chr
        and returns it as a string
        optionally strip string of '\00'
        """
        chars = [chr(self.bytes[i]) for i in range(start,stop)]
        result = ''.join(chars)
        if strip:
            result = result.strip('\x00')
        return result

    def wordsToString(self, start, stop):
        """Return words within range(start,stop) (eg. (10,14) converts words 10,11,12,13 to chr
        and returns it as a string
        """
        result = ''.join([chr(self.intValues[i]) for i in range(start,stop)])
        return result
