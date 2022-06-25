import numpy as np
import matplotlib.pyplot as plt

import costants

def extrapolate_zero_counts(injlist, inj_not_zero, cnt_not_zero):
    """ Create an array with counts equal to zero
    """
    injs = injlist[:]
    cnts = np.zeros(len(injs))
    cnt_vs_inj = {inj: cnt for inj, cnt in zip(inj_not_zero, cnt_not_zero)}
    for i in range(len(injs)):
        if injs[i] in cnt_vs_inj:
            cnts[i] = cnt_vs_inj[injs[i]]
    return injs, cnts

def hits_histogram(row, col, show = False):
    """
    """
    col_bins = np.linspace(-0.5, costants.n_col - 0.5, costants.n_col + 1)
    row_bins = np.linspace(-0.5, costants.n_row - 0.5, costants.n_row + 1)
    cnts, _, _ = np.histogram2d(row, col, bins = [row_bins, col_bins])
    if show == True:
        plt.imshow(cnts, origin ='lower', norm = LogNorm(vmin=1, vmax=1000))
        plt.colorbar()
    return cnts

def create_scurve_hist(row, col, inj, inj_min, inj_max):
    """
    """
    inj_bins = np.linspace(inj_min - 0.5, inj_max + 0.5, (inj_max - inj_min) + 2)
    col_bins = np.linspace(-0.5, costants.n_col - 0.5, costants.n_col + 1)
    row_bins = np.linspace(-0.5, costants.n_row - 0.5, costants.n_row + 1)
    cnts, _ = np.histogramdd((row, col, inj), bins=[row_bins, col_bins, inj_bins])
    return cnts

def create_scurve_tot(row, col, inj, tot, inj_min, inj_max):
    """
    """
    inj_bins = np.linspace(inj_min - 0.5, inj_max + 0.5, (inj_max - inj_min) + 2)
    col_bins = np.linspace(-0.5, costants.n_col - 0.5, costants.n_col + 1)
    row_bins = np.linspace(-0.5, costants.n_row - 0.5, costants.n_row + 1)
    tot, _ = np.histogramdd((row, col, inj), bins=[row_bins, col_bins, inj_bins], weights = tot)
    return tot

def create_tot_hist(row, col, tot, tot_min = 0, tot_max=64):
    tot_bins = np.linspace(tot_min-0.5, tot_max-0.5, (tot_max-tot_min) + 1)
    col_bins = np.linspace(-0.5, costants.n_col - 0.5, costants.n_col + 1)
    row_bins = np.linspace(-0.5, costants.n_row - 0.5, costants.n_row + 1)
    cnts, _ = np.histogramdd((row, col, tot), bins=[row_bins, col_bins, tot_bins])
    return cnts
