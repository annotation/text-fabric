import sys

from .mylib import *


def transform():
    check_raw_files(part)
    process_lines(part)





if len(sys.argv) != 3:
    print('''
Usage:
text-fabric src dst

src: The Emdros mql source file
dst: The directory where the text-fabric conversion results are put
 (will be created if it does not exist)
''')
    sys.exit(1)
src = sys.argv[1]
dst = sys.argv[2]
em = Emdros()
prog_start = Timestamp()

print(prog_start.elapsed)
print("INFO: Start converting {} => {}".format(src, dst))
print("INFO: End converting {} => {}".format(src, dst))
print(prog_start.elapsed)
