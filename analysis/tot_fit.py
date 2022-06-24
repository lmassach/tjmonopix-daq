#python3 -i calibration/tot_fit.py -f calibration/calibration_data/20220506_cnts_tot_t40 -i 1 100

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

"""This script used the histgrams of the cnts and the average tot save by scurve_tot_histo.py and fit the scurve and the tot vs Qinj relation.
    To perform the fit the script used the data cutted data: it exludes the rollover-data.
    The tot vs Qinj datas are fitted both with a line and with a 2nd order polynomial function.
    The fit parameters are saved on an .npz file as a map on the matrix (ex: the slope of the pixel c 3, r 100 is saved as:
    line_parameters[100][3][0], while the intercept: line_parameters[100][3][1])
"""

options_parser = argparse.ArgumentParser(description = '')
options_parser.add_argument('-input_file_data', '-f', default=None, type=str, help='input_file')
options_parser.add_argument('-injlist', '-i', default=None, type=int, nargs = '+', help='injlist')

if __name__ == '__main__' :
    start_time = time.time()
    options = vars(options_parser.parse_args())
    input_file_data = options['input_file_data']
    injlist = utilities.convert_option_list(options['injlist'])


    input_file = glob.glob(input_file_data + '*cnts_tot_t*.npz')[0]
    threshold = input_file[-2:]
    data = np.load(input_file)
    cnts = data['cnts']
    tot = data['tot_cutted']

    errf_parameters =  np.full((costants.n_row, costants.n_col, 3), 0, dtype=np.float32 )
    errf_parameters_err =  np.full((costants.n_row, costants.n_col, 3), 0, dtype=np.float32 )
    tot_cal_line_param =  np.full((costants.n_row, costants.n_col, 2), 0, dtype=np.float32)
    tot_cal_line_param_err =  np.full((costants.n_row, costants.n_col, 2), 0, dtype=np.float32 )
    tot_cal_line1p_param = np.full((costants.n_row, costants.n_col, 1), 0, dtype=np.float32)
    tot_cal_line1p_param_err = np.full((costants.n_row, costants.n_col, 1), 0, dtype=np.float32)
    tot_calibrated_range_per_pixel = np.full((costants.n_row, costants.n_col, 2), 0, dtype=np.float32 )
    tot_cal_2ord_param =  np.full((costants.n_row, costants.n_col, 3), 0, dtype=np.float32)
    tot_cal_2ord_param_err =  np.full((costants.n_row, costants.n_col, 3), 0, dtype=np.float32 )

    imp_scurve_fit = 0
    cordinates_line = []
    cordinates_2ord = []
    imp_line_fit = 0
    imp_2ord_fit = 0
    print("Doing fit for every pixel ...   %s seconds " % (time.time() - start_time))
    for c in range (0, costants.n_col):
        print('th, col: {}, {} ... {}'.format(threshold, c, time.time() -start_time))
        for r in range (0, costants.n_row):
            fitted_cnts = cnts[r][c]
            fitted_injlist_cnts = injlist
            #Let's do the s-curve fit
            try:
                p0 = [100, 15, 3]
                opt_errf, pcov_errf = curve_fit(functions.err_func, fitted_injlist_cnts, fitted_cnts, sigma = None, p0 = p0)
                error_erf = np.sqrt(pcov_errf.diagonal())
            except :
                print("Impossibele doing fit")
                imp_scurve_fit = imp_scurve_fit +1
                opt_errf = np.full(3, 0)
                pcov_errf = np.full((3, 3), 0)
                error_erf = np.full(3, 0)
            fitted_tot = tot[r][c][1:][tot[r][c][1:] > 0]
            fitted_injlist_tot = injlist[1:][tot[r][c][1:] > 0]

            #Let's do the tot fit with a line
            try:
                opt_line, pcov_line = curve_fit(functions.line, fitted_injlist_tot,
                                fitted_tot, sigma = None, p0 = None)
                error_line = np.sqrt(pcov_line.diagonal())
                q0 = -opt_line[0]/opt_line[1]
                min_tot_range = (0. - opt_line[1])/opt_line[0]
                max_tot_range = (63. - opt_line[1])/opt_line[0]

            except :
                print("Impossibele doing fit")
                imp_line_fit = imp_line_fit + 1
                opt_line = np.full(2, 0)
                error_line = np.full(2, 0)
                min_range = 0
                max_range = 0
                min_tot_range = 0
                max_tot_range = 0
                cordinates_line.append((r, c))

            #Let's do the tot fit with a 2ord pol
            try:
                opt_pol2ord, pcov_pol2ord = curve_fit(functions.pol_2order, fitted_injlist_tot,
                                fitted_tot, sigma = None, p0 = None)
                error_pol2ord = np.sqrt(pcov_pol2ord.diagonal())

            except :
                print("Impossibele doing fit")
                imp_2ord_fit = imp_2ord_fit + 1
                opt_pol2ord = np.full(3, 0)
                error_pol2ord = np.full(3, 0)
                cordinates_2ord.append((r, c))

            #Let's do the tot fit with a 1 param line
            try:
                opt_line1p, pcov_line1p = curve_fit(functions.line1p, fitted_injlist_tot-opt_errf[1],
                                fitted_tot, sigma = None, p0 = None)
                error_line1p = np.sqrt(pcov_line1p)

            except :
                print("Impossibele doing fit")
                opt_line1p = 0
                error_line1p = 0

            errf_parameters[r][c][0] = opt_errf[0]
            errf_parameters[r][c][1] = opt_errf[1]
            errf_parameters[r][c][2] = opt_errf[2]
            errf_parameters_err[r][c][0] = error_erf[0]
            errf_parameters_err[r][c][1] = error_erf[1]
            errf_parameters_err[r][c][2] = error_erf[2]
            tot_cal_line_param[r][c][0] = opt_line[0]
            tot_cal_line_param[r][c][1] = opt_line[1]
            tot_cal_line_param_err[r][c][0] = error_line[0]
            tot_cal_line_param_err[r][c][1] = error_line[1]

            tot_cal_line1p_param[r][c][0] = opt_line1p
            tot_cal_line1p_param_err[r][c][0] = error_line1p

            tot_cal_2ord_param[r][c][0] = opt_pol2ord[0]
            tot_cal_2ord_param[r][c][1] = opt_pol2ord[1]
            tot_cal_2ord_param[r][c][2] = opt_pol2ord[2]
            tot_cal_2ord_param_err[r][c][0] = error_pol2ord[0]
            tot_cal_2ord_param_err[r][c][1] = error_pol2ord[1]
            tot_cal_2ord_param_err[r][c][2] = error_pol2ord[2]

            tot_calibrated_range_per_pixel[r][c][0] = min_tot_range
            tot_calibrated_range_per_pixel[r][c][1] = max_tot_range

    print('Number of impossible fit with a line function: %d\n\
            Number of impossible fit with a line function: %d\n\
            Number of impossible fit with a 2 ord pol: %d ' % (imp_scurve_fit, imp_line_fit, imp_2ord_fit) )

    print('Pixel where the line fit failed: {}\n\
            Pixel where the 2ord-pol fit failed: {}'.format(cordinates_line, cordinates_2ord))
    output_file_fitparam = input_file.replace('cnts_tot', 'fit_param')

    np.savez(output_file_fitparam, error_function_param = errf_parameters, error_function_error = errf_parameters_err,
            tot_cal_line_param = tot_cal_line_param, tot_cal_line_param_err = tot_cal_line_param_err,
            tot_calibrated_range_per_pixel = tot_calibrated_range_per_pixel ,
            tot_cal_2ord_param = tot_cal_2ord_param, tot_cal_2ord_param_err = tot_cal_2ord_param_err,
            tot_cal_line1p_param = tot_cal_line1p_param, tot_cal_line1p_param_err = tot_cal_line1p_param_err)
    print("Closing file ...   %s seconds " % (time.time() - start_time))
