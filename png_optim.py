#!/usr/bin/env python3
# coding: utf-8

"""
Optimize png files
"""

from __future__ import division
import os
import argparse
import multiprocessing
import time
import imghdr
from pathlib import Path
from threading import Thread, Lock
from queue import Queue
from shlex import quote
from utils import common

total_original_bytes = 0
total_opt_bytes = 0
LOCK = Lock()

def optipng(path: Path) -> Path:
    """optipng"""
    outfile = path.with_name(str(path.name) + "-opt")
    cmd = f'optipng -quiet -o7 -preserve -out {quote(str(outfile))} {quote(str(path))}'
    print(f"{common.COLOR_PURPLE}{cmd}{common.COLOR_WHITE}")
    os.system(cmd)
    return outfile

def handle_png_files(p_queue: Queue):
    """Thread"""
    while p_queue.empty() is False:
        original_png_file: Path = p_queue.get()

        # Optimize
        print(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{original_png_file}")
        optimized = optipng(original_png_file)
        if optimized.exists() is True and optimized.is_file() is True:
            global total_original_bytes
            global total_opt_bytes
            LOCK.acquire()
            total_original_bytes += original_png_file.stat().st_size
            total_opt_bytes += optimized.stat().st_size
            LOCK.release()
            original_png_file.unlink() # Remove original
            # Rename optimized version to original
            optimized.rename(original_png_file)

        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or png file")
    args = parser.parse_args()

    if common.which("optipng") is None:
        common.abort("[!] optipng not found in $PATH")

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    path: Path = args.src.resolve()
    files = common.walk_directory(path, lambda x: imghdr.what(x) == "png")
    queue = common.as_queue(files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to consider")

    # Optimize
    t = common.parallel(handle_png_files, (queue,))
    bytes_saved = total_original_bytes - total_opt_bytes
    print("{}[+] {} bytes saved ({:.2f}Mb) in {:.2f}s".format(common.COLOR_WHITE, bytes_saved, (bytes_saved / 1048576), t))
