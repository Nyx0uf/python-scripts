#!/usr/bin/env python3
# coding: utf-8

"""
logger
"""

class Singleton(type):
    """Singleton metaclass"""
    def __init__(cls, _name, bases, _dict):
        super(Singleton, cls).__init__(cls, bases, dict)
        cls._instanceDict = {}

    def __call__(cls, *args, **kwargs):
        argdict = {'args': args}
        argdict.update(kwargs)
        argset = frozenset(argdict)
        if argset not in cls._instanceDict:
            cls._instanceDict[argset] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instanceDict[argset]


class Logger():
    """Logger class"""
    __metaclass__ = Singleton

    def __init__(self, verbose: bool):
        self.verbose = verbose
        self.verboseprint = print if verbose is True else lambda *a, **k: None

    def log(self, msg):
        """like print function"""
        self.verboseprint(msg)
