#!/usr/bin/env python3
# coding: utf-8

"""
Tag a .mkv file or directory of .mkv files
[!] mkvtoolnix must be installed and in your $PATH
ex: mkv_metadata_setter.py -src /path/to/file.mkv -vn "Video track" -an "Audio track" -sn "Sub track"
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from utils import common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or video file")
    parser.add_argument("-vn", action="store", dest="video_name", type=str, default=None, help="Name of the video track")
    parser.add_argument("-an", action="store", dest="audio_name", type=str, default=None, help="Name of the audio track")
    parser.add_argument("-sn", action="store", dest="sub_name", type=str, default=None, help="Name of the subtitle track")
    parser.add_argument("-vl", action="store", dest="video_lang", type=str, default="und", help="Lang of the video track")
    parser.add_argument("-al", action="store", dest="audio_lang", type=str, default="jpn", help="Lang of the audio track")
    parser.add_argument("-sl", action="store", dest="sub_lang", type=str, default="eng", help="Lang of the subtitle track")
    parser.add_argument("-repl", action="store", dest="repl", type=str, default="", help="Pattern to replace for the Title")
    args = parser.parse_args()

    # Sanity checks
    if common.which("mkvpropedit") is None:
        common.abort("[!] mkvtoolnix not found in $PATH")

    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.src.resolve(), lambda x: x.suffix == ".mkv", True)

    for f in files:
        name = f.stem.replace(args.repl, "")
        cmd = f'mkvpropedit {quote(str(f))}'
        if args.video_name is not None:
            cmd += f' --edit track:v1 --set language={args.video_lang} --set flag-default=1 --set name={quote(args.video_name)}'
        if args.audio_name is not None:
            audio_names = args.audio_name.split(",")
            audio_langs = args.audio_lang.split(",")
            tid = 1
            for an in audio_names:
                cmd += f' --edit track:a{tid} --set language={audio_langs[tid - 1]} --set flag-default=0 --set name={quote(an)}'
                tid += 1
        if args.sub_name is not None:
            sub_names = args.sub_name.split(",")
            sub_langs = args.sub_lang.split(",")
            tid = 1
            for sn in sub_names:
                forced = "forced" in sn.lower()
                cmd += f' --edit track:s{tid} --set language={sub_langs[tid - 1]} --set flag-default=0 --set name={quote(sn)}'
                cmd += f' --set flag-forced=1' if forced is True else f' --set flag-forced=0'
                tid += 1
        cmd += f' --edit info --set title={quote(name)}'
        os.system(cmd)
