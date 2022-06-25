#python3 -i calibration/threshold_noise_histograms.py -f calibration/calibration_data/20220506_fit_param_t40.npz
import argparse
import numpy as np
import matplotlib.pyplot as plt

import plot_functions
import costants
import functions

""" This script creates some histograms and colormap of the threshold and noise and of the fit parameters of scurve and tot with the injection
"""

def double_scale_histo_plot(x, hist_range, param_names, param_units, bins=50, xlabel1='', xlabel2='', title='', legend=''):
    fig, ax = plt.subplots(1,1, figsize=(8, 8))
    fig.suptitle(title, fontsize=14)
    n, bins_edge, _ = ax.hist(x, bins=bins, range = hist_range, alpha = 0.4, label = legend)
    centered_bins = (bins_edge[:-1:] + bins_edge[1::]) * 0.5
    mean = np.mean(x)
    stdev = np.std(x)
    p0 = [1e+5, mean, stdev]
    opt, pcov = plot_functions.do_fit(centered_bins, n, param_names, param_units,
                          functions.gauss, dy = None, show = True, p0 = p0)
    ax.set_xbound(hist_range.min(), hist_range.max())
    ax.set_xlabel(xlabel1, fontsize=14)
    ax.set_ylabel("Counts", fontsize=14)
    ax2 = ax.twiny()
    ax3 = ax.twinx()
    ax2.set_xbound(hist_range.min() * costants.CAP, hist_range.max() *costants.CAP)
    ax3.set_ylabel("norm", fontsize=14)
    ax2.set_xlabel(xlabel2, fontsize=14), functions.gauss
    ax.legend()
    return

description = ''
options_parser = argparse.ArgumentParser(description = description)
options_parser.add_argument('-input_file', '-f', default=None, type=str, help='input_file')

