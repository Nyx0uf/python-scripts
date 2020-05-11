#!/usr/bin/env python3
# coding: utf-8

"""
Extract tracks in a given .mkv file
[!] mkvtoolnix must be installed and in your $PATH
ex: mkv_explode.py /path/to/file.mkv
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from typing import List
from utils import mkvfile
from utils import common, logger

LOGGER: logger.Logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to MKV file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    parser.add_argument("-x", "--videos", dest="videos", type=common.str2bool, default="True", help="flag: extract video tracks?")
    parser.add_argument("-y", "--audios", dest="audios", type=common.str2bool, default="True", help="flag: extract audio tracks?")
    parser.add_argument("-z", "--subtitles", dest="subtitles", type=common.str2bool, default="True", help="flag: extract subtitles tracks?")
    parser.add_argument("-c", "--chapters", dest="chapters", type=common.str2bool, default="True", help="flag: extract chapters?")
    parser.add_argument("-l", "--audio-langs", dest="audio_langs", type=str, default="all", help="Audio langs to extract [3 chars code, comma separated]")
    parser.add_argument("-m", "--subtitles-langs", dest="subtitles_langs", type=str, default="eng,fre,jpn", help="Subtitles langs to extract [3 chars code, comma separated]")
    parser.add_argument("-t", "--subtitles-types", dest="subtitles_types", type=str, default="ass,srt", help="Subtitles types to extract [all,ass,pgs,srt, comma separated]")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["mkvmerge", "mkvextract"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    mkv = mkvfile.MkvFile(args.input)
    if mkv.is_valid is False:
        common.abort(f"{common.COLOR_RED}[!] ERROR: Invalid mkv file {common.COLOR_WHITE}{args.input}")

    # Only tracks type we want
    allowed_track_types = list()
    if args.videos is True:
        allowed_track_types.append("video")
    if args.audios is True:
        allowed_track_types.append("audio")
    if args.subtitles is True:
        allowed_track_types.append("subtitles")

    # Only langs we want
    audio_langs = ["eng", "fre", "jpn"] if args.audio_langs == "all" else args.audio_langs.split(',')
    subtitles_langs = ["eng", "fre"] if args.subtitles_langs == "all" else args.subtitles_langs.split(',')
    subtitles_types = [mkvfile.CODEC_SUBTITLE_ASS, mkvfile.CODEC_SUBTITLE_PGS, mkvfile.CODEC_SUBTITLE_SRT, mkvfile.CODEC_SUBTITLE_VOBSUB] if args.subtitles_types == "all" else list(map(lambda x: mkvfile.CODEC_SUBTITLE_TYPE_MAP[x], args.subtitles_types.split(',')))

    commands = {}
    for track in mkv.tracks:
        # Check if we want this track
        if track.type not in allowed_track_types:
            LOGGER.log(f"{common.COLOR_WHITE}[+] Track {track.id}: {track.type}, skipping…")
            continue

        if track.file_extension is None:
            LOGGER.log(f"{common.COLOR_WHITE}[+] Track {track.id}: Unknown codec {common.COLOR_YELLOW}{track.codec}{common.COLOR_WHITE}, skipping…")
            continue

        if track.type == "video":
            commands[track] = f"{track.id}:{quote(str(mkv.path))}.{track.id}.vid{track.file_extension}"
        else:
            if track.is_commentary():
                LOGGER.log(f"{common.COLOR_WHITE}[+] Track {track.id}: Commentary, skipping…")
                continue
            if track.lang is None:
                LOGGER.log(f"{common.COLOR_WHITE}[+] Track {track.id}: Unknown lang, skipping…")
                continue

            if track.type == "audio":
                if track.lang in audio_langs:
                    commands[track] = f"{track.id}:{quote(str(mkv.path))}.{track.id}.{track.lang}{track.file_extension}"
            elif track.type == "subtitles":
                if track.lang in subtitles_langs and track.codec in subtitles_types:
                    force = ""
                    if track.forced is True:
                        force = "-forced"
                    commands[track] = f"{track.id}:{quote(str(mkv.path))}.{track.id}.{track.lang}{force}{track.file_extension}"

    # Find best quality audio track
    for lang in audio_langs:
        tracks_per_lang: List[mkvfile.MkvTrack] = list(filter(lambda x: x.lang == lang and x.type == "audio", commands.keys()))
        #print("{} --> {}".format(lang, tracks_per_lang))
        if len(tracks_per_lang) > 1:
            bestTrack: mkvfile.MkvTrack = None
            for track in tracks_per_lang:
                if bestTrack is None:
                    bestTrack = track
                elif bestTrack.audio_score() < track.audio_score():
                    del commands[bestTrack]
                    bestTrack = track
                else:
                    del commands[track]
            #print("[+] Best track is {}".format(bestTrack))

    mkvextract = f"mkvextract tracks {quote(str(mkv.path))} "
    for track, arg in commands.items():
        mkvextract += f"{arg} "
    LOGGER.log(f"{common.COLOR_PURPLE}{mkvextract}{common.COLOR_WITE}")
    os.system(mkvextract)

    if mkv.chaptered and args.chapters is True:
        os.system(f"mkvextract chapters {quote(str(mkv.path))} > {quote(str(args.input))}.chap.xml")
