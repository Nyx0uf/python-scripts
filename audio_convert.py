#!/usr/bin/env python3
# coding: utf-8

"""
Convert an audio file or directory of audio files to the highest quality in the specified format
[!] ffmpeg (with libfdk_aac, libvorbis, libopus) must be installed and in your $PATH
ex: audio_convert.py -fmt aac /path/to/file/or/dir
"""

import os
import argparse
from pathlib import Path
from typing import List, Dict
from shlex import quote
from queue import Queue
from utils import av, common, logger

LOGGER: logger.Logger

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
        if infile.suffix == out_extension:
            LOGGER.log(f"{common.COLOR_WHITE}[+] No conversion needed for {common.COLOR_YELLOW}{infile}{common.COLOR_WHITE}")
            p_queue.task_done()
            continue
        outfile = infile.with_suffix(out_extension)
        cmd = f"ffmpeg -i {quote(str(infile))} {ffmpeg_options} {quote(str(outfile))}"
        LOGGER.log(f"{common.COLOR_WHITE}[+] Converting {common.COLOR_YELLOW}{infile}{common.COLOR_WHITE} with {common.COLOR_PURPLE}{cmd}{common.COLOR_WHITE}")
        os.system(cmd)
        if delete is True:
            LOGGER.log(f"{common.COLOR_WHITE}[+] Removing {common.COLOR_YELLOW}{infile}{common.COLOR_WHITE}")
            infile.unlink()
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory or single audio file")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode")
    parser.add_argument("-f", "--format", dest="format", type=str, help="Format to convert to")
    parser.add_argument("-s", "--samplerate", dest="samplerate", type=str, help="Samplerate in Hertz (ex: 44100)")
    parser.add_argument("-b", "--bit-depth", dest="bit_depth", type=str, help="Bit depth between 8, 16, 24, 32")
    parser.add_argument("-e", "--extension", dest="extension", type=str, help="Overwrite default output file extension (ex: for aac, .aac instead of .m4a)")
    parser.add_argument("-d", "--delete", dest="delete", action="store_true", help="Delete original file after conversion")
    args = parser.parse_args()
    LOGGER = logger.Logger(args.verbose)

    # Sanity checks
    common.ensure_exist(["ffmpeg"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    if args.format is None:
        common.abort(parser.format_help())

    if args.samplerate is not None and args.samplerate not in SUPPORTED_SAMPLERATES:
        samplerates = '\n- '.join(SUPPORTED_SAMPLERATES)
        common.abort(f"{common.COLOR_RED}[!] ERROR: Invalid samplerate {common.COLOR_WHITE}{args.samplerate}\n{common.COLOR_YELLOW}[+] Available samplerates:\n- {samplerates}")

    if args.bit_depth is not None and args.bit_depth not in SUPPORTED_BIT_DEPTH:
        bds = '\n- '.join(SUPPORTED_BIT_DEPTH)
        common.abort(f"{common.COLOR_RED}[!] ERROR: Invalid bit depth {common.COLOR_WHITE}{args.bit_depth}\n{common.COLOR_YELLOW}[+] Available bit depth:\n- {bds}")

    out_format = args.format.lower()
    if is_valid_output_format(out_format) is False:
        formats = '\n- '.join(sorted(SUPPORTED_OUTPUT_TYPES.keys()))
        common.abort(f"{common.COLOR_RED}[!] ERROR: Invalid format {common.COLOR_WHITE}{out_format}\n{common.COLOR_YELLOW}[+] Available formats:\n- {formats}")

    # Get a list of files
    files = common.walk_directory(args.input.resolve(), is_valid_audio_file)
    queue = common.as_queue(files)

    # Convert
    common.parallel(convert, (queue, out_format, args.samplerate, args.bit_depth, args.extension, args.delete,))
