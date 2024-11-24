#!/usr/bin/env python3
# coding: utf-8

import argparse
import subprocess
import os
from datetime import timedelta
from shlex import quote
from pathlib import Path
from typing import List, Dict
from utils import common


G_FILES_LIST='videos_list.txt'
G_MKV_META_FILE='mkv_metadata.xml'
G_FFM_META_FILE='ffmpeg_metadata.txt'


def generate_chapters_infos(files: List[Path]) -> List[Dict]:
    """Parse"""
    chapters: List[Dict] = []
    chap_number = 1
    chap_start_time = 0
    for vid_file in files:
        command = f"ffprobe -v quiet -of csv=p=0 -show_entries format=duration {quote(str(vid_file))}"
        duration_in_microseconds = int((subprocess.run(command, shell=True, capture_output=True, check=False).stdout.decode().strip().replace(".", "")))
        chap_end_time = chap_start_time + duration_in_microseconds
        chapters.append({"id": chap_number, "duration": duration_in_microseconds, "start": chap_start_time, "end": chap_end_time, "title": vid_file.stem})
        chap_start_time = chap_end_time + 1
        chap_number += 1
    return chapters

def create_ffmpeg_chapters_file(files: List[Path]):
    """Create chapters file in ffmpeg metadata format"""
    chapters = generate_chapters_infos(files)

    with open(G_FFM_META_FILE, "w+", encoding="utf-8") as outfile:
        outfile.writelines(";FFMETADATA1\n")
        for chapter in chapters:
            chap = f"""
[CHAPTER]
TIMEBASE=1/1000000
START={chapter['start']}
END={chapter['end']}
title={chapter['id']}
"""
            outfile.writelines(chap)


def create_mkv_chapters_file(files: List[Path]):
    """Create chapters file in mkv format"""
    chapters = generate_chapters_infos(files)

    with open(G_MKV_META_FILE, "w+", encoding="utf-8") as outfile:
        outfile.writelines('<?xml version="1.0"?>\n')
        outfile.writelines('<!-- <!DOCTYPE Chapters SYSTEM "matroskachapters.dtd"> -->\n')
        outfile.writelines("<Chapters>\n")
        outfile.writelines("<EditionEntry>\n")
        outfile.writelines("<EditionUID>11921230654547845397</EditionUID>\n")
        for chapter in chapters:
            chap = f"""
                <ChapterAtom>
                    <ChapterUID>{chapter['id']}</ChapterUID>
                    <ChapterTimeStart>{timedelta(microseconds=chapter['start'])}</ChapterTimeStart>
                    <ChapterTimeEnd>{timedelta(microseconds=chapter['end'])}</ChapterTimeEnd>
                    <ChapterDisplay>
                        <ChapterString>{chapter['title']}</ChapterString>
                    </ChapterDisplay>
                </ChapterAtom>
            """
            outfile.writelines(chap)
        outfile.writelines("</EditionEntry>\n")
        outfile.writelines("</Chapters>")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to directory")
    parser.add_argument("-m", "--merge", dest="merge", action="store_true", help="Merge all videos files into a single chaptered one")
    parser.add_argument("-f", "--format", dest="format", action="store", type=str, default="mkv", help="Output file format (mkv or mp4)")
    args = parser.parse_args()

    # Sanity checks
    common.ensure_exist(["ffmpeg", "ffprobe", "mkvpropedit"])
    if args.input.exists() is False:
        common.abort(parser.format_help())

    output_format = args.format.lower()
    if output_format not in ["mp4", "mkv"]:
        common.abort(parser.format_help())

    os.chdir(args.input)

    # list vids
    video_files = common.list_directory(Path("."), lambda x: x.suffix in (".mkv", ".mp4"), True)

    # Make the list of videos in ffmpeg format
    vlname = Path(G_FILES_LIST)
    if vlname.exists():
        vlname.unlink()
    for filename in video_files:
        with open(vlname, mode="a", encoding="utf-8") as f:
            f.write(f"file '{filename}'\n")

    if output_format == "mkv":
        create_mkv_chapters_file(video_files)
    else:
        create_ffmpeg_chapters_file(video_files)

    if args.merge is True:
        if output_format == "mkv":
            ffmpeg_cmd = f"ffmpeg -y -f concat -safe 0 -i {quote(str(vlname))} -c copy merged.mkv"
            os.system(ffmpeg_cmd)
            os.system(f"mkvpropedit --chapters {quote(G_MKV_META_FILE)} merged.mkv")
        else:
            ffmpeg_cmd = f"ffmpeg -y -f concat -safe 0 -i {quote(str(vlname))} -i {quote(G_FFM_META_FILE)} -map_metadata 1 -c copy merged.mp4"
            os.system(ffmpeg_cmd)
