#!/usr/bin/env python3
# coding: utf-8

"""
Optimize jpeg files
"""

from __future__ import division
import os
import argparse
import subprocess
from pathlib import Path
from threading import Lock
from queue import Queue
from shlex import quote
from utils import common

G_metadata = False
G_pretend = False
G_subsample = False
G_verbose = False
total_original_bytes = 0
total_opt_bytes = 0
lock = Lock()

def nyx_print(string: str):
    """print function"""
    if G_verbose is True or G_pretend is True:
        print(string)

def is_420_subsampled(path: Path) -> bool:
    """Check if the jpeg file is 420"""
    try:
        process = subprocess.Popen(['identify', '-format', '%[jpeg:sampling-factor]', str(path)], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        (out, _) = process.communicate()
        process.wait()
        ch = ''.join(str(out.split()))
        return '2x2,1x1,1x1' in ch
    except OSError as e:
        if e.errno == 2:
            raise NameError("identify not found, check that ImageMagick is installed and in your $PATH")
        raise

def convert_to_420(path: Path) -> Path:
    """Subsample jpeg file"""
    outfile = path.with_name(str(path.name) + "-420")
    cmd_convert = f'convert {quote(str(path))} -sampling-factor "2x2,1x1,1x1" {quote(str(outfile))}'
    nyx_print(f"{common.COLOR_PURPLE}{cmd_convert}{common.COLOR_WHITE}")
    if G_pretend is False:
        os.system(cmd_convert)
    return outfile

def jpegtran(path: Path) -> Path:
    """jpegtran"""
    outfile = path.with_name(str(path.name) + "-moz")
    metadata = "-copy all" if G_metadata is True else "-copy none"
    cmd = f'jpegtran -optimize {metadata} -progressive -outfile {quote(str(outfile))} {quote(str(path))}'
    nyx_print(f"{common.COLOR_PURPLE}{cmd}{common.COLOR_WHITE}")
    if G_pretend is False:
        os.system(cmd)
    return outfile

def handle_jpeg_files(p_queue: Queue):
    """Thread"""
    while p_queue.empty() is False:
        original_jpeg_file: Path = p_queue.get()

        file_to_optimize = original_jpeg_file
        # Subsample if needed
        if G_subsample is True and not is_420_subsampled(original_jpeg_file):
            nyx_print(f"{common.COLOR_WHITE}[+] Subsampling {common.COLOR_YELLOW}{original_jpeg_file}")
            subsampled = convert_to_420(original_jpeg_file)
            if subsampled.is_file() or G_pretend is True:
                file_to_optimize = subsampled
        # Optimize
        nyx_print(f"{common.COLOR_WHITE}[+] Optimizing {common.COLOR_YELLOW}{file_to_optimize}")
        optimized = jpegtran(file_to_optimize)
        if optimized.is_file() and G_pretend is False:
            global total_original_bytes
            global total_opt_bytes
            lock.acquire()
            total_original_bytes += original_jpeg_file.stat().st_size
            total_opt_bytes += optimized.stat().st_size
            lock.release()
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
    parser.add_argument('-ss', action='store_true', dest="subsample", default=False, help="Subsample flag")
    parser.add_argument('-m', action='store_true', dest="metadata", default=False, help="Keep metadata flag")
    parser.add_argument('-p', action='store_true', dest="pretend", default=False, help="Pretend flag")
    parser.add_argument('-verbose', action='store_true', dest="verbose", default=False, help="Verbose flag")
    args = parser.parse_args()

    if common.which("identify") is None or common.which("convert") is None:
        common.abort("[!] ImageMagick not found in $PATH")
    if common.which("jpegtran") is None:
        common.abort("[!] jpegtran/mozjpeg not found in $PATH")

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    G_metadata = args.metadata
    G_pretend = args.pretend
    G_subsample = args.subsample
    G_verbose = args.verbose

    # Get files list
    files = common.walk_directory(args.src.resolve(), lambda x: x.suffix == ".jpg" or x.suffix == ".jpeg")
    queue = common.as_queue(files)
    print(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to consider")

    # Optimize
    t = common.parallel(handle_jpeg_files, (queue,))
    bytes_saved = total_original_bytes - total_opt_bytes
    if G_pretend is False:
        print("{}[+] {} bytes saved ({:.2f}Mb) in {:.2f}s".format(common.COLOR_WHITE, bytes_saved, (bytes_saved / 1048576), t))
