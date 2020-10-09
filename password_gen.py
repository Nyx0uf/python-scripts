#!/usr/bin/env python3
# coding: utf-8

"""
Generate a random password of a given length
"""

import argparse
import string
import random
from typing import List
from utils import common

MIN_PASSWORD_LENGTH = int(8)
MAX_PASSWORD_LENGTH = int(128)
DEFAULT_PASSWORD_LENGTH = int(16)

def generate_password(charset: List[str], length: int) -> str:
    """Generate the password from the charset"""
    randomized = list(charset)
    random.shuffle(randomized)
    password = random.choices(randomized, k=length)
    return "".join(password)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--length", dest="length", type=int, default=DEFAULT_PASSWORD_LENGTH, help="Length of the password")
    parser.add_argument("-u", "--no-uppercase", dest="uppercase", action="store_false", help="Do not include uppercase letters")
    parser.add_argument("-n", "--no-numbers", dest="numbers", action="store_false", help="Do not include numbers")
    parser.add_argument("-s", "--no-symbols", dest="symbols", action="store_false", help="Do not include symbols")
    args = parser.parse_args()

    charset = string.ascii_lowercase
    if args.uppercase is True:
        charset += string.ascii_uppercase
    if args.numbers is True:
        charset += string.digits
    if args.symbols is True:
        charset += string.punctuation

    password = generate_password(charset, common.clamp(args.length, MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH))

    print(password)
