#!/usr/bin/env python3
# coding: utf-8

"""
Merge separate video and audio files into a single .mkv file
[!] mkvtoolnix must be installed and in your $PATH
[!] videos and audio must have the same name, ex : ep1.avi,ep1.mp3 | ep2.avi,ep2.mp3
ex: merge_video_subs.py -src /path/to/movies/
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from typing import List
from utils import av, common

def merge_subs(audios: List[Path], vids: List[Path], lang: str, name: str):
    """Merge `audios` into `vids` as a .mkv file, assuming `audios` and `vids` are the exact same length"""
    for idx, _ in enumerate(audios):
        audio = audios[idx]
        vid = vids[idx]
        str_vid = str(vid)
        mkvmerge = f'mkvmerge -o {quote(str_vid + ".mkv")} {quote(str_vid)} --language 0:{lang} --track-name 0:{quote(name)} {quote(str(audio))}'
        os.system(mkvmerge)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory")
    parser.add_argument("-al", action="store", dest="audio_lang", type=str, default="eng", help="Audio lang (eng, fre, ...)")
    parser.add_argument("-an", action="store", dest="audio_name", type=str, default="", help="Audio track name")
    args = parser.parse_args()

    # Sanity checks
    if common.which("mkvmerge") is None:
        common.abort("[!] mkvtoolnix not found in $PATH")

    if args.src.exists() is False or args.src.is_dir() is False:
        common.abort(parser.format_help())

    if len(args.audio_lang) != 3:
        common.abort(parser.format_help())

    # list audios
    audio_files = common.list_directory(args.src, lambda x: x.suffix in av.AUDIO_EXTENSIONS, True)
    # list vids
    video_files = common.list_directory(args.src, lambda x: x.suffix in av.VIDEO_EXTENSIONS, True)

    if len(audio_files) != len(video_files):
        common.abort(f"[!] Error: {len(audio_files)} audio files and {len(video_files)} video files")

    # Merge
    merge_subs(audio_files, video_files, args.audio_lang, args.audio_name)
