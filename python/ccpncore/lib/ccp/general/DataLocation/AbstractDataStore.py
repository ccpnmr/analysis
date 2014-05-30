__author__ = 'rhf22'

import os
from ccpncore.util import Path
from ccpncore.api.memops import Implementation

def changeDataStoreUrl(dataStore, newPath):
  """ Change the url for this dataStore, so that the end we have
  dataStore.dataUrl.url.path = newPath.  This changes all dataUrls
  with the same old path if the old path does not exist and the
  new one does.
  """

  newPath = Path.normalisePath(newPath, makeAbsolute=True)
  oldDataUrl = dataStore.dataUrl
  oldUrl = oldDataUrl.url
  oldPath = oldUrl.dataLocation
  oldExists = os.path.exists(oldPath)
  if newPath != oldPath:
    dataLocationStore = dataStore.dataLocationStore
    newUrl = Implementation.Url(path=newPath)  # TBD: should use oldUrl.clone(path=newPath)

    # first check if have a dataUrl with this path
    newDataUrl = dataLocationStore.findFirstDataUrl(url=newUrl)
    if not newDataUrl:
      # if old path exists and there is more than one dataStore with
      # this dataUrl then create new one
      dataUrlStores = dataLocationStore.findAllDataStores(dataUrl=oldDataUrl)
      if oldExists and len(dataUrlStores) > 1:
        newDataUrl = dataLocationStore.newDataUrl(name=oldDataUrl.name, url=newUrl)

    # if have found or have created newDataUrl then set dataStore to point to it
    # else just change url of oldDataUrl (which could affect other dataStores)
    if newDataUrl:
      dataStore.dataUrl = newDataUrl
    else:
      oldDataUrl.url = newUrl

    # if old path does not exist and new path exists then change urls of
    # all data urls which have old path to new path (there might be none)
    if not oldExists:
      newExists = os.path.exists(newPath)
      if newExists:
        for dataUrl in dataLocationStore.dataUrls:
          if dataUrl.url == oldUrl:
            dataUrl.url = newUrl

