#python3 -i calibration/tot_charge_plotting.py -f calibration/calibration_data/20220506
import argparse
import numpy as np
import matplotlib.pyplot as plt
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
import time

inj_min = 1
inj_max = 100
cnt_max = 120
tot_max = 64
cut = 80
delta_residuals = 2

"""This scipt saves the plots of the scurve and the tot vs Qinj.
"""

def scurve_tot_plot(cnts, tot, opt_errf, pcov_errf, opt_line, pcov_line, opt_2ord='', pcov_2ord='', opt_line1p='',
                    pcov_line1p='', title = '', inj_min = inj_min, inj_max = inj_max, cnt_max = cnt_max,
                    tot_max = tot_max, save = True, pol_2ord = False, line1p = False):

    legend_erf = plot_functions.fit_legend(param_values = opt_errf, param_errors = pcov_errf,
                      param_names = ['norm', 'mean', 'sigma'],
                     param_units = ['#', 'dac', 'dac'], chi2 = None, ndof = None)
    legend_line = plot_functions.fit_legend(param_values = opt_line, param_errors = pcov_line,
                      param_names = ['slope', 'q'],
                     param_units = ['ua/dac', 'ua'], chi2 = None, ndof = None)
    if pol_2ord == True:
        legend_2ord = plot_functions.fit_legend(param_values = opt_2ord,
                        param_errors = pcov_2ord, param_names = ['a', 'b', 'c'],
                         param_units = ['ua/dac^2', 'ua/dac', 'ua'], chi2 = None, ndof = None)
    if line1p == True:
        legend_line1p = plot_functions.fit_legend(param_values=opt_line1p, param_errors = pcov_line1p,
                    param_names = ['slope'], param_units=['ua/dac'], chi2 = None, ndof = None )


    injlist = np.linspace(inj_min, inj_max, (inj_max - inj_min + 1))
    qinj = np.linspace(inj_min, inj_max, 1000)

    fig, ax = plt.subplots(1,1, figsize=(8, 7))
    ax.plot(injlist, cnts, "C0o")
    ax.plot(qinj, functions.err_func(qinj, *opt_errf), '-b', label = legend_erf)
    ax.set_ylim(0, cnt_max)
    ax.set_xbound(inj_min, inj_max)
    ax.set_xlabel("Injection [DAC]")
    ax.set_ylabel("Counts")
    ax2 = ax.twiny()
    ax3 = ax.twinx()
    ax3.plot(injlist, tot, "or")
    ax3.plot(qinj, functions.line(qinj, *opt_line), 'C1-', label = legend_line)
    if pol_2ord == True:
        ax3.plot(qinj, functions.pol_2order(qinj, *opt_2ord), '-g', label = legend_2ord)
    if line1p == True:
        ax3.plot(qinj, functions.line1p(qinj-opt_errf[1], *opt_line1p), '-m', label = legend_line1p)

    ax3.set_xbound(inj_min, inj_max)
    ax3.set_ylim(0, tot_max)
    ax3.set_ylabel("ToT [ua = 25 ns]")
    ax2.set_xlabel("Charge [e]")
    ax2.set_xbound(inj_min*costants.CAP, inj_max*costants.CAP)
    ax.legend(loc = 'upper left')
    ax3.legend(loc='lower right')
    plt.suptitle(title, fontsize=12)
    if save == True:
        pdf.savefig()
        plt.cla()
        plt.close(fig)
    return

def residuals_plot(tot, opt_line, opt_2ord, opt_line1p, threshold, inj_min = inj_min, inj_max = inj_max, title = ''):
    injlist = np.linspace(inj_min, inj_max, (inj_max - inj_min + 1))
    fig, ax = plt.subplots(1,1, figsize=(8, 7))
    ax.errorbar(injlist, tot - functions.line(injlist, *opt_line), yerr = 0.1, fmt= "C1.", label = 'line 2 parameters')
    ax.set_xlabel("Injection [DAC]")
    ax.set_ylabel("Line residuals")
    ax.set_ylim(-delta_residuals, +delta_residuals)
    ax2 = ax.twiny()
    ax3 = ax.twinx()
    ax3.set_ylabel("2nd order pol residuals")
    ax2.set_xlabel("Charge [e]")
    ax2.set_xbound(inj_min*costants.CAP, inj_max*costants.CAP)
    ax3.errorbar(injlist, tot - functions.pol_2order(injlist, *opt_2ord), yerr=0.1, fmt=".g", label = '2nd order polynomial')
    ax3.errorbar(injlist, tot - functions.line1p(injlist-threshold, opt_line1p), yerr=0.1, fmt=".m", label = 'line 1 parameter')
    ax.legend(loc='upper right')
    ax3.legend(loc = 'lower center')
    ax3.set_ylim(-delta_residuals, +delta_residuals)
    plt.title(title, fontsize=12, loc='right')
    return


