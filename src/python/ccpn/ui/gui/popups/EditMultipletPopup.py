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
__dateModified__ = "$dateModified: 2017-07-07 16:32:24 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.core.Multiplet import Multiplet, MULTIPLET_TYPES
from ccpn.core.MultipletList import MultipletList
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList


NEW = "Add New"
PopupTitle = 'Multiplet Editor '

class EditMultipletPopup(CcpnDialog):
    def __init__(self, parent=None,  mainWindow=None, multiplet = None, spectrum = None, isNewMultipletList=False, title=PopupTitle, **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, size=(700, 600), **kwds)

        self.project = None

        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.current = self.application.current
            self.project = mainWindow.project
            self.multiplet = multiplet
            self.multipletList = None
            self.spectrum = spectrum
            self._isNewMultipletList = isNewMultipletList
            if self.multiplet:
                self.multipletList = self.multiplet.multipletList
                self.spectrum = self.multipletList.spectrum
                self.setWindowTitle(str(PopupTitle + self.multiplet.pid))
            # self._registerNotifiers() #not really needed in a popup

        self._createWidgets()
        # self._enableButtons()

    def _createWidgets(self):

        tipText = ''

        self.getLayout().setContentsMargins(10,10,10,10)
        row =  0
        self.mtLabel = Label(self, 'Select Multiplet List', grid=(row, 0), hAlign='l')
        self.label2 = Label(self, 'Select Peaks Source', grid=(row, 1), hAlign='l')
        row += 1
        self.mtPullDown = PulldownList(self, texts=[NEW], headerText='Select', callback=self._populateMultipletPulldown, grid=(row, 0))
        self.sourcePullDown = PulldownList(self, texts=['All in spectrum', ], headerText='Select', callback=self._populateSourceMultipletListsWidget, grid=(row, 1))
        row += 1
        self.mlLabel = Label(self, 'Select Multiplet', grid=(row, 0), hAlign='l')
        row += 1
        self.mlPullDown = PulldownList(self, texts=[NEW], headerText='Select', callback=self._populatePeaksListsWidget, grid=(row, 0))
        row += 1

        self.mlPeaksLabel = Label(self, 'Peaks', grid=(row, 0), hAlign='l')
        self.outputMultipletListsWidgetLabel = Label(self, 'Available Peaks',  grid=(row, 1),  hAlign='l')
        row += 1
        self.multipletPeaksListWidget = ListWidget(self, multiSelect= True, callback=self._activateOkButton,acceptDrops=True, copyDrop=False, tipText=tipText, grid=(row, 0))
        self.peaksSourceListWidget = ListWidget(self, multiSelect= True, callback=self._activateOkButton, contextMenu=False, acceptDrops=True,copyDrop=False, tipText=tipText, grid=(row, 1))

        row += 1
        self.typeLabel = Label(self, 'Type', grid=(row, 0), hAlign='l')
        self.typePullDown = FilteringPulldownList(self, texts=MULTIPLET_TYPES, headerText=' ', headerEnabled=True, callback=None,
                                       grid=(row, 1))
        row += 1
        self.commentLabel = Label(self, 'Comment', grid=(row, 0), hAlign='l')
        self.commentText = TextEditor(self, grid=(row, 1))
        self.commentText.setFixedHeight(40)
        row += 1


        self.selectButtons = ButtonList(self, texts=['Select from Current Peaks','Close', 'Ok'],
                                        callbacks=[self._selectCurrentPeaks, self._closePopup, self._okCallback],
                                        tipTexts=['Select on the list all the current peaks',
                                                  '',''], grid=(row, 0), gridSpan=(row,2))


        self.multipletPeaksListWidget.setAcceptDrops(True)
        self.peaksSourceListWidget.setAcceptDrops(True)

        # self.selectButtons.buttons[-1].setDisabled(True)
        self._populateMultipletPulldown()
        self._populateSourceMultipletListsWidget()
        self._setPullDownData()
        if self.project:
            if self.multiplet:
                self._selectMultiplet()
                print('comment',self.multiplet.comment)
                self.commentText.setText(self.multiplet.comment)
            else:
                if self._isNewMultipletList:
                    self.mtPullDown.select(NEW)
                    # self.mlPullDown.select(NEW)

    def _setPullDownData(self):
        if self.project:
            for multipletList in self.project.multipletLists:
                self.mtPullDown.addItem(text=multipletList.pid, object=multipletList)

    def _selectMultiplet(self):
        if self.multiplet:
            self.mtPullDown.select(self.multiplet.multipletList.pid)
            self.mlPullDown.select(self.multiplet.pid)

    def _populateMultipletPulldown(self, *args):
        obj = self.mtPullDown.getObject()

        if isinstance(obj, MultipletList):
            self.spectrum = obj.spectrum
            for multiplet in obj.multiplets:
                self.mlPullDown.addItem(text=multiplet.pid, object=multiplet)
        self._refreshAvailableSpectra()

    def _populatePeaksListsWidget(self, *args):

        obj = self.mlPullDown.getObject()
        if isinstance(obj, Multiplet):
            self.multipletPeaksListWidget.setObjects(obj.peaks, name='pid')
        else:
            if self.project:
                if self.mlPullDown.getText() != NEW:
                    self.multipletPeaksListWidget.setObjects(self.project.peaks, name='pid')

        self._refreshAvailableSpectra()
        self._activateOkButton()


    def _populateSourceMultipletListsWidget(self, *args):

        obj = self.sourcePullDown.getObject()
        if isinstance(obj, Multiplet):
            self.peaksSourceListWidget.setObjects(obj.peaks, name='pid')
        else:
            self._refreshAvailableSpectra()

    def _refreshAvailableSpectra(self):
        if self.project:
            if self.sourcePullDown.getText() == 'All in spectrum':
                if self.spectrum:
                    if self.mlPullDown.getText() != NEW:
                        availablePeaks = [pp for peakList in self.spectrum.peakLists for pp in peakList.peaks if pp not in self.multipletPeaksListWidget._getDroppedObjects(self.project)]
                    else:
                        availablePeaks = [pp for peakList in self.spectrum.peakLists for pp in peakList.peaks]
                    self.peaksSourceListWidget.setObjects(availablePeaks, name='pid')


    def _refreshInputMultipletsWidget(self, *args):
        self._populateMultipletPulldown()

    def _refreshInputMultipletsListWidget(self, *args):
        self._populateSourceMultipletListsWidget()

    def _selectSpectrum(self, spectrum):
        self.mtPullDown.select(spectrum)

    def _activateOkButton(self):

        if self.project:
            if self.mtPullDown.getText == NEW:
                self.selectButtons.buttons[-1].setDisabled(False)
            elif self.mlPullDown.getText == NEW:
                self.selectButtons.buttons[-1].setDisabled(False)

    def _okCallback(self):

        if self.project:
            multipletListText = self.mtPullDown.getText()
            if multipletListText == NEW:
                self.multipletList = self.spectrum.newMultipletList()
            else:
                multipletList = self.mtPullDown.getObject()
                if isinstance(multipletList, MultipletList):
                    self.multipletList = multipletList
                else:
                    # raise a warning
                    showWarning("No MultipletList Selected", "Select a multipletList option")
                    return

            multipletText = self.mlPullDown.getText()
            if multipletText == NEW:
                if self.multipletList:
                    self.multiplet = self.multipletList.newMultiplet()
            else:
                pdObj = self.mlPullDown.getObject()
                if isinstance(pdObj, Multiplet):
                    self.multiplet = pdObj
                else:
                    # raise a warning
                    showWarning("No Multiplet Selected", "Select a multiplet option")
                    return


            sourceMultipletText = self.sourcePullDown.getText()
            sourceMultiplet = self.project.getByPid(sourceMultipletText)
            sourcePeaks = self.peaksSourceListWidget._getDroppedObjects(self.project)
            if sourceMultiplet:
                if list(set(sourcePeaks)) != list(set(sourceMultiplet.peaks)):
                    sourceMultiplet.peaks = sourcePeaks

            multipletPeaks = self.multipletPeaksListWidget._getDroppedObjects(self.project)

            if self.multiplet:
                if list(set(multipletPeaks)) != list(set(self.multiplet.peaks)):
                    self.multiplet.peaks = multipletPeaks
                comment = self.commentText.get()
                self.multiplet.comment = comment
            # try:
            #   # todo 'Implement getLogger  info '
            #   # getLogger().info('')
            # except Exception as es:
            #   showWarning(str(self.windowTitle()), str(es))
            self._closePopup()


    def _selectPeaks(self, peaks):
        self.multipletPeaksListWidget.selectObjects(peaks)

    def clearSelections(self):
        self.multipletPeaksListWidget.clearSelection()
        self.peaksSourceListWidget.clearSelection()
        self.copyButtons.buttons[1].setDisabled(True)

    def _selectCurrentPeaks(self):
        if self.project:
            self.multipletPeaksListWidget.clearSelection()
            peaks = self.current.peaks
            self._selectPeaks(peaks)

    def _enableButtons(self):
        if len(self.current.peaks)>0:
            self.selectButtons.buttons[0].setDisabled(False)
        else:
            self.selectButtons.buttons[0].setDisabled(True)

    def _closePopup(self):
        """

        """
        # self._deregisterNotifiers()
        self.reject()

    #
    # def _registerNotifiers(self):
    #   if self.project:
    #     self._multipletNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'Multiplet', self._refreshInputMultipletsWidget)
    #     self._multipletListNotifier = Notifier(self.project, [Notifier.DELETE, Notifier.CREATE, Notifier.RENAME], 'MultipletList', self._refreshInputMultipletsListWidget)
    #
    #
    # def _deregisterNotifiers(self):
    #   if self.project:
    #     if self._multipletNotifier:
    #       self._multipletNotifier.unRegister()
    #     if self._multipletListNotifier:
    #       self._multipletListNotifier.unRegister()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog

    app = TestApplication()
    popup = EditMultipletPopup(None)

    popup.show()
    popup.raise_()
    app.start()
