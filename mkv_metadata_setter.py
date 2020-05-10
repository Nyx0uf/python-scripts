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
from typing import List
from utils import common
from utils import mkvfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single MKV file")
    parser.add_argument("-v", "--video-name", dest="video_name", type=str, default=None, help="Name of the video track")
    parser.add_argument("-a", "--audio-name", dest="audio_name", type=str, default=None, help="Name of the audio tracks, comma separated")
    parser.add_argument("-s", "--sub-name", dest="sub_name", type=str, default=None, help="Name of the subtitles tracks, comma separated")
    parser.add_argument("-x", "--video-lang", dest="video_lang", type=str, default="und", help="Lang of the video track")
    parser.add_argument("-y", "--audio-lang", dest="audio_lang", type=str, default="jpn", help="Lang of the audio tracks, comma separated")
    parser.add_argument("-z", "--sub-lang", dest="sub_lang", type=str, default="eng", help="Lang of the subtitles tracks, comma separated")
    parser.add_argument("-r", "--repl", dest="repl", type=str, default="", help="Pattern to replace for the Title")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["mkvpropedit", "mediainfo"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve(), lambda x: x.suffix == ".mkv", True)

    for f in files:
        mkv = mkvfile.MkvFile(f)
        cmd = f'mkvpropedit {quote(str(f))}'
        # Handle video track
        vtrack: mkvfile.MkvTrack = list(filter(lambda x: x.type == "video", mkv.tracks))[0]
        vn = f'{args.video_lang.upper()} — {mkv.video_codec_desc()}{" — " + args.video_name if args.video_name is not None else ""}'
        cmd += f' --edit track:v1 --set language={args.video_lang} --set name={quote(vn)}'
        # Handle audio tracks
        atracks: List[mkvfile.MkvTrack] = list(filter(lambda x: x.type == "audio", mkv.tracks))
        audio_langs = args.audio_lang.split(",")
        audio_names = args.audio_name.split(",") if args.audio_name else []
        tid = 1
        for track in atracks:
            if tid <= len(audio_langs):
                al = audio_langs[tid - 1]
            else:
                al = "und"
            if track.audio_channels in [1, 2]:
                channels = f'{track.audio_channels}.0'
            else:
                channels = f'{track.audio_channels - 1}.1'
            an = f'{al.upper()} — {track.codec.upper()} {channels}'
            if track.audio_bits is not None:
                an += f' / {track.audio_bits}bits'
            if tid <= len(audio_names):
                an += f' — {audio_names[tid - 1]}'
            cmd += f' --edit track:a{tid} --set language={al} --set name={quote(an)}'
            tid += 1
        # Handle subtitles tracks
        stracks = list(filter(lambda x: x.type == "subtitles", mkv.tracks))
        sub_langs = args.sub_lang.split(",")
        sub_names = args.sub_name.split(",") if args.sub_name else []
        tid = 1
        for track in stracks:
            if tid <= len(sub_langs):
                sl = sub_langs[tid - 1]
            else:
                sl = "und"
            sn = f'{sl.upper()}'
            forced = False
            if tid <= len(sub_names):
                s = sub_names[tid - 1]
                forced = "forced" in s.lower()
                sn += f' — {s}'
            cmd += f' --edit track:s{tid} --set language={sl} --set name={quote(sn)} --set flag-forced={1 if forced is True else 0}'
            tid += 1
        title = f.stem.replace(args.repl, "")
        cmd += f' --edit info --set title={quote(title)}'
        os.system(cmd)
