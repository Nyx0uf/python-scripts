#!/usr/bin/env python3
# coding: utf-8

"""
Optimize png files (pngquant + optipng)
"""

from __future__ import division
import os
import argparse
import imghdr
from pathlib import Path
from queue import Queue
from shlex import quote
from utils import common, logger

LOGGER: logger.Logger

def pngquant(path: Path) -> Path:
    """pngquant"""
    outfile = path.with_name(f"{path.stem}.pngquant.png")
    cmd = f"pngquant -f -o {quote(str(outfile))} --speed 1 --quality 75-100 --strip --skip-if-larger {quote(str(path))}"
    os.system(cmd)
    return outfile

def optipng(path: Path) -> Path:
    """optipng"""
    outfile = path.with_name(f"{path.stem}.optipng.png")
    cmd = f"optipng -quiet -o7 -preserve -out {quote(str(outfile))} {quote(str(path))}"
    os.system(cmd)
    return outfile

def zopflipng(path: Path) -> Path:
    """zopflipng"""
    outfile = path.with_name(f"{path.stem}.zopflipng.png")
    cmd = f"zopflipng --iterations=50 --filters=01234mepb --lossy_transparent {quote(str(path))} {quote(str(outfile))} > /dev/null"
    os.system(cmd)
    return outfile

def handle_png_files(p_queue: Queue):
    """pngquant + optipng"""
    while p_queue.empty() is False:
        original_png_file: Path = p_queue.get()
        LOGGER.log(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{original_png_file}")
        # pngquant
        pngquanted = pngquant(original_png_file)
        # zopflipng
        optimized = zopflipng(pngquanted if pngquanted.exists() else original_png_file)
        if pngquanted.exists():
            pngquanted.unlink()
        if optimized.exists():
            original_png_file.unlink()
            optimized.rename(original_png_file)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single PNG file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["pngquant", "zopflipng"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.input.resolve(), lambda x: imghdr.what(x) == "png")
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")

    # Optimize
    t = common.parallel(handle_png_files, (queue,))
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
