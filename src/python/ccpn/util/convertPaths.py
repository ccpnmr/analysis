"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import string

# PATH1 = '/Users/wb104/miniconda3/envs/ccpnmr_dist'
# PATH2 = '/Users/wb104/release/ccpnmr3.0.b2/miniconda'


def istext(filename):
  try:
    print (filename)
    s = open(filename).read(512)
    print (map(chr, range(32, 127)) , list("\n\r\t\b"))
    return

    text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
    _null_trans = string.maketrans("", "")
    if not s:
      # Empty files are considered text
      return True
    if "\0" in s:
      # Files with null bytes are likely binary
      return False
    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_null_trans, text_characters)
    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t)) / float(len(s)) > 0.30:
      return False
    return True
  except:
    return False


def main(ROOT, PATH1, PATH2):
  for directory in ('bin', 'lib'):

    # os.chdir('miniconda/%s' % directory)
    os.chdir(ROOT+'/%s' % directory)

    filenames = os.listdir('.')
    filenames = [filename for filename in filenames if
                 os.path.isfile(filename) and not os.path.islink(filename)]

    for filename in filenames:
      # if istext(filename):

      try:
        # print('%s is text' % filename)
        with open(filename, 'r') as fp:
          data = fp.read()
        if PATH1 in data:
          print('changing path in %s' % filename)
          data = data.replace(PATH1, PATH2)
          with open(filename, 'w') as fp:
            fp.write(data)

            # else:
            # print('%s is binary' % filename)
      except:
        # print ('  error reading:. %s' % filename)
        pass

    os.chdir('../..')


if __name__ == '__main__':
  inRoot = sys.argv[1]
  inPath1 = sys.argv[2]
  inPath2 = sys.argv[3]

  main(inRoot, inPath1, inPath2)
