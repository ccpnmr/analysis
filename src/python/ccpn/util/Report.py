"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-13 14:34:26 +0100 (Wed, May 13, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtWidgets
from ccpn.util.Path import aPath
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, BaseDocTemplate, NextPageTemplate, PageTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4, LETTER
from contextlib import contextmanager
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import SPECTRUM_STACKEDMATRIX, SPECTRUM_MATRIX
from collections import OrderedDict
import io
import numpy as np
from reportlab.lib import colors
from reportlab.graphics import renderSVG, renderPS
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group, Path
from reportlab.lib.units import mm

DEFAULTMARGIN = 2.0 * cm


class Report():
    """
    Class container for generating pdf reports
    """

    def __init__(self, parent, project, filename, pagesize=A4,
                 leftMargin=DEFAULTMARGIN, rightMargin=DEFAULTMARGIN, topMargin=DEFAULTMARGIN, bottomMargin=DEFAULTMARGIN):
        """
        Initialise a new pdf report

        :param parent:
        :param project - current project:
        :param filename - filename to save pdf as:
        :param pagesize - pagesize; e.g. LETTER, A4:
        :param leftMargin:
        :param rightMargin:
        :param topMargin:
        :param bottomMargin:
        """

        # set the class attributes
        self._parent = parent
        self.project = project
        self.filename = filename
        self.canv = None
        self.defaultMargin = DEFAULTMARGIN

        # buffer for exporting
        self.buf = io.BytesIO()

        self.doc = SimpleDocTemplate(
                self.buf,
                rightMargin=rightMargin,
                leftMargin=leftMargin,
                topMargin=topMargin,
                bottomMargin=bottomMargin,
                pagesize=pagesize,
                )

        # Styling paragraphs
        styles = getSampleStyleSheet()

        # initialise a new story - the items that are to be added to the document
        self.story = []

    def addItemToStory(self, item):
        """
        Add a new item to the current story
        :param item; e.g., paragraph or drawing:
        """
        self.story.append(item)

    def buildDocument(self):
        """
        Build the document from the story
        """
        self.doc.build(self.story)

    def writeDocument(self):
        """
        Write the document to the file
        """
        with open(aPath(self.filename), 'wb') as fn:
            fn.write(self.buf.getvalue())
