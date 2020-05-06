#!/usr/bin/env python3
# coding: utf-8

"""
Optimize jpeg files with jpegtran/mozjpeg
"""

from __future__ import division
import os
import argparse
from pathlib import Path
from queue import Queue
from shlex import quote
from utils import common

def is_420_subsampled(path: Path) -> bool:
    """Check if the jpeg file at `path` is 420"""
    ch = common.system_call(f"identify -format %[jpeg:sampling-factor] {str(path)}").decode("utf-8").strip()
    return '2x2,1x1,1x1' in ch

def convert_to_420(path: Path) -> Path:
    """Subsample jpeg file"""
    outfile = path.with_name(str(path.stem) + ".420.jpg")
    cmd_convert = f'convert {quote(str(path))} -sampling-factor "2x2,1x1,1x1" {quote(str(outfile))}'
    os.system(cmd_convert)
    return outfile

def jpegtran(path: Path, keep_metadata: bool) -> Path:
    """jpegtran"""
    outfile = path.with_name(str(path.stem) + ".jpegtran.jpg")
    metadata = "-copy all" if keep_metadata is True else "-copy none"
    cmd = f'jpegtran -optimize {metadata} -progressive -outfile {quote(str(outfile))} {quote(str(path))}'
    os.system(cmd)
    return outfile

def handle_jpeg_files(p_queue: Queue, keep_metadata: bool, subsample: bool):
    """Thread"""
    while p_queue.empty() is False:
        original_jpeg_file: Path = p_queue.get()

        file_to_optimize = original_jpeg_file
        # Subsample if needed
        if subsample is True and not is_420_subsampled(original_jpeg_file):
            print(f"{common.COLOR_WHITE}[+] Subsampling {common.COLOR_YELLOW}{original_jpeg_file}")
            subsampled = convert_to_420(original_jpeg_file)
            if subsampled.is_file():
                file_to_optimize = subsampled
        # Optimize
        print(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{file_to_optimize}")
        optimized = jpegtran(file_to_optimize, keep_metadata)
        if optimized.is_file():
            original_jpeg_file.unlink() # Remove original jpeg
            if file_to_optimize != original_jpeg_file:
                # Remove eventual intermediate subsampled file
                file_to_optimize.unlink()
            # Rename optimized version to original
            optimized.rename(original_jpeg_file)

        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    parser.add_argument('-ss', action='store', dest="subsample", type=common.str2bool, default=False, help="Subsample flag")
    parser.add_argument('-m', action='store', dest="metadata", type=common.str2bool, default=False, help="Keep metadata flag")
    args = parser.parse_args()

    if common.which("identify") is None or common.which("convert") is None:
        common.abort("[!] ImageMagick not found in $PATH")
    if common.which("jpegtran") is None:
        common.abort("[!] jpegtran/mozjpeg not found in $PATH")

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: x.suffix == ".jpg" or x.suffix == ".jpeg")
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")

    # Optimize
    t = common.parallel(handle_jpeg_files, (queue, args.metadata, args.subsample,))
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    print(f"{common.COLOR_WHITE}[+] {bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
