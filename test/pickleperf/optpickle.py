import sys
import time
import gc
import pickletools

pVersion = sys.version_info[1]
jitRep = "+" if pVersion == "14" and sys._jit.is_enabled() else "-"

with open("_temp/pickled", "rb") as fh:
    p = fh.read()


def opt():
    s = pickletools.optimize(p)
    len(s)


def measure(gcEnabled=True):
    if gcEnabled:
        gc.enable()
    else:
        gc.disable()

    tStart = time.perf_counter(), time.process_time()
    opt()
    tEnd = time.perf_counter(), time.process_time()

    gcRep = "+" if gcEnabled else "-"

    print(f"{pVersion} | {jitRep} | {gcRep} | {tEnd[0] - tStart[0]:.3f} | {tEnd[1] - tStart[1]:.3f}")


print(f"{sys.version=}")
print("""Python version | JIT enabled | GC enabled | Real (s)| CPU (s)""")
print("""--- | --- | --- | --- | ---""")

measure(gcEnabled=True)
measure(gcEnabled=False)
