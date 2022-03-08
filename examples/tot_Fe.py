import tables as tb
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import argparse

description = ''
options_parser = argparse.ArgumentParser(description = description)
options_parser.add_argument('-input_file', '-f', default=None, type=str, nargs ='+', help='input_file')

if __name__ == '__main__' :
    options = vars(options_parser.parse_args())
    input_file_list = options['input_file']

    for i, input_file in enumerate(input_file_list):
        f = tb.open_file(input_file, "r")
        col = f.root.Hits.col("col")
        row = f.root.Hits.col("row")
        le = f.root.Hits.col("le")
        te = f.root.Hits.col("te")
        duration = f.root.Hits.attrs["duration"]

        tot = (te - le)&0x3F
        tot = tot[tot>10]
        range = (0, 60)
        n_bins = max(range)-min(range)+1
        plt.yscale('log')
        legend = '%d hits in %d sec' % (len(tot), int(duration))
        n, bins, patches = plt.hist(tot, bins = n_bins, range = range, label = legend, alpha = 0.4)


    plt.show()
    plt.ion()
