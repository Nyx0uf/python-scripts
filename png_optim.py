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
from utils import common

def handle_png_files(p_queue: Queue):
    """pngquant + optipng"""
    while p_queue.empty() is False:
        original_png_file: Path = p_queue.get()
        print(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{original_png_file}")
        # pngquant
        pngquanted = original_png_file.with_name(f"{original_png_file.stem}.pngquant.png")
        os.system(f"pngquant -f -o {quote(str(pngquanted))} --speed 1 --quality 75-100 --strip --skip-if-larger {quote(str(original_png_file))}")
        # optipng
        optimized = original_png_file.with_name(f"{original_png_file.stem}.optipng.png")
        if pngquanted.exists():
            os.system(f"optipng -quiet -o7 -preserve -out {quote(str(optimized))} {quote(str(pngquanted))}")
            pngquanted.unlink()
        else:
            os.system(f"optipng -quiet -o7 -preserve -out {quote(str(optimized))} {quote(str(original_png_file))}")
        original_png_file.unlink()
        # Rename optimized version to original
        optimized.rename(original_png_file)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or single png file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["pngquant", "optipng"])
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: imghdr.what(x) == "png")
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")

    # Optimize
    t = common.parallel(handle_png_files, (queue,))
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    print(f"{common.COLOR_WHITE}[+] {bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
