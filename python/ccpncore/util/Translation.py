"""Module Documentation here

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
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
"""Translation and translation dictionary handling"""

import importlib
import sys

from ccpncore.util import Logging

# the application should call setTranslationLanguage() before doing anything else
# the other two functions should be called by modules as and when the modules are used
# updateTranslationDict() should be called as objects are created (but only needs to be called once per directory)
# getTranslation() should be called as needed

# there are translation dictionaries associated with this module for really common words like "Help"

defaultLanguage = 'English'
translationDirectory = 'translation'  # assumes that all translations are in sub-directory with this name in a file language.py

translationLanguage = defaultLanguage
translationDebug = False
translationDict = {}  # maps from default language text to translated text

def setTranslationLanguage(language=defaultLanguage, debug=False):
  """ Set the translation language """
  
  global translationLanguage, translationDict, translationDebug

  translationLanguage = language
  translationDebug = debug
  translationDict = {}
  
  updateTranslationDict()

### CARE: Problem is that we want to find the module in which the object is created,
### not the module in which the code which creates it lives.
### The code below is dangerous and could not work in some Python implementations.

def updateTranslationDict(moduleName=None):
  """ Add all the translations for directory in which this object is located.
      The depth is how far up calling stack to go (not including this function itself).
  """

  if translationLanguage == defaultLanguage:
    return
  
  if moduleName is None:
    moduleName = 'ccpncore.util'
    
  translationModuleName = '%s.%s.%s' % (moduleName, translationDirectory, translationLanguage)
    
  try:
    module = importlib.import_module(translationModuleName)
  except ImportError as e:
    logger = Logging.getLogger()
    logger.warning('translation for module "%s" not available for language "%s"' % (moduleName, translationLanguage))
    return
    
  try:
    moduleTranslationDict = module.translationDict
  except AttributeError as e:
    logger = Logging.getLogger()
    logger.warning('translation module "%s" does not have a translationDict' % moduleName)
    return
  
  translationDict.update(moduleTranslationDict)
  
def getTranslation(text):
  """ Translate a specific text into the previously specified language. """

  if translationLanguage == defaultLanguage:
    return text
    
  translatedText = translationDict.get(text)

  if translatedText is None:
    logger = Logging.getLogger()
    logger.warning('text "%s" not in %s translation dictionary' % (text, translationLanguage))
    translatedText = text
  
  if translationDebug:
    translatedText += ' (%s)' % text
    
  return translatedText

class Translation:
  def translate(self, text):
    return getTranslation(text)
