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
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import importlib
import sys

from ccpn.util import Logging


defaultLanguage = 'English-UK'
translationDirectory = 'translation'  # assumes that all translations are in sub-directory with this name in a file language.py

#languages = ['English-UK', 'Italiano']
import pkgutil
import ccpn.framework.languages as tModule


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

    def setLanguage(self, language=defaultLanguage):
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
            logger.warning('Translation for language "%s" not available' % (language))
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
        if not text:
            return
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

######################################################################################

import os
import json
from functools import partial

from ccpn.util.Path import getTopDirectory
from ccpn.util.Logging import getLogger


logger = getLogger()

__all__ = ['getTranslator']


def _get_languages():
    languagesPath = os.path.join(getTopDirectory(), 'config', 'languages')
    languageFiles = [f for f in os.listdir(languagesPath)
                     if os.path.isfile(os.path.join(languagesPath, f))]
    logger.debug('Found {} language files'.format(languageFiles))
    languages = [l.split('.')[0] for l in languageFiles]
    return languages


def _get_translation_dictionary(language):
    languagesPath = os.path.join(getTopDirectory(), 'config', 'languages')
    try:
        languageFilePath = os.path.join(languagesPath, language + '.json')
        with open(languageFilePath, encoding='utf-8') as f:
            tDict = json.load(f)
        return tDict
    except:
        logger.error('Language file for {} failed to load'.format(language))
        return dict()


def _translator(translationDict, word):
    t = translationDict.get(word, word)
    logger.debug('Translating {} to {}'.format(word, t))  # The string interpolation can be costly.
    return t


def getTranslator(language):
    tDict = _get_translation_dictionary(language)
    tr = partial(_translator, tDict)
    return tr


######################################################################################

if __name__ == '__main__':
    tr = Translation()
    tr.setLanguage('Italian')
    print(tr.translate("New"))
