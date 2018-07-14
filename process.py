import os
import re
import sys

import mutagen
from mutagen.easyid3 import EasyID3

def get_next_tracknumber(prev_data, new_year, new_month):
    if prev_data[0] == new_year and prev_data[1] == new_month:
        return str(int(prev_data[2]) + 1)
    return '1'

def extract_data(filename):
    match = re.search('(\d{4})-(\d{2})-(\d{2}) - .* - (.*)[.]mp3', filename)
    if not match:
        return None, None, None
    year = '%04d' % int(match.group(1))
    month = '%02d' % int(match.group(2))
    day = '%02d' % int(match.group(3))
    title = match.group(4)
    full_title = '%s (%s-%s-%s)' % (title, year, month, day) 
    return full_title, year, month

"""
['albumartistsort', 'musicbrainz_albumstatus', 'lyricist', 'musicbrainz_workid', 'releasecountry', 'date', 'performer', 'musicbrainz_albumartistid', 'composer', 'catalognumber', 'encodedby', 'tracknumber', 'musicbrainz_albumid', 'album', 'asin', 'musicbrainz_artistid', 'mood', 'copyright', 'author', 'media', 'length', 'acoustid_fingerprint', 'version', 'artistsort', 'titlesort', 'discsubtitle', 'website', 'musicip_fingerprint', 'conductor', 'musicbrainz_releasegroupid', 'compilation', 'barcode', 'performer:*', 'composersort', 'musicbrainz_discid', 'musicbrainz_albumtype', 'genre', 'isrc', 'discnumber', 'musicbrainz_trmid', 'acoustid_id', 'replaygain_*_gain', 'musicip_puid', 'originaldate', 'language', 'artist', 'title', 'bpm', 'musicbrainz_trackid', 'arranger', 'albumsort', 'replaygain_*_peak', 'organization', 'musicbrainz_releasetrackid']
"""

def update_metadata(podcast, name, id3, latest_data):
    print ("Updating metadata for:", name)

    print('Before:')
    print(id3.pprint())
    
    id3['albumartistsort'] = podcast
    id3['albumartistsort'] = podcast
    id3['lyricist'] = podcast
    id3['performer'] = podcast
    id3['composer'] = podcast
    id3['author'] = podcast
    id3['artistsort'] = podcast
    id3['composersort'] = podcast
    id3['artist'] = podcast
    
    title, year, month = extract_data(name)
    
    id3['title'] = title
    id3['titlesort'] = title
    
    id3['album'] = year
    id3['albumsort'] = year
    id3['date'] = year
    
    id3['discnumber'] = month

    track = get_next_tracknumber(latest_data, year, month)
    
    id3['tracknumber'] = track

    id3['encodedby'] = 'doubletissue'

    print('\nAfter:')
    print(id3.pprint())
    print("\n")
    id3.save()

    return year, month, track

def get_id3_data(id3):
    try:
        return id3['album'], id3['discnumber'], id3['tracknumber']
    except:
        return 0,0,0

def is_processed(id3):
    try:
        return id3['encodedby'][0] == 'doubletissue'
    except:
        return False

    
def find_num_new(files):
    for i in range(len(files)):
        try:
            id3 = EasyID3(files[len(files) - i - 1].path)
        except mutagen.id3.ID3NoHeaderError:
            continue
        if is_processed(id3):
            return i
    return len(files)

    
def process_podcast(dir_entry):
    podcast = dir_entry.name
    print ("Processing Podcast:", podcast)
    files = list(os.scandir(dir_entry.path))
    files = list(filter(lambda x: x.name[-3:] == 'mp3', files))
    files.sort(key=lambda x: x.name)
    num_new = find_num_new(files)
    print ("Updating",num_new,"of",len(files))
    latest_year, latest_month, latest_track = 0,0,0
    for file_entry in files[-(num_new+1):]:
        try:
            id3 = EasyID3(file_entry.path)
        except mutagen.id3.ID3NoHeaderError:
            id3 = mutagen.File(file_entry.path, easy=True)
            id3.add_tags()
        processed = is_processed(id3)
        year, month, track = get_id3_data(id3)
        if processed:
            latest_year, latest_month, latest_track = year, month, track
            continue
        latest_year, latest_month, latest_track = update_metadata(podcast, file_entry.name, id3, (latest_year, latest_month, latest_track))

def process_podcasts(directory):
    for dir_entry in os.scandir(directory):
        if dir_entry.is_file():
            continue
        process_podcast(dir_entry)

def main():
    process_podcasts(sys.argv[1])

main()
