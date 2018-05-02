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
    self.canv = None

    self.buf = io.BytesIO()         # for canvas
    return


    # self._buildCanvas()
    # self.buf = StringIO()         # for canvas
    # return

    self.buf = io.BytesIO()       # for renderPDF
    self.doc = SimpleDocTemplate(
      self.buf,
      rightMargin=2 * cm,
      leftMargin=2 * cm,
      topMargin=2 * cm,
      bottomMargin=2 * cm,
      pagesize=A4,
    )
    self.doc.compression = None
    self.doc.pageCompression = None

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
    self._buildCanvas()
    self.buf.write(self.canv.getpdfdata())       # for canvas
    self.buf.seek(0)

    return self.buf.getvalue()

  def _buildCanvas(self):
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.graphics import renderSVG
    from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group
    from reportlab.lib.units import mm

    self.canv = canvas.Canvas(None)
    self.canv.setPageSize(A4)

    # define a clipping path
    pageWidth = A4[0]
    pageHeight = A4[1]

    # keep aspect ratio of the original screen
    ratio = self.parent.h/self.parent.w
    pixHeight = pageWidth * ratio
    pageBottom = pageHeight - pixHeight
    pageLeft = 0.0

    # # define a clipping region
    # p = self.canv.beginPath()
    # p.moveTo(pageLeft, pageBottom)
    # p.lineTo(pageLeft, pageHeight)
    # p.lineTo(pageWidth, pageHeight)
    # p.lineTo(pageWidth, pageBottom)
    # p.close()
    # self.canv.clipPath(p, fill=0, stroke=0)

    # write stuff into the region
    colour = colors.Color(*self.parent.background[0:3], alpha=float(self.parent.background[3]))
    # colour = colors.Color(0.8, 0.8, 0.8, alpha=float(self.parent.background[3]))
    # self.canv.setFillColor(colour)
    # self.canv.rect(pageLeft, pageBottom, pageWidth, pixHeight, fill=True, stroke=False)

    grid  = self.parent.gridList[0]  # main grid

    self.canv.setLineWidth(0.5)
    p = self.canv.beginPath()

    colour = colors.Color(*grid.colors[0:3], alpha=grid.colors[0])
    self.canv.setStrokeColor(colour)

    self.canv._code = self.canv._code + ['n']
    for ii in range(0, len(grid.indices), 2):
      ii0 = grid.indices[ii]
      ii1 = grid.indices[ii+1]

      newLine = [grid.vertices[ii0*2],
                 grid.vertices[ii0 * 2+1],
                 grid.vertices[ii1 * 2],
                 grid.vertices[ii1 * 2+1]]

      # colour = colors.Color(*grid.colors[ii0*4:ii0 * 4+3], alpha=1.0)     #grid.colors[ii0 * 4+4])
      # self.canv.setStrokeColor(colour)
      # if self.parent.lineVisible(newLine, x=pageLeft, y=pageBottom, width=pageWidth, height=pixHeight):
        # p.moveTo(newLine[0], newLine[1])
        # p.lineTo(newLine[2], newLine[3])

      if self.parent.lineVisible(newLine, x=pageLeft, y=pageBottom, width=pageWidth, height=pixHeight):
        colour = colors.Color(*grid.colors[ii0*4:ii0 * 4+3], alpha=ii/len(grid.indices))    #grid.colors[ii0 * 4+4])
        self.canv.setStrokeColor(colour)
        self.canv.setStrokeAlpha(ii/len(grid.indices))
        # self.canv.line(*newLine)

        # self.canv._code = self.canv._code + ['%s %s %s RG' % tuple(grid.colors[ii0*4:ii0 * 4+3])]
        self.canv._code = self.canv._code + ['%s %s m %s %s l' % tuple(newLine)]

    self.canv._code = self.canv._code + ['S']

    # self.canv.drawPath(p, fill=False, stroke=True)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    for spectrumView in self.strip.orderedSpectrumViews():

      if spectrumView.isDeleted:
        continue
      if spectrumView.isVisible():

        if spectrumView.spectrum.dimensionCount > 1:
          # if spectrumView in self._spectrumSettings.keys():
          #   self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
          #                                              1, GL.GL_FALSE,
          #                                              self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])
          #
          #   # draw the spectrum - call the existing glCallList
          #   spectrumView._paintContoursNoClip()
          pass

        else:
          if spectrumView in self.parent._contourList.keys():
            # if self.parent._stackingValue:
            #
            #   # use the stacking matrix to offset the 1D spectra
            #   # self.parent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
            #   #                                       1, self.parent.GL.GL_FALSE,
            #   #                                       self.parent._spectrumSettings[spectrumView][self.parent.SPECTRUM_STACKEDMATRIX])
            #   #
            #   # self.parent._contourList[spectrumView].drawVertexColor()
            #   mat = self.parent._spectrumSettings[spectrumView][self.parent.SPECTRUM_STACKEDMATRIX]
            #
            thisSpec = self.parent._contourList[spectrumView]
            colour = colors.Color(*thisSpec.colors[0:3], alpha=float(thisSpec.colors[3]))
            self.canv.setStrokeColor(colour)

            # drawVertexColor
            p = self.canv.beginPath()
            self.canv._code = self.canv._code + ['n']
            for vv in range(0, len(thisSpec.vertices)-2, 2):

              # vectStart = mat.dot([thisSpec.vertices[vv],
              #                      thisSpec.vertices[vv+1], 0.0, 1.0])
              # vectEnd = mat.dot([thisSpec.vertices[vv+2],
              #                      thisSpec.vertices[vv+3], 0.0, 1.0])
              # newLine = [*vectStart, *vectEnd]

              newLine = list(thisSpec.vertices[vv:vv+4])

              # colour = colors.Color(*thisSpec.colors[vv*2:vv*2 + 3], alpha=float(thisSpec.colors[vv*2 + 4]))
              if self.parent.lineVisible(newLine, x=pageLeft, y=pageBottom, width=pageWidth, height=pixHeight):
                p.moveTo(newLine[0], newLine[1])
                p.lineTo(newLine[2], newLine[3])

            self.canv.drawPath(p, fill=False, stroke=True)
            self.canv._code = self.canv._code + ['S']       # cheat to make a subgroup

          else:
            pass

    print ('>>>drawCanvas')

  def _buildAll(self):
    # add a drawing and build it up

    from reportlab.lib import colors
    from reportlab.graphics import renderSVG
    from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group
    from reportlab.lib.units import mm

    dpi = 72                        # drawing object is hard-coded to this
    mmwidth = 160
    pixwidth = int(mmwidth * mm)    # 566 points
    # mmheight = 160
    # pixHeight = int(mmheight * mm)

    # keep aspect ratio of the original screen
    ratio = self.parent.h/self.parent.w
    pixHeight = pixwidth * ratio

    d = Drawing(pixwidth, pixHeight)

    # colour = colors.Color(*self.parent.background[0:3], alpha=float(self.parent.background[3]))
    # d.add(Rect(0, 0, pixwidth, pixHeight, fillColor=colour, stroke=0), name='background')
    # d.add(Rect(0, 0, pixwidth, pixHeight, fill=None, stroke=None), name='border')

    # colour = colors.Color(*self.parent.background[0:3], alpha=float(self.parent.background[3]))
    # gr = Group()
    # gr.add(Rect(0, 0, pixwidth/2, pixHeight/2, fillColor=colour))
    # gr.add(Rect(pixwidth/2, 0, pixwidth, pixHeight/2, fillColor=colour))
    # d.add(gr, name='background')

    # gr = Group()
    # gr.add(Rect(0, pixHeight/2, pixwidth/2, pixHeight/2, fillColor=colour))
    # # gr.add(Rect(pixwidth/2, pixHeight/2, pixwidth, pixHeight/2, fillColor=colour))
    #
    # d.add(gr, name='moreBackground')
    # self.story.append(d)
    #
    #
    # return

    # renderSVG.drawToFile(d, '/Users/ejb66/Desktop/testCCPNsvg.svg', 'testCCPNoutput')
    # return

    # d.add(String(150, 100, 'Hello World', fontSize=18, fillColor=colors.red))
    # d.add(String(180, 86, 'Special characters \
    #                           \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
    #            fillColor=colors.red))


    grid  = self.parent.gridList[0]  # main grid

    gr = Group()
    for ii in range(0, len(grid.indices), 2):
      ii0 = grid.indices[ii]
      ii1 = grid.indices[ii+1]

      newLine = [grid.vertices[ii0*2],
                 grid.vertices[ii0 * 2+1],
                 grid.vertices[ii1 * 2],
                 grid.vertices[ii1 * 2+1]]

      colour = colors.Color(*grid.colors[ii0*4:ii0 * 4+3], alpha=grid.colors[ii0 * 4+4])
      if self.parent.lineVisible(newLine, x=0, y=0, width=pixwidth, height=pixHeight):

        pl = Line(*newLine, strokeWidth=0.5, strokeColor=colour, strokeLineCap=1)
        gr.add(pl)

    # add the grid to the main drawing
    d.add(gr, name='mainGrid')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    specGroup = Group()
    for spectrumView in self.strip.orderedSpectrumViews():

      if spectrumView.isDeleted:
        continue

      if spectrumView.isVisible():

        if spectrumView.spectrum.dimensionCount > 1:
          # if spectrumView in self._spectrumSettings.keys():
          #   self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
          #                                              1, GL.GL_FALSE,
          #                                              self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])
          #
          #   # draw the spectrum - call the existing glCallList
          #   spectrumView._paintContoursNoClip()
          pass

        else:
          if spectrumView in self.parent._contourList.keys():
            # if self.parent._stackingValue:
            #
            #   # use the stacking matrix to offset the 1D spectra
            #   # self.parent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
            #   #                                       1, self.parent.GL.GL_FALSE,
            #   #                                       self.parent._spectrumSettings[spectrumView][self.parent.SPECTRUM_STACKEDMATRIX])
            #   #
            #   # self.parent._contourList[spectrumView].drawVertexColor()
            #   mat = self.parent._spectrumSettings[spectrumView][self.parent.SPECTRUM_STACKEDMATRIX]
            #
            thisSpec = self.parent._contourList[spectrumView]
            colour = colors.Color(*thisSpec.colors[0:3], alpha=float(thisSpec.colors[3]))

            # drawVertexColor
            gr = Group()
            for vv in range(0, len(thisSpec.vertices)-2, 2):

              # vectStart = mat.dot([thisSpec.vertices[vv],
              #                      thisSpec.vertices[vv+1], 0.0, 1.0])
              # vectEnd = mat.dot([thisSpec.vertices[vv+2],
              #                      thisSpec.vertices[vv+3], 0.0, 1.0])
              # newLine = [*vectStart, *vectEnd]

              newLine = list(thisSpec.vertices[vv:vv+4])

              # colour = colors.Color(*thisSpec.colors[vv*2:vv*2 + 3], alpha=float(thisSpec.colors[vv*2 + 4]))
              if self.parent.lineVisible(newLine, x=0, y=0, width=pixwidth, height=pixHeight):
                pl = Line(*newLine, strokeWidth=0.5, strokeColor=colour)
                gr.add(pl)
            specGroup.add(gr, name=spectrumView.pid)

          else:
            pass
    d.add(specGroup, name='spectrumGroups')


    # ejb - the next two lines a are a quick one page renderer
    # from reportlab.graphics import renderPDF
    # renderPDF.drawToFile(d, 'example1.pdf', 'My First Drawing')

    # test putting it in twice :)
    self.story.append(d)
    renderSVG.drawToFile(d, '/Users/ejb66/Desktop/testCCPNsvg.svg', 'testCCPNoutput')

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
  from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Group
  from reportlab.lib.units import mm

  dpi = 72
  mmwidth = 150
  mmheight = 150
  pixwidth = int(mmwidth * mm)
  pixHeight = int(mmheight * mm)

  # the width doesn't mean anything, but the height defines how much space is added to the story
  # co-ordinates are origin bottom-left
  d = Drawing(pixwidth, pixHeight)

  d.add(Rect(0.0, 0.0, pixwidth, pixHeight, fillColor=colors.yellow, stroke=0, fill=0))
  d.add(String(150.0, 100.0, 'Hello World', fontSize=18, fillColor=colors.red))
  d.add(String(180.0, 86.0, 'Special characters \
                            \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
               fillColor=colors.red))

  pl = PolyLine([120, 110, 130, 150],
                strokeWidth=2,
                strokeColor=colors.red)

  gr = Group()
  gr.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
  gr.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))
  d.add(gr)
  # d.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
  # d.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))

  paragraphs.append(d)

  doc.pageCompression = None
  # this generates the buffer to write to the file
  doc.build(paragraphs)

  # Write the PDF to a file
  with open('/Users/ejb66/Desktop/testCCPNpdf.pdf', 'wb') as fd:
    fd.write(buf.getvalue())

  from reportlab.pdfgen import canvas

  c = canvas.Canvas(filename='/Users/ejb66/Desktop/testCCPNpdf2.pdf', pagesize=A4)

  # define a clipping path
  pageWidth = A4[0]
  pageHeight = A4[1]

  p = c.beginPath()
  p.moveTo(0,0)
  p.lineTo(0, 200)
  p.lineTo(200, 200)
  p.lineTo(200, 0)
  p.close()
  c.clipPath(p, fill=0, stroke=0)

  red50transparent = colors.Color(100, 0, 0, alpha=0.5)
  c.setFillColor(colors.black)
  c.setFont('Helvetica', 10)
  c.drawString(25, 180, 'solid')
  c.setFillColor(colors.blue)
  c.rect(25, 25, 100, 100, fill=True, stroke=False)
  c.setFillColor(colors.red)
  c.rect(100, 75, 100, 100, fill=True, stroke=False)
  c.setFillColor(colors.black)
  c.drawString(225, 180, 'transparent')
  c.setFillColor(colors.blue)
  c.rect(225, 25, 100, 100, fill=True, stroke=False)
  c.setFillColor(red50transparent)
  c.rect(300, 75, 100, 100, fill=True, stroke=False)

  c.rect(0, 0, 100, 100, fill=True, stroke=False)

  # this is much better as it remembers the transparency and object grouping
  from reportlab.lib.units import inch
  h = inch / 3.0
  k = inch / 2.0
  c.setStrokeColorRGB(0.2, 0.3, 0.5)
  c.setFillColorRGB(0.8, 0.6, 0.2)
  c.setLineWidth(4)
  p = c.beginPath()
  for i in (1, 2, 3, 4):
    for j in (1, 2):
      xc, yc = inch * i, inch * j
      p.moveTo(xc, yc)
      p.arcTo(xc - h, yc - k, xc + h, yc + k, startAng=0, extent=60 * i)
      # close only the first one, not the second one
      if j == 1:
        p.close()
  c.drawPath(p, fill=1, stroke=1)

  c.save()