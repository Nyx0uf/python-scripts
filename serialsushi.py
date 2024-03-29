#!/usr/bin/env python3
# coding: utf-8

"""
bla bla
"""

import os
import argparse
import sys


def list_directory(p_path, p_sorted=False):
    """Returns the list of files at p_path"""
    ret = list()
    if os.path.isdir(p_path) is False:
        ret.append(p_path)
    else:
        for f in os.listdir(p_path):
            if f.startswith('.') is True or f.endswith('mkv') is False:
                continue
            p = os.path.join(p_path, f)
            ret.append(p)
    return ret if p_sorted is False else sorted(ret)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=str, help="Path to directory or video file")
    parser.add_argument("-dst", action="store", dest="dst", type=str, help="Path to directory or video file")
    parser.add_argument("-src-script", action="store", dest="srcscript", type=str, help="mkvmerge script index")
    parser.add_argument("-src-audio", action="store", dest="srcaudio", type=str, help="mkvmerge audio index")
    parser.add_argument("-win", action="store", dest="win", type=str, default="100", help="Path to directory or video file")
    parser.add_argument("-c", "--no-cleanup", dest="no_cleanup", action="store_true", help="cleanup files")
    args = parser.parse_args()

    # Sanity check
    if args.src is None or args.dst is None:
        print(parser.format_help())
        sys.exit(-1)

    # Get a list of files
    src_files = list_directory(os.path.abspath(args.src), True)

    dst_path = os.path.abspath(args.dst)
    dst_files = list()
    if os.path.isdir(dst_path) is True:
        dst_files = list_directory(dst_path, True)
    else:
        dst_files.append(dst_path)

    for idx, val in enumerate(src_files):
        src_file = src_files[idx]
        dst_file = dst_files[idx]
        sushi = 'sushi --no-grouping --window ' + args.win
        if args.no_cleanup is True:
            sushi += ' --no-cleanup '
        sushi += ' --src "' + src_file + '"'
        if args.srcscript is not None:
            sushi += ' --src-script ' + args.srcscript
        if args.srcaudio is not None:
            sushi += ' --src-audio ' + args.srcaudio
        sushi += ' --dst "' + dst_file + '"'
        os.system(sushi)
