"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-31 10:23:46 +0100 (Tue, May 31, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# icons directory removed in revision 9360
# iconsNew renamed to icons in revision 9361

from PyQt5 import QtGui, QtWidgets, QtCore

import os


ICON_DIR = os.path.dirname(__file__)


class Icon(QtGui.QIcon):

    def __init__(self, image=None, color=None, size=21):


        if color:
            image = QtGui.QPixmap(10, 10)
            painter = QtGui.QPainter(image)

            if isinstance(color, str):
                color = QtGui.QColor(color[:7])
                image.fill(color)

            elif isinstance(color, (tuple, list)):
                image.fill(color[0][:7])
                dx = (size+1) / float(len(color))

                x = dx
                for i, c in enumerate(color[1:]):
                    col = QtGui.QColor(c[:7])
                    painter.setPen(col)
                    painter.setBrush(col)
                    painter.drawRect(int(x), 0, int(x + dx), size)
                    x += dx

            else:
                image.fill(color)

            painter.setPen(QtGui.QColor('#000000'))
            painter.setBrush(QtGui.QBrush())
            painter.drawRect(0, 0, size, size)
            painter.end()

        elif not isinstance(image, QtGui.QIcon):
            image = self._get_image_name(image)

        super().__init__(image)

    def _get_image_name(self, image):
        if not os.path.exists(image):
            image = os.path.join(ICON_DIR, image)
        png_file = '%s.png' % image
        png_file_a2x = '%s@2x.png' % image
        if os.path.exists(png_file) or os.path.exists(png_file_a2x):
            image = '%s.png' % image
        self._filePath = png_file
        return image

    def addFile(self, fileName: str, **kwargs):
        fileName = self._get_image_name(fileName)
        return super().addFile(fileName)




if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Button import Button
    from ccpn.ui.gui.widgets.Application import TestApplication


    app = TestApplication()

    window = QtWidgets.QWidget()


    def click():
        print("Clicked")


    button = Button(window, icon='icons/system-help.png', callback=click,
                    tipText='An icon button', grid=(0, 3))

    window.show()

    app.start()
