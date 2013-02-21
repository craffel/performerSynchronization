# onsetDetection.py
# Given a spectrogram, return indices of frames which are onsets
#
# Created by Colin Raffel on 4/6/12

import numpy as np
import mfcc
#import scipy.signal as signal

class ODF:
  def __init__( self, spectrogram, onsetDetectionAlgorithm, **kwargs ):
    self.spectrogram = spectrogram
    self.onsetDetectionFunction = onsetDetectionAlgorithm( self, **kwargs )
  
  def plotAllOnsetFunctions( self ):
    import matplotlib.pyplot as plt
    algorithms = (self.HFCMasri,\
                  self.HFCJensen,\
                  self.HFCMasriBello,\
                  self.spectralDistance,\
                  self.complex,\
                  self.phase,\
                  self.KLDivergence,\
                  self.melDifference)
    plotColors = ('b-', 'g-', 'r-', 'c-', 'm-', 'y-', 'k-', 'b--', 'g--', 'r--', 'c--')
    for onsetDetectionAlgorithm, color in zip( algorithms, plotColors ):
      onsetDetectionFunction = onsetDetectionAlgorithm()
      plt.plot( onsetDetectionFunction/np.max(np.abs(onsetDetectionFunction)), color )
    plt.legend( [f.__name__ for f in algorithms] )
    plt.show()
  
  # This doesn't seem to work well.
  def HFCMasri( self, **kwargs ):
    # Equation 3 from "Improved Modelling of Attack Transients in Music Analysis-Resynthesis"
    HFC = np.zeros( self.spectrogram.shape[0] )
    DF = np.zeros( self.spectrogram.shape[0] )
    # Scale for summing frequency bins, with a weighting on high frequencies
    scale = np.arange( self.spectrogram[0].shape[0] - 1 ) + 2
    for n in np.arange( 1, self.spectrogram.shape[0] ):
      # Get power spectrum
      power = np.abs( self.spectrogram[n][1:] )**2
      # Calculate high frequency content
      HFC[n] = np.sum( power*scale )
      # Denominator for detection function
      denominator = HFC[n-1]*np.sum( power )
      # Denominator should be minimum of 1
      if denominator > 1:
        DF[n] = (HFC[n]**2)/denominator      
      else:
        DF[n] = 0
    return DF

  def HFCJensen( self, **kwargs ):
    # Equation 3 from "Real-time beat estimation using feature extraction"
    HFC = np.zeros( self.spectrogram.shape[0] )
    # Scale for summing frequency bins, with a weighting on high frequencies
    scale = (np.arange( self.spectrogram[0].shape[0] - 1 ) + 1)**2
    for n in np.arange( 1, self.spectrogram.shape[0] ):
      # Calculate high frequency content
      HFC[n] = np.sum( scale*np.abs( self.spectrogram[n][1:] ) )
    return HFC
      
  def HFCMasriBello( self, **kwargs ):
    # Equation 4 from "A Tutorial on Onset Detection in Music Signals"
    HFC = np.zeros( self.spectrogram.shape[0] )
    # Scale for summing frequency bins, with a weighting on high frequencies
    scale = np.arange( self.spectrogram[0].shape[0] - 1 ) + 2
    for n in np.arange( 1, self.spectrogram.shape[0] ):
      # Calculate high frequency content
      HFC[n] = np.sum( scale*np.abs( self.spectrogram[n][1:] ) )
    return HFC
      
  def spectralDistance( self, **kwargs ):
    # Equation 7 from "A hybrid approach to musical note onset detection"
    DM = np.zeros( self.spectrogram.shape[0] )
    magnitudeSpectrogram = np.abs( self.spectrogram )
    for n in np.arange( 1, self.spectrogram.shape[0] ):
      difference = magnitudeSpectrogram[n] - magnitudeSpectrogram[n - 1]
      difference = np.clip( difference, 0, np.inf )
      DM[n] = np.sum( difference*difference )
    return DM
 
  # Verified working against http://www.mathworks.com/matlabcentral/fileexchange/33451-integrated-stft-istft-onset-detection
  def complex( self, **kwargs ):
    # Eqn 18 from "COMPLEX DOMAIN ONSET DETECTION FOR MUSICAL SIGNALS"
    # Phi = unwrapped phase of spectra
    phi = np.unwrap( np.angle( self.spectrogram ), axis=1 )
    # Dphi = princarg( phi[n] - 2*phi[n-1] + phi[n-2] )
    dphi = np.zeros( self.spectrogram.shape )
    dphi[2:,:] = np.mod( phi[2:] - 2*phi[1:-1] + phi[:-2] + np.pi, -2*np.pi ) + np.pi
    Rhat = np.zeros( self.spectrogram.shape )
    Rhat[2:,:] = np.abs( self.spectrogram[1:-1] )
    R = np.zeros( self.spectrogram.shape )
    R[2:,:] = np.abs( self.spectrogram[2:] )
    gamma = np.sqrt( np.clip( Rhat**2 + R**2 - 2*Rhat*R*np.cos( dphi ), 0, np.inf ) )
    return np.sum( gamma, axis = 1 )

  # I don't think this is working properly.
  def phase( self, **kwargs ):
    # Eqn 5 from "A COMBINED PHASE AND AMPLITUDE BASED APPROACH TO ONSET DETECTION FOR AUDIO SEGMENTATION"
    eta = np.zeros( self.spectrogram.shape[0] )
    # Phi = unwrapped phase of spectra (don't unwrap)
    phi = np.unwrap( np.angle( self.spectrogram ), axis=1 )
    # Dphi = princarg( phi[n] - 2*phi[n-1] + phi[n-2] )
    dphi = np.zeros( self.spectrogram.shape )
    dphi[2:] = np.mod( phi[2:] - 2*phi[1:-1] + phi[:-2] + np.pi, -2*np.pi ) + np.pi
    for n in np.arange( 2, self.spectrogram.shape[0] ):
      eta[n] = np.mean( np.histogram( np.abs( dphi[n] ), bins=1000, density=True )[0] )
    eta[0] = np.median( eta[2:] )
    eta[1] = eta[0]
    eta = eta - np.min( eta )
    eta = eta/np.max( eta )
    '''import matplotlib.pyplot as plt
    plt.imshow( np.abs( dphi.T ), origin='lower', aspect='auto', interpolation='nearest', cmap=plt.cm.gray )
    plt.plot( eta*dphi.shape[1] )
    plt.show()'''
    return eta

  def KLDivergence( self, **kwargs ):
    KLDivergence = np.zeros( self.spectrogram.shape[0] )
    magnitudeSpectrogram = np.abs( self.spectrogram )
    # Calculate KL divergence of successive spectra, and take mean of each spectrum's KL divergence as ODF
    KLDivergence[1:] = np.mean( magnitudeSpectrogram[1:]*np.log( 1.0 + magnitudeSpectrogram[1:]/(magnitudeSpectrogram[:-1] + 1E-10) ), axis = 1 )
    return KLDivergence
  
  # DAn's Mel-spectrum difference ODF
  def melDifference( self, **kwargs ):
    fs = kwargs.get( 'fs', 44100 )
    melSpectrum = mfcc.MFCC( fs, 2*(self.spectrogram.shape[1] - 1) ).getMelSpectrum( self.spectrogram )
    return np.mean( np.clip( np.diff( np.log( melSpectrum + 1E-10 ), axis=0 ), 0, np.inf ), axis=1 )