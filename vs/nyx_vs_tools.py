#!/usr/bin/env python3
# coding: utf-8

"""
Vapoursynth functions
"""

#pylint: disable=no-name-in-module
#pylint: disable=too-many-arguments
#pylint: disable=too-many-locals

import functools
from vapoursynth import core, VideoNode, YUV, GRAY
import numpy as np
#import vsTAAmbk as taa

def eedi3nnedi3Scale(input_clip: VideoNode, width: int = 1280, height: int = 720, eedi3_mode: str = 'cpu', nnedi3_mode: str = 'cpu', device: int = -1, pscrn: int = 1, alpha: float = 0.2, beta: float = 0.25, gamma: float = 1000.0) -> VideoNode:
    """Some eedi3-based upscale function. Luma will be upscaled with eedi3+nnedi3 filters, chroma with nnedi3, taken from https://github.com/DJATOM/VapourSynth-atomchtools/blob/master/atomchtools.py"""
    def nnedi3_superclip(clip: VideoNode, nnedi3Mode: str = 'cpu', device: int = -1, pscrn: int = 1, dw: bool = False):
        if dw and nnedi3Mode != 'opencl':
            step   = core.nnedi3.nnedi3(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn)
            rotate = core.std.Transpose(step)
            step  = core.nnedi3.nnedi3(rotate, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn)
            return core.std.Transpose(step)
        if nnedi3Mode == 'opencl':
            return core.nnedi3cl.NNEDI3CL(clip, field=1, dh=True, dw=dw, nsize=0, nns=4, pscrn=pscrn, device=device)
        elif nnedi3Mode == 'znedi3':
            return core.znedi3.nnedi3(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn)
        else:
            return core.nnedi3.nnedi3(clip, field=1, dh=True, nsize=0, nns=4, pscrn=pscrn)

    def eedi3_instance(clip: VideoNode, eedi3_mode: str = 'cpu', nnedi3_mode: str = 'cpu', device: int = -1, pscrn: int = 1, alpha: float = 0.2, beta: float = 0.25, gamma: float = 1000.0):
        if eedi3_mode == 'opencl':
            return core.eedi3m.EEDI3CL(clip, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, sclip=nnedi3_superclip(clip, nnedi3_mode, device, pscrn), device=device)
        return core.eedi3m.EEDI3(clip, field=1, dh=True, alpha=alpha, beta=beta, gamma=gamma, vcheck=3, sclip=nnedi3_superclip(clip, nnedi3_mode, device, pscrn))

    w = input_clip.width
    h = input_clip.height
    if isinstance(device, int):
        luma_device, chroma_device = device, device
    elif len(device) == 2:
        luma_device, chroma_device = device
    else:
        raise ValueError("eedi3nnedi3Scale: 'device' must be single int value or tuple with 2 int values")
    ux = w * 2
    uy = h * 2
    if input_clip.format.num_planes == 3:
        cw = width >> input_clip.format.subsampling_w
        cy = height >> input_clip.format.subsampling_h

    Y = core.std.ShufflePlanes(input_clip, 0, GRAY)
    if input_clip.format.num_planes == 3:
        U = core.std.ShufflePlanes(input_clip, 1, GRAY)
        V = core.std.ShufflePlanes(input_clip, 2, GRAY)
    Y = eedi3_instance(Y, eedi3_mode, nnedi3_mode, luma_device, pscrn, alpha, beta, gamma)
    Y = core.std.Transpose(Y)
    Y = eedi3_instance(Y, eedi3_mode, nnedi3_mode, luma_device, pscrn, alpha, beta, gamma)
    Y = core.std.Transpose(Y)
    Y = core.resize.Spline36(Y, width, height, src_left=-0.5, src_top=-0.5, src_width=ux, src_height=uy)
    if input_clip.format.num_planes == 3:
        U = core.resize.Spline36(nnedi3_superclip(U, device=chroma_device, pscrn=pscrn, dw=True), cw, cy, src_left=-0.25, src_top=-0.5)
        V = core.resize.Spline36(nnedi3_superclip(V, device=chroma_device, pscrn=pscrn, dw=True), cw, cy, src_left=-0.25, src_top=-0.5)
        return core.std.ShufflePlanes([Y, U, V], [0, 0, 0], YUV)
    else:
        return Y

def adaptive_grain(clip: VideoNode, source: VideoNode = None, strength: float = 0.25, static: bool = True, luma_scaling: float = 10.0, show_mask: bool = False) -> VideoNode:
    """Adaptive grain"""
    def fill_lut(y: float):
        x = np.arange(0, 1, 1 / (1 << src_bits))
        z = (1 - (1.124 * x - 9.466 * x ** 2 + 36.624 * x ** 3 - 45.47 * x ** 4 + 18.188 * x ** 5)) ** (
            (y ** 2) * luma_scaling) * ((1 << src_bits) - 1)
        z = np.rint(z).astype(int)
        return z.tolist()

    def generate_mask(n, clip: VideoNode):
        frameluma = round(clip.get_frame(n).props.PlaneStatsAverage * 999)
        table = lut[int(frameluma)]
        return core.std.Lut(clip, lut=table)

    if source is None:
        source = clip
    if clip.num_frames != source.num_frames:
        raise ValueError("The length of the filtered and unfiltered clips must be equal")
    source = core.fmtc.bitdepth(source, bits=8)
    src_bits = 8
    clip_bits = clip.format.bits_per_sample

    lut = [None] * 1000
    for y in np.arange(0, 1, 0.001):
        lut[int(round(y * 1000))] = fill_lut(y)

    luma = core.std.ShufflePlanes(source, 0, GRAY)
    luma = core.std.PlaneStats(luma)
    grained = core.grain.Add(clip, var=strength, constant=static)

    mask = core.std.FrameEval(luma, functools.partial(generate_mask, clip=luma))
    mask = core.resize.Bilinear(mask, clip.width, clip.height)

    if src_bits != clip_bits:
        mask = core.fmtc.bitdepth(mask, bits=clip_bits)

    if show_mask:
        return mask

    return core.std.MaskedMerge(clip, grained, mask)

def flow_fps(clip: VideoNode) -> VideoNode:
    """Smooth video"""
    sup = core.mv.Super(clip, pel=2, hpad=0, vpad=0)
    bvec = core.mv.Analyse(sup, blksize=8, isb=True, chroma=True, search=3, searchparam=1)
    fvec = core.mv.Analyse(sup, blksize=8, isb=False, chroma=True, search=3, searchparam=1)
    clip = core.mv.FlowFPS(clip, sup, bvec, fvec, num=0, den=0, mask=2)
    return clip
