#python3 -i calibration/scurve_tot_histo.py -f calibration/calibration_data/20220506 -i 1 100
import argparse
import tables as tb
import numpy as np
import os
import glob
from scipy.optimize import curve_fit
import time
import itertools

import functions
import histograms_library
import utilities
import costants

""" This script creates the histogram file .npz (faster than .h5) of the counts and of the average tot.
    This data can be used to fit the line and the scurve.
    It saves the average tot calculated in each bin of injection charge with and without the cut related to the rollover.
    The cut is a line with parameters slope=0.833, intercept=-43.
    To see the cut in the tot-space run 'tot_histo2d.py'.
"""

options_parser = argparse.ArgumentParser(description = '')
options_parser.add_argument('-input_file_data', '-f', default=None, type=str, help='input_file')
options_parser.add_argument('-injlist', '-i', default=None, type=int, nargs = '+', help='injlist')

if __name__ == '__main__' :
    start_time = time.time()
    options = vars(options_parser.parse_args())
    input_file_data = options['input_file_data']
    injlist = utilities.convert_option_list(options['injlist'])

    param = [0.833, -43]

    input_file = glob.glob(input_file_data + '*ev.h5') [0]
    print("Reading files %s ... %s" % (input_file, time.time() - start_time))
    fev = tb.open_file(input_file, "r")
    col = fev.root.Hits.col("col")
    row = fev.root.Hits.col("row")
    inj = fev.root.Hits.col("inj")
    tot = fev.root.Hits.col("tot")
    threshold = np.unique(fev.root.Hits.col("th"))

    print("Creating output file ...   %s seconds " % (time.time() - start_time))
    output_file_data = input_file + '_cnts_tot_t%d.npz' % threshold
    output_file_fitparam = input_file + '_fitparam_t%d.npz' % threshold

    evt_per_chunk = 1.e+6
    n_chunk = int(len(tot)/evt_per_chunk)
    print('%d chunk of %d events per chunk ... %s' % (n_chunk, evt_per_chunk, time.time()-start_time))

    cnts = np.full((costants.n_row, costants.n_col, injlist.max()-injlist.min()+1), 0)
    average_tot = np.full((costants.n_row, costants.n_col, injlist.max()-injlist.min()+1), 0)
    cnts_cutted = np.full((costants.n_row, costants.n_col, injlist.max()-injlist.min()+1), 0)
    average_cutted_tot = np.full((costants.n_row, costants.n_col, injlist.max()-injlist.min()+1), 0)

    print("creating histograms ...   %s seconds " % (time.time() - start_time))
    for n in range(0, n_chunk+1):
        print('chunk %d of %d ... %s' % (n, n_chunk, time.time()-start_time))
        min_index = int(n * evt_per_chunk)
        max_index = int((n + 1) * evt_per_chunk)
        chunked_row = row[min_index:max_index]
        chunked_col = col[min_index:max_index]
        chunked_tot =  tot[min_index:max_index]
        chunked_inj = inj[min_index:max_index]
        cnts_per_chunk = histograms_library.create_scurve_hist(chunked_row, chunked_col,
                                    chunked_inj, injlist.min(), injlist.max())
        total_tot_per_chunk = histograms_library.create_scurve_tot(chunked_row, chunked_col,
                                    chunked_inj, chunked_tot, injlist.min(), injlist.max())
        cnts = cnts + cnts_per_chunk
        average_tot_per_chunk = total_tot_per_chunk/cnts_per_chunk
        average_tot_per_chunk[cnts_per_chunk == 0] = 0
        average_tot = average_tot + average_tot_per_chunk

        for i in range(80, 101):
            cut_mask = (chunked_tot > (i * param[0] + param[1])) * (chunked_inj == i)
            cnts_cutted_per_chunk = histograms_library.create_scurve_hist(chunked_row[cut_mask], chunked_col[cut_mask],
                                        chunked_inj[cut_mask], injlist.min(), injlist.max())
            total_cutted_tot_per_chunk = histograms_library.create_scurve_tot(chunked_row[cut_mask], chunked_col[cut_mask],
                                        chunked_inj[cut_mask], chunked_tot[cut_mask], injlist.min(), injlist.max())
            rms_tot_per_chunk = histograms_library.create_scurve_tot(chunked_row[cut_mask], chunked_col[cut_mask],
                                        chunked_inj[cut_mask], chunked_tot[cut_mask], injlist.min(), injlist.max())

            cnts_cutted = cnts_cutted + cnts_cutted_per_chunk
            average_cutted_tot_per_chunk = total_cutted_tot_per_chunk/cnts_cutted_per_chunk
            average_cutted_tot_per_chunk[cnts_cutted_per_chunk == 0] = 0
            average_cutted_tot = average_cutted_tot + average_cutted_tot_per_chunk

    cnts_cutted[:, :, 0:80] = cnts[:, :, 0:80]
    average_cutted_tot[:, :, 0:80] = average_tot[:, :, 0:80]

    print("Writing histograms file %s ...   %s seconds " % (output_file_data, time.time() - start_time))
    np.savez(output_file_data, cnts = cnts, tot = average_tot, cnts_cutted = cnts_cutted, tot_cutted = average_cutted_tot)
