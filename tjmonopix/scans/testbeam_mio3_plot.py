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
    # Set the maximum so that 98% of the pixels do not overflow
    hf = h.reshape(-1)
    m = np.ceil(np.quantile(hf[hf>0], 0.98) * 1.2)
    # Color in red pixels that overflow
    cm = mpl.cm.get_cmap('viridis')
    cm.set_bad('#ff3333')
    cm.set_over('#ff3333')
    plt.hist2d(tjm_hits["col"], tjm_hits["row"], bins=[112, 224], range=[[0, 112], [0, 224]],
               vmin=0, vmax=m, cmap=cm)
    plt.colorbar().set_label("Number of hits (red for out of scale)")
    plt.xlabel("Column")
    plt.ylabel("Row")
    plt.title("Hit map")
    plt.savefig(output_file + "_hitmap.png")
    plt.clf()
    # List pixels that overflow (may be useful for detecting noisy pixels)
    print("List of pixels with > %d hits" % m)
    print([(a, b) for a, b in np.argwhere(h > m)])

    # ToT histogram
    plt.hist((tjm_hits["te"] - tjm_hits["le"]) & 0x3f, bins=64, range=[0, 64])
    plt.xlabel("ToT [25 ns]")
    plt.ylabel("Hit count")
    plt.title("ToT")
    plt.grid(axis='y')
    plt.savefig(output_file + "_tot.png")
    plt.clf()

    # Hit delta-t histogram
    dt = np.diff(tjm_hits["timestamp"]) / 40
    # Set the maximum to include 98% of the samples
    m = np.ceil(np.quantile(dt, 0.98) * 1.2)
    plt.hist(dt, bins=100, range=[0, m])
    plt.xlabel("$\\Delta t$ between hits [$\\mu$s]")
    plt.ylabel("Count")
    plt.title("Interval between successive hits")
    plt.grid(axis='y')
    plt.yscale('log')
    plt.savefig(output_file + "_hit-dt.png")
    plt.clf()

    # Trigger delta-t histogram
    dt = np.diff(trg_hits["timestamp"]) / 640
    # Set the maximum to include 98% of the samples
    m = np.ceil(np.quantile(dt, 0.98) * 1.2)
    plt.hist(dt, bins=100, range=[0, m])
    plt.xlabel("$\\Delta t$ between triggers [$\\mu$s]")
    plt.ylabel("Count")
    plt.title("Interval between successive triggers")
    plt.grid(axis='y')
    plt.yscale('log')
    plt.savefig(output_file + "_trg-dt.png")
    plt.clf()

    # Divide hits by trigger
    trg_idxs = np.argwhere(~mask).reshape(-1)
    if len(trg_idxs) and trg_idxs[0] == 0:
        trg_idxs = trg_idxs[1:]
    if len(trg_idxs):
        tjm_hits_split = np.split(tjm_hits, trg_idxs - np.arange(len(trg_idxs)))
        # This is a list of pixel hits arrays

        # Number of hits per trigger
        n = np.fromiter((len(x) for x in tjm_hits_split), np.int32, len(tjm_hits_split))
        r = [np.floor(np.quantile(n, 0.02) * 0.8), np.ceil(np.quantile(n, 0.98) * 1.2)]
        plt.hist(n, bins=min(100, int(r[1] - r[0])), range=r)
        plt.xlabel("N. hits per trigger")
        plt.ylabel("Hits")
        plt.title("Hits per trigger")
        plt.grid(axis='y')
        plt.savefig(output_file + "_trg-cnt.png")
        plt.clf()
