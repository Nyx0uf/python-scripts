#!/usr/bin/env python3
# coding: utf-8

"""
Adaptation of the Apple Digital Masters droplets
https://www.apple.com/apple-music/apple-digital-masters/
Only works on macOS because it uses afconvert.
"""

import os
import argparse
from pathlib import Path
from shlex import quote
from queue import Queue
from utils import av, common, logger

LOGGER: logger.Logger


def is_valid_audio_file(path: Path) -> bool:
    """Check if `path` is a supported audio file"""
    return path.suffix.lower() in [str('.flac'), str('.wav')]


def convert(p_queue: Queue, delete_orig: bool):
    """Convert thread"""

    while p_queue.empty() is False:
        infile: Path = p_queue.get()

        # Create wav file
        wavfile = infile.with_suffix(".wav")
        infos = av.get_file_infos(infile)
        sr = "44100" if "44100" in infos else "48000"
        cmd_wav = f"afconvert {quote(str(infile))} {quote(str(wavfile))} -d LEI24@{sr} --quality 127 -r 127 --src-complexity bats -f WAVE"
        LOGGER.log(f"{common.COLOR_WHITE}[$] {common.COLOR_PURPLE}{cmd_wav}")
        os.system(cmd_wav)
        if wavfile.exists() is True:
            # Create caf file
            caffile = infile.with_suffix(".caf")
            cmd_caf = f"afconvert {quote(str(wavfile))} {quote(str(caffile))} -d 0 -f caff --soundcheck-generate"
            LOGGER.log(
                f"{common.COLOR_WHITE}[$] {common.COLOR_PURPLE}{cmd_caf}")
            os.system(cmd_caf)
            if caffile.exists() is True:
                # Create aac file
                outfile = infile.with_suffix(".m4a")
                cmd_aac = f"afconvert {quote(str(caffile))} -d aac -f m4af -u pgcm 2 --soundcheck-read -b 256000 -q 127 -s 2 {quote(str(outfile))}"
                LOGGER.log(
                    f"{common.COLOR_WHITE}[$] {common.COLOR_PURPLE}{cmd_aac}")
                os.system(cmd_aac)
                caffile.unlink()
                if delete_orig is True:
                    infile.unlink()
            wavfile.unlink()
        p_queue.task_done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path,
                        help="Path to directory or single audio file")
    parser.add_argument("-v", "--verbose", dest="verbose",
                        action="store_true", help="Verbose mode")
    parser.add_argument("-d", "--delete", dest="delete",
                        action="store_true", help="Delete original file after conversion")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["afconvert"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get a list of files
    files = common.list_directory(args.input.resolve(), is_valid_audio_file)
    queue = common.as_queue(files)

    # Convert
    common.parallel(convert, (queue, args.delete,))
