import hjson
import os
import pathlib
import sys
from glob import glob
from operator import itemgetter
import random

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt, QRectF, QPointF
from PyQt5.QtGui import QPixmap, QBrush, QColor, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QWizard, QWizardPage, QCheckBox, QPushButton, QLabel, QGridLayout, \
    QSizePolicy, QFrame, QTextBrowser, QGraphicsScene, QGraphicsView

RANDOM_TIP_BUTTON = QWizard.CustomButton1
DONT_SHOW_TIPS_BUTTON = QWizard.CustomButton2

MODE_TIP_OF_THE_DAY = 'TIP_OF_THE_DAY'
MODE_OVERVIEW = 'OVERVIEW'


TITLE = 'TITLE'
BUTTONS = 'BUTTONS'
DEFAULT = 'DEFAULT'
MIN_SIZE = 'MIN_SIZE'
LAYOUT = 'LAYOUT'
DIRECTORIES = 'DIRECTORIES'
IDENTIFIERS = 'IDENTIFIERS'
KEY_DEPTH = 'KEY_DEPTH'
EMPTY_TEXT = 'EMPTY_TEXT'
USE_DOTS = 'USE_DOTS'
HAS_DIVIDER = 'HAS_DIVIDER'
DIVIDER_COLOR = 'DIVIDER_COLOR'
DIVIDER_WIDTH = 'DIVIDER_WIDTH'

HEADER = 'header'
ORDER = 'order'
STYLES = 'styles'
TYPE = 'type'
PLACE_HOLDER = '_'
PATH = 'path'
PICTURE = 'picture'
SIMPLE_HTML = 'simple-html'
CONTENTS = 'contents'
COLOR = 'color'
MAX_ORDER = sys.maxsize

STYLE_FILE = 'style_file'

tip_defaults_file = pathlib.Path(__file__).parent.absolute() / "tip_config.hjson"
DEFAULTS = hjson.loads(open(tip_defaults_file, 'r').read())

BUTTON_IDS = {
    'Random': RANDOM_TIP_BUTTON,
    'Stretch': QWizard.Stretch,
    'Dont_show': DONT_SHOW_TIPS_BUTTON,
    'BackButton': QWizard.BackButton,
    'NextButton': QWizard.NextButton,
    'CancelButton': QWizard.CancelButton
}


class Dots(QGraphicsView):

    def __init__(self, parent=None):
        super(Dots, self).__init__(parent=parent)
        self._dot_size = 10

        self._pos = 0
        self._length = 0

        self.setFixedHeight(self._dot_size*2)

        self.setScene(QGraphicsScene())
        self._blackBrush = QBrush(QColor('black'))
        self._whiteBrush = QBrush(QColor('transparent'))

        self.setStyleSheet("border-width: 0px; border-style: solid;")

    def _assure_children(self):
        error = self._length - len(self.items())
        if error != 0:
            if error > 0:
                for i in range(error):
                    ellipse = self.scene().addEllipse(QRectF(0, 0, self._dot_size, self._dot_size))
                    ellipse.setBrush(self._whiteBrush)

        center = self.sceneRect().center()
        items = self.items()
        dot_size_2 = self._dot_size / 2
        for i in range(self._length):

            gaps = self._length / 2
            dots = self._length

            total = dots+gaps
            width = total * self._dot_size
            width_2 = width/2

            x_center = center.x() - width_2

            items[i].setPos(QPointF(x_center + i * self._dot_size * 2, center.y()-dot_size_2))

    def setLength(self, length):
        self._length = length
        self._assure_children()

    def setIndicatorPos(self, pos):
        self.items()[self._pos].setBrush(self._whiteBrush)
        self._pos = pos
        self.items()[self._pos].setBrush(self._blackBrush)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        our_scene = self.scene()
        if our_scene:
            width = event.size().width()
            height = event.size().height()

            self.scene().setSceneRect(0, 0, width, height)


