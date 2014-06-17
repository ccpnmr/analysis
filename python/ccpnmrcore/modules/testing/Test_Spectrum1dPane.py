from ccpnmrcore.testing.Testing import Testing

from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane

from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem

from ccpn.lib import Spectrum

import pprint

from numpy import NaN, Inf, arange, isscalar, asarray, array

import pyqtgraph as pg

from PySide import QtGui

import sys


import ccpn

class Spectrum1dPaneTest(Testing):

  def __init__(self, *args, **kw):
    Testing.__init__(self, projectPath='Ccpn1Dtesting', *args, **kw)
    self.spectrumName = '1D'
    self.project = ccpn.openProject(self.projectPath)


  def test_spectrum1dPane(self):

    spectrumPane = Spectrum1dPane()
    spectrum = self.getSpectrum()
    data = Spectrum1dItem(spectrumPane,spectrum).spectralData
    return data





if __name__ == '__main__':
  def testMain():

    spectrum = Spectrum1dPaneTest()
    w = QtGui.QWidget()
    layout = QtGui.QGridLayout()
    spectrumPane=Spectrum1dPane()
    widget = spectrumPane.widget
    layout.addWidget(widget)
    widget.plot(spectrum.test_spectrum1dPane())
    xData = []
    yData = []
    for x,y in spectrum.test_spectrum1dPane():
      # print('x:',x,'\ny:',y)
      xData.append(x)
      yData.append(y)
    xData = array(xData)
    yData = array(yData)
    maxtab,mintab = peakdet(yData,2e6,xData)
    # print(array(maxtab)[:,0], array(maxtab)[:,1])
    peaks = array(maxtab)[:,0],array(maxtab)[:,1]
    # print(peaks)
    positions = []
    for i,j in zip(array(maxtab)[:,0],array(maxtab)[:,1]):
      print(i,j)
      text = pg.TextItem(text=str("%.3f" % i),anchor=(-0.1,0))
      widget.addItem(text)
      text.setPos(i,j)


    # for peak in peaks:
    #   vLine = pg.InfiniteLine(angle=90, movable=False)
    #   widget.addItem(vLine)
    #   vLine.setPos(peak)
    widget.plotItem.layout.setContentsMargins(0, 0, 0, 0)
    w.setLayout(layout)
    w.show()
    w.raise_()
    sys.exit(spectrum.exec_())

  def peakdet(v, delta, x = None):
      """
      Converted from MATLAB script at http://billauer.co.il/peakdet.html

      Returns two arrays

      function [maxtab, mintab]=peakdet(v, delta, x)
      %PEAKDET Detect peaks in a vector
      %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
      %        maxima and minima ("peaks") in the vector V.
      %        MAXTAB and MINTAB consists of two columns. Column 1
      %        contains indices in V, and column 2 the found values.
      %
      %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
      %        in MAXTAB and MINTAB are replaced with the corresponding
      %        X-values.
      %
      %        A point is considered a maximum peak if it has the maximal
      %        value, and was preceded (to the left) by a value lower by
      %        DELTA.

      % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
      % This function is released to the public domain; Any use is allowed.

      """
      maxtab = []
      mintab = []

      if x is None:
          x = arange(len(v))

      v = asarray(v)

      if len(v) != len(x):
          sys.exit('Input vectors v and x must have same length')

      if not isscalar(delta):
          sys.exit('Input argument delta must be a scalar')

      if delta <= 0:
          sys.exit('Input argument delta must be positive')

      mn, mx = Inf, -Inf
      mnpos, mxpos = NaN, NaN

      lookformax = True

      for i in arange(len(v)):
          this = v[i]
          if this > mx:
              mx = this
              mxpos = x[i]
          if this < mn:
              mn = this
              mnpos = x[i]

          if lookformax:
              if this < mx-delta:
                  maxtab.append((mxpos, mx))
                  mn = this
                  mnpos = x[i]
                  lookformax = False
          else:
              if this > mn+delta:
                  mintab.append((mnpos, mn))
                  mx = this
                  mxpos = x[i]
                  lookformax = True

      return array(maxtab), array(mintab)

  testMain()




