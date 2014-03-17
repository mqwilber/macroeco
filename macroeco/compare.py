"""
===========================
Compare (:mod:`macroeco.compare`)
===========================

This module contains functions that compare the goodness of fit of a
distribution/curve to data or the fit of two distributions/curves to each 
other.

Comparison Functions
====================

.. autosummary::
   :toctree: generated/

   get_AIC
   get_AICC
   get_AIC_weights
   get_nll
   get_empirical_cdf
   get_sum_of_squares


"""

from __future__ import division

import numpy as np
import scipy as sp
import scipy.stats as stats
import pandas as pd

from distributions import *

# NOTE: get_* functions usually refer to a method within a class.  I would
# suggest dropping all of the get prefixes


def get_nll(values):
    """
    Calculate negative log likelihood from an array of pdf/pmf values.
    """

    values = _to_arrays(values)[0]
    return -np.sum(np.log(values))

def get_AIC(values, params):
    """
    Calculate AIC given values of a pdf/pmf and a set of model parameters.
    """
    values, params = _to_arrays(values, params)
    k = len(params)  # Num parameters
    L = get_nll(values)
    return 2*k + 2*L

def get_AICC(values, params):
    """
    Calculate AICC given values of a pdf/pmf and a set of model parameters.

    Notes
    -----
    Should be used when the number of observations is < 40.

    References
    ----------
    .. [#]
        Burnham, K and Anderson, D. (2002) Model Selection and Multimodel
        Inference: A Practical and Information-Theoretic Approach (p. 66). New
        York City, USA: Springer.

    """
    
    values, params = _to_arrays(values, params)
    k = len(params)  # Num parameters
    n = len(values)  # Num observations
    return get_AIC(values, params) + (2*k * (k + 1)) / (n - k - 1)

def get_AIC_weights(aic_values):
    """
    Calculates the aic_weights for a given set of models

    Parameters
    ----------
    aic_values : array-like object
        Array-like object containing AIC values from different models
    
    Returns
    -------
    (weights, delta) : tuple
        First element contains the relative AIC weights, second element
        contains the delta AIC values.

    Notes
    -----
    AIC weights can be interpreted as the probability that a given model is the
    best model in comparison to the other models
    """

    aic_values = _to_arrays(aic_values)[0]
    minimum = np.min(aic_values) 
    delta = aic_values - minimum
    values = np.exp(-delta / 2)
    weights = values / np.sum(values)

    return weights, delta


def get_empirical_cdf(data):
    """
    Generates an empirical cdf from empirical data

    Parameters
    ----------
    data : array-like object
        Empirical data 

    Returns
    --------
    : array
        The empirical cdf corresponding to the inputted data

    """

    vals = pd.Series(data).value_counts()
    ecdf = pd.DataFrame(data).set_index(keys=0)
    probs = pd.DataFrame(vals.sort_index().cumsum() / np.float(len(data)))
    ecdf = ecdf.join(probs)

    return np.array(ecdf[0])

class gen_loss_function(object):
    """
    Generic class for loss function between observed and predicted data

    """

    def __init__(self, loss_fxn_str):
        """
        Parameters
        ----------
        loss_fxn_str : string
            A Python string representing the loss function between observed
            (obs) and predicted (pred).

        Notes
        -----

        Ex. 'np.abs(obs - pred)' or '(obs - pred)**2'

        
        """
        self.loss_fxn = loss_fxn_str

    def total_loss(self, obs, pred):
        """
        Total loss for observed and predicted 

        Parameters
        ----------
        obs, pred : array-like objects
            observed and predicted data

        Returns
        -------
        : float
            The sum of the loss function
        """

        obs, pred = _to_arrays(obs, pred)
        return np.sum(eval(self.loss_fxn))

get_sum_of_squares = gen_loss_function('(obs - pred)**2').total_loss

def get_r_squared(obs, pred):
    """

    Get's the R^2 value for a regression of observed data (X) and predicted (Y)

    Parameters
    ----------
    obs, pred : array-like objects

    Returns
    -------
    : float
        The R**2 value for the regression of 

    """

    b0, b1, r, p_value, se = stats.linregress(obs, pred)
    return r**2

def get_ks_two_sample():
    """
    Two sample Kolmogorov Smirnov distribution.  Uses the cumulative
    distribution functions to test whether two samples were drawn from the same
    continuous distribution. Can be a decent approxmiation for discrete data
    (CHECK THIS), but the chi-squared test may be more appropriate. 

    """

    pass

def get_ks_one_sample():
    pass

def get_lrt():
    pass

def get_bayes_factor():
    pass

def get_chi_squared(dists):
    """
    Chi-squared test to compare two or more distributions. 

    Parameters
    ------------------
    dists : list
        List of distributions to compare.  Each distribution in list should be
        the same length and the location of each value in a list should be
        compareable.  This list will be made into a Chi-Squared contingency
        table to analyze.

    Returns
    ------------
    chi2 : float
        The test statistic.
    p : float
        The p-value of the test
    dof : int
        Degrees of freedom
    expected : ndarray, same shape as `observed`
        The expected frequencies, based on the marginal sums of the table.

    Notes
    ---------
    Assumption of the Chi-squared test is that the expected value of 80% of
    the cells is > 5.  If this does not hold, the Normal approximation is not
    valid and you should try an alternative approach.
    """

    assert len(dists) > 1, "Length of dists must be greater than 1"
    test_len = len(dists[0])
    assert np.all([len(dt) == test_len for dit in dists], "All dists must have"
        + " equal length"

    chi_table = np.array(dists, dtype=np.float)
    chi2, p, dof, expected = stats.chi2_contingency(chi_table, correction=False)

    return chi2, p, dof, expected

def bin_data(data, max_num):
    """
    Bins the data on base 2. Bins such that the right boundary is exlusive and
    the left boundary is inclusive.  Does not split density between bins.

    Parameters
    ------------------
    data : array-like
        Data to be binned 

    max_num :  float
        The maximum upper most boundary of the data

    base : float
        The base for log binning

    Returns
    ------------
    tuple : (binned_data, bins_edges)
    
    """
    log_ub = np.ceil(np.log2(max_num))
    boundaries = 2**np.arange(0, log_ub + 1)

    hist_data = np.histogram(data, bins=boundaries)
    return hist_data


def _to_arrays(*args):
    '''
    Converts all args to np.arrays
    '''
    return tuple([np.array(ta) if np.iterable(ta) else np.array([ta]) for ta in
                                            args])   
