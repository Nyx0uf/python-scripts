#!/usr/bin/env python3
# coding: utf-8

"""
bla.
"""

import os
import argparse
import imghdr
import multiprocessing
import time
from pathlib import Path
from queue import Queue
from threading import Thread
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

def cl_is_grey(p_rgb, p_cl_context, p_cl_queue, p_cl_program) -> bool:
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

def optimize_png(p_queue: Queue):
    """pngquant + optipng"""
    while p_queue.empty() is False:
        original_png_file: Path = p_queue.get()
        pngquanted = "{}.pngquant.png".format(str(original_png_file))
        cmd = "pngquant -f -o {} --speed 1 --quality 100 --strip {}".format(quote(pngquanted), quote(str(original_png_file)))
        os.system(cmd)
        optimized = "{}.optipng.png".format(pngquanted)
        cmd = 'optipng -quiet -o7 -preserve -out {} {}'.format(quote(optimized), quote(pngquanted))
        os.system(cmd)
        os.remove(pngquanted) # Remove pngquant
        os.remove(original_png_file) # Remove original
        # Rename optimized version to original
        os.rename(optimized, original_png_file)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=Path, default=Path("."), help="Path to directory or audio file")
    args = parser.parse_args()

    # Sanity check
    if args.src.exists() is False:
        common.abort(parser.format_help())

    # Get files list
    path = args.src.resolve()
    if path.is_dir() is False:
        common.abort(parser.format_help())
    all_files = common.walk_directory(path, lambda x: x.suffix in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tif", ".tiff"])
    print(f"{common.COLOR_WHITE}[+] {len(all_files)} file(s) to analyze…")

    # Analyze files
    q_grey_conv = Queue()
    q_color_conv = Queue()
    t_start = time.time()
    cl_ctx = cl.create_some_context()
    cl_queue = cl.CommandQueue(cl_ctx)
    cl_program = cl.Program(cl_ctx, CL_KERNEL).build()
    for file in all_files:
        img = Image.open(file).convert('RGBA')
        is_grey = cl_is_grey(img, cl_ctx, cl_queue, cl_program)
        if is_grey is True and imghdr.what(file) != "png":
            q_grey_conv.put(file)
        elif is_grey is False and imghdr.what(file) == "png":
            q_color_conv.put(file)
    t_end = time.time()
    grey_count = q_grey_conv.qsize()
    color_count = q_color_conv.qsize()
    print("{} ↳ Done in {:.2f}s :".format(common.COLOR_GREEN, (t_end - t_start)))
    print(f"{common.COLOR_PURPLE}\t→ {grey_count} grayscaled file(s) need to be converted")
    print(f"{common.COLOR_PURPLE}\t→ {color_count} colorized file(s) need to be converted")

    # Convert grayscaled images to png
    if grey_count > 0:
        print(f"{common.COLOR_WHITE}[+] Converting {grey_count} grayscaled files…")
        t_start = time.time()
        for i in range(multiprocessing.cpu_count()):
            th = Thread(target=save_to_format, args=(q_grey_conv, ".png"))
            th.setDaemon(True)
            th.start()
        q_grey_conv.join()
        t_end = time.time()
        print("{} ↳ Done in {:.2f}s".format(common.COLOR_GREEN, (t_end - t_start)))

    # Convert colorized images to jpg
    if color_count > 0:
        print(f"{common.COLOR_WHITE}[+] Converting {color_count} colorized files…")
        t_start = time.time()
        for i in range(multiprocessing.cpu_count()):
            th = Thread(target=save_to_format, args=(q_color_conv, ".jpg"))
            th.setDaemon(True)
            th.start()
        q_color_conv.join()
        t_end = time.time()
        print("{} ↳ Done in {:.2f}s".format(common.COLOR_GREEN, (t_end - t_start)))

    # Optimize png (pngquant + optipng)
    png_files = common.walk_directory(path, lambda x: os.path.splitext(x)[1] in [".png"])
    print(f"{common.COLOR_WHITE}[+] Optimizing {len(png_files)} PNG files…")
    t_start = time.time()
    q_png = Queue()
    for png in png_files:
        q_png.put(png)
    for i in range(multiprocessing.cpu_count()):
        th = Thread(target=optimize_png, args=(q_png,))
        th.setDaemon(True)
        th.start()
    q_png.join()
    t_end = time.time()
    print("{} ↳ Done in {:.2f}s".format(common.COLOR_GREEN, (t_end - t_start)))

    # Optimize jpg
    jpg_files = common.walk_directory(path, lambda x: os.path.splitext(x)[1] in [".jpg", ".jpeg"])
    print(f"{common.COLOR_WHITE}[+] Optimizing {len(jpg_files)} JPEG files…")
    t_start = time.time()
    os.system(f"~/Dropbox/scripts/jpeg_optim.py -src {quote(args.src)} -ss")
    t_end = time.time()
    print("{} ↳ Done in {:.2f}s".format(common.COLOR_GREEN, (t_end - t_start)))

    # txz
    print(f"{common.COLOR_WHITE}[+] Compressing {path}")
    t_start = time.time()
    os.system(f'XZ_OPT="-T 0 -9" tar -Jcvf {quote(path + ".txz")} {quote(path)}')
    t_end = time.time()
    print("{} ↳ Done in {:.2f}s".format(common.COLOR_GREEN, (t_end - t_start)))
