import os
import pickle

x = {i: f"ii{i:>07}" for i in range(1, 1000000)}

if not os.path.exists("_temp"):
    os.makedirs("_temp")

with open("_temp/pickled", "wb") as fh:
    pickle.dump(x, fh, protocol=4)