if __name__ == '__main__' :
    description = 'Please enter: -f <input file> - o <output file dir> '
    options_parser = argparse.ArgumentParser(description = description)
    options_parser.add_argument('-input_file_data', '-f', default=None, type=str, help='data of the selected input file')
    options_parser.add_argument('-output_file', '-o', default=None, type=str, help='output_file')
    options_parser.add_argument('-col', '-c', default=None, type=int, help='colum of the pixel selected')
    options_parser.add_argument('-row', '-r', default=None, type=int, help='row of the pixel selected')

    options = vars(options_parser.parse_args())
    start_time = time.time()
    input_file_data = options['input_file_data']
    output_file = options['output_file']
    c = options['col']
    r = options['row']

    print("Opening and reading file ...   %s seconds " % (time.time() - start_time))
    input_file_param = glob.glob(input_file_data + '*fit*.npz' )[0]
    input_file_datas = glob.glob(input_file_data + '*cnts_tot_*.npz' )[0]
    threshold = input_file_param[-6:-4]
    data = np.load(input_file_param)
    histograms = np.load(input_file_datas)
    cnts = histograms['cnts']
    tot = histograms['tot_cutted']

    if (c == None) * (r == None):
        if output_file == None:
            output_file = input_file + '_scurve_t' + str(threshold) + '.pdf'
        print("Saving plot for every pixel ...   %s seconds " % (time.time() - start_time))
        with PdfPages(output_file) as pdf:
            for c in range(4, costants.n_row):
                for r in range(0, costants.n_row):
                    title = "idb = %s DAC, col, row: %d, %d" % (threshold, c, r)
                    print(title + '... %s' %(time.time() -start_time))
                    opt_errf = np.array([data['error_function_param'][r][c][0],  data['error_function_param'][r][c][1],  data['error_function_param'][r][c][2]])
                    pcov_errf = np.array([data['error_function_error'][r][c][0], data['error_function_error'][r][c][1], data['error_function_error'][r][c][2]])
                    opt_line = np.array([data['tot_cal_line_param'][r][c][0], data['tot_cal_line_param'][r][c][1]])
                    pcov_line = np.array([data['tot_cal_line_param_err'][r][c][0], data['tot_cal_line_param_err'][r][c][1]])
                    scurve_tot_plot(cnts[r][c][:-1], tot[r][c][:-1], opt_errf, pcov_errf, opt_line, pcov_line, inj_min = 1, inj_max = len(cnts[r][c][:-1]), title=title, save = True)

    if (c != None) * (r != None):
        title = "idb = %s DAC, col, row: %d, %d " % (threshold, c, r)
        print("idb = %s DAC, col, row: %d, %d ... %s" % (threshold, c, r, time.time() - start_time))
        opt_errf = np.array([data['error_function_param'][r][c][0],  data['error_function_param'][r][c][1],  data['error_function_param'][r][c][2]])
        pcov_errf = np.array([data['error_function_error'][r][c][0], data['error_function_error'][r][c][1], data['error_function_error'][r][c][2]])
        opt_line1p = data['tot_cal_line1p_param'][r][c]
        pcov_line1p = data['tot_cal_line1p_param_err'][r][c]
        opt_line = np.array([data['tot_cal_line_param'][r][c][0], data['tot_cal_line_param'][r][c][1]])
        pcov_line = np.array([data['tot_cal_line_param_err'][r][c][0], data['tot_cal_line_param_err'][r][c][1]])
        opt_2ord = np.array([data['tot_cal_2ord_param'][r][c][0],  data['tot_cal_2ord_param'][r][c][1],  data['tot_cal_2ord_param'][r][c][2]])
        pcov_2ord = np.array([data['tot_cal_2ord_param_err'][r][c][0], data['tot_cal_2ord_param_err'][r][c][1], data['tot_cal_2ord_param_err'][r][c][2]])

        scurve_tot_plot(cnts[r][c][:-1], tot[r][c][:-1], opt_errf, pcov_errf, opt_line, pcov_line, opt_2ord, pcov_2ord,
                        opt_line1p, pcov_line1p, inj_min = 1, inj_max = len(cnts[r][c][:-1]), title=title, save = False, pol_2ord = True, line1p = True)
        residuals_plot(tot[r][c][:], opt_line, opt_2ord, opt_line1p, threshold=opt_errf[1], inj_min=1, inj_max= len(cnts[r][c][:]), title = title)
        plt.axvline(x= np.argwhere(tot[r][c][1:]>0).min(), color = 'k', linestyle ='dashed')
        plt.show()
    plt.ion()
