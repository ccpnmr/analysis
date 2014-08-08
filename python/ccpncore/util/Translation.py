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
translationModuleSet = set()  # keeps track of which translation modules have been loaded

def setTranslationLanguage(language=defaultLanguage, debug=False):
  """ Set the translation language """
  
  global translationLanguage, translationDict, translationDebug, translationModuleSet

  translationLanguage = language
  translationDebug = debug
  translationDict = {}
  translationModuleSet = set()
  
  updateTranslationDict()

### CARE: Problem is that we want to find the module in which the object is created,
### not the module in which the code which creates it lives.
### The code below is dangerous and could not work in some Python implementations.

def updateTranslationDict(depth=None):
  """ Add all the translations for directory in which this object is located.
      The depth is how far up calling stack to go (not including this function itself).
  """

  if translationLanguage == defaultLanguage:
    return
  
  if depth is None:
    objModuleName = 'ccpncore.util'
  else:
    fileName = sys._getframe(depth+1).f_code.co_filename
    for objModuleName in sys.modules:
      module = sys.modules[objModuleName]
      try:
        if module.__file__ == fileName:
          break
      except:
        pass
    else:
      logger = Logging.getLogger()
      logger.warning('translation module not found for path "%s"' % fileName)
      return
    n = objModuleName.rfind('.')
    if n < 0:
      logger = Logging.getLogger()
      logger.warning('translation module missing . for path "%s"' % fileName)
      return
    objModuleName = objModuleName[:n]
    
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
  def __init__(self, depth=2):
    """ The depth is how far up calling stack to go (not including this function itself).
        In general want to go 2 up the stack because that is the module in which the widget lives.
        (0 is normally Base.py and 1 is normally the ccpncore.gui file, e.g. Action.py or Button.py)
    """
    updateTranslationDict(depth+1)

  def translate(self, text):
    return getTranslation(text)
