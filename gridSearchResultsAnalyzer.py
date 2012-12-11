# gridSearchResultsAnalyzer.py
# Plot histograms and print diagnostic info for grid search results
#
# Created by Colin Raffel on 12/1/12

import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import collections

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "Usage: %s gridSearchResults.csv nDimensions" % sys.argv[0]
    sys.exit(-1)
  
  nDimensions = int(sys.argv[2])

  gridSearchResults = []
  for n in xrange( nDimensions ):
    gridSearchResults += [collections.defaultdict(list)]
  
  with open(sys.argv[1], 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
      for n in xrange( nDimensions ):
        gridSearchResults[n][row[n]] += [float(row[-1])]

  for n in xrange( nDimensions ):
    labels = []
    nValues = np.ceil(len(gridSearchResults[n])/2.0)
    m = 1
    tallestBin = 0
    axes = []

    for value, accuracies in gridSearchResults[n].iteritems():
      labels += [value]
      axes += [plt.subplot( 2, nValues, m )]
      m += 1
      binCounts, _, _ = axes[-1].hist( np.array(accuracies), bins=50, range=[0, 1] )
      if np.max( binCounts ) > tallestBin:
        tallestBin = np.max( binCounts )
      plt.title( value )
      print value, '->', np.mean( accuracies ), np.std(accuracies), np.max(accuracies), np.min( accuracies )
    for axis in axes:
      axis.axis( [0, 1, 0, tallestBin] )
    #plt.legend( labels )
    plt.show()

    accuraciesArray = [[]]
    for value, accuracies in gridSearchResults[n].iteritems():
      accuraciesArray += [accuracies]

    accuraciesArray.remove([])
    accuraciesArray = (np.array(accuraciesArray).T)*100
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    plt.boxplot( accuraciesArray, whis=100 )
    xtickNames = plt.setp(ax1, xticklabels=['SD', 'MSD', 'HFCR', 'HFCL', 'C', 'HFCQ', 'KD'])
    plt.xlabel( 'Onset Detection Function' )
    plt.ylabel( 'Percent of pieces' )
    plt.show()