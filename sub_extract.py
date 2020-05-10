#!/usr/bin/env python3
# coding: utf-8

"""
Extract all subtitles streams of a given movie or directory of movies
[!] ffmpeg must be installed and in your $PATH
ex: extract_subs.py -src /path/to/movies/
"""

import os
import subprocess
import re
import argparse
from pathlib import Path
from queue import Queue
from collections import namedtuple
from shlex import quote
from utils import common

SubtitlesStreamInfo = namedtuple('SubtitlesStreamInfo', ['id', 'infos', 'extension', 'title'])

def get_file_infos(path: Path) -> str:
    """ffmpeg -i `path`"""
    try:
        process = subprocess.Popen(['ffmpeg', '-hide_banner', '-i', str(path)], stderr=subprocess.PIPE)
        (_, err) = process.communicate()
        process.wait()
        return err.decode("utf8")
    except OSError as e:
        if e.errno == 2:
            raise NameError("ffmpeg not found.")
        raise

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
    return [SubtitlesStreamInfo(int(x[0]), x[1].strip(), sanitize_type(x[2]), x[3].strip()) for x in streams]

def extract_subtitles(p_queue: Queue):
    """Extract thread"""
    while p_queue.empty() is False:
        f: Path = p_queue.get()
        infos = get_file_infos(f)
        streams = get_subs_streams(infos)
        for sub_stream in streams:
            sub_file = f'{quote(str(f))}.{sub_stream.id}{sub_stream.extension}'
            ffmpeg = f'ffmpeg -i {quote(str(f))} -v quiet -map 0:{sub_stream.id} -c copy {sub_file}'
            print(ffmpeg)
            os.system(ffmpeg)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single video file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["ffmpeg"])
    if args.input.exists() is None:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve())
    queue = common.as_queue(files)

    # Extract
    common.parallel(extract_subtitles, (queue,))