class TipPage(QWizardPage):

    def __init__(self, data):
        super(TipPage, self).__init__()
        self._data = data

        self.setLayout(QGridLayout())

        if self._data[USE_DOTS]:
            self._dots = Dots(parent=self)
            self._dots.show()

    def setupPage(self):

        divider = ""
        if HAS_DIVIDER in self._data and self._data[HAS_DIVIDER]:

            divider_width = '1px'
            divider_color = '#a9a9a9'
            if DIVIDER_WIDTH in self._data:
                divider_width =  self._data[DIVIDER_WIDTH]
            if DIVIDER_COLOR in self._data:
                divider_color = self._data[DIVIDER_COLOR]

            divider = f'border-top: {divider_width} solid {divider_color};'

        if COLOR in self._data:
            if COLOR in self._data:

                stylesheet = f"background-color: {self._data[COLOR]}; {divider}"

                self.parent().setStyleSheet(stylesheet)

        else:
            self.parent().setStyleSheet(f"{divider}")

        self.setStyleSheet("border-top: 0px solid transparent;")

        if self._data[USE_DOTS]:
            self._dots.setLength(len(self.wizard().pageIds()))
            self._dots.setIndicatorPos(self.wizard()._current_page_index())

    def showEvent(self, a0: QtGui.QShowEvent):
        self.setupPage()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:

        if self._data[USE_DOTS]:
            self._dots.setGeometry(0, self.height()-self._dots.height(), self.width(), self._dots.height())
            self._dots.raise_()


class PictureTipPage(TipPage):
    def __init__(self, data):
        super(PictureTipPage, self).__init__(data)

        self._label = None
        self._picture = None

    @staticmethod
    def _load_from_path(path):
        return QPixmap(str(path))

    def initializePage(self) -> None:

        super(PictureTipPage, self).initializePage()

        if not self._label:

            self._picture = self._load_from_path(self._data[CONTENTS][0])
            self._label = QLabel(self)
            self._label.setPixmap(self._picture)

            self.layout().setContentsMargins(0, 0, 0, 0)
            self._label.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Expanding)

            self.layout().addWidget(self._label, 0, 0)


class SimpleHtmlTipPage(TipPage):
    def __init__(self, data):
        super(SimpleHtmlTipPage, self).__init__(data)
        self._data = data
        self._text_browser = None

    def _load_from_path(self):
        text = None

        if len(self._data) > 0:
            with open(self._data[0], 'r') as file_h:
                text = file_h.read()

        if not text:
            text = f'file {self._data[0]} missing...'

        return text

    def initializePage(self) -> None:

        super(SimpleHtmlTipPage, self).initializePage()

        if not self._text_browser:
            self._text_browser = QTextBrowser(self)
            self.layout().addWidget(self._text_browser, 0, 0)
            self._text_browser.setFrameStyle(QFrame.NoFrame)

            self._text_browser.setOpenExternalLinks(True)
            text = _read_text_from_field_or_file(self._data, CONTENTS)

            self._text_browser.setHtml(text)
        self.layout().setContentsMargins(0, 0, 0, 0)


TIP_PAGE_TYPE_TO_HANDLER = {
    SIMPLE_HTML: SimpleHtmlTipPage,
    PICTURE: PictureTipPage
}


# wizard pages: picture, html, movie (not implemented yet)
def _read_text_from_field_or_file(data, field):
    result = ""

    if field in data:
        result = data[field]
        if isinstance(result, list):
            result = '\n'.join(result)

        try:
            if PATH in data:
                text_file_name = data[PATH].parents[0] / result
                if text_file_name.exists() and text_file_name.is_file():
                    with open(text_file_name, 'r') as file_h:
                        result = file_h.read()
        except OSError:
            pass
    return result


