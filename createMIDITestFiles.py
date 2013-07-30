# createMIDITestFiles.py
# Given a MIDI file, create an audio file and a file listing the onset times
#
# Created by Colin Raffel on 11/9/12  

import midi
import numpy as np
import os
import random
import string
import tempfile

class MIDIToTestFiles:
  def __init__( self, MIDIFile ):
    # Read in the MIDI data
    self.MIDIData = midi.read_midifile( MIDIFile )
    self.originalMIDIFile = MIDIFile

  def createMIDITestFiles( self, outputDirectory, start, end, randomScales ):
    channelsToUse = self.getBestChannels( start, end )
    filesWritten = []
    if channelsToUse is None:
      return filesWritten
    for index, channel in enumerate( channelsToUse ):
      for randomScale in randomScales:
        file = os.path.join( outputDirectory, str(index) + '-' + str(randomScale) + 'ms.wav' )
        self.writeFileForChannel( file, channel, start, end, randomScale )
        filesWritten.append( file )
    return filesWritten
    
  def getTickScaling( self ):
    # Scale for MIDI tick numbers, to convert to seconds
    tickScale = 1
    foundTempo = 0
    tempoEvent = None
    # Find the tempo setting message
    for track in self.MIDIData:
      for event in track:
        if event.name == 'Set Tempo':
          if foundTempo:
            print "Warning: Multiple tempi found."
            break
          else:
            tickScale = 60.0/(event.get_bpm()*self.MIDIData.resolution)
            tempoEvent = event
            foundTempo = 1
    return tickScale, tempoEvent
  
  def getBestChannels( self, start, end ):

    tickScale, tempoEvent = self.getTickScaling()
      
    if tempoEvent is None:
      return None
    
    # Recalculate start and end times according to tick location
    start = int( start/tickScale )
    end = int( end/tickScale )
        
    eventLocations = {}

    # Cycle through tracks to find note-on events in the specified channel
    for track in self.MIDIData:
      # We will need to increment ticks according to the ticks we find
      currentTick = 0
      hasNotes = 0
      # Cycle through all events in the track
      for event in track:
        # Increment tick value because they can happen across channels
        currentTick += event.tick
        # Are we within the time limits we care about?
        if currentTick > start and currentTick < end:
          # Only record note on events
          if event.name == 'Note On' and event.velocity > 0:
            if eventLocations.has_key( event.channel ) and eventLocations[event.channel].count( currentTick ) == 0:
              eventLocations[event.channel].append( currentTick )
            else:
              eventLocations[event.channel] = [currentTick]
  
    bestNumberOfMatches = 0
    bestPair = None
    for mainChannel in eventLocations:
      for compareChannel in eventLocations:
        if mainChannel == compareChannel:
          continue
        matches = 0
        for tick in eventLocations[mainChannel]:
          matches += eventLocations[compareChannel].count( tick )
        if matches > bestNumberOfMatches:
          bestNumberOfMatches = matches
          bestPair = (mainChannel, compareChannel)
    
    return bestPair
    
  # Write out the unique time of note-ons
  def writeFileForChannel( self, filename, channel, start, end, randomScale ):
    
    # Hold all the tracks in our output pattern
    tracks = []

    tickScale, tempoEvent = self.getTickScaling()
    
    # Convert random scale to 1/2 std. dev. with tick scaling
    randomScale = (randomScale/2.0)/tickScale
    # Convert to ms
    randomScale /= 1000.0
    
    if tempoEvent is None:
      return 0
  
    # Recalculate start and end times according to tick location
    start = int( start/tickScale )
    end = int( end/tickScale )
    # Do we even need this track?  I don't know.
    tracks.append( [midi.TimeSignatureEvent(tick=0, data=[4, 2, 24, 8]),
                    midi.KeySignatureEvent(tick=0, data=[0, 0]),
                    midi.EndOfTrackEvent(tick=1, data=[])] )

    # Cycle through tracks to find note-on events in the specified channel
    for track in self.MIDIData:
      # Current track we're constructing
      currentTrack = []
      # We will need to increment ticks according to the ticks we find
      currentTick = 0
      time = 0
      lastTick = start
      hasNotes = 0
      # Cycle through all events in the track
      for event in track:
        # Keep the instrument in tact
        if event.name == 'Program Change' and event.channel == channel:
          currentTrack.append( midi.ProgramChangeEvent( tick=1, channel=channel, data=event.data ) )
        # Increment tick value because they can happen across channels
        currentTick += event.tick
        # Are we within the time limits we care about?
        if currentTick > start and currentTick < end:
          # Only record note events
          if event.name == 'Note On' or event.name == 'Note Off':
            # Is this on the channel we're writing out?
            if event.channel == channel:
              tick = currentTick - lastTick + int(randomScale*np.random.randn())
              if tick < 0:
                tick = 0
              if event.name == 'Note On':
                currentTrack.append( midi.NoteOnEvent( tick=tick, channel = event.channel, data = event.data ) )
              else:
                currentTrack.append( midi.NoteOffEvent( tick=tick, channel = event.channel, data = event.data ) )
              lastTick = currentTick
              hasNotes = 1
      if hasNotes:
        currentTrack.insert( 0, tempoEvent )
        currentTrack.append( midi.EndOfTrackEvent(tick=1, data=[]) )
        tracks.append( currentTrack )
    
    if len( tracks ) > 1:
      # Construct MIDI pattern...
      pattern = midi.Pattern( tracks=tracks, resolution=self.MIDIData.resolution )
      # And write it out to a temp location...
      tempMIDIFile = tempfile.NamedTemporaryFile()
      midi.write_midifile( tempMIDIFile.name, pattern )
      # Write the wav
      os.system( 'fluidsynth -a file -F "' + filename + '" -g 1 -T wav SGM-V2.01.sf2 "' + tempMIDIFile.name + '"' )
      tempMIDIFile.close()
      return 1
    else:
      print "No events found on that track!"
      return 0
    
  
  # Write out the MIDI data as an audio file
  def writeWavFile( self, filename ):
    # Wish I could do this without subprocess, but the pyfluidsynth won't let me read in a MIDI file...
    os.system( 'fluidsynth -a file -F "' + filename + '" -g 1 -T wav SGM-V2.01.sf2 "' + self.MIDIFile + '"' )    

# Run function as script
if __name__ == "__main__":
  import sys
  if len(sys.argv) < 2:
    print "Usage: %s filename.mid" % sys.argv[0]
  converter = MIDIToTestFiles( sys.argv[1] )
  converter.createMIDITestFiles( '.', 10, 20, [0] )