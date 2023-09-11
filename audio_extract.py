#!/usr/bin/env python3
# coding: utf-8

"""
Extract all audio streams of a given movie or directory of movies
[!] ffmpeg must be installed and in your $PATH
ex: extract_audio.py /path/to/movies/
"""

import os
import re
import argparse
from pathlib import Path
from queue import Queue
from collections import namedtuple
from shlex import quote
from utils import av, common, logger

LOGGER: logger.Logger

AudioStreamInfo = namedtuple('AudioStreamInfo', ['id', 'infos', 'title'])


def get_audio_streams(infos: str):
    """Parse `ffmpeg -i` output to grab only audio streams"""
    z = re.findall(r'Stream\s\#0:(\d+).*?Audio:\s*(.*?(?:\((default)\))?)\s*?(?:\(forced\))?\r?\n(?:\s*Metadata:\s*\r?\n\s*title\s*:\s*(.*?)\r?\n)?', infos)
    return [AudioStreamInfo(int(x[0]), x[1].strip(), x[2]) for x in z]


def extension_for_audio_info(audio_type: str) -> str:
    """Returns the extension for a given audio info from `ffmpeg -i`"""
    maps = {
        'aac': '.m4a',
        'ac3': '.ac3',
        'dts': '.dts',
        'flac': '.flac',
        'pcm_': '.wav',
        'true': '.thd',
        'alac': '.m4a',
        'opus': '.opus',
    }

    def sanitize_type(x: str) -> str:
        """Clean extension"""
        return maps[x] if x in maps else x
    return sanitize_type(audio_type[:4].strip().replace(",", "").lower())


def extract_audio(p_queue: Queue):
    """Extract thread"""
    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        infos = av.get_file_infos(infile)
        streams = get_audio_streams(infos)
        for audio_stream in streams:
            outfile = f"{str(infile)}.{audio_stream.id}{extension_for_audio_info(audio_stream.infos)}"
            cmd = f"ffmpeg -i {quote(str(infile))} -v quiet -map 0:{audio_stream.id} -c copy {quote(outfile)}"
            LOGGER.log(f"{common.COLOR_WHITE}[+] Extracting track {audio_stream.id} from {common.COLOR_YELLOW}{infile} with {common.COLOR_PURPLE}{cmd}{common.COLOR_WHITE}")
            os.system(cmd)
        p_queue.task_done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single video file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["ffmpeg"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve())
    queue = common.as_queue(files)

    # Extract
    common.parallel(extract_audio, (queue,))
