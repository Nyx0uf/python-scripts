#!/usr/bin/env python3
# coding: utf-8

"""
Trim Mach-O fat binaries, need to be executed as root for MAS apps
"""

import argparse
import os
from macholib import MachO, mach_o # pip3 install macholib
from pathlib import Path
from queue import Queue
from shlex import quote
from threading import Lock
from typing import List
from utils import common

ARCHS: List[str] = [
    "arm64",
    "armv6",
    "armv7",
    "i386",
    "ppc",
    "x86_64"
]

LOCK = Lock()

def get_archs(path: Path) -> List[str]:
    """Get architecture(s) of `path`"""
    m = None
    archs: List[str] = []
    try:
        m = MachO.MachO(path)
    except:
        return []
    for header in m.headers:
        cpu_type = header.header.cputype
        cpu_subtype = header.header.cpusubtype
        arch = str(mach_o.CPU_TYPE_NAMES.get(cpu_type, cpu_type)).lower()
        if cpu_type == 12:
            if cpu_subtype == 0:
                arch = 'armall'
            elif cpu_subtype == 5:
                arch = 'armv4t'
            elif cpu_subtype == 6:
                arch = 'armv6'
            elif cpu_subtype == 7:
                arch = 'armv5tej'
            elif cpu_subtype == 8:
                arch = 'arm_xscale'
            elif cpu_subtype == 9:
                arch = 'armv7'
            elif cpu_subtype == 10:
                arch = 'armv7f'
            elif cpu_subtype == 11:
                arch = 'armv7s'
            elif cpu_subtype == 12:
                arch = 'armv7k'
            elif cpu_subtype == 13:
                arch = 'armv8'
            elif cpu_subtype == 14:
                arch = 'armv6m'
            elif cpu_subtype == 15:
                arch = 'armv7m'
            elif cpu_subtype == 16:
                arch = 'armv7em'
        elif cpu_type == 16777228:
            arch = 'arm64'
        archs.append(arch)
    return archs

def remove_arch(arch: str, path: Path):
    """lipo -remove `arch` `path` -output `path.bak`"""
    trimmed = path.with_name(f"{path.stem}.bak")
    os.system(f"lipo -remove {arch} {quote(str(path))} -output {quote(str(trimmed))}")
    if trimmed.exists() is True:
        path.unlink()
        trimmed.replace(path)

def th_filter(p_queue: Queue, arch: str, fat_binaries: List[Path]):
    """Filter binaries that have more than one arch and the arch to remove"""
    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        archs = get_archs(infile)
        if len(archs) > 1 and arch in archs:
            LOCK.acquire()
            fat_binaries.append(infile)
            LOCK.release()
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arch", type=str, help="Arch to remove (arm64, i386, x86_64...)")
    parser.add_argument("input", type=Path, help="Path to binary or directory")
    parser.add_argument("-p", "--pretend", dest="pretend", action="store_true", help="Do not trim, just print")
    args = parser.parse_args()

    # Sanity check
    if args.arch not in ARCHS:
        common.abort(f"{common.COLOR_RED}[!] ERROR: Invalid arch {common.COLOR_WHITE}{args.arch}\n{common.COLOR_YELLOW}[+] Available archs:\n- {ARCHS}")

    # Get executable list
    tmp: List[Path] = []
    if args.input.is_dir() is True:
        tmp = common.walk_directory(args.input, common.is_executable)
    elif common.is_executable(args.input):
        tmp.append(args.input)

    paths: List[Path] = []
    q = common.as_queue(tmp)
    common.parallel(fct=th_filter, args=(q, args.arch, paths, ))

    bytes_saved = int(0)
    for path in paths:
        print(f"{common.COLOR_WHITE}[+] Trimming {common.COLOR_YELLOW}{path}{common.COLOR_WHITE}")
        if args.pretend is False:
            osize = path.stat().st_size
            remove_arch(args.arch, path)
            nsize = path.stat().st_size
            bytes_saved += (osize - nsize)

    if args.pretend is False:
        print(f"{common.COLOR_WHITE}[+] {common.COLOR_GREEN if bytes_saved > 0 else common.COLOR_RED}{bytes_saved} bytes saved ({bytes_saved / 1048576:4.2f}Mb)")
