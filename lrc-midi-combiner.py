import os
from mido import MidiFile, MidiTrack, MetaMessage, second2tick, tempo2bpm

def LRC(filename: str):
    lines = {}
    prefixes = {'ar': 'artist', 'al': 'album', 'ti': 'title', 'length': 'length'}
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    data = {
        'songData': {},
        'lyrics': []
    }

    for line in lines:
        split = line.split(':')
        prefix = split[0][1:]
        
        if prefix in prefixes:
            if prefix == 'length':
                lengthString = ':'.join(split[1:]).removesuffix(']\n')
                timeSplit = lengthString.split(':')
                time = float(timeSplit[0]) * 60 + float(timeSplit[1])

                data['songData'][prefixes[prefix]] = time
            else:
                data['songData'][prefixes[prefix]] = split[1].removesuffix(']\n')
        elif prefix != '':
            split = line.split('] ')

            timeSplit = (split[0][1:]).split(':')
            time = float(timeSplit[0]) * 60 + float(timeSplit[1])

            data['lyrics'].append({'time': time, 'lyric': split[1].removesuffix('\n')})
    
    return data

def getBPM(mid):
    for msg in mid:     # Search for tempo
        if msg.type == 'set_tempo':
            return tempo2bpm(msg.tempo)
    return tempo2bpm(500000)       # If not found return default tempo

def mergeMidiAndLRC(midifilename: str, lrcfilename: str):
    lrcData = LRC(lrcfilename)
    mid = MidiFile(midifilename)

    print('Cloning MIDI...')
    new_mid = MidiFile(ticks_per_beat=mid.ticks_per_beat)  #initialize with the right tempo
    new_track = MidiTrack()

    for i, track in enumerate(mid.tracks):
        for msg in track:
            if (msg.is_meta and msg.time == 0) or not msg.is_meta:
                new_track.append(msg)
    
    for key in lrcData['songData'].keys():
        val = lrcData['songData'][key]
        info = key + ' = ' + str(val)
        new_track.append(MetaMessage('text', text=info, time=0))

        print(f'Injected song information: "{info}" @ time (ticks) = 0')
    
    ticksIn = 0
    for lyric in lrcData['lyrics']:
        time = int(second2tick(lyric['time'], mid.ticks_per_beat, getBPM(mid)))
        lyricText = lyric['lyric']
        ticksIn += time

        if lyricText == '♪':
            lyricText = '[Music]'

        new_track.append(MetaMessage('lyrics', text=lyricText, time=time))

        print(f'Injected song lyrics: "{lyricText}" @ delta-time (ticks) = {str(time)}')

    filename = os.path.splitext(midifilename)[0]

    print('Finishing up...')
    new_mid.tracks.append(new_track)
    new_mid.save(f'{filename}-merge.mid')
    mid.save(midifilename)

    print(f'Saved as {filename}-merge.mid')

mergeMidiAndLRC('like-him.mid', 'like-him.lrc')