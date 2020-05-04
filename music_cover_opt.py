#!/usr/bin/env python3
# coding: utf-8

"""
Strip useless metadata in flac files
[!] flac must be installed and in your $PATH
ex: flac_cleaner.py -src /path/to/files
"""

import os
import argparse
from pathlib import Path
from queue import Queue
from shlex import quote
from PIL import Image
from utils import common

def scale_down(path: Path, max_size: int) -> Path:
    """scale image"""
    outfile = path.with_name(str(path.name) + "-scaled")
    convert = f"convert {quote(str(path))} -quality 75 -resize {max_size}x{max_size}\\> {quote(str(outfile))}"
    os.system(convert)
    return outfile

def opt(p_queue: Queue, max_size: int):
    """Thread"""
    while p_queue.empty() is False:
        orig_cover_file: Path = p_queue.get()

        im = Image.open(orig_cover_file)
        if im.size[0] > max_size or im.size[1] > max_size:
            print(f"{str(orig_cover_file)} too big {im.size}")
            scaled_file = scale_down(orig_cover_file, max_size)
            orig_cover_file.unlink()
            scaled_file.rename(orig_cover_file)

        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    parser.add_argument("-ms", action="store", dest="ms", type=int, default=1512, help="Max size")
    args = parser.parse_args()

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: x.suffix == ".jpg" or x.suffix == ".jpeg")
    queue = common.as_queue(files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to consider")

    # Optimize
    common.parallel(opt, (queue, args.ms,))
