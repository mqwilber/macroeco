from __future__ import division

import numpy as np
import scipy as sp
import scipy.stats as stats
import pandas as pd

from ..misc import doc_sub

_data_doc = \
    """data : iterable
        Data for analysis"""

_model_doc = \
    """model : obj
        Scipy frozen distribution object. When freezing, keyword args ``loc``
        and ``scale`` should only be included if they represent a parameter.
    """

_obs_pred_doc = \
    """obs, pred : array-like objects
        Observed and predicted data
    """


@doc_sub(_data_doc, _model_doc)
def nll(data, model):
    """
    Negative log likelihood given data and a model

    Parameters
    ----------
    {0}
    {1}

    Returns
    -------
    float
        Negative log likelihood

    """

    try:
        log_lik_vals = model.logpmf(data)
    except:
        log_lik_vals = model.logpdf(data)
    return -np.sum(log_lik_vals)


@doc_sub(_data_doc)
def lrt(data, model_null, model_alt, df=None):
    """
    Compare two nested models using a likelihood ratio test

    Parameters
    ----------
    {0}
    model_null : obj
        A frozen scipy distribution object representing the null model.
    model_alt : scipy distribution object
        A frozen scipy distribution object representing the alternative model.
    df : int
        The degrees of freedom for the lrt (optional). If none, df is
        calculated as the difference between the number of parameters in the
        null and alternative models.

    Returns
    -------
    tuple
        G^2 statistic, p-value

    Notes
    -----
    Parameters of distribution objects must be given as keyword arguments. Ex.
    ``norm = stats.norm(loc=0, scale=1)``

    A p-value < alpha suggests signficant evidence for the alternative model.

    The LRT only applies to nested models. The G^2 statistic and G-test rely on
    the the assumption that -2log(Likelihood_null / Likelihood_alt) is
    approximately chi-squared distributed. This assumption breaks down for
    small samples sizes.

    """

    # Calculate G^2 statistic
    ll_null = nll(data, model_null) * -1
    ll_alt = nll(data, model_alt) * -1
    test_stat = -2 * (ll_null - ll_alt)

    # Set df if necessary
    if not df:
        df =  ( len(model_alt.args) + len(model_alt.kwds)
              - len(model_null.args) - len(model_null.kwds) )

    return test_stat, stats.chisqprob(test_stat, df)


@doc_sub(_data_doc, _model_doc)
def AIC(data, model, params=None, corrected=True):
    """
    Akaike Information Criteria given data and a model

    Parameters
    ----------
    {0}
    {1}
    params : int
        Number of parameters in the model. If None, calculated from model
        object.
    corrected : bool
        If True, calculates the small-sample size correct AICC. Default False.

    Returns
    -------
    float
        AIC(C) value

    Notes
    -----
    AICC should be used when the number of observations is < 40.

    References
    ----------
    .. [#]
       Burnham, K and Anderson, D. (2002) Model Selection and Multimodel
       Inference: A Practical and Information-Theoretic Approach (p. 66). New
       York City, USA: Springer.

    """
    n = len(data)  # Number of observations
    L = nll(data, model)

    if not params:
        k = len(model.kwds) + len(model.args)
    else:
        k = params

    if corrected:
        aic_value = 2 * k + 2 * L + (2 * k * (k + 1)) / (n - k - 1)
    else:
        aic_value = 2 * k + 2 * L

    return aic_value


def AIC_compare(aic_list):
    """
    Calculates delta AIC and AIC weights from a list of AIC values

    Parameters
    -----------------
    aic_list : iterable
        AIC values from set of candidat models

    Returns
    -------------
    tuple
        First element contains the delta AIC values, second element contains
        the relative AIC weights.

    Notes
    -----
    AIC weights can be interpreted as the probability that a given model is the
    best model in the set.

    """

    aic_values = np.array(aic_list)
    minimum = np.min(aic_values)
    delta = aic_values - minimum
    values = np.exp(-delta / 2)
    weights = values / np.sum(values)

    return delta, weights


def sum_of_squares(obs, pred):
    """
    Sum of squares between observed and predicted data

    Parameters
    ----------
    obs : iterable
        Observed data
    pred : iterable
        Predicted data

    Returns
    -------
    float
        Sum of squares

    Notes
    -----
    The length of observed and predicted data must match.

    """

    return np.sum((np.array(obs) - np.array(pred)) ** 2)


def r_squared(obs, pred, one_to_one=False, log_trans=False):
    """
    R^2 value for a regression of observed and predicted data

    Parameters
    ----------
    obs : iterable
        Observed data
    pred : iterable
        Predicted data
    one_to_one : bool
        If True, calculates the R^2 based on the one-to-one line (see [#]_),
        and if False, calculates the standard R^2 based on a linear regression.
        Default False.
    log_trans : bool
        If True, log transforms obs and pred before R^2 calculation.

    Returns
    -------
    float
        R^2 value

    Notes
    -----
    Using the traditional R^2 to compare the fit of observed and predicted
    values may be misleading as the relationship may not be one-to-one but the
    R^2 value may be quite high. The one-to-one option alleviates this problem.

    References
    ----------
    .. [#]
       White, E., Thibault, K., & Xiao, X. (2012). Characterizing the species
       abundance distributions across taxa and ecosystems using a simple
       maximum entropy model. Ecology, 93(8), 1772-8

    """

    if log_trans:
        obs = np.log(obs)
        pred = np.log(pred)

    if one_to_one:
        r_sq = 1 - (sum_of_squares(obs, pred) /
                    sum_of_squares(obs, np.mean(obs)))
    else:
        b0, b1, r, p_value, se = stats.linregress(obs, pred)
        r_sq = r ** 2

    return r_sq

def preston_bin(data, max_num):
    """
    Bins data on base 2 using Preston's method

    Parameters
    ----------
    data : array-like
        Data to be binned
    max_num :  float
        The maximum upper value of the data

    Returns
    -------
    tuple
        (binned_data, bin_edges)

    Notes
    -----
    Uses Preston's method of binning, which has exclusive lower boundaries and
    inclusive upper boundaries. Densities are not split between bins.

    References
    ----------
    .. [#]
       Preston, F. (1962). The canonical distribution of commonness and rarity.
       Ecology, 43, 185-215

    """

    log_ub = np.ceil(np.log2(max_num))

    # Make an exclusive lower bound in keeping with Preston
    if log_ub == 0:
        boundaries = np.array([0, 1])
    elif log_ub == 1:
        boundaries = np.arange(1, 4)
    else:
        boundaries = 2 ** np.arange(0, log_ub + 1)
        boundaries = np.insert(boundaries, 2, 3)
        boundaries[3:] = boundaries[3:] + 1

    hist_data = np.histogram(data, bins=boundaries)
    return hist_data