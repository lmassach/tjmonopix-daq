#!/usr/bin/env python2
"""Plots the .h5 file of a past acquisition, and allows to find noisy pixels."""
import argparse
import sys
from matplotlib.colors import LogNorm
import matplotlib.pyplot as plt
import numpy as np
import tables


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
    args = parser.parse_args()

    # Reads hits from the h5 file (col, row and ToT)
    with tables.open_file(args.input_file) as input_file:
        hits_col = input_file.root.Hits.col("col")
        hits_row = input_file.root.Hits.col("row")
        hits_le = input_file.root.Hits.col("le")
        hits_te = input_file.root.Hits.col("te")
    hits_tot = (hits_te - hits_le) & 0x3F
    del hits_le, hits_te

    # Allow opening plots while the script is still running
    plt.ion()
    fig, ax = plt.subplots(1, 2)
    # Terminate script when the figure is closed
    fig.canvas.mpl_connect('close_event', lambda evt: sys.exit())

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

    # Allow the figure to redraw
    while True:
        plt.pause(2)
