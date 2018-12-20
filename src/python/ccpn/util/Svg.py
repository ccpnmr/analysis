"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.PrintFile import PrintFile


class Svg(PrintFile):

    def __enter__(self):

        PrintFile.__enter__(self)
        self.fp.write('<svg width="%s" height="%s">\n' % (self.width, self.height))

        return self

    def __exit__(self, *args):

        self.fp.write('</svg>\n')
        PrintFile.__exit__(self)

    def startRegion(self, xOutputRegion, yOutputRegion, xNumber=0, yNumber=0):

        self.x0, self.x1 = xOutputRegion
        self.y0, self.y1 = yOutputRegion
        self.xNumber = xNumber
        self.yNumber = yNumber

        self.fp.write('''<defs>
  <clipPath id="cpth_{4}_{5}">
  <polyline points="{0},{2} {1},{2} {1},{3} {0},{3} {0},{2}" />
  </clipPath>
</defs>
'''.format(self.x0, self.x1, self.y0, self.y1, self.xNumber, self.yNumber))

    def writeLine(self, x1, y1, x2, y2, colour='#000000'):

        if self.xNumber is not None and self.yNumber is not None:
            self.fp.write('<line x1="%s" y1="%s" x2="%s" y2="%s" style="fill:none;stroke:%s;stroke-width:1" clip-path="url(#cpth_%d_%d)" />\n' % (
            x1, y1, x2, y2, colour, self.xNumber, self.yNumber))
        else:
            self.fp.write('<line x1="%s" y1="%s" x2="%s" y2="%s" style="fill:none;stroke:%s;stroke-width:1" />\n' % (x1, y1, x2, y2, colour))

    def writePolyline(self, polyline, colour='#000000'):

        if len(polyline) == 0:
            return

        self.fp.write('<polyline points="')
        for (x, y) in polyline:
            self.fp.write('%s,%s' % (x, self.height - y))
            self.fp.write(' ')
        (x, y) = polyline[0]  # close loop
        self.fp.write('%s,%s' % (x, self.height - y))

        if self.xNumber is not None and self.yNumber is not None:
            self.fp.write('" style="fill:none;stroke:%s;stroke-width:0.3" clip-path="url(#cpth_%d_%d)" />\n' % (colour, self.xNumber, self.yNumber))
        else:
            self.fp.write('" style="fill:none;stroke:%s;stroke-width:0.3" />\n' % (colour,))

    def writeText(self, text, x, y, colour='#000000', fontsize=10, fontfamily='Lucida Grande'):

        if self.xNumber is not None and self.yNumber is not None:
            self.fp.write('<text x="%s" y="%s" fill="%s" font-family="%s" font-size="%s" clip-path="url(#cpth_%d_%d)">%s</text>\n' % (
            x, y, colour, fontsize, fontfamily, self.xNumber, self.yNumber, text))
        else:
            self.fp.write('<text x="%s" y="%s" fill="%s" font-family="%s" font-size="%s">%s</text>\n' % (x, y, colour, fontsize, fontfamily, text))
