#!/usr/bin/python3

import os
import re
import sys
import subprocess

import mutagen
from mutagen.easyid3 import EasyID3

def get_duration(filename):
    base_command = "ffprobe -i %s -show_entries format=duration -v quiet -of csv='p=0'"
    chunked_command = base_command.split()
    chunked_command[2] = in_filename
    try:
        return float(subprocess.check_output(chunked_command))
    except:
        return -1

def file_is_converted(in_filename, out_filename):
    duration_in = get_duration(in_filename)
    duration_out = get_duration(out_filename)
    print("Durations: %f, %f" % (duration_id, duration_out))
    return duration_in == duration_out

def convert_to_mp3(in_filename):
    if in_filename.endswith("mp3"):
        return in_filename
    if in_filename.endswith("bak"):
        return ""
    if in_filename.endswith("jpg"):
        return ""
    if in_filename.endswith("jpeg"):
        return ""
    if in_filename.endswith("png"):
        return ""
    out_filename = os.path.splitext(in_filename)[0]
    out_filename = out_filename + ".mp3"
    if file_is_converted(in_filename, out_filename):
        return out_filename
    command = "ffmpeg -y -i %s -vn -ar 44100 -ac 2 -b:a 192k -f mp3 %s"
    chunked_command = command.split()
    chunked_command[3] = in_filename
    chunked_command[-1] = out_filename
    print("Converting\n", in_filename, "\nto\n", out_filename, "\nwith\n", ' '.join(chunked_command))
    if subprocess.call(chunked_command) != 0:
        return ""
    if subprocess.call(['mv', in_filename, in_filename+'.bak']) != 0:
        return ""
    return out_filename

def convert_files(path):
    files = list(os.scandir(path))
    for filename in files:
        convert_to_mp3(filename.path)

def get_next_tracknumber(prev_data, new_year, new_month):
    #print(prev_data, " ", new_year, " ", new_month)
    if prev_data[0] == new_year and prev_data[1] == new_month:
        return str(int(prev_data[2]) + 1)
    return '1'

def extract_data(filename):
    match = re.search('(\d{4})-(\d{2})-(\d{2}) - .* - (.*)[.]mp3', filename)
    if not match:
        match = re.search('(\d{4})-(\d{2})-(\d{2}) - .*', filename)
    if not match:
        return filename.replace(".mp3", ""), "1900", "01", "01"
    year = '%04d' % int(match.group(1))
    month = '%02d' % int(match.group(2))
    day = '%02d' % int(match.group(3))
    try:
        title = match.group(4)
        title = title.replace('_', ':')
    except:
        title = None
    return title, year, month, day

"""
['albumartistsort', 'musicbrainz_albumstatus', 'lyricist', 'musicbrainz_workid', 'releasecountry', 'date', 'performer', 'musicbrainz_albumartistid', 'composer', 'catalognumber', 'encodedby', 'tracknumber', 'musicbrainz_albumid', 'album', 'asin', 'musicbrainz_artistid', 'mood', 'copyright', 'author', 'media', 'length', 'acoustid_fingerprint', 'version', 'artistsort', 'titlesort', 'discsubtitle', 'website', 'musicip_fingerprint', 'conductor', 'musicbrainz_releasegroupid', 'compilation', 'barcode', 'performer:*', 'composersort', 'musicbrainz_discid', 'musicbrainz_albumtype', 'genre', 'isrc', 'discnumber', 'musicbrainz_trmid', 'acoustid_id', 'replaygain_*_gain', 'musicip_puid', 'originaldate', 'language', 'artist', 'title', 'bpm', 'musicbrainz_trackid', 'arranger', 'albumsort', 'replaygain_*_peak', 'organization', 'musicbrainz_releasetrackid']
"""

def update_metadata(podcast, name, id3, latest_data):
    print ("Updating metadata for:", name)

    print('Before:')
    print(id3.pprint())
    
    podcast = podcast.replace("_", ":")
    id3['albumartist'] = podcast
    id3['albumartistsort'] = podcast
    id3['lyricist'] = podcast
    id3['performer'] = podcast
    id3['composer'] = podcast
    id3['author'] = podcast
    id3['artistsort'] = podcast
    id3['composersort'] = podcast
    id3['artist'] = podcast
    
    title, year, month, day = extract_data(name)
    date_str = '(%s-%s-%s)' % (year, month, day)
    if 'title' in id3 and len(id3['title']) > 0:
        title = id3['title'][0]
    if not title.endswith(date_str):
        title = '%s (%s-%s-%s)' % (title, year, month, day)
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
    #print("\nis_processed")
    try:
        #print("trying...")
        #print(id3['encodedby'][0], " ", id3['encodedby'][0] == 'doubletissue')
        return id3['encodedby'][0] == 'doubletissue'
    except:
        #print("returning false")
        return False

    
def find_num_new(files):
    for i in range(len(files)):
        try:
            id3 = EasyID3(files[len(files) - i - 1].path)
        except:
            continue
        if is_processed(id3):
            return i
    return len(files)

    
def process_podcast(dir_entry):
    podcast = dir_entry.name
    print ("Processing Podcast:", podcast)
    convert_files(dir_entry.path)
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
        if processed:
            year, month, track = get_id3_data(id3)
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