class TipOfTheDayWindow(QWizard):
    dont_show = pyqtSignal(bool)

    def __init__(self, parent=None, mode=MODE_TIP_OF_THE_DAY):
        super(TipOfTheDayWindow, self).__init__(parent=parent)

        self._page_list = []
        self._id_path = {}
        self._visited_pages = set()
        self._id_page = {}

        self._mode = mode

        self.setWizardStyle(QWizard.ModernStyle)

        self._dont_show_tips_button = QCheckBox(PLACE_HOLDER)
        self._random_tip_button = QPushButton(PLACE_HOLDER)

        self.setOption(QWizard.HaveCustomButton1, True)
        self.setOption(QWizard.HaveCustomButton2, True)

        self.setOption(QWizard.HaveNextButtonOnLastPage, True)

        self.setButton(DONT_SHOW_TIPS_BUTTON, self._dont_show_tips_button)
        self.setButton(RANDOM_TIP_BUTTON, self._random_tip_button)

        self.button(BUTTON_IDS[DEFAULTS[DEFAULT]]).setAutoDefault(True)

        self.setOption(QWizard.NoCancelButton, False)

        for button, text in DEFAULTS[self._mode][BUTTONS].items():
            button = BUTTON_IDS[button]
            self.setButtonText(button, text)

        layout = [BUTTON_IDS[button] for button in DEFAULTS[self._mode][LAYOUT]]
        self.setButtonLayout(layout)

        self.setWindowTitle(DEFAULTS[self._mode][TITLE])

        self.customButtonClicked.connect(self._button_clicked)
        self.currentIdChanged.connect(self._page_visited)

        self._load_pages()

        self.setTitleFormat(Qt.RichText)

        random.seed(1)

        self._centre_window()


    def _current_page_index(self):
        return self._page_list.index(self.currentId())

    @staticmethod
    def _load_tip_dict(path):
        result = None
        try:
            with open(path, 'r') as file_h:
                result = hjson.loads(file_h.read())
        except (EnvironmentError, hjson.HjsonDecodeError) as e:
            print(f"WARNING: couldn't load tip file {path} because {e}")

        return result

    def _load_tip_file_data(self):

        files = []
        for directory_name in DEFAULTS[self._mode][DIRECTORIES]:

            identifiers = [identifier.split('/') for identifier in DEFAULTS[self._mode][IDENTIFIERS]]
            for identifier_parts in identifiers:

                identifier_pattern = os.path.join(directory_name, *identifier_parts)

                files.extend(glob(identifier_pattern))

        files = [pathlib.Path(file) for file in files]

        results = []
        for file in files:
            tip_data = self._load_tip_dict(file)
            if ORDER not in tip_data:
                tip_data[ORDER] = MAX_ORDER

            for i, data_file in enumerate(tip_data[CONTENTS]):
                tip_data[CONTENTS][i] = str(file.parent / tip_data[CONTENTS][i])

            tip_data[PATH] = file
            results.append(tip_data)

        results.sort(key=itemgetter(ORDER))

        return results

    def setup_page_from_tip_file(self, tip_file):
        tip_type = tip_file[TYPE]
        handler = TIP_PAGE_TYPE_TO_HANDLER[tip_type]

        copy_attributes = HAS_DIVIDER, DIVIDER_WIDTH, DIVIDER_COLOR

        for attribute in copy_attributes:
            if attribute in DEFAULTS[self._mode]:
                tip_file[attribute] = DEFAULTS[self._mode][attribute]

        if USE_DOTS not in tip_file:
            tip_file[USE_DOTS] = DEFAULTS[self._mode][USE_DOTS]

        if handler is not None:

            styles = {}
            if STYLES in tip_file:
                styles_data = tip_file[STYLES]
                if isinstance(styles_data, str):
                    styles.update(self._load_styles_from_file(styles, tip_file))
                elif isinstance(styles_data, dict):
                    for style, value in styles_data.items():
                        if style == STYLE_FILE:
                            styles.update(self._load_styles_from_file(value, tip_file))
                        else:
                            styles[style] = value

            title = _read_text_from_field_or_file(tip_file, HEADER)

            try:
                title = title % styles
            except Exception as e:
                print(f'WARNING: failed to apply style because of {e}')

            page = handler(tip_file)

            page.setTitle(title)

            page.setMinimumSize(*DEFAULTS[self._mode][MIN_SIZE])

            return page

    @staticmethod
    def _load_styles_from_file(styles, tip_file):
        try:
            style_path = tip_file[PATH].parents[0] / styles
            with open(style_path, 'r') as file_h:
                styles = hjson.loads(file_h.read())
        except IOError:
            pass
        if not isinstance(styles, dict):
            print(f"WARNING: styles field in file {tip_file[PATH]} is not a dict!")
        return styles

    def _load_pages(self):

        tip_files = self._load_tip_file_data()

        for tip_file in tip_files:

            page = self.setup_page_from_tip_file(tip_file)

            tip_id = self.addPage(page)
            self._id_path[tip_id] = tip_file
            self._page_list.append(tip_id)
            self._id_page[tip_id] = page

        if len(self._page_list) == 1:
            self._disable_random_tips()

        if len(self._page_list) == 0:
            info_page = {
                HEADER: "Note: the overview is not correctly configured...",

                TYPE: "simple-html",

                CONTENTS: DEFAULTS[self._mode][EMPTY_TEXT],
                
                PATH: pathlib.Path(os.path.realpath(__file__)),

                USE_DOTS:  False
            }

            page = self.setup_page_from_tip_file(info_page)
            tip_id = self.addPage(page)
            self._page_list.append(tip_id)

    def nextId(self) -> int:

        current_id = self.currentId()
        if len(self._page_list) and current_id in self._page_list:
            index = self._page_list.index(current_id)
        else:
            index = -1

        result = -1
        if index >= 0:
            if index < len(self._page_list) - 1:
                result = self._page_list[index + 1]
            else:
                result = -1
        elif index == -1 and len(self._page_list) > 0:
            result = self._page_list[0]

        if not self._have_more_pages():
            self._disable_random_tips()

        return result

    def _have_more_pages(self):
        return len(self._visited_page_ids()) != len(self._page_list) - 1

    def setMode(self, mode):
        self._mode = mode

    # https://stackoverflow.com/questions/42324399/how-to-center-a-qdialog-in-qt
    def _centre_window(self):

        host = self.parentWidget()

        if host:
            hostRect = host.geometry()
            self.move(hostRect.center() - self.rect().center())

        else:
            screenGeometry = QApplication.desktop().screenGeometry()
            x = int((screenGeometry.width() - self.width()) / 2)
            y = int((screenGeometry.height() - self.height()) / 2)
            self.move(x, y)

    def _visited_page_ids(self):
        return set(self._visited_pages)

    def _all_page_ids(self):
        return set(self.pageIds())

    def _unvisited_page_ids(self):
        return self._all_page_ids() - self._visited_page_ids()

    def _button_clicked(self, button_clicked):
        if button_clicked == RANDOM_TIP_BUTTON:
            self._random_tip()

    def _random_tip(self):

        available_ids = list(self._unvisited_page_ids())
        next_id = random.choice(available_ids)

        current_index = self._page_list.index(self.currentId())
        self._page_list.remove(next_id)
        self._page_list.insert(current_index + 1, next_id)

        if len(available_ids) <= 1:
            self._disable_random_tips()

        self.next()

    def _disable_random_tips(self):
        self.button(RANDOM_TIP_BUTTON).setEnabled(False)

    def done(self, result):
        super(TipOfTheDayWindow, self).done(result)

        seen_tips = []
        for page_id in self._visited_pages:
            if page_id in self._id_path:
                seen_tips.append(self._id_path[page_id][PATH])

    def _page_visited(self, page_id):
        if page_id != -1:
            self._visited_pages.add(page_id)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self._centre_window()
        super(TipOfTheDayWindow, self).showEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # wizard = TipOfTheDayWindow(mode=MODE_OVERVIEW)
    wizard = TipOfTheDayWindow(mode=MODE_TIP_OF_THE_DAY)

    wizard.show()
    sys.exit(app.exec())
