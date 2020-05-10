#!/usr/bin/env python3
# coding: utf-8

"""
Extract all audio streams of a given movie or directory of movies
[!] ffmpeg must be installed and in your $PATH
ex: extract_audio.py -src /path/to/movies/
"""

import os
import subprocess
import re
import argparse
from pathlib import Path
from queue import Queue
from collections import namedtuple
from shlex import quote
from utils import common, logger

LOGGER: logger.Logger

AudioStreamInfo = namedtuple('AudioStreamInfo', ['id', 'infos', 'title'])

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
        'alac': '.m4a'
    }

    def sanitize_type(x: str) -> str:
        """Clean extension"""
        return maps[x] if x in maps else x
    extension = sanitize_type(audio_type[:4].strip())
    return extension

def extract_audio(p_queue: Queue, fmt: str):
    """Extract thread"""
    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        infos = get_file_infos(infile)
        streams = get_audio_streams(infos)
        for audio_stream in streams:
            outfile = f"{quote(str(infile))}.{audio_stream.id}"
            cmd = f"ffmpeg -i {quote(str(infile))} -v quiet -map 0:{audio_stream.id}"
            if fmt == "wav":
                cmd += f" -c pcm_s16le {outfile}.wav"
            else:
                cmd += f" -c copy {outfile}{extension_for_audio_info(audio_stream.infos)}"
            LOGGER.log(f"{common.COLOR_WHITE}[+] Extracting track {audio_stream.id} from {common.COLOR_YELLOW}{infile} with {common.COLOR_PURPLE}{cmd}")
            os.system(cmd)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single JPEG file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="verbode mode")
    parser.add_argument("-f", "--format", dest="format", type=str, help="Which format to export the audio to, between: copy, wav")
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
    common.parallel(extract_audio, (queue, args.format,))
