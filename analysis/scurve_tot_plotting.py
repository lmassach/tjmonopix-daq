#python3 -i scurve_tot_plotting.py -f input_file_dir -o output_file.pdf -s
#NON MI RICORDO PIÙ A COSA SERVE QUESTO
import argparse
import tables as tb
import numpy as np
import os
import glob
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

from matplotlib.backends.backend_pdf import PdfPages
from scipy.special import erf

import functions
import plot_functions
import histograms_library
import utilities
import costants

description = ''
options_parser = argparse.ArgumentParser(description = description)
options_parser.add_argument('-input_file_dir', '-f', default=None, type=str, help='input_file_dir')
options_parser.add_argument('-output_file', '-o', default=None, type=str, help='output_dir')
options_parser.add_argument('-save_fig', '-s', default=False, action='store_true', help='save fig')

if __name__ == '__main__' :
    options = vars(options_parser.parse_args())
    input_file_dir = options['input_file_dir']
    output_file = options['output_file']
    save_fig = options['save_fig']

    param_file_list = glob.glob(input_file_dir + '2022*_fitparam_t*.npz')
    param_file_list.sort()
    data_file_list = glob.glob(input_file_dir + '2022*_cnts_tot_*.npz')
    data_file_list.sort()

    hist_dict = {}
    dict_keys = []
    for data_file, param_file in zip(data_file_list, param_file_list):
        print(data_file, param_file, '#')
        threshold = param_file[-8:-6]
        dict_keys.append(threshold)
        data = np.load(data_file)
        cnts = data['cnts']
        tot = data['tot']
        data = np.load(param_file)
        error_function_param = data['error_function_param']
        error_function_error = data['error_function_error']
        tot_calibration_param = data['tot_calibration_param']
        tot_calibration_parameters_err = data['tot_calibration_parameters_err']
        tot_calibrated_range = data['tot_calibrated_range_per_pixel']


        c, r, n, _, m, _, s, _, _, _, _, _ = np.loadtxt(param_file, unpack = True)
        opt = np.array([int(threshold), c, r, n, m ,s])
        hist_dict[str(threshold)] = [cnts, tot, opt]

    injlist = np.linspace(0, 40, 41)
    print(dict_keys)
    with PdfPages(output_file) as pdf:
        for col in range(0, costants.n_col):
            for row in range(0, costants.n_row):
                title = 'col, row: %d, %d' % (col, row)
                print(title)
                for key, fmt in zip(dict_keys, ['+r', '*b', '.g']):
                    cnts = hist_dict[key][0]
                    legend = 'th:' + key
                    plot_functions.scatter_plot(injlist, cnts[row][col][:], 'inj', '#',
                                    title = title, legend = legend, fmt=fmt)
                    qinj = np.linspace(injlist.min(), injlist.max(), 1000)
                    opt = hist_dict[key][2]
                    mask = (opt[1] == col) & (opt[2] == row)

                    #print(opt[0], opt[1])
                    n = opt[3][mask]
                    m = opt[4][mask]
                    s = opt[5][mask]
                    plt.plot(qinj, functions.err_func(qinj, n, m, s))

                pdf.savefig()
                plt.clf()

    plt.ion()
