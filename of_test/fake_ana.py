"""Interprets random data from h5 to h5. Must be run with Python 2."""
import argparse
import numpy as np
import tables as tb

################## MAIN ##################
parser = argparse.ArgumentParser()
parser.add_argument("input_file")
args = parser.parse_args()
out_fn = args.input_file[:-3] + "_hits.h5"

print("Opening %s" % args.input_file)

with tb.open_file(out_fn, "w") as oh5, tb.open_file(args.input_file) as ih5:
    desc = np.dtype([("col", "<u1"), ("row", "<u1")])
    hit_table = oh5.create_table(oh5.root, name="Hits", description=desc, title='hit_data')
    raw = ih5.root.raw_data[:]
    hit = np.empty(raw.shape, dtype=desc)
    hit['row'] = raw & 0xff
    hit['col'] = (raw >> 8)& 0x7f
    hit_table.append(hit)
    hit_table.flush()

print("Done")