if __name__ == '__main__' :
    options = vars(options_parser.parse_args())
    input_file = options['input_file']
    threshold = input_file[-6:-4]
    data = np.load(input_file)
    #ERROR FUNCTION PARAMETERS:
    mean = np.hstack(data['error_function_param'][:, :, 1])
    sigma = np.hstack(data['error_function_param'][:, :, 2])
    mean_top = np.hstack(data['error_function_param'][0:112, :, 1])
    mean_bottom = np.hstack(data['error_function_param'][112:224, :, 1])
    sigma_top = np.hstack(data['error_function_param'][0:112, :, 2])
    sigma_bottom = np.hstack(data['error_function_param'][112:224, :, 2])

    #Make threshold disperion and noise histrograms for the uper and lower part of the chip
    title_bottom = 'rows: 0-111, idb = %s DAC, CAP$\sim$%d e-/DAC' % (threshold, costants.CAP)
    title_top = 'rows: 111-223, idb = %s DAC, CAP$\sim$%d e-/DAC' % (threshold, costants.CAP)
    title = 'idb = %s DAC, CAP$\sim$%d e-/DAC' % (threshold, costants.CAP)
    mean_range = np.array([10, 30])
    sigma_range = np.array([0, 2])
    n_bins = 50
    param_names = ['norm', '$\mu$', '$\sigma$']
    param_units = ['cnts', 'DAC', 'DAC']
    double_scale_histo_plot(mean_top, param_names = param_names, param_units=param_units, hist_range=mean_range, bins = n_bins,
                xlabel1='threshold [DAC]', xlabel2='threshold [e-]', title=title_bottom, legend='')
    double_scale_histo_plot(mean_bottom, param_names = param_names, param_units=param_units,
                hist_range=mean_range, bins = n_bins, xlabel1='threshold [DAC]', xlabel2='threshold [e-]', title=title_top, legend='')
    double_scale_histo_plot(sigma_top, param_names = param_names, param_units=param_units,
                hist_range=sigma_range, bins = n_bins, xlabel1='noise [DAC]', xlabel2='noise [e-]', title=title_bottom, legend='')
    double_scale_histo_plot(sigma_bottom, param_names = param_names, param_units=param_units,
                hist_range=sigma_range, bins = n_bins, xlabel1='noise [DAC]', xlabel2='noise [e-]', title=title_top, legend='')

    double_scale_histo_plot(mean, param_names = param_names, param_units=param_units, hist_range=mean_range, bins = n_bins,
                xlabel1='threshold [DAC]', xlabel2='threshold [e-]', title=title, legend='')
    double_scale_histo_plot(sigma, param_names = param_names, param_units=param_units, hist_range=sigma_range, bins = n_bins,
                xlabel1='noise [DAC]', xlabel2='noise [e-]', title=title, legend='')

    mth = data['error_function_param'][:, :, 1]
    msigma = data['error_function_param'][:, :, 2]

    plt.figure(figsize=(10, 8))
    plt.subplot(1, 2, 1)
    vmin, vmax = np.quantile(mth*costants.CAP, [0.02, 0.98])
    plot_functions.colormap(mth * costants.CAP, vmin = 300, vmax = 500, xlabel = 'col',
                            ylabel = 'row', title = 'Threshold [electron]')
    plt.gca().invert_yaxis()

    plt.subplot(1, 2, 2)
    vmin, vmax = np.quantile(msigma*costants.CAP, [0.02, 0.98])
    plot_functions.colormap(msigma * costants.CAP, vmin = 5, vmax = 20, xlabel = 'col',
                            ylabel = 'row', title = 'Noise [electron]')
    plt.gca().invert_yaxis()


	
    #LINE PARAMETERS:
    mslope = data['tot_cal_line_param'][:, :, 0]
    mintercept = data['tot_cal_line_param'][:, :, 1]

    plt.figure(figsize=(15, 8))
    plt.subplot(1, 3, 1)
    vmin, vmax = np.quantile(mslope, [0.02, 0.98])
    plot_functions.colormap(mslope, vmin = vmin, vmax = vmax , xlabel = 'col',
                            ylabel = 'row', title = 'Slope')
    plt.gca().invert_yaxis()

    plt.subplot(1, 3, 2)
    plot_functions.colormap(mintercept, vmin = np.quantile(mintercept, 0.02), vmax = np.quantile(mintercept, 0.98), xlabel = 'col',
                            ylabel = 'row', title = 'Intercept')
    plt.gca().invert_yaxis()

    plt.subplot(1, 3, 3)
    q0 = -mintercept/mslope
    plot_functions.colormap(q0, vmin = np.nanquantile(q0, 0.02), vmax = np.nanquantile(q0, 0.98), xlabel = 'col',
                            ylabel = 'row', title = 'q0 = -intercept/slope')
    plt.gca().invert_yaxis()

    plt.figure(figsize=(8, 8))
    bins_edge, n, dn = plot_functions.plot_histogram(np.concatenate(mslope), 'slope [ua/DAC]', 'Cnts', n_bins = None, range = (0.5, 1),
                        title = 'idb = {} DAC'.format(threshold), legend = '')
    centered_bins = (bins_edge[:-1:] + bins_edge[1::]) * 0.5
    opt, pcov = plot_functions.do_fit(centered_bins, n, param_names, ['cnts', 'ua/DAC', 'ua/DAC'] , functions.gauss)

    plt.figure(figsize=(8, 8))
    bins_edge, n, dn = plot_functions.plot_histogram(np.concatenate(mintercept), 'intercept [ua]', 'Cnts', n_bins = None,
                    range = (-20,0), title = 'idb = {} DAC'.format(threshold), legend = '')
    centered_bins = (bins_edge[:-1:] + bins_edge[1::]) * 0.5
    opt, pcov = plot_functions.do_fit(centered_bins, n, param_names, ['cnts', 'ua', 'ua'] , functions.gauss, p0 = [500., -10., 3])

    plt.figure(figsize=(8, 8))
    bins_edge, n, dn = plot_functions.plot_histogram(np.hstack(q0), '$Q_{0}$ [DAC]', 'Cnts', n_bins = None,
                    range = (5, 25), title = 'idb = {} DAC'.format(threshold), legend = '')
    centered_bins = (bins_edge[:-1:] + bins_edge[1::]) * 0.5
    opt, pcov = plot_functions.do_fit(centered_bins, n, param_names, ['cnts', 'DAC', 'DAC'] , functions.gauss, p0 = [500., 16, 5])


    plt.show()
    plt.ion()
