#!/usr/bin/env python3
# coding: utf-8

"""
Optimize jpeg files
"""

from __future__ import division
import os
import argparse
import multiprocessing
import threading
from pathlib import Path
from queue import Queue
from shlex import quote
from typing import List
from utils import common, io, logger

LOGGER: logger.Logger
O_SUBSAMPLE = str("subsample")
O_JPEGTRAN = str("jpegtran")
O_GUETZLI = str("guetzli")


def is_420_subsampled(path: Path) -> bool:
    """Check if the jpeg file at `path` is 420"""
    ch = common.system_call(f"identify -format %[jpeg:sampling-factor] {quote(str(path))}").decode("utf-8").strip().lower()
    return '2x2,1x1,1x1' in ch


def command_for_filter(program: str, infile: Path, outfile: Path, keep_metadata: bool) -> str:
    """returns the command corresponding to `program`"""
    if program == O_SUBSAMPLE:
        return f"magick {quote(str(infile))} -sampling-factor '2x2,1x1,1x1' {quote(str(outfile))}"
    if program == O_GUETZLI:
        return f"guetzli --quality 84 --nomemlimit {'--keep-exif' if keep_metadata is True else ''} {quote(str(infile))} {quote(str(outfile))}"
    if program == O_JPEGTRAN:
        return f"jpegtran -optimize -copy {'all' if keep_metadata is True else 'none'} -progressive -outfile {quote(str(outfile))} {quote(str(infile))}"
    return None


def th_optimize(p_queue: Queue, all_programs: List[str], keep_metadata: bool):
    """Optimization thread"""
    while p_queue.empty() is False:
        original_file: Path = p_queue.get()
        last_processed_file = original_file
        for prg in all_programs:
            if prg == O_SUBSAMPLE and is_420_subsampled(original_file) is True:
                # Already subsampled, skip to next filter
                LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] {common.COLOR_YELLOW}{original_file}{common.COLOR_WHITE} is already subsampled, skipping…")
                continue

            outfile = original_file.with_name(f"{original_file.stem}.{prg}.jpg")
            cmd = command_for_filter(prg, last_processed_file, outfile, keep_metadata)
            if cmd is None:
                LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[!] {common.COLOR_RED}ERROR: No command for {common.COLOR_YELLOW}{prg}{common.COLOR_WHITE}")
                continue
            LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[$] {common.COLOR_PURPLE}{cmd}")
            os.system(cmd)
            if outfile.exists() is True:
                if outfile.stat().st_size < last_processed_file.stat().st_size:
                    LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] {common.COLOR_BLUE}{prg} {common.COLOR_GREEN}successful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_processed_file}")
                    if last_processed_file.samefile(original_file) is False:
                        LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] Removing {common.COLOR_YELLOW}{last_processed_file}")
                        last_processed_file.unlink()
                    last_processed_file = outfile
                else:
                    # new file is same size or bigger than previous
                    if prg == O_SUBSAMPLE:
                        last_processed_file = outfile
                    else:
                        LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] {common.COLOR_BLUE}{prg} {common.COLOR_RED}unsuccessful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_processed_file}")
                        outfile.unlink()
            else:
                LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] {common.COLOR_BLUE}{prg} {common.COLOR_RED}unsuccessful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_processed_file}")
        if last_processed_file.samefile(original_file) is False:
            LOGGER.log(f"{common.COLOR_WHITE}(th_{threading.current_thread().name})[-] Renaming {common.COLOR_YELLOW}{last_processed_file}{common.COLOR_WHITE} to {common.COLOR_YELLOW}{original_file}")
            original_file.unlink()
            last_processed_file.rename(original_file)
        p_queue.task_done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single JPEG file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    parser.add_argument("-s", "--subsample", dest="subsample", action='store_true', help="Subsample image to 420 if needed, default: false")
    parser.add_argument("-g", "--guetzli", dest="use_guetzli", action='store_true', help="Use guetzli (very slow and huge memory consumption), default: false")
    parser.add_argument("-j", "--jpegtran", dest="use_jpegtran", action="store_true", default=True, help="Use jpegtran, default: true")
    parser.add_argument("-m", "--keep-metadata", dest="keep_metadata", action='store_true', help="Keep metadata, default: false")
    parser.add_argument("-t", "--threads", dest="threads", type=int, default=0, help="Number of files to process simultaneously")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    programs: List[str] = []
    if args.subsample is True and common.which("identify") is not None and common.which("magick") is not None:
        programs.append(O_SUBSAMPLE)
    if args.use_guetzli is True and common.which("guetzli") is not None:
        programs.append(O_GUETZLI)
    if args.use_jpegtran is True and common.which("jpegtran") is not None:
        programs.append(O_JPEGTRAN)

    # Sanity checks
    if len(programs) == 0:
        common.abort(f"{common.COLOR_WHITE}[!] {common.COLOR_RED}ERROR: No optimization programs specified or found, aborting…")

    # Get files list
    files = common.list_directory(args.input.resolve(), lambda x: io.match_signature(x, [b"\xFF\xD8\xFF\xE0", b"\xFF\xD8\xFF\xE1", b"\xFF\xD8\xFF\xE2", b"\xFF\xD8\xFF\xEE", b"\xFF\xD8\xFF\xDB"]), sort=True)
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")
    LOGGER.log(f"{common.COLOR_WHITE}[+] Using {common.COLOR_BLUE}{', '.join(programs)}")

    # Optimize
    max_threads = multiprocessing.cpu_count() if args.threads <= 0 or args.threads > multiprocessing.cpu_count() else args.threads
    if args.use_guetzli is True and args.threads <= 0:
        max_threads = int(max_threads / 2)
    t = common.parallel(fct=th_optimize, args=(queue, programs, args.keep_metadata,), max_threads=max_threads)
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {common.COLOR_GREEN if bytes_saved > 0 else common.COLOR_RED}{bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
