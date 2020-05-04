#!/usr/bin/env python3
# coding: utf-8

"""
Strip useless metadata in flac files
[!] flac must be installed and in your $PATH
ex: flac_cleaner.py -src /path/to/files
"""

import os
import argparse
from pathlib import Path
from queue import Queue
from shlex import quote
from utils import common

TAGS_TO_REMOVE = ['45B1D925-1448-5784-B4DA-B89901050A13', '8E90F26B-372A-5C8B-BB05-1EC0F36EE60C', '93A74BEA-CE97-5571-A56A-C5084DBA9873', 'ACCURATERIPDISCID', 'ACCURATERIPRESULT', 'ACOUSTID ID', 'ALBUMARTISTSORT', 'ALBUMARTIST_CREDIT', 'ALBUMSORT', 'ALLDISCCOUNT', 'ALLTRACKCOUNT', 'ARRANGED', 'ARTISTSORT', 'ARTIST_CREDIT', 'AccurateRipDiscID', 'AccurateRipResult', 'Acoustid Id', 'BAND', 'BE242671-3D48-5AC8-B762-7D2DB4F584B8', 'BPM', 'CATALOG', 'CATALOG NUMBER', 'CATALOGID', 'COMMENT', 'COMPILATION', 'COMPOSER', 'COMPOSERSORT', 'CONTENTGROUP', 'COPYRIGHT', 'Catalog', 'Comment', 'DESCRIPTION', 'DJMIXER', 'ENCODEDBY', 'ENCODER', 'GROUPING', 'INITIALKEY', 'ITUNES_CDDB_1', 'ITUNNORM', 'LYRICS', 'MCN', 'MUSICBRAINZ ALBUM ARTIST ID', 'MUSICBRAINZ ALBUM ID', 'MUSICBRAINZ ALBUM RELEASE COUNTRY', 'MUSICBRAINZ ALBUM STATUS', 'MUSICBRAINZ ALBUM TYPE', 'MUSICBRAINZ ARTIST ID', 'MUSICBRAINZ RELEASE GROUP ID', 'MUSICBRAINZ RELEASE TRACK ID', 'MUSICBRAINZ TRACK ID', 'MusicBrainz Album Artist Id', 'MusicBrainz Album Id', 'MusicBrainz Album Release Country', 'MusicBrainz Album Status', 'MusicBrainz Album Type', 'MusicBrainz Artist Id', 'MusicBrainz Release Group Id', 'MusicBrainz Release Track Id', 'MusicBrainz Track Id', 'NOTES', 'ORGANIZATION', 'ORIGARTIST', 'ORIGINAL RELEASE DATE', 'ORIGINAL YEAR', 'ORIGINTYPE', 'OST', 'Organization', 'R128_ALBUM_GAIN', 'R128_TRACK_GAIN', 'RATING', 'RCALBUMID', 'RCARTISTID', 'RCMUSICID', 'REMIXEDBY', 'REMIXER', 'RIPPER', 'Release Type', 'Retail Date', 'Rip Date', 'Ripping Tool', 'STYLE', 'SUPPLIER', 'Source', 'TBPM', 'TDOR', 'TIPL', 'TITLESORT', 'TITLESORTEN', 'TMED', 'TORY', 'TSO2', 'TSRC', 'UPC', 'URL', 'account_id', 'artist-sort', 'be242671-3d48-5ac8-b762-7d2db4f584b8', 'compilation', 'composer', 'copyright', 'encoder', 'iTunNORM', 'iTunes_CDDB_1', 'iTunes_CDDB_TrackNumber', 'id3v2_priv.AverageLevel', 'id3v2_priv.PeakValue', 'id3v2_priv.ZuneCollectionID', 'lyrics-', 'lyrics-XXX', 'major_brand', 'media_type', 'minor_version', 'publisher', 'purchase_date', 'rating', 'sort_album', 'sort_album_artist', 'sort_artist', "musicbrainz_albumstatus", "musicbrainz_albumcomment", "musicbrainz_albumtype", 'DISC', 'DISCC', 'track', 'trackc', 'ALBUM ARTIST', 'year']

def remove_tags_cmd() -> str:
    """generate metaflac command"""
    metaflac = "metaflac --dont-use-padding"
    for tag in TAGS_TO_REMOVE:
        metaflac += f" --remove-tag='{tag}'"
    return metaflac

def clean_flac(p_queue: Queue, metaflac: str, blocks_only: bool):
    """Thread"""
    while p_queue.empty() is False:
        flac_file: Path = p_queue.get()
        sflac = str(flac_file)
        print(f"Cleaning <{sflac}>")
        if blocks_only is False:
            os.system(f'{metaflac} {quote(sflac)}')
        # Remove picture if any, padding, seektable
        os.system(f"metaflac --dont-use-padding --remove --block-type=PADDING,PICTURE,SEEKTABLE {quote(sflac)}")
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    parser.add_argument("-b", action="store", dest="blocks", type=common.str2bool, default=False, help="only remove PADDING, PICTURE and SEEKTABLE blocks")
    args = parser.parse_args()

    if common.which("metaflac") is None:
        common.abort("[!] flac not found in $PATH")

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: x.suffix == ".flac")
    queue = common.as_queue(files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to consider")

    # Clean
    metaflac = remove_tags_cmd()
    common.parallel(clean_flac, (queue, metaflac, args.blocks))