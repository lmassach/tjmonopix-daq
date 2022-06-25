"""Generates random data in h5 format. Must be run with Python 2."""
import datetime
import os
import time
import numpy as np
import tables as tb

################## MAIN ##################
if not os.path.isdir("output_data"):
    os.mkdir("output_data")

now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
rt = np.random.randint(5, 10)  # Seconds to run
print(now)
print("Running for %d seconds" % rt)

h5_file = tb.open_file("output_data/" + now + '_scan.h5', mode="w", title="")
raw_data_earray = h5_file.create_earray(
    h5_file.root,
    name="raw_data",
    atom=tb.UIntAtom(),
    shape=(0,),
    title="Raw data",
    filters=tb.Filters(complib="blosc", complevel=5, fletcher32=False))

for i in range(rt):
    print(i)
    l = np.random.randint(100, 200)
    col = np.random.randint(0, 112, size=l)
    row = np.random.randint(0, 224, size=l)
    raw = (col << 8) | row
    raw_data_earray.append(raw)
    raw_data_earray.flush()
    time.sleep(1)

print("Closing output file")
h5_file.close()
