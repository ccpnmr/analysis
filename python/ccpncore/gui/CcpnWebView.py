__author__ = 'simon1'

from PyQt4.QtCore import QUrl
from PyQt4.QtWebKit import QWebView


class CcpnWebView(QWebView):

  def __init__(self, urlPath, parent=None):

    QWebView.__init__(self, parent)
    self.load(QUrl(urlPath))
    self.show()