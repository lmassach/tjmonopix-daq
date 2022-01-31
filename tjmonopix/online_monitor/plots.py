import matplotlib.pyplot as plt
import numpy as np

from scipy.optimize import curve_fit
from scipy.stats import chisquare
from matplotlib.colors import LogNorm
import scipy.stats


def decimal_places(val):
    """Calculate the number of decimal places so that a given value is rounded
    to exactly two signficant digits.
    Note that we add epsilon to the argument of the logarithm in such a way
    that, e.g., 0.001 is converted to 0.0010 and not 0.00100. For values greater
    than 99 this number is negative.
    """
    return 1 - int(numpy.log10(val + sys.float_info.epsilon)) + 1 * (val < 1.)


def decimal_power(val):
    """Calculate the order of magnitude of a given value,i.e., the largest
    power of ten smaller than the value.
    """
    return int(numpy.log10(val + sys.float_info.epsilon)) - 1 * (val < 1.)


def format_value(value, precision=3):
    """Format a number with a reasonable precision
    """
    if isinstance(value, str):
        return value
    else:
        fmt = '%%.%dg' % precision
        return fmt % value


def format_value_error(value, error, pm='+/-', max_dec_places=6):
    """Format a measurement with the proper number of significant digits.
    """
    value = float(value)
    error = float(error)
    if not numpy.isnan(error):
        assert error >= 0
    else:
        return '%s %s nan' % (format_value(value), pm)
    if error == 0 or error == numpy.inf:
        return '%e' % value
    dec_places = decimal_places(error)
    if dec_places >= 0 and dec_places <= max_dec_places:
        fmt = '%%.%df %s %%.%df' % (dec_places, pm, dec_places)
    else:
        p = decimal_power(abs(value))
        scale = 10 ** p
        value /= scale
        error /= scale
        dec_places = decimal_places(error)
        if dec_places > 0:
            if p > 0:
                exp = 'e+%02d' % p
            else:
                exp = 'e-%02d' % abs(p)
            fmt = '%%.%df%s %s %%.%df%s' %\
                  (dec_places, exp, pm, dec_places, exp)
        else:
            fmt = '%%d %s %%d' % pm
    return fmt % (value, error)

def make_opt_string(opt, pcov, s = '', s_f = ''):
  numpy.set_printoptions(linewidth=numpy.inf, precision=5)
  opt_err = numpy.sqrt(pcov.diagonal())
  array_str = numpy.array_str(numpy.concatenate((opt, opt_err)) )
  array_str = array_str.strip('[]')  
  string = s + ' ' + array_str + s_f + '\n'
  return string 
  
  
  
####################################################################

def set_plot(xlabel, ylabel, title = ''):
  plt.title(title, fontsize=12)
  plt.xlabel(xlabel, fontsize=14)
  plt.ylabel(ylabel, fontsize=14)
  plt.yticks(fontsize=14, rotation=0)
  plt.xticks(fontsize=14, rotation=0) 
  plt.subplots_adjust(bottom = 0.13, left = 0.15)
  plt.grid(True)  
  plt.legend() 
  return  

def fit_legend(param_values, param_errors, param_names, param_units, chi2=None, ndof=None):   
  legend = ''
  for (name, value, error, unit) in zip(param_names, param_values, param_errors, param_units):
      legend += ("%s: %s %s\n" % (name, format_value_error(value, error), unit))
  if chi2 is not None: 
      legend += ("$\chi^2$/d.o.f.=%.2f/%d "% (chi2, ndof))
  return legend


def plot_histogram(x, xlabel, ylabel, n_bins = None, range = None, title = '', legend = '', fmt = '.b', as_scatter = False):
  if(n_bins is None ): 
    n_bins = int(np.sqrt(len(x)))
  if (range is None):
   range = (x.min(), x.max()) 
  n, bins = np.histogram(x,  bins = n_bins, range = range)
  
  if (as_scatter is True):
    errors = np.sqrt(n)
    #errors = errors/n.sum()
    #n = n/n.sum()  
    bin_centers = 0.5 * (bins[1:] + bins[:-1])    
    mask = (n > 0.)
    new_bins = bin_centers[mask]
    n = n[mask]
    dn = errors[mask]
    plt.errorbar(new_bins, n, yerr = dn, fmt = fmt, label = legend)
    set_plot(xlabel, ylabel, title = title)
    return new_bins, n, dn
  else:
    n, bins, patches = plt.hist(bins[1:],  weights = n, bins = bins, label = legend, alpha = 0.4)
    dn = np.sqrt(n)
    set_plot(xlabel, ylabel, title = title)
    return bins, n, dn


