"""
Translation and translation dictionary handling

the application can import the translator instance for translation and use:

translator.setLanguage(language)
translator.translate(text)

To silence the message, e.g. when initiating dynamical menus with recent files use:
translator.setSilent()
translator.setLoud()

To have both defaultLanguage and translated language:
translator.setDebug(True)

there are translation dictionaries associated with this module for really common words like "Help"


"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: gvuister $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

import importlib
import sys

from ccpncore.util import Logging

defaultLanguage = 'English-UK'
translationDirectory = 'translation'  # assumes that all translations are in sub-directory with this name in a file language.py

#languages = ['English-UK', 'Italiano']
import pkgutil
import ccpncore.util.translation as tModule
languages = [defaultLanguage] + [name for _, name, _ in pkgutil.iter_modules(tModule.__path__)]
if 'rude' in languages:
  languages.remove('rude')


class Translation:

  # class variables as the class is used in many instances and there is only one language!
  _language = defaultLanguage
  _translationDict = {}  # maps from default language text to translated text
  _silentTranslation = False
  _translationDebug = False

  def __init__(self):
    pass

  def setLanguage(self, language = defaultLanguage):
    """Set the language. Return True on error
    """
    if language == defaultLanguage: return
    if language == Translation._language: return

    translationModuleName = '%s.%s' % (tModule.__package__, language)
    #print(translationModuleName)

    try:
      module = importlib.import_module(translationModuleName)
    except ImportError as e:
      logger = Logging.getLogger()
      logger.warning('translation for language "%s" not available' % (language))
      return True

    try:
      moduleTranslationDict = module.translationDict
    except AttributeError as e:
      logger = Logging.getLogger()
      logger.warning('translation module "%s" does not have a translationDict' % translationModuleName)
      return True

    Translation._translationDict.update(moduleTranslationDict)
    Translation._language = language
    return False

  def translate(self, text):
    """ Translate a specific text into the previously specified language. """

    if len(text) == 0:
      return text

    # default language;
    if Translation._language == defaultLanguage:
      return text

    translatedText = Translation._translationDict.get(text)

    #print('>>translate: "%s" -> "%s"' % (text,translatedText))

    if translatedText is None:
      translatedText = text
      if not Translation._silentTranslation:
        logger = Logging.getLogger()
        logger.warning('text "%s" not in "%s" translation dictionary' % (text, Translation._language))
        # only warn once for 'text' by putting the string in the translation dictionary
        Translation._translationDict[text] = translatedText

    if Translation._translationDebug:
      translatedText += ' (%s)' % text

    return translatedText

  def setSilent(self):
    Translation._silentTranslation = True

  def setLoud(self):
    Translation._silentTranslation = False

  def setDebug(self, value):
    Translation._translationDebug = value

translator = Translation()

if __name__ == '__main__':

  tr = Translation()
  tr.setLanguage('Italiano')
  print(tr.translate("New"))