
import numpy as np
import pandas as pd
import glob
import os
from collections import namedtuple

filePathsProtein = glob.glob("/Users/luca/Desktop/PlainDataKen/Protein/*.tsv")
filePathsReference = glob.glob("/Users/luca/Desktop/PlainDataKen/Reference/*.tsv")


ExpType = {
          'H':'water',
          'H[t1rho(H)]': 't1',
          'Water-LOGSY.H':'wlogsy',
          'STD.H':'satxfer',
          }



def _getDataFrame(fileName):
  dataFrame = pd.read_table(fileName)
  dataFrame.columns = ['x', 'y','n']
  dataFrame = dataFrame.drop('n', 1)
  return dataFrame



def __getExpType(fileName):
  for n, e in ExpType.items():
    filename = fileName.split('_')
    if str(e) in filename:
      return n


def __getSpectra(filePaths):
  spectra = []
  for path in filePaths:
    fileName = path.split('/')[-1].split('.')[0]
    # try:
    #   pid = fileName.split('-')[1]
    # except:
    #   pid = fileName.split('-')[0]
    dataFrame = _getDataFrame(path)
    x = dataFrame.as_matrix(columns=['x']).ravel()
    y = dataFrame.as_matrix(columns=['y']).ravel()
    expType = __getExpType(fileName)
    spectrum  = (fileName, x, y, expType)
    spectra.append(spectrum)
  return spectra

Spectra_Protein = __getSpectra(filePathsProtein)
Spectra_Reference = __getSpectra(filePathsReference)


def _createDummies(spectra, suffix=None):
  for sp in Spectra_Protein:
    fileName, x, y, expType = sp
    ds = project.createDummySpectrum(('H',), str(suffix)+fileName)
    ds._positions = x
    ds._intensities = y
    ds.experimentType = expType


_createDummies(Spectra_Protein,  suffix='Pr-')
_createDummies(Spectra_Reference, suffix='Ref-')