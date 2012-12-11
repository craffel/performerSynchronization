# batchCreateMIDITestFiles.py
# Given some MIDI files, mes
#
# Created by Colin Raffel on 10/7/10

import utility
import createMIDITestFiles
import numpy as np
import sys
import os

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print "Usage: %s datasetDirectory outputDirectory" % sys.argv[0]
    sys.exit(-1)

  files = utility.getFiles( sys.argv[1], '.mid' )

  for file in files:
    filename = os.path.split( os.path.splitext( file )[0] )[1]
    outputDirectory = os.path.join( sys.argv[2], filename )
    os.makedirs( outputDirectory )
    filesWritten = createMIDITestFiles.MIDIToTestFiles( file ).createMIDITestFiles( outputDirectory, 10, 20, np.arange(0, 100, 10) )
    if len(filesWritten) is 0:
      os.rmdir( outputDirectory )