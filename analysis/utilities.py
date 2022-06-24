import numpy
import sys

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
    """ Make a string starting from an array (opt) and a matrix (pcov)
    """
    numpy.set_printoptions(linewidth = numpy.inf, precision = 5)
    opt_err = numpy.sqrt(pcov.diagonal())
    array_str = numpy.array_str(numpy.concatenate((opt, opt_err)) )
    array_str = array_str.strip('[]')
    string = s + ' ' + array_str + s_f + '\n'
    return string

def convert_option_list(l, dtype = int):
    """
    """
    if len(l) == 1:
        l = numpy.array([l[0]], dtype = dtype)
    elif len(l) == 2:
        l = numpy.arange(l[0], l[1] + 1, dtype = dtype)
    else:
        l = numpy.array(l, dtype = dtype)
    return l
