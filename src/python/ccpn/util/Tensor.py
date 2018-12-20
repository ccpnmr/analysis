"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:33:00 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy

from ccpn.util import Common as commonUtil


class Tensor:
    """Rank 2 tensor value.

    Unlike most other ccpn classes Tensor is NOT linked to a Project and does not have a pid"""

    def __init__(self, xx: float = 0.0, yy: float = 0.0, zz: float = 0.0,
                 isotropic: float = 0.0, axial: float = 0.0, rhombic: float = 0.0,
                 orientationMatrix=None):

        if any((isotropic, axial, rhombic)):
            if any((xx, yy, zz)):
                raise ValueError(
                        "Creating a Tensor you must give values for xx,yy,zz OR isotropic,axial,rhombic")
            else:
                tmpval = isotropic - axial / 3.0
                self._xx = tmpval + 0.5 * rhombic
                self._yy = self._xx - rhombic
                self._zz = tmpval + axial
        else:
            self._xx = xx
            self._yy = yy
            self._zz = zz

        if orientationMatrix is None:
            self._orientationMatrix = numpy.identity(3)
        else:
            mm = numpy.array(orientationMatrix).reshape((3, 3))
            # NBNB TBD we also need to check that mm.transpose() == mm.inverse()
            if commonUtil.isClose(numpy.linalg.det(mm), 1.0):
                self._orientationMatrix = numpy.array(orientationMatrix).reshape((3, 3))
            else:
                raise ValueError("Invalid data for orientation matrix: %s" % orientationMatrix)

    def _toDict(self) -> dict:
        """return dict representation of tensor - for use in persistence"""
        om = self._orientationMatrix
        if om is not None:
            om = om.toList()
        #
        return {'xx': self._xx, 'yy': self._yy, 'zz': self._zz, 'orientationMatrix': om}

    @classmethod
    def _fromDict(cls, dd):
        """Create Tensor from dict representation - for use in persistence"""
        dd = dd.copy()
        om = dd.get('orientationMatrix')
        if om is not None:
            dd['orientationMatrix'] = numpy.asarray(om)
        #
        return cls(**dd)

    @property
    def xx(self) -> float:
        """xx component of tensor"""
        return self._xx

    @property
    def yy(self) -> float:
        """yy component of tensor"""
        return self._yy

    @property
    def zz(self) -> float:
        """zz component of tensor"""
        return self._zz

    @property
    def isotropic(self) -> float:
        """isotropic component of tensor"""
        return (self._xx + self._yy + self._zz) / 3.0

    @property
    def axial(self) -> float:
        """axial component of tensor (along z axis)"""
        return (self._xx + self._yy) * -0.5 + self._zz

    @property
    def rhombic(self) -> float:
        """rhombic component of tensor"""
        return self._xx - self._yy

    @property
    def orientationMatrix(self) -> numpy.array:
        """3,3 numpy array containing orientation matrix of tensor.
        NBNB TBD agree on a sign convention and modify documentation to suit"""
        return numpy.array(self._orientationMatrix)
