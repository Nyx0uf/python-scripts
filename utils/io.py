#!/usr/bin/env python3
# coding: utf-8

"""
Common IO functions
"""

import os
import shutil
from distutils.dir_util import copy_tree
from pathlib import Path
from typing import List

def cp_file(src: Path, dst: Path):
    """Copy `src` to `dst` if src is a file"""
    path = Path(src)
    if path.exists() is True and path.is_file() is True:
        shutil.copy(src, dst, follow_symlinks=True)

def cp_dir(src: Path, dst: Path):
    """Copy `src` to `dst` if src is a directory"""
    path = Path(src)
    if path.exists() is True and path.is_dir() is True:
        copy_tree(src, dst)

def rm(path: Path):
    """Remove a file or directory at `path`"""
    p = Path(path)
    if p.exists() is True:
        if p.is_dir() is True:
            shutil.rmtree(path, ignore_errors=True)
        elif p.is_file() is True:
            os.remove(path)

def rm2(paths: List[Path]):
    """Remove a list of items"""
    for path in paths:
        rm(path)

def cd(path: Path):
    """cd"""
    os.chdir(path)

def mv(src: Path, dst: Path):
    """mv"""
    shutil.move(src, dst)

def mkdir(path: Path):
    """mkdir -p"""
    os.makedirs(path)

def chmod(path: Path, mode: int):
    """chmod"""
    os.chmod(path, mode)

def chown(path: Path, usr: str, grp: str):
    """chown"""
    shutil.chown(path, user=usr, group=grp)

def tar_xz(src: Path, dst: Path):
    """XZ_OPT=-9 tar -Jcf"""
    os.system(f"XZ_OPT=-9 tar -Jcf {str(dst)} {str(src)}")
