#!/usr/bin/env python2
"""Plots the .h5 file of a past acquisition, and allows to find noisy pixels."""
import argparse
import sys
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import numpy as np
import tables

COLOR = "\x1b[36m" if sys.stdout.isatty() else ""
RESET = "\x1b[0m" if sys.stdout.isatty() else ""


def get_log_spaced_bins(max_value):
    """Returns a list of log-spaced bin edges, such that max_value is included.

    For example, if max_value is 14, the function returns
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    """
    log_spaced_bins = [0.1, 1]
    for e in range(10):
        if 10**e > max_value:
            break
        for i in range(2, 11):
            log_spaced_bins.append(i * 10**e)
    return log_spaced_bins


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", help="The acquisition .h5 file.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", metavar="MIN_HITS", type=int, default=None,
                       help="Returns a list of pixels with more than MIN_HITS hits.")
    group.add_argument("-f", metavar="MIN_FREQ", type=float, default=None,
                       help="Returns a list of pixels with more than MIN_FREQ hits per second.")
    args = parser.parse_args()
    min_hits = args.n
    duration = 0

    # Reads hits from the h5 file (col, row and ToT)
    with tables.open_file(args.input_file) as input_file:
        hits_col = input_file.root.Hits.col("col")
        hits_row = input_file.root.Hits.col("row")
        hits_le = input_file.root.Hits.col("le")
        hits_te = input_file.root.Hits.col("te")
        try:
            duration = float(input_file.root.Hits.attrs.duration)
            if args.f is not None:
                min_hits = int(args.f * duration)
        except Exception:
            if args.f is not None:
                print("Missing duration attribute in the H5 file.")
                print("Please use -n instead of -f (see --help for details).")
    hits_tot = (hits_te - hits_le) & 0x3F
    del hits_le, hits_te

    fig, ax = plt.subplots(1, 2)

    # Plot the 2D histogram of the hits
    hist2d, _, _ = np.histogram2d(
        hits_col, hits_row, bins=[112,224], range=[[0,112],[0,224]])
    hist2d_img = ax[0].imshow(hist2d.transpose(), origin="lower", norm=LogNorm())
    ax[0].set_xlabel("Column")
    ax[0].set_ylabel("Row")
    colorbar = fig.colorbar(hist2d_img, ax=ax[0])
    colorbar.set_label("Hit count / pixel")

    # Plot the histogram of the number of hits per pixel, with log-scale x
    counts_per_pixel = hist2d.reshape(-1) + 0.1
    hist1d, hist1d_edges = np.histogram(
        counts_per_pixel, bins=get_log_spaced_bins(counts_per_pixel.max()))
    # Normalize by bin width
    hist1d = hist1d.astype(np.float) / np.ceil(hist1d_edges[1:] - hist1d_edges[:-1])
    ax[1].bar(hist1d_edges[:-1], hist1d, hist1d_edges[1:] - hist1d_edges[:-1], align='edge')
    ax[1].set_xlabel("Hits per pixel")
    ax[1].set_xscale('log')
    ax[1].set_ylabel("Pixel count / (1 hit)")
    ax[1].set_yscale('log')
    ax[1].grid(axis='y')

    # Return a list of noisy pixels
    if min_hits:
        if duration:
            print("List of noisy pixels (pixels with >= %d hits = %.3g hits/s)" % (min_hits, min_hits / duration))
        else:
            print("List of noisy pixels (pixels with >= %d hits)" % min_hits)
        print(COLOR + "NOISY_PIXELS = [")
        n = 0
        for col, row in zip(*np.nonzero(hist2d >= min_hits)):
            print("    (%d, %d)," % (col, row))
            n += 1
        print("]" + RESET)
        print("Number of noisy pixels = %s%d%s" % (COLOR, n, RESET))
        print("Use this code to set the mask to the pixels above:")
        print(COLOR + "chip.unmask_all()")
        print("for col, row in NOISY_PIXELS:")
        print("    chip.mask(chip.fl_n, col, row)")
        print("chip['CONF_SR'].write()" + RESET)

    plt.show()
