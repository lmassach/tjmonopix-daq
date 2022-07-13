"""Plot script for testbeam_mio3."""
import argparse
import tables as tb
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', help="The _interpreted.h5 file produced by testbeam_mio3_analyze.py")
    args = parser.parse_args()

    # Output file name = input file name without the _interpreted.h5 suffix
    output_file = args.input_file[:-3]
    if output_file.endswith("_interpreted"):
        output_file = output_file[:-12]

    # Open input file and get the hits as a composite numpy array
    with tb.open_file(args.input_file) as f:
        hits = f.root.Hits[:]
    mask = hits["col"] < 224
    tjm_hits = hits[mask]  # Actual pixel hits
    trg_hits = hits[~mask]  # Trigger pulses

    # Hitmap
    h, _, _ = np.histogram2d(tjm_hits["col"], tjm_hits["row"], bins=[112, 224],
                             range=[[0, 112], [0, 224]])
    m = np.quantile(h.reshape(-1), 0.98)  # Set the maximum so that 98% of the pixels do not overflow
    m = np.ceil(m * 1.2)
    cm = mpl.cm.get_cmap('viridis')
    cm.set_bad('#ff3333')
    cm.set_over('#ff3333')  # Color in red pixels that overflow
    plt.hist2d(tjm_hits["col"], tjm_hits["row"], bins=[112, 224], range=[[0, 112], [0, 224]],
               vmin=0, vmax=m, cmap=cm)
    plt.colorbar().set_label("Number of hits (red for out of scale)")
    plt.xlabel("Column")
    plt.ylabel("Row")
    plt.title("Hit map")
    plt.savefig(output_file + "_hitmap.png")
