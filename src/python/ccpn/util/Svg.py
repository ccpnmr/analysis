"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: skinnersp $"
__date__ = "$Date: 2015-03-16 16:57:10 +0000 (Mon, 16 Mar 2015) $"
__version__ = "$Revision: 8180 $"

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
    
    self.fp.write('<line x1="%s" y1="%s" x2="%s" y2="%s" style="fill:none;stroke:%s;stroke-width:1" />\n' % (x1, y1, x2, y2, colour))

  def writePolyline(self, polyline, colour='#000000'):

    if len(polyline) == 0:
      return
    
    self.fp.write('<polyline points="')
    for (x, y) in polyline:
      self.fp.write('%s,%s' % (x, self.height-y))
      self.fp.write(' ')
    (x, y) = polyline[0] # close loop
    self.fp.write('%s,%s' % (x, self.height-y))
   
    self.fp.write('" style="fill:none;stroke:%s;stroke-width:0.3" clip-path="url(#cpth_%d_%d)" />\n' % (colour, self.xNumber, self.yNumber))

  def writeText(self, text, x, y, colour='#000000', fontsize=10, fontfamily='Verdana'):
    
    self.fp.write('<text x="%s" y="%s" fill="%s" font-family="%s" font-size="%s">%s</text>\n' % (x, y, colour, fontsize, fontfamily, text))
