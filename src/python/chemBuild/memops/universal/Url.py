
"""
======================COPYRIGHT/LICENSE START==========================

Url.py: Url code for CCPN

Copyright (C) 2003-2010  (CCPN Project)

=======================================================================

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.
 
A copy of this license can be found in ../../../license/LGPL.license
 
This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Lesser General Public License for more details.
 
You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


======================COPYRIGHT/LICENSE END============================

for further information, please contact :

- CCPN website (http://www.ccpn.ac.uk/)

- email: ccpn@bioc.cam.ac.uk

=======================================================================

If you are using this software for academic purposes, we suggest
quoting the following references:

===========================REFERENCE START=============================
R. Fogh, J. Ionides, E. Ulrich, W. Boucher, W. Vranken, J.P. Linge, M.
Habeck, W. Rieping, T.N. Bhat, J. Westbrook, K. Henrick, G. Gilliland,
H. Berman, J. Thornton, M. Nilges, J. Markley and E. Laue (2002). The
CCPN project: An interim report on a data model for the NMR community
(Progress report). Nature Struct. Biol. 9, 416-418.

Rasmus H. Fogh, Wayne Boucher, Wim F. Vranken, Anne
Pajon, Tim J. Stevens, T.N. Bhat, John Westbrook, John M.C. Ionides and
Ernest D. Laue (2005). A framework for scientific data modeling and automated
software development. Bioinformatics 21, 1678-1684.

===========================REFERENCE END===============================

"""

def fetchUrl(url, values=None, headers=None, timeout=None):

  import socket
  import urllib.request, urllib.parse, urllib.error
  import urllib.request, urllib.error, urllib.parse

  if not headers:
    headers = {}

  try:
    # from Python 2.6 there is a timeout option in urlopen()
    # but for now assume Python 2.5 compatibility
    oldTimeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    if values:
      data = {}
      for key in values:
        value = values[key]
        if isinstance(value, str):
          value = value.encode('utf-8')
        data[key] = value
      data = urllib.parse.urlencode(data)
    else:
      data = None
    request = urllib.request.Request(url, data, headers)
    response = urllib.request.urlopen(request)
    result = response.read()
  finally:
    socket.setdefaulttimeout(oldTimeout)

  return result

# uploadFiles() is slightly modified version of code from Michael Foord
# and that said:

# Copyright Michael Foord, 2004 & 2005.
# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/documents/BSD-LICENSE.txt
# Based on http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/146306
# With inspiration from urllib2_file.py by Fabien Seisen, http://fabien.seisen.org/python/ (without his twiddly bits)
# It actually uses my upload script located at http://www.voidspace.xennos.com

def uploadFiles(url, fileFields, fields=None, boundary=None):
  """Uploads regular fields and files to specified url
  url is the Url to send data to.
  fileFields is a sequence of (name, fileName) elements, or the dictionary
  equivalent, for file form fields.
  fields is a sequence of (name, value) elements, or the dictionary equivalent,
  for regular form fields.
  Returns response."""

  import mimetypes
  import mimetools
  import os
  import urllib.request, urllib.error, urllib.parse

  if not fields:
    fields = ()

  if not boundary:
    boundary = '-----' + mimetools.choose_boundary() + '-----'

  CRLF = '\r\n'
  xx = []
  if isinstance(fields, dict):
    fields = list(fields.items())
  for (key, value) in fields:
    xx.append('--' + boundary)
    xx.append('Content-Disposition: form-data; name="%s"' % key)
    xx.append('')
    xx.append(str(value))

  if isinstance(fileFields, dict):
    fileFields = list(fileFields.items())
  for (key, fileName) in fileFields:
    fp = open(fileName, 'rb')
    value = fp.read()
    fp.close()

    fileName = os.path.basename(fileName)
    fileType = mimetypes.guess_type(fileName)[0] or 'application/octet-stream'
    xx.append('--' + boundary)
    xx.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, fileName))
    xx.append('Content-Type: %s' % fileType)
    xx.append('')
    xx.append(value)

  xx.append('--' + boundary + '--')
  xx.append('')
  body = CRLF.join(xx)

  contentType = 'multipart/form-data; boundary=%s' % boundary
  headers = {
    'Content-type': contentType,
    'Content-length': str(len(body)),
  }

  request = urllib.request.Request(url, body, headers)
  handle = urllib.request.urlopen(request)
  try:
    result = handle.read()
  finally:
    handle.close()

  return result

def uploadFile(url, fileKey, fileName, fields=None, boundary=None):
  """Uploads regular fields and file to specified url
  url is the Url to send data to.
  fileKey is the form key for the file.
  fileName is the full path for the file.
  fields is a sequence of (name, value) elements, or the dictionary equivalent,
  for regular form fields.
  Returns response."""

  return uploadFiles(url, ((fileKey, fileName),), fields, boundary)

