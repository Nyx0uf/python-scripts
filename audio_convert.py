#!/usr/bin/env python3
# coding: utf-8

"""
Convert an audio file or directory of audio files to the highest quality in the specified format
[!] ffmpeg (with libfdk_aac, libvorbis, libopus) must be installed and in your $PATH
ex: audio_convert.py -src /path/to/file.dts -fmt aac
"""

import os
import argparse
from pathlib import Path
from typing import List, Dict
from shlex import quote
from queue import Queue
from utils import common, av

SUPPORTED_OUTPUT_TYPES: Dict[str, str] = {
    str('aac'): str('.m4a'),
    str('ac3'): str('.ac3'),
    str('alac'): str('.m4a'),
    str('flac'): str('.flac'),
    str('mp3'): str('.mp3'),
    str('opus'): str('.ogg'),
    str('vorbis'): str('.ogg'),
}

SUPPORTED_SAMPLERATES: List[str] = [
    str("8000"),
    str("11025"),
    str("16000"),
    str("22050"),
    str("32000"),
    str("37800"),
    str("44056"),
    str("44100"),
    str("47250"),
    str("48000"),
    str("50000"),
    str("50400"),
    str("64000"),
    str("88200"),
    str("96000"),
    str("176400"),
    str("192000"),
    str("352800"),
]

SUPPORTED_BIT_DEPTH: List[str] = [
    str("8"),
    str("16"),
    str("24"),
    str("32"),
]

BIT_DEPTH_MAP: Dict[str, str] = {
    str('8'): str('u8'),
    str('16'): str('s16'),
    str('24'): str('s32'),
    str('32'): str('s32'),
}

def is_valid_audio_file(path: Path) -> bool:
    """Check if `path` is a supported audio file"""
    return path.suffix.lower() in av.AUDIO_EXTENSIONS

def is_valid_output_format(fmt: str) -> bool:
    """Check if `fmt` is a supported output format"""
    return fmt in SUPPORTED_OUTPUT_TYPES

def convert(p_queue: Queue, fmt: str, sr: str, bd: str, ext: str, delete: bool):
    """Convert thread"""
    ffmpeg_options = '-y -hide_banner -loglevel quiet -vn -c:a '
    if fmt == 'alac':
        ffmpeg_options += 'alac'
    elif fmt == 'flac':
        ffmpeg_options += 'flac -compression_level 12'
    elif fmt == 'aac':
        ffmpeg_options += 'libfdk_aac -vbr 5 -movflags +faststart'
    elif fmt == 'mp3':
        ffmpeg_options += 'libmp3lame -q:a 0'
    elif fmt == 'ac3':
        ffmpeg_options += 'ac3'
    elif fmt == 'opus':
        ffmpeg_options += 'libopus -compression_level 10 -vbr on'
    elif fmt == 'vorbis':
        ffmpeg_options += 'libvorbis -qscale:a 10'
    else:
        raise "Error."

    if sr is not None:
        ffmpeg_options += f" -ar {sr}"

    if bd is not None:
        ffmpeg_options += f" -sample_fmt {bd}"

    out_extension = SUPPORTED_OUTPUT_TYPES[fmt]
    if ext is not None:
        out_extension = ext.lower()
        if out_extension.startswith('.') is False:
            out_extension = f".{out_extension}"

    while p_queue.empty() is False:
        infile: Path = p_queue.get()
        outfile = infile.with_suffix(out_extension)
        print(f"[+] Converting <{infile}>")
        cmd = f"ffmpeg -i {quote(str(infile))} {ffmpeg_options} {quote(str(outfile))}"
        os.system(cmd)
        if delete is True:
            infile.unlink()
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    parser.add_argument("-fmt", action="store", dest="fmt", type=str, help="Output format")
    parser.add_argument("-sr", action="store", dest="sr", type=str, help="Samplerate in Hertz")
    parser.add_argument("-bd", action="store", dest="bd", type=str, help="Bit depth (8/16/24/32)")
    parser.add_argument("-ext", action="store", dest="ext", type=str, help="Force output file extension (ex for aac, .aac instead of .m4a)")
    parser.add_argument("-d", action="store_true", dest="delete", default=False, help="Delete original file")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["ffmpeg"])
    if args.src.exists() is False:
        common.abort(parser.format_help())

    if args.fmt is None:
        common.abort(parser.format_help())

    if args.sr is not None and args.sr not in SUPPORTED_SAMPLERATES:
        samplerates = ', '.join(SUPPORTED_SAMPLERATES)
        common.abort(f"Invalid samplerate: {args.sr}\nAvailable samplerates: {samplerates}")

    if args.bd is not None and args.bd not in SUPPORTED_BIT_DEPTH:
        bds = ', '.join(SUPPORTED_BIT_DEPTH)
        common.abort(f"Invalid bit depth: {args.bd}\nAvailable bit depth: {bds}")

    out_format = args.fmt.lower()
    if is_valid_output_format(out_format) is False:
        formats = ', '.join(sorted(SUPPORTED_OUTPUT_TYPES.keys()))
        common.abort(f"Invalid format: {out_format}\nAvailable formats: {formats}")

    # Get a list of files
    files = common.walk_directory(args.src.resolve(), is_valid_audio_file)
    queue = common.as_queue(files)

    # Convert
    common.parallel(convert, (queue, out_format, args.sr, args.bd, args.ext, args.delete,))
