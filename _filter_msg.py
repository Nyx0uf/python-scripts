#!/usr/bin/env python3
# coding: utf-8

"""
get a list of outlook emails (.msg) matching an hour
"""

import os
import argparse
import multiprocessing
import queue
import datetime
import csv
from threading import Thread, Lock
from typing import Dict, List
import extract_msg
from utils import common

DAY_HOUR_MAP: Dict[str, str] = {
    'mon': '18',
    'wed': '17',
    'fri': '16',
}

LOCK = Lock()

def day_from_date(date: str) -> str:
    """Get 3 letters day from a date with format %a, %d %b %Y %H:%M:%S %z"""
    return date.split(',')[0].lower()

def is_interesting_day(day: str) -> bool:
    """lundi, mercredi, vendredi uniquement"""
    return day.lower() in ["mon", "wed", "fri"]

def contains_terms(message: str, terms: List[str]) -> bool:
    """Search for `terms` in `message`"""
    for term in terms:
        if term in message:
            return True
    return False

def th_filter(p_queue: queue.Queue, results: List[Dict[str, str]], errors: List[str], ignored_days: List[str], ignored_hours: List[str], terms: List[str]):
    """Filter thread"""
    while p_queue.empty() is False:
        infile = p_queue.get()
        filename = os.path.basename(os.path.normpath(infile))
        try:
            msg = extract_msg.Message(infile)
            date = msg.date
            day = day_from_date(date)
            if is_interesting_day(day) is True:
                max_hour = DAY_HOUR_MAP[day]
                mail_date = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
                if int(mail_date.hour) >= int(max_hour) and int(mail_date.minute) > 1:
                    if terms:
                        if contains_terms(msg.body.lower(), terms) is True:
                            ddd = {}
                            ddd[filename] = date
                            LOCK.acquire()
                            results.append(ddd)
                            LOCK.release()
                    else:
                        ddd = {}
                        ddd[filename] = date
                        LOCK.acquire()
                        results.append(ddd)
                        LOCK.release()
                else:
                    ignored_hours.append(filename)
            else:
                ignored_days.append(filename)
        except (IOError, TypeError):
            errors.append(filename)
        p_queue.task_done()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-src", action="store", dest="src", type=str, help="Directory containing emails")
    parser.add_argument("-csv", action="store", dest="output", type=str, default=None, help="Output file (csv)")
    parser.add_argument("-terms", action="store", dest="terms", type=str, default=None, help="Words to look for, comma separated (ex: work,car)")
    args = parser.parse_args()

    # Sanity checks
    if args.src is None:
        common.abort(parser.format_help())

    terms: List[str] = []
    if args.terms:
        terms = args.terms.strip().split(',')

    # Get a list of files (.msg) and queue it
    emails = common.walk_directory(os.path.abspath(args.src), lambda x: x.endswith(".msg"))
    queue = queue.Queue()
    for mail in emails:
        queue.put(mail)

    # Launch threads
    results: List[Dict[str, str]] = []
    errors: List[str] = []
    ignored_days: List[str] = []
    ignored_hours: List[str] = []
    for i in range(multiprocessing.cpu_count()):
        th = Thread(target=th_filter, args=(queue, results, errors, ignored_days, ignored_hours, terms,))
        th.daemon = True
        th.start()
    queue.join()

    print(f"{len(emails)} emails :")
    print(f"\t- {len(results)} matching results")
    print(f"\t- {len(errors)} errors")
    print(f"\t- {len(ignored_days)} ignored (mardi ou jeudi)")
    print(f"\t- {len(ignored_hours)} ignored (hour)")

    # Write to a csv
    if args.output is not None:
        csv_file = open(args.output if args.output.endswith(".csv") else f"{args.output}.csv", 'w')
        csv_writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for d in results:
            csv_writer.writerows(d.items())
        csv_file.close()
