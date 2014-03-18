from ccpncore.util import Translation

def test_setLanguageDefault():
  Translation.setTranslationLanguage()

def test_setLanguageEnglish():
  Translation.setTranslationLanguage('english')

def test_setLanguageFrench():
  Translation.setTranslationLanguage('french')

def test_setLanguageGerman():
  Translation.setTranslationLanguage('german')

def test_translateDefaultText():
  Translation.setTranslationLanguage()
  assert Translation.getTranslation('Help') == 'Help'

def test_translateEnglishText():
  Translation.setTranslationLanguage('english')
  assert Translation.getTranslation('Help') == 'Help'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('french')
  assert Translation.getTranslation('Help') == 'Aidez'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('french')
  assert Translation.getTranslation('Help Me') == 'Help Me'
