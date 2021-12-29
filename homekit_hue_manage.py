#!/usr/bin/env python3
# coding: utf-8

"""
bla
"""

import argparse
import sys
import time
from typing import List, Dict
from phue import Bridge  # pip3 install phue

TIME_TO_SLEEP: int = 10
TIME_TO_KILL: int = 60 * 5
LIGHTS_TO_WATCH: List[str] = [
    "Lampe toilettes haut",
    "Lampe toilettes bas"
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str, help="Hue bridge IP address")
    args = parser.parse_args()

    bridge = Bridge(args.ip)

    lights = list(filter(lambda x: x.name in LIGHTS_TO_WATCH, bridge.lights))
    if len(lights) == 0:
        sys.exit(0)

    # Initialize state
    status: Dict[str, int] = {}
    for l in lights:
        status[l.name] = 0

    while True:
        for light in lights:
            if light.on is True:
                #print(f"{light.name} is on")
                status[light.name] += TIME_TO_SLEEP
            else:
                status[light.name] = 0
            # If lamp still on after `TIME_TO_KILL`, change state
            if status[light.name] >= TIME_TO_KILL:
                #print(f"{light.name} has been on for {status[light.name]}s, shutting down.")
                light.on = False
        time.sleep(TIME_TO_SLEEP)
