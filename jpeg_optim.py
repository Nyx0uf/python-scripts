#!/usr/bin/env python3
# coding: utf-8

"""
Optimize jpeg files with jpegtran/mozjpeg
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

def is_420_subsampled(path: Path) -> bool:
    """Check if the jpeg file at `path` is 420"""
    ch = common.system_call(f"identify -format %[jpeg:sampling-factor] {str(path)}").decode("utf-8").strip()
    return '2x2,1x1,1x1' in ch

def convert_to_420_and_optimize(path: Path, keep_metadata: bool) -> Path:
    """Subsample jpeg file"""
    outfile = path.with_name(str(path.stem) + ".420.jpg")
    cmd = f'convert {quote(str(path))} -sampling-factor "2x2,1x1,1x1" jpeg:- | jpegtran -optimize -copy {"all" if keep_metadata is True else "none"} -progressive -outfile {quote(str(outfile))}'
    os.system(cmd)
    return outfile

def jpegtran(path: Path, keep_metadata: bool) -> Path:
    """jpegtran"""
    outfile = path.with_name(str(path.stem) + ".jpegtran.jpg")
    cmd = f'jpegtran -optimize -copy {"all" if keep_metadata is True else "none"} -progressive -outfile {quote(str(outfile))} {quote(str(path))}'
    os.system(cmd)
    return outfile

def handle_jpeg_files(p_queue: Queue, keep_metadata: bool, subsample: bool):
    """Thread"""
    while p_queue.empty() is False:
        original_jpeg_file: Path = p_queue.get()

        # Subsample if needed
        if subsample is True and is_420_subsampled(original_jpeg_file) is False:
            LOGGER.log(f"{common.COLOR_WHITE}[+] Subsampling {common.COLOR_YELLOW}{original_jpeg_file}")
            subsampled = convert_to_420_and_optimize(original_jpeg_file, keep_metadata)
            if subsampled.exists():
                original_jpeg_file.unlink()
                subsampled.rename(original_jpeg_file)
        else:
            # Optimize
            LOGGER.log(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{original_jpeg_file}")
            optimized = jpegtran(original_jpeg_file, keep_metadata)
            if optimized.exists():
                original_jpeg_file.unlink()
                optimized.rename(original_jpeg_file)

        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single JPEG file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="verbode mode")
    parser.add_argument("-s", "--subsample", dest="subsample", action='store_true', help="Subsample image to 420 if needed")
    parser.add_argument("-m", "--keep-metadata", dest="keep_metadata", action='store_true', help="Don't delete metadata")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["identify", "convert", "jpegtran"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.input.resolve(), lambda x: imghdr.what(x) == "jpeg")
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")

    # Optimize
    t = common.parallel(handle_jpeg_files, (queue, args.keep_metadata, args.subsample,))
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
