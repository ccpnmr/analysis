from ccpncore.util import Translation

def test_setLanguageDefault():
  Translation.setTranslationLanguage()

def test_setLanguageEnglish():
  Translation.setTranslationLanguage('English')

def test_setLanguageFrench():
  Translation.setTranslationLanguage('French')

def test_setLanguageGerman():
  Translation.setTranslationLanguage('German')

def test_translateDefaultText():
  Translation.setTranslationLanguage()
  assert Translation.getTranslation('Help') == 'Help'

def test_translateEnglishText():
  Translation.setTranslationLanguage('English')
  assert Translation.getTranslation('Help') == 'Help'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('French')
  assert Translation.getTranslation('Help') == 'Aidez'

def test_translateFrenchText1():
  Translation.setTranslationLanguage('French')
  assert Translation.getTranslation('Help Me') == 'Help Me'
