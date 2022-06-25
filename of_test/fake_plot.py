"""Plots the analyzed data. Must be run with Python 3."""
import argparse
import numpy as np
import tables as tb
import matplotlib.pyplot as plt

################## MAIN ##################
parser = argparse.ArgumentParser()
parser.add_argument("input_file")
args = parser.parse_args()
out_fn = args.input_file[:-3] + ".png"

print(f"Opening {args.input_file}")

with tb.open_file(args.input_file) as f:
    hits = f.root.Hits[:]

plt.hist2d(hits["col"], hits["row"], bins=[112,224], range=[[0,112],[0,224]])
plt.colorbar(label="Hits")
plt.xlabel("Column")
plt.ylabel("Row")
plt.title(args.input_file)
plt.savefig(out_fn)

print("Done")
