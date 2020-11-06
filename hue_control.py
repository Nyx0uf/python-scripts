#!/usr/bin/env python3
# coding: utf-8

"""
Cycle Hue lamps color at random for an interval

config file example:

{
    "bridge": "192.168.13.37",
    "lamps": [
        {
            "name": "bla",
            "hours": [
                0,
                1,
                2,
                3,
                4,
                5,
                22,
                23
            ],
            "brightness": [127, 254],
            "interval": 2
        }
    ]
}

"""

import argparse
import datetime
import json
import os
import random
import socket
import sys
import threading
import time
from threading import Thread
from pathlib import Path
from typing import List, Tuple
from phue import Bridge # pip3 install phue
from utils import common

class HueLampConfig:
    """Represents a lamp with its cfg and light object"""
    def __init__(self, json_data):
        self.name = str(json_data["name"])
        self.brightness_min = common.clamp(int(json_data["brightness"][0]), 0, 254)
        self.brightness_max = common.clamp(int(json_data["brightness"][1]), 0, 254)
        self.hours: List[int] = json_data["hours"]
        self.interval = int(json_data["interval"])
        self.light = None
        self.managed = False

    def __str__(self):
        return f"{self.name}:{self.brightness_min}-{self.brightness_max}"

    def __repr__(self):
        return f"{self.name}:{self.brightness_min}-{self.brightness_max}"

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

def is_valid_ipv4_address(address: str) -> bool:
    """Check if address is a valid ip / hostname"""
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True

def rgb_to_xy(red: float, green: float, blue: float) -> List[float]:
    """
    conversion of RGB colors to CIE1931 XY colors
    Formulas implemented from: https://gist.github.com/popcorn245/30afa0f98eea1c2fd34d
    Args:
        red (float): a number between 0.0 and 1.0 representing red in the RGB space
        green (float): a number between 0.0 and 1.0 representing green in the RGB space
        blue (float): a number between 0.0 and 1.0 representing blue in the RGB space
    Returns:
        xy (list): x and y
    """

    # gamma correction
    red = pow((red + 0.055) / (1.0 + 0.055), 2.4) if red > 0.04045 else (red / 12.92)
    green = pow((green + 0.055) / (1.0 + 0.055), 2.4) if green > 0.04045 else (green / 12.92)
    blue =  pow((blue + 0.055) / (1.0 + 0.055), 2.4) if blue > 0.04045 else (blue / 12.92)

    # convert rgb to xyz
    x = red * 0.649926 + green * 0.103455 + blue * 0.197109
    y = red * 0.234327 + green * 0.743075 + blue * 0.022598
    z = green * 0.053077 + blue * 1.035763

    # convert xyz to xy
    x = x / (x + y + z)
    y = y / (x + y + z)

    return [x, y]

def random_rgb() -> Tuple[float, float, float]:
    """Returns a random RGB tuple, range 0.0—1.0"""
    r = random.random()
    g = random.random()
    b = random.random()
    return (r, g ,b)

def load_cfg(path: Path):
    """Open and load the configuration file (json)"""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    else:
        raise IOError(f"[!] {path} not found")

def th(lamp: HueLampConfig):
    """Thread"""
    print(f"[+] Starting {threading.current_thread().name}")
    while True:
        now = datetime.datetime.now()
        hour = int(now.hour)

        if hour in lamp.hours:
            lamp.managed = True
            lamp.light.on = True
            rgb = random_rgb()
            bright = random.randint(lamp.brightness_min, lamp.brightness_max)
            lamp.light.xy = rgb_to_xy(rgb[0], rgb[1], rgb[2])
            lamp.light.brightness = bright
            print(f"[{threading.get_ident()}] Setting {lamp.name} to color {rgb}[{bright}]")
        else:
            if lamp.managed is True:
                if lamp.light.on is True:
                    lamp.light.on = False
                lamp.managed = False
        time.sleep(lamp.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg", type=Path, help="Path to the configuration file")
    parser.add_argument("-l", "--list", dest="list", action="store_true", help="List all rooms and lamps and exit")
    args = parser.parse_args()

    # Sanity checks
    cfg = load_cfg(args.cfg)
    if is_valid_ipv4_address(cfg["bridge"]) is False:
        common.abort(f"[!] Invalid IP address {cfg['bridge']}")

    bridge = Bridge(cfg["bridge"])

    # Print rooms and lamps then exit
    if args.list is True:
        for group in bridge.groups:
            print(f"--- {group.name} ---")
            for light in group.lights:
                print(f"\t- {light.name} [{'on' if light.on is True else 'off'}]")
        sys.exit(0)

    lamps: List[HueLampConfig] = list(map(HueLampConfig, cfg["lamps"]))
    lights = bridge.lights
    for lamp in lamps:
        l = list(filter(lambda x: x.name == lamp.name, lights))
        if len(l) > 0:
            lamp.light = l[0]

    thread_to_join = None
    for lamp in lamps:
        th = Thread(target=th, args=(lamp,), name=str(f"th_{lamp.name}"), daemon=True)
        th.start()
        thread_to_join = th

    if thread_to_join:
        thread_to_join.join()
