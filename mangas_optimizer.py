#!/usr/bin/env python3
# coding: utf-8

"""
Optimize a directory of manga scans :
- Convert grayscale images to png
- Convert color images to jpg
- Optimize jpg & png files
- Compress directory
"""

import os
import argparse
import imghdr
import time
from pathlib import Path
from queue import Queue
from shlex import quote

import numpy
from PIL import Image # pip3 install Pillow
import pyopencl as cl

from utils import common

CL_KERNEL = """
__kernel void isGrey(read_only image2d_t src, __global unsigned int* color)
{
    const sampler_t sampler = CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_CLAMP_TO_EDGE | CLK_FILTER_NEAREST;
    int2 pos = (int2)(get_global_id(0), get_global_id(1));
    uint4 pix = read_imageui(src, sampler, pos);
    if (pix.x != pix.y || pix.x != pix.z || pix.y != pix.z)
    {
        *color += 1;
    }
}
"""

def cl_is_grey(p_rgb, p_cl_context: cl.Context, p_cl_queue: cl.CommandQueue, p_cl_program: cl.Program) -> bool:
    """Check if an image is grey using OpenCL"""
    pixels = numpy.array(p_rgb)
    dev_buf = cl.image_from_array(p_cl_context, pixels, 4)

    color = numpy.uint32(0)
    dev_color = cl.Buffer(p_cl_context, cl.mem_flags.COPY_HOST_PTR, hostbuf=color)

    p_cl_program.isGrey(p_cl_queue, (pixels.shape[0], pixels.shape[1]), None, dev_buf, dev_color)

    nb_colors = numpy.empty_like(color)
    cl.enqueue_copy(p_cl_queue, nb_colors, dev_color)
    return bool(nb_colors == 0)

def save_to_format(p_queue: Queue, fmt: str):
    """PNG export thread"""
    while p_queue.empty() is False:
        original_file: Path = p_queue.get()
        img2 = Image.open(original_file).convert('RGB')
        png_path = original_file.with_suffix(fmt)
        img2.save(png_path, quality=100, optimize=False, progressive=False, icc_profile=None)
        original_file.unlink()
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Path to manga directory")
    args = parser.parse_args()

    # Sanity checks
    path = args.input.resolve()
    if path.exists() is False or path.is_dir() is False:
        common.abort(parser.format_help())

    # Get files list
    all_files = common.list_directory(path, lambda x: x.suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"])
    print(f"{common.COLOR_WHITE}[+] {len(all_files)} file(s) to analyze…")

    # Analyze files
    q_grey_conv = Queue()
    q_color_conv = Queue()
    t_start = time.time()
    cl_ctx = cl.create_some_context()
    cl_queue = cl.CommandQueue(cl_ctx)
    cl_program = cl.Program(cl_ctx, CL_KERNEL).build()
    for f in all_files:
        img = Image.open(f).convert('RGBA')
        is_grey = cl_is_grey(img, cl_ctx, cl_queue, cl_program)
        if is_grey is True and imghdr.what(f) != "png":
            q_grey_conv.put(f)
        elif is_grey is False and imghdr.what(f) == "png":
            q_color_conv.put(f)
    t_end = time.time()
    grey_count = q_grey_conv.qsize()
    color_count = q_color_conv.qsize()
    print(f"{common.COLOR_GREEN} ↳ Done in {t_end - t_start:4.2f}s :")
    print(f"{common.COLOR_PURPLE}\t→ {grey_count} grayscaled file(s) need to be converted")
    print(f"{common.COLOR_PURPLE}\t→ {color_count} colorized file(s) need to be converted")

    # Convert grayscaled images to png
    if grey_count > 0:
        print(f"{common.COLOR_WHITE}[+] Converting {grey_count} grayscaled files…")
        t = common.parallel(save_to_format, (q_grey_conv, ".png", ))
        print(f"{common.COLOR_GREEN} ↳ Done in {t:4.2f}s")

    # Convert colorized images to jpg
    if color_count > 0:
        print(f"{common.COLOR_WHITE}[+] Converting {color_count} colorized files…")
        t = common.parallel(save_to_format, (q_color_conv, ".jpg", ))
        print(f"{common.COLOR_GREEN} ↳ Done in {t:4.2f}s")

    # Optimize png
    png_files = common.list_directory(path, lambda x: x.suffix == ".png")
    print(f"{common.COLOR_WHITE}[+] Optimizing {len(png_files)} PNG files…")
    t_start = time.time()
    os.system(f"png_optim.py -v -q -z -n {quote(str(path))}")
    t_end = time.time()
    print(f"{common.COLOR_GREEN} ↳ Done in {t_end - t_start:4.2f}s")

    # Optimize jpg
    jpg_files = common.list_directory(path, lambda x: x.suffix in [".jpg", ".jpeg"])
    print(f"{common.COLOR_WHITE}[+] Optimizing {len(jpg_files)} JPEG files…")
    t_start = time.time()
    os.system(f"jpeg_optim.py -v -s -g {quote(str(path))}")
    t_end = time.time()
    print(f"{common.COLOR_GREEN} ↳ Done in {t_end - t_start:4.2f}s")

    # txz
    print(f"{common.COLOR_WHITE}[+] Compressing {path}")
    t_start = time.time()
    os.system(f'XZ_OPT="-T 0 -9" tar -Jcf {quote(str(path) + ".txz")} {quote(str(path))}')
    t_end = time.time()
    print(f"{common.COLOR_GREEN} ↳ Done in {t_end - t_start:4.2f}s")
