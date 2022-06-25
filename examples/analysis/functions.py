import numpy as np
from scipy.special import erf
from scipy.special import erfc
from scipy.stats import crystalball

def line(x, m, q):
    return m * x + q


def line1p(x, m):
    return m * x

def two_line(x, m1, q1, m2, q2):
    xlim = (q2 - q1) / (m1 - m2)
    mask = x < xlim#np.argwhere(x < xlim)
    y = np.zeros(len(x))
    y[mask] = x[mask] * m1 + q1
    mask = x >= xlim
    y[mask] = x[mask] * m2 + q2
    return y


def pol_2order(x, a, b, c):
    return a * x**2 + b * x + c

def err_func(x, norm, mean, sigma):
    z = (x - mean)/sigma
    return norm * 0.5 * (1 + erf(z/np.sqrt(2)))

def cerr_func(x, norm, mean, sigma):
    z = (x - mean)/sigma
    return norm * 0.5 * (1 + erfc(z/np.sqrt(2)))


def gauss(x, norm, mean, sigma):
    return (norm/(sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean)/sigma )**2)

def gauss_line(x, a, b, n, m, s):
    return a * x + b + gauss(x, n, m, s)

def my_crystalball(x, beta, m, loc, scale):
    return crystalball.pdf(x, beta = beta, m = m, loc = loc, scale = scale)
