from ccpncore.util.Color import Color

from nose.tools import raises

@raises(TypeError)
def test_color_create_blank():
  c = Color()

def test_color_create_known_name():
  c = Color('red')

@raises(KeyError)
def test_color_create_unknown_name():
  c = Color('really-red')

def test_color_create_hex():
  c = Color('#ff00ff')
  print(c.name)
  c = Color('#FF00FFFF')
  print(c.name)

def test_color_create_rgb():
  c = Color((255, 0, 255))
  print(c.name)
  c = Color((255, 0, 255, 127))
  print(c.name)


