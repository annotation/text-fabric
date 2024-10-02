import sys

from .mylib import *
from .settings import Settings
from .etcbc import Etcbc
from .laf import Laf
from .validate import Validate
from .transform import Transform

def init():
    global settings, val, et, lf, tr, prog_start, task_start
    settings = Settings()
    val = Validate(settings)
    et = Etcbc(settings)
    lf = Laf(settings, et, val)
    tr = Transform(settings, et, lf)
    prog_start = Timestamp()
    task_start = Timestamp()
def dotask(part):    
    print("INFO: Start Task {}".format(part))
    task_start = Timestamp()
    tr.transform(part)
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
    print("INFO: End Task {}".format(part))
def final():
    task_start = Timestamp()
    lf.makeheaders()
    val.validate()
    val.report()
    lf.report()
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
def processor():
    init()
    print("{} - {}".format(prog_start.elapsed(), task_start.elapsed()))
    print("INFO: Doing parts: {}".format(','.join(settings.given_parts)))
    for part in settings.given_parts: dotask(part)
    final()
