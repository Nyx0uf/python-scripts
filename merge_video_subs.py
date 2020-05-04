#!/usr/bin/env python3
# coding: utf-8

"""
Merge separate videos and subtitles files into a single .mkv file
[!] mkvtoolnix must be installed and in your $PATH
[!] videos and subtitles must have the same name, ex : ep1.avi,ep1.srt | ep2.avi,ep2.srt
ex: merge_video_subs.py --src /path/to/movies/
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from typing import List
from utils import common, av

def merge_subs(subs: List[Path], vids: List[Path], lang: str, name: str):
    """Merge `subs` into `vids` and output a .mkv file, assuming `subs` and `vids` are the exact same length"""
    for idx, _ in enumerate(subs):
        sub = subs[idx]
        vid = vids[idx]
        str_vid = str(vid)
        mkvmerge = f'mkvmerge -o {quote(str_vid + ".mkv")} {quote(str_vid)} --language 0:{lang} --track-name 0:{name} {quote(str(sub))}'
        os.system(mkvmerge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory")
    parser.add_argument("-sl", action="store", dest="sub_lang", type=str, default="fre", help="Subtitles lang (eng, fre, ...)")
    parser.add_argument("-sn", action="store", dest="sub_name", type=str, default="SRT", help="Subtitles track name")
    args = parser.parse_args()

    # Sanity checks
    if common.which("mkvmerge") is None:
        common.abort("[!] mkvtoolnix not found in $PATH")

    if args.src.exists() is False or args.src.is_dir() is False:
        common.abort(parser.format_help())

    if len(args.sub_lang) != 3:
        common.abort(parser.format_help())

    # list subs
    subs_files = common.list_directory(args.src, lambda x: x.suffix in av.SUBTITLE_EXTENSIONS, True)
    # list vids
    video_files = common.list_directory(args.src, lambda x: x.suffix in av.VIDEO_EXTENSIONS, True)

    if len(subs_files) != len(video_files):
        common.abort(f"[!] Error: {len(subs_files)} sub files and {len(video_files)} video files")

    # Merge
    merge_subs(subs_files, video_files, args.sub_lang, args.sub_name)
