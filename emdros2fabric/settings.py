import os
import sys
import collections
import glob

import configparser
import argparse

NAME = 'Text-Fabric'
VERSION = '0.0.0'
APIREF = 'http://text-fabric.readthedocs.org/en/latest/texts/API-reference.html'

class Settings:
    def __init__(self):
        print('This is {} {}\n{}'.format(NAME, VERSION, APIREF))

        argsparser = argparse.ArgumentParser(description = 'Conversion of Emdros to LAF')
        argsparser.add_argument(
            '--src',
            nargs = 1,
            type = str,
            metavar = 'Source',
            help = 'Emdros mql source file',
        )
        argsparser.add_argument(
            '--dst',
            nargs = 1,
            type = str,
            metavar = 'Destination',
            help = 'Text-Fabric result directory',
        )
