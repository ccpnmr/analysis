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





# this generates the buffer to write to the file
doc.build(paragraphs)

# Write the PDF to a file
with open('/Users/ejb66/Desktop/testCCPNpdf.pdf', 'wb') as fd:
  fd.write(buf.getvalue())