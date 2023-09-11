#!/usr/bin/env python3
# coding: utf-8

"""
Extract all subtitles streams of a given movie or directory of movies
[!] ffmpeg must be installed and in your $PATH
ex: extract_subs.py /path/to/movies/
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

SubtitlesStreamInfo = namedtuple('SubtitlesStreamInfo', ['id', 'infos', 'extension', 'title'])


def get_subs_streams(infos: str) -> str:
    """Parse `ffmpeg -i` output to grab only subtitles streams"""
    maps = {
        'ssa': '.ass',
        'ass': '.ass',
        'subrip': '.srt',
        'pgs': '.pgs'
    }

    def sanitize_type(x: str) -> str:
        """clean extension"""
        return maps[x] if x in maps else x

    streams = re.findall(r'Stream #0:(\d+).*?Subtitle:\s*((\w*)\s*?.*?)\r?\n(?:\s*Metadata:\s*\r?\n\s*title\s*:\s*(.*?)\r?\n)?', infos)
    return [SubtitlesStreamInfo(int(x[0]), x[1].strip(), sanitize_type(x[2].replace(",", "").strip()), x[3].strip()) for x in streams]


def extract_subtitles(p_queue: Queue):
    """Extract thread"""
    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        infos = av.get_file_infos(infile)
        streams = get_subs_streams(infos)
        for sub_stream in streams:
            outfile = f'{str(infile)}.{sub_stream.id}{sub_stream.extension}'
            cmd = f'ffmpeg -i {quote(str(infile))} -v quiet -map 0:{sub_stream.id} -c copy {quote(outfile)}'
            LOGGER.log(f"{common.COLOR_WHITE}[+] Extracting track {sub_stream.id} from {common.COLOR_YELLOW}{infile} with {common.COLOR_PURPLE}{cmd}{common.COLOR_WHITE}")
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
    if args.input.exists() is None:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve())
    queue = common.as_queue(files)

    # Extract
    common.parallel(extract_subtitles, (queue,))
