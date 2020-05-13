#!/usr/bin/env python3
# coding: utf-8

"""
Optimize png files
"""

from __future__ import division
import os
import argparse
from pathlib import Path
from queue import Queue
from shlex import quote
from typing import List
from utils import common, logger

LOGGER: logger.Logger
F_OPTIPNG = str("optipng")
F_PNGQUANT = str("pngquant")
F_ZOPFLI = str("zopfli")

def command_for_filter(program: str, infile: Path, outfile: Path) -> str:
    """returns the command corresponding to `filt`"""
    if program == F_PNGQUANT:
        return f"pngquant -f --speed 1 --quality 65-80 --strip --skip-if-larger -o {quote(str(outfile))} {quote(str(infile))}"
    if program == F_ZOPFLI:
        return f"zopflipng --iterations=50 --filters=01234mepb --lossy_transparent {quote(str(infile))} {quote(str(outfile))} > /dev/null"
    if program == F_OPTIPNG:
        return f"optipng -quiet -o7 -preserve -out {quote(str(outfile))} {quote(str(infile))}"
    return None

def th_optimize(p_queue: Queue, programs: List[str]):
    """Optimization thread"""
    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        last_file = infile
        for prg in programs:
            outfile = infile.with_name(f"{infile.stem}.{prg}.png")
            cmd = command_for_filter(prg, last_file, outfile)
            if cmd is None:
                LOGGER.log(f"{common.COLOR_WHITE}[!] {common.COLOR_RED}ERROR: No command for {common.COLOR_YELLOW}{prg}{common.COLOR_WHITE}")
                continue
            LOGGER.log(f"{common.COLOR_WHITE}[$] {common.COLOR_PURPLE}{cmd}")
            os.system(cmd)
            if outfile.exists() is True:
                if outfile.stat().st_size < last_file.stat().st_size:
                    LOGGER.log(f"{common.COLOR_WHITE}[-] {common.COLOR_BLUE}{prg} {common.COLOR_GREEN}successful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_file}")
                    if last_file.samefile(infile) is False:
                        LOGGER.log(f"{common.COLOR_WHITE}[-] Removing {common.COLOR_YELLOW}{last_file}")
                        last_file.unlink()
                    last_file = outfile
                else:
                    LOGGER.log(f"{common.COLOR_WHITE}[-] {common.COLOR_BLUE}{prg} {common.COLOR_RED}unsuccessful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_file}")
                    outfile.unlink()
            else:
                LOGGER.log(f"{common.COLOR_WHITE}[-] {common.COLOR_BLUE}{prg} {common.COLOR_RED}unsuccessful{common.COLOR_WHITE} for {common.COLOR_YELLOW}{last_file}")
        if last_file.samefile(infile) is False:
            LOGGER.log(f"{common.COLOR_WHITE}[-] Renaming {common.COLOR_YELLOW}{last_file}{common.COLOR_WHITE} to {common.COLOR_YELLOW}{infile}")
            infile.unlink()
            last_file.rename(infile)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single PNG file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    parser.add_argument("-q", "--quant", dest="use_pngquant", action="store_true", help="Use pngquant (png8b)")
    parser.add_argument("-z", "--zopfli", dest="use_zopfli", action="store_true", help="Use zopfli (very slow)")
    parser.add_argument("-n", "--disable-optipng", dest="use_optipng", action="store_false", default=True, help="Disable optipng")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    programs: List[str] = []
    if args.use_pngquant is True and common.which("pngquant") is not None:
        programs.append(F_PNGQUANT)
    if args.use_zopfli is True and common.which("zopflipng") is not None:
        programs.append(F_ZOPFLI)
    if args.use_optipng is True and common.which("optipng") is not None:
        programs.append(F_OPTIPNG)

    # Sanity checks
    if len(programs) == 0:
        common.abort(f"{common.COLOR_WHITE}[!] {common.COLOR_RED}ERROR: No optimization programs specified or found, aborting…")

    # Get files list
    files = common.walk_directory(args.input.resolve(), lambda x: x.suffix == ".png")
    queue = common.as_queue(files)
    total_original_bytes = sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {len(files)} file{'s' if len(files) != 1 else ''} to optimize ({total_original_bytes / 1048576:4.2f}Mb)")
    LOGGER.log(f"{common.COLOR_WHITE}[+] Using {common.COLOR_BLUE}{', '.join(programs)}")

    # Optimize
    t = common.parallel(th_optimize, (queue, programs, ))
    bytes_saved = total_original_bytes - sum(x.stat().st_size for x in files)
    LOGGER.log(f"{common.COLOR_WHITE}[+] {common.COLOR_GREEN if bytes_saved > 0 else common.COLOR_RED}{bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb) in {t:4.2f}s")
