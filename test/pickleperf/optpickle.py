import sys
import time
import gc
import pickletools

pVersion = sys.version_info[1]
jitRep = "yes" if pVersion == 14 and sys._jit.is_enabled() else "no"

with open("_temp/pickled", "rb") as fh:
    p = fh.read()


def opt():
    s = pickletools.optimize(p)
    len(s)


fh = open("results.md", "a")


def measure(gcEnabled=True):
    if gcEnabled:
        gc.enable()
    else:
        gc.disable()

    gcRep = "yes" if gcEnabled else "no"
    print(f"Python 3.{pVersion}, {jitRep} JIT, {gcRep} GC")

    tStart = time.perf_counter(), time.process_time()
    opt()
    tEnd = time.perf_counter(), time.process_time()

    fh.write(
        f"{pVersion} | {jitRep} | {gcRep} | "
        f"{tEnd[0] - tStart[0]:.3f} | {tEnd[1] - tStart[1]:.3f}\n"
    )


measure(gcEnabled=True)
measure(gcEnabled=False)
fh.close()
