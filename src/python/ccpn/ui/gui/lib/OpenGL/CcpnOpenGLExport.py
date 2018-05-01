"""
Code for exporting OpenGL stripDisplay to a pdf file.
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
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

# routines to export vbo's to a pdf file

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4

# simple test

import io


class CcpnOpenGLExporter():
  """
  Class container for exporting OpenGL stripDisplay to a pdf file
  """
  def __init__(self, parent, strip, filename, params):
    """
    Initialise the exporter
    :param fileName - not required:
    :param params - parameter dict from the exporter dialog:
    """
    self.parent = parent
    self.strip = strip
    self.filename = filename
    self.params = params
    self.dpi = 0

    self.buf = io.BytesIO()
    self.doc = SimpleDocTemplate(
      self.buf,
      rightMargin=2 * cm,
      leftMargin=2 * cm,
      topMargin=2 * cm,
      bottomMargin=2 * cm,
      pagesize=A4,
    )

    # Styling paragraphs
    styles = getSampleStyleSheet()
    self.story = []

    # build all the sections of the pdf
    self._buildAll()

    # this generates the buffer to write to the file
    self.doc.build(self.story)

  @property
  def exporter(self):
    """
    Return the buffer for the created pdf document
    :return buffer:
    """
    return self.buf.getvalue()

  def _buildAll(self):
    # add a drawing and build it up

    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line
    from reportlab.lib.units import mm

    dpi = 72                        # drawing object is hard-coded to this
    mmwidth = 150
    mmheight = 150
    pixwidth = int(mmwidth * mm)    # 566 points
    pixheight = int(mmheight * mm)

    d = Drawing(pixwidth, pixheight)

    # d.add(Rect(50, 50, 300, 100, fillColor=colors.yellow))
    # d.add(String(150, 100, 'Hello World', fontSize=18, fillColor=colors.red))
    # d.add(String(180, 86, 'Special characters \
    #                           \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
    #            fillColor=colors.red))


    grid  = self.parent.gridList[0]  # main grid

    for ii in range(0, len(grid.indices)-2, 2):
      ii0 = grid.indices[ii]
      ii1 = grid.indices[ii+1]

      newLine = [grid.vertices[ii0*2],
                 grid.vertices[ii0 * 2+1],
                 grid.vertices[ii1 * 2],
                 grid.vertices[ii1 * 2+1]]

      colour = colors.Color(*grid.colors[ii0*4:ii0 * 4+3], alpha=grid.colors[ii0 * 4+4])
      if self.parent.lineVisible(newLine, pixwidth, pixheight):

        pl = Line(*newLine, strokeWidth=1, strokeColor=colour)
        d.add(pl)




    # ejb - the next two lines a are a quick one page renderer
    # from reportlab.graphics import renderPDF
    # renderPDF.drawToFile(d, 'example1.pdf', 'My First Drawing')

    # test putting it in twice :)
    self.story.append(d)
    self.story.append(d)

if __name__ == '__main__':
  buf = io.BytesIO()

  # Setup the document with paper size and margins
  doc = SimpleDocTemplate(
    buf,
    rightMargin=2 * cm,
    leftMargin=2 * cm,
    topMargin=2 * cm,
    bottomMargin=2 * cm,
    pagesize=A4,
  )

  # Styling paragraphs
  styles = getSampleStyleSheet()

  # Write things on the document
  paragraphs = []
  paragraphs.append(
    Paragraph('This is a paragraph testing CCPN pdf generation', styles['Normal']))
  paragraphs.append(
    Paragraph('This is another paragraph', styles['Normal']))

  from reportlab.lib import colors
  from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine
  from reportlab.lib.units import mm

  dpi = 72
  mmwidth = 150
  mmheight = 150
  pixwidth = int(mmwidth * mm)
  pixheight = int(mmheight * mm)

  # the width doesn't mean anything, but the height defines how much space is added to the story
  # co-ordinates are origin bottom-left
  d = Drawing(pixwidth, pixheight)

  d.add(Rect(0.0, 0.0, pixwidth, pixheight, fillColor=colors.yellow))
  d.add(String(150.0, 100.0, 'Hello World', fontSize=18, fillColor=colors.red))
  d.add(String(180.0, 86.0, 'Special characters \
                            \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
               fillColor=colors.red))

  pl = PolyLine([120, 110, 130, 150],
                strokeWidth=2,
                strokeColor=[colors.purple, colors.red])

  d.add(pl)

  paragraphs.append(d)

  # this generates the buffer to write to the file
  doc.build(paragraphs)

  # Write the PDF to a file
  with open('/Users/ejb66/Desktop/testCCPNpdf.pdf', 'wb') as fd:
    fd.write(buf.getvalue())