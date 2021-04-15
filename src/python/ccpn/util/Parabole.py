"""
Class representing a simple parabolic function:
    f(x) = y = ax**2 + bx + c

Some (simple) maths:
  coefficients a, b, c from three points:

  f(x0) = y0 = a*x0**2 + b*x0 + c
  f(x1) = y1 = a*x1**2 + b*x1 + c
  f(xm1) = ym1 = a*xm1**2 + b*xm1 + c

  y0 - y1 = a (x0-x1)(x0+x1) + b(x0-x1)
  y0 - ym1 = a (x0-xm1)(x0+xm1) + b(x0-xm1)

but if spaced 1 unit apart:
  xm1 = x0-1
  x1 = x0+1

  y0 - y1 = a*(2x0+1) - b
  y0 - ym1 = a*(2x0-1) + b
==>
  a = -y0 + 0.5*y1 + 0.5*ym1
  b = -y0 + y1 - a*(2x0+1)
  c = a*x0**2 + (y0-y1+a)*x0 + y0

max at df(x)/dx = 2a*x + b = 0

xmax = -b/2a
     = x0 + (y0-y1) / 2a + 0.5
     = x0 + (y0-y1) / (-2*y0 + y1 + ym1) + 0.5


NB  numpy can do all of this, but this class is just a simple wrapper using
high-school algebra for some simple methods.
Its usage is mainly to easily find the parabolic interpolation of a peak maximum
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

class Parabole(object):
    """A class to implement  a simple implementation of a parabolic function:
    f(x) = y = ax**2 + bx + c
    """

    def __init__(self, a, b, c):
        """Initialise
        """
        if a == 0.0:
            raise ValueError('Parameter "a" of Parabole cannot be zero')
        self.a = a
        self.b = b
        self.c = c

    def value(self, x):
        """Return the value of the parabole at 'x'
        """
        if not isinstance(x, (float, int)):
            raise ValueError("parameter 'x' should be a float or int")
        x = float(x)
        return self.a*x*x +self.b*x + self.c

    def derivativeValue(self, x):
        """Return the value of the derivative of parabole at 'x'
        """
        if not isinstance(x, (float, int)):
            raise ValueError("parameter 'x' should be a float or int")
        x = float(x)
        return 2.0*self.a*x +self.b

    @staticmethod
    def fromPoints(points):
        """return a new instance derived from 3 points spaced one unit apart

        :param points: list/tuple with exactly three (x,y) tuples defining three succesive
                                points spaced one unit apart; i.e. if x0 defines the centre point:

                                points = [ (x0-1.0, f(x0-1.0)), (x0, f(x0)), (x0+1.0, f(x0+1.0)) ]

        :return new Parabole instance
        """
        if len(points) != 3:
            raise ValueError('There should be exactly three (x,y) points to define the new Parabole instance')

        for point in points:
            if not isinstance(point, tuple) or len(point) != 2:
                raise ValueError('Expected a (x,y) tuple, got %r' % point)

        if points[1][0] - points[0][0] != 1.0 or points[2][0] - points[1][0] != 1.0:
            raise ValueError('Expected 3 (x,y) points spaced 1.0 apart, got %r' % points)


        x0 = points[1][0]
        y0 = points[1][1]

        y1 = points[2][1]
        ym1 = points[0][1]

        a = -1.0 * y0 + 0.5 * ym1 + 0.5 * y1
        b = -1.0 * y0 + y1 - a * (2.0*x0 + 1.0)
        c = a*x0**2 + (y0-y1+a)*x0 + y0

        return Parabole(a, b, c)

    def maxValue(self):
        """Return a (xmax, f(xmax)) tuple

        max at:
            d(f(x)/dx = 2a*x + b = 0

        ==>
            xmax = -b/2a
        """
        xmax = -1.0*self.b / (2.0*self.a)
        return (xmax, self.value(xmax))

    def __str__(self):
        return '<%s: a=%s, b=%s, c=%s>' % (self.__class__.__name__, self.a, self.b, self.c)


if __name__ == '__main__':

    import numpy

    p1 = Parabole(-10.3, 40.0, 45.5)
    print(p1)

    for x in numpy.arange(-1,10,0.5):
        print(x, p1.value(x))

    print(p1.maxValue())

    points = [(p, p1.value(p)) for p in (1.0, 2.0, 3.0)]
    print('points>', points)

    p2 = Parabole.fromPoints(points)
    print(p2)
    points2 = [(p, p2.value(p)) for p in (1.0, 2.0, 3.0)]
    print('points2>', points2)