import numpy
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import chisquare
from matplotlib.colors import LogNorm
import scipy.stats

import utilities

def set_plot(xlabel, ylabel, title = '', grid = True):
    """ Set the format of the plot
    """
    plt.title(title, fontsize=12)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.yticks(fontsize=14, rotation=0)
    plt.xticks(fontsize=14, rotation=0)
    plt.subplots_adjust(bottom = 0.13, left = 0.15)
    #plt.legend()
    return

def fit_legend(param_values, param_errors, param_names, param_units, chi2 = None, ndof = None):
    """ Format (in a readable way) the fit parameters legend
    """
    legend = ''
    for (name, value, error, unit) in zip(param_names, param_values, param_errors, param_units):
        legend += ("%s: %s %s\n" % (name, utilities.format_value_error(value, error), unit))
    if chi2 is not None:
        legend += ("$\chi^2$/d.o.f.=%.2f/%d "% (chi2, ndof))
    return legend


def plot_histogram(x, xlabel, ylabel, n_bins = None, range = None, title = '', legend = '', fmt = '.b', as_scatter = False):
    """ Do histogram: you can give so many option to the funcion and get a well formatted hist
    """
    if(n_bins is None ):
      n_bins = int(numpy.sqrt(len(x)))
    if (range is None):
     range = (x.min(), x.max())

    if (as_scatter is True):
      errors = numpy.sqrt(n)
      n, bins = numpy.histogram(x,  bins = n_bins, range = range)
      #  errors = errors/n.sum() Use for the norm histogram: I should add an option
      #  n = n/n.sum()
      bin_centers = 0.5 * (bins[1:] + bins[:-1])
      mask = (n > 0.)
      new_bins = bin_centers[mask]
      n = n[mask]
      dn = errors[mask]
      plt.errorbar(new_bins, n, yerr = dn, fmt = fmt, label = legend)
      set_plot(xlabel, ylabel, title = title)
      return new_bins, n, dn
    else:
      n, bins, patches = plt.hist(x, bins = n_bins, range = range, label = legend, alpha = 0.4)#bins[1:],  weights = n
      dn = numpy.sqrt(n)
      set_plot(xlabel, ylabel, title = title)
      return bins, n, dn

def hist2d(x, y, xlabel, ylabel, bins = None, range_x = None, range_y = None, norm = None, title = '', legend = ''):
    """ """
    if (range_x is None):
      range_x = (x.min(), x.max())
    if (range_y is None):
      range_y = (y.min(), y.max())
    if(bins is None ):
      bins = int(numpy.sqrt(len(x)))
    data = plt.hist2d(x, y,  bins=bins , range = (range_x, range_y), norm=norm, label = legend)
    set_plot(xlabel, ylabel, title=title)
    plt.colorbar()
    return data

def scatter_plot(x, y, xlabel, ylabel, dx = None, dy = None, range_x = None, range_y = None,
                 title = '', legend = '', fmt='.'):
    """ Do a scatter plot
    """
    plt.errorbar(x, y, xerr = dx, yerr = dy , fmt = fmt, label = legend)
    #if range_x is None:
    #    range_x = (x.min(), x.max())
    #if range_y is None:
    #    range_y = (y.min(), y.max())
    #plt.xlim(range_x)
    #plt.ylim(range_y)
    set_plot(xlabel, ylabel, title = title)
    return

def do_fit(x, y, param_names, param_units, fit_function, dy = None, p0 = None, bounds = (-numpy.inf, numpy.inf),
           x_fit_min = -numpy.inf, x_fit_max = numpy.inf, ex__fit_int = (numpy.inf, -numpy.inf), show = True,
           draw_on_points = False, output_file = ''):
    """ Do a fit with an input function within an interval; you can also show the plot and save an output file
    with the results of the fit.
    """
    mask = (x > x_fit_min ) * (x < x_fit_max) * (( x < ex__fit_int[0]) | (x > ex__fit_int[1]))
    x = x[mask]
    y = y[mask]
    if dy == None: #len(dy) == 1:
        chi2 = None
        ndof = None
    else:
        dy = dy[mask]
    try:
        opt, pcov = curve_fit(fit_function, x, y, sigma = dy, p0 = p0, bounds = bounds)
        if dy != None: #len(dy)!=1:
            chi2 = (y - fit_function(x, *opt))**2 / dy**2
            chi2 = chi2.sum()
            ndof = len(y)-len(opt)
    except RuntimeError:
        print("WARNING: fit did not converge")
        opt = numpy.full(3, numpy.nan)
        pcov = numpy.full((3, 3), numpy.nan)
    legend = fit_legend(opt, numpy.sqrt(pcov.diagonal()), param_names, param_units, chi2 = chi2, ndof = ndof)
    print("LEGEND:\n", legend)
    if show:
        if draw_on_points is True:
            bin_grid = x
        else:
            bin_grid = numpy.linspace(x.min(), x.max(), 1000)
        plt.plot(bin_grid, fit_function(bin_grid, *opt), label = legend)
        plt.legend()
    if output_file:
        legend = legend + '\n'
        with open(output_file, 'a') as of:
            of.write(legend)
    return opt, pcov

def colormap(z, vmin=None, vmax=None, xlabel = '', ylabel = '', title = '', norm=None):
    """ Create a colormap
    """
    set_plot(xlabel = xlabel, ylabel = ylabel, title = title)
    plt.imshow(z, vmin = vmin, vmax = vmax, norm = norm)
    plt.colorbar()
    return

def scatter_plot_shared_axes(x, y1, y2, dx1=None, dy1=None, dx2=None, dy2=None,
                            xlabel = '', ylabel1='', ylabel2='', fmt =['b.','r.'], legend=''):
    plt.errorbar(x, y1, xerr = dx1, yerr = dy1 , fmt = fmt[0], label = legend)
    set_plot(xlabel, ylabel1, title = '', grid = True)
    ax2 = plt.gca().twinx()
    ax2.errorbar(x, y2, xerr = dx2, yerr = dy2 , fmt = fmt[1])
    set_plot(xlabel, ylabel2, title = '', grid = True)
    return
