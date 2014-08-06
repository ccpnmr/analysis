"""Translation and translation dictionary handling"""

import importlib

from ccpncore.util import Logging

# the application should call setTranslationLanguage() before doing anything else
# the other two functions should be called by modules as and when the modules are used
# updateTranslationDict() should be called as objects are created (but only needs to be called once per directory)
# getTranslation() should be called as needed

# there are translation dictionaries associated with this module for really common words like "Help"

defaultLanguage = 'english'  # make all languages lowercase
translationDirectory = 'translation'  # assumes that all translations are in sub-directory with this name in a file language.py

translationLanguage = defaultLanguage
translationDebug = False
translationDict = {}  # maps from default language text to translated text
translationModuleSet = set()  # keeps track of which translation modules have been loaded

def setTranslationLanguage(language=defaultLanguage, debug=False):
  """ Set the translation language """
  
  global translationLanguage, translationDict, translationDebug, translationModuleSet

  translationLanguage = language
  translationDebug = debug
  translationDict = {}
  translationModuleSet = set()
  
  updateTranslationDict()

def updateTranslationDict(obj=None):
  """ Add all the translations for directory in which this object is located """
  
  if translationLanguage == defaultLanguage:
    return
  
  if obj:
    objModuleName = obj.__module__
  else:
    objModuleName = 'ccpncore.util'
    
  if objModuleName in translationModuleSet:  # translations already been added for this directory
    return
    
  moduleName = '%s.%s.%s' % (objModuleName, translationDirectory, translationLanguage)
  
  try:
    module = importlib.import_module(moduleName)
  except ImportError as e:
    logger = Logging.getLogger()
    logger.warning('translation module "%s" not available' % moduleName)
    return
    
  try:
    moduleTranslationDict = module.translationDict
  except AttributeError as e:
    logger = Logging.getLogger()
    logger.warning('translation module "%s" does not have a translationDict' % moduleName)
    return
  
  translationDict.update(moduleTranslationDict)
  
  translationModuleSet.add(objModuleName)
  
def getTranslation(text):
  """ Translate a specific text into the previously specified language. """

  if translationLanguage == defaultLanguage:
    return text
    
  translatedText = translationDict.get(text)
  
  if not translatedText:
    logger = Logging.getLogger()
    logger.warning('text "%s" not in %s translation dictionary' % (text, translationLanguage))
    translatedText = text
  
  if translationDebug:
    translatedText += ' (%s)' % text
    
  return translatedText

class Translation:
  def __init__(self):
    updateTranslationDict(self)

  def translate(self, text):
    return Translation.getTranslation(text)
