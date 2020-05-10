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
from utils import av, common

def merge_subs(subs: List[Path], vids: List[Path], lang: str, name: str):
    """Merge `subs` into `vids` and output a .mkv file, assuming `subs` and `vids` are the exact same length"""
    flag_forced = "forced" in name.lower()
    for idx, _ in enumerate(subs):
        sub = subs[idx]
        vid = vids[idx]
        str_vid = str(vid)
        mkvmerge = f'mkvmerge -o {quote(str_vid + ".mkv")} {quote(str_vid)} --language 0:{lang} --track-name 0:{quote(name)} --forced-track 0:{flag_forced} {quote(str(sub))}'
        os.system(mkvmerge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    parser.add_argument("-l", "--sub-lang", dest="sub_lang", type=str, default="fre", help="Subtitles lang (eng, fre, ...)")
    parser.add_argument("-n", "--sub-name", dest="sub_name", type=str, default="SRT", help="Subtitles track name")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvmerge"])

    if args.input.exists() is False or args.input.is_dir() is False:
        common.abort(parser.format_help())

    if len(args.sub_lang) != 3:
        common.abort(parser.format_help())

    # list subs
    subs_files = common.list_directory(args.input, lambda x: x.suffix in av.SUBTITLE_EXTENSIONS, True)
    # list vids
    video_files = common.list_directory(args.input, lambda x: x.suffix in av.VIDEO_EXTENSIONS, True)

    if len(subs_files) != len(video_files):
        common.abort(f"[!] Error: {len(subs_files)} sub files and {len(video_files)} video files")

    # Merge
    merge_subs(subs_files, video_files, args.sub_lang, args.sub_name)