def do_fit(x, y, dy, param_names, param_units, fit_function, p0 = None, bounds = (-np.inf, np.inf), x_min = -np.inf, x_max = np.inf, ex_int = (np.inf, -np.inf), show=True, draw_on_points = False, output_file = ''): 
  mask = (x > x_min ) * (x < x_max) * (( x < ex_int[0]) | (x > ex_int[1]))
  x = x[mask]
  y = y[mask]
  dy = dy[mask]
  
  opt, pcov = curve_fit(fit_function, x, y, sigma = dy, p0 = p0, bounds = bounds)   
  chi2 = (y - fit_function(x, *opt))**2 / dy**2
  chi2 = chi2.sum()
  ndof = len(y)-len(opt)  
  
  if show:
      legend = fit_legend(opt, np.sqrt(pcov.diagonal()), param_names, param_units, chi2, ndof)
      if draw_on_points is True: 
          bin_grid = x
      else:    
          bin_grid = np.linspace(x.min(), x.max(), 1000)  
      plt.plot(bin_grid, fit_function(bin_grid, *opt), label = legend)        
      plt.legend() 
      print("LEGEND:", legend)

  if output_file is not '': 
        legend = legend + '\n'
        with open(output_file, 'a') as of:
          of.write(legend)
  return opt, pcov
  
def scatter_plot(x, y, xlabel, ylabel, dx = None, dy = None,  title = '', legend = '', fmt='.'):
  plt.errorbar(x, y, xerr = dx, yerr = dy , fmt = fmt, label = legend)
  #plt.xlim(x.min(), x.max())
  #plt.ylim(y.min(), y.max())  
  set_plot(xlabel, ylabel, title = title)
  return   


def hist2d(x, y, xlabel, ylabel, bins=None, range_x = None, range_y = None, norm = None, title = '', legend = ''):
  plt.figure()
  if (range_x is None):
    range_x = (x.min(), x.max()) 
  if (range_y is None):
    range_y = (y.min(), y.max())   
  if(bins is None ): 
    bins = int(np.sqrt(len(x)))
  plt.hist2d(x, y,  bins=bins , range = (range_x, range_y), norm=norm, label = legend)  
  set_plot(xlabel, ylabel, title=title)
  plt.colorbar()
  return   


def line_fit(x, y, xlabel, ylabel, param_units, param_names = ['m', 'q'], dy = None, dx = None, err_fit = None, title = ''):
    def line(x, m, q):
      return m * x + q 
    p0 = [1., 1. ]
    opt, pcov = curve_fit(line, x, y, sigma = err_fit)    
    param_errors = np.sqrt(np.diagonal(pcov)[0])  
    res = y - line(x, *opt)
    chi2 = (res**2)/(err_fit**2)
    chi2 = chi2.sum()
    ndof = len(x) - len(opt)
  
    plt.figure()
    plt.subplot(2, 1, 1)   
    plt.errorbar(x, y, yerr = dy, xerr = dx, fmt = '.')
    legend = fit_legend(opt, param_errors, param_names, param_units, chi2, ndof)
    x_new = np.linspace(0., 300., 1000)
    plt.plot(x_new, line(x_new, *opt), 'r', label = legend)
    set_plot(xlabel, ylabel, title = title)  
    plt.subplot(2, 1, 2)
    plt.errorbar(x, res, yerr = err_fit, fmt = '.')  
    set_plot(xlabel, "residui", title = '')
    return opt, pcov
    
################################################################################################à

def tj_plot(chip, dt=0.2, wait_inj=False):
    """Matrix 2d histogram"""
    chip.enable_data_rx()
    hits, pixels, hits_per_pixel = chip.recv_data_summary(dt, wait_inj)
    
    print("Got %d hits in %g s" % (len(hits), dt))
    
    # Plot of the pixel matrix (2D histogram of number of hits vs row/col)
    plt.figure()
    plt.subplot(1, 2, 1)
    plt.hist2d(hits["col"], hits["row"], bins=[112,224], range=[[0,112],[0,224]],
               )#norm=matplotlib.colors.LogNorm(vmin=1))
    plt.colorbar()
    plt.xlabel('rows')
    plt.ylabel('columns')

    # Histogram of the hits-per-pixel distribution (to choose noise threshold)
    plt.subplot(1, 2, 2)
    plt.hist(hits_per_pixel, bins=min(100, np.max(hits_per_pixel)+1), range=[-0.5, np.max(hits_per_pixel)+0.5])
    plt.yscale('log')
    plt.grid(axis="y")
    plt.xlabel('hits per pixel')
    plt.ylabel('counts')    
    return hits, pixels, hits_per_pixel
    
    

def s_curve(injlist, cnt, n_total_pulse, capacity):
    """Plot the s-curve for one pixel """
    approx_theshold = injlist[np.argmin( np.abs(cnt - n_total_pulse/2) )]
    print "approx. th = %d DAC = %g e-" % (approx_theshold, approx_theshold*capacity)
    fig,ax = plt.subplots(1,1)
    ax.plot(injlist, cnt, "C0o", label="count")
    ax2 = ax.twiny()
    ax3 = ax.twinx()
    ax3.plot(injlist,tot,"C1x",label="ToT")
    ax.plot([],[],"C1x",label="ToT")

    ax.set_xlabel("Injection [ADC]")
    ax.set_ylabel("#")
    ax3.set_ylabel("ToT [40MHz]")
    ax2.set_xlabel("Charge [e]")
    ax.set_xbound(np.min(injlist), np.max(injlist))
    ax2.set_xbound(np.min(injlist)*CALCAP, np.max(injlist)*CALCAP)
    ax.legend()
    
    return  approx_theshold
