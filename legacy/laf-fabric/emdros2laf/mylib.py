import sys,os
import datetime
import time
import subprocess
import pprint

pp = pprint.PrettyPrinter(indent = 4)

def pretty(data): pp.pprint(data)
def camel(text):
    words = text.split(" ")
    return ''.join(words[x].capitalize() if x > 0 else words[x] for x in range(len(words)))
def fillup(size, val, lst): return tuple(lst[x] if x < len(lst) else val for x in range(size)) 
def today(): return datetime.date.today()
def run(cmd, dyld=False):
    if dyld:
        result = subprocess.check_call(
            'export DYLD_LIBRARY_PATH=$DYLDLIBRARYPATH; '+cmd+' 2>&1', shell=True, env=dict(os.environ, DYLDLIBRARYPATH=os.environ.get('DYLD_LIBRARY_PATH', '')),
        )
    else:
        result = subprocess.check_call(cmd+' 2>&1', shell=True)
    return result
    # subprocess.check_call(cmd + ' 2>&1', shell = True)

def runx(cmd, dyld=False):
    if dyld:
        result = subprocess.call(
            'export DYLD_LIBRARY_PATH=$DYLDLIBRARYPATH; '+cmd+' 2>&1', shell=True, env=dict(os.environ, DYLDLIBRARYPATH=os.environ.get('DYLD_LIBRARY_PATH', '')),
        )
    else:
        result = subprocess.call(cmd+' 2>&1', shell=True)
    return result
    # subprocess.call(cmd + ' 2>&1', shell = True)

class Timestamp():
    timestamp = None
    def __init__(self): self.timestamp = time.time()
    def elapsed(self):
        interval = time.time() - self.timestamp
        if interval < 10: return "{: 2.2f}s".format(interval)
        interval = int(round(interval))
        if interval < 60: return "{:>2d}s".format(interval)
        if interval < 3600: return "{:>2d}m {:>02d}s".format(interval // 60, interval % 60)
        return "{:>2d}h {:>02d}m {:>02d}s".format(interval // 3600, (interval % 3600) // 60, interval % 60)
    def progress(self, msg):
        print("{} {}".format(self.elapsed(), msg))
        sys.stdout.flush()

