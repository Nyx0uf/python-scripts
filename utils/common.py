#!/usr/bin/env python3
# coding: utf-8

"""
Commonly used functions
"""

import os
import sys
import subprocess
import multiprocessing
import time
from threading import Thread
from queue import Queue
from pathlib import Path
from typing import List

COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_PURPLE = '\033[95m'
COLOR_RED = '\033[91m'
COLOR_WHITE = '\033[0m'
COLOR_YELLOW = '\033[93m'

def str2bool(value: str) -> bool:
    """Convert `value` to a bool"""
    lpv = value.lower()
    if lpv in ('yes', 'true', 't', 'y', '1'):
        return True
    if lpv in ('no', 'false', 'f', 'n', '0'):
        return False
    raise f"<{value}> can't be converted to a bool"

def list_directory(path: Path, filt=None, sort=False) -> List[Path]:
    """Returns the list of files at `path`"""
    ret: List[Path] = []
    if path.is_dir() is False:
        if filt is None or callable(filt) is False:
            ret.append(path)
        elif filt(path) is True:
            ret.append(path)
        return ret

    for entry in os.listdir(path):
        if entry.startswith('.') is True:
            continue
        p = path / entry
        if filt is None or callable(filt) is False:
            ret.append(p)
        elif filt(p) is True:
            ret.append(p)
    return ret if sort is False else sorted(ret)


def walk_directory(path: Path, filt=None) -> List[Path]:
    """walk a directory"""
    ret: List[Path] = []
    if path.is_dir() is False:
        if filt is None or callable(filt) is False:
            ret.append(path)
        elif filt(path) is True:
            ret.append(path)
        return ret

    for root, _, files in os.walk(path):
        for entry in files:
            p = Path(root) / entry
            if filt is None or callable(filt) is False:
                ret.append(p)
            elif filt(p) is True:
                ret.append(p)
    return ret

def which(program: str) -> str:
    """Like the unix which command"""
    def is_exe(path: str) -> bool:
        """Check if `path` is executable"""
        return os.path.isfile(path) and os.access(path, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def as_queue(lst) -> Queue:
    """returns `lst` as a Queue"""
    q = Queue()
    for x in lst:
        q.put(x)
    return q

def parallel(fct, args: tuple) -> float:
    """Execute `fct` with `args` in parallel"""
    t_start = time.time()
    queue = args[0]
    for i in range(multiprocessing.cpu_count()):
        th = Thread(target=fct, args=args, name=str(i), daemon=True)
        th.start()
    queue.join()
    t_end = time.time()
    return t_end - t_start

def abort(msg: str = None):
    """Exits the program and optionally display `msg`"""
    if msg is not None:
        print(msg)
    sys.exit(-1)

def system_call(command: str) -> str:
    """Execute `command` and returns stdout"""
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    return process.stdout.read()
