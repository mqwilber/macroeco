#!/usr/bin/python

'''
Contains functions to help analyze a given sad

This module is the interface between the theoretical functions
found in predict_sad and the empirical sad's generated by 
empirical

'''

from __future__ import division
import numpy as np


__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of University of California"
__credits__ = "John Harte"
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

def get_cdf(sad, full_pmf=None):
    '''Generates cdf from an SAD or a full pmf
    
    Parameters
    ----------
    sad : array-like object
        array-like object containing an SAD
    full_pmf : optional argument
        If full_pmf is None, function builds a cdf using just sad.  If full_pmf
        is not None it is assumed to be a full_pmf (array-like object) and the
        function builds a cdf using this information.  A full_pmf has support 
        from 1 to N.

    Returns
    -------
    : 1D np.array
        an array containing the cdf
    '''
    sad = np.array(sad)
    assert np.all(sad != 0), "SAD cannot contain zeros"
    if full_pmf == None:
        unq_sad = np.unique(sad)
        S = len(sad)
        cdf = []
        count = 0
        for i in unq_sad:
            tot_in = sum((i == sad))
            count += tot_in
            #Removing or adding (1/(2*S)) can change the graphs
            for s in xrange(tot_in):
                cdf.append((count / S))# - (1/(2*S)))
        return np.array(cdf)
    else:
        assert type(full_pmf) is tuple or type(full_pmf) is list or\
               type(full_pmf) is np.ndarray, "Improper type for full_pmf"
        assert len(full_pmf) == sum(sad), "full_pmf must be of length sum(sad)"
        cdf = np.cumsum(full_pmf)
        sad_sort = np.sort(sad)
        cdf_corr = []
        for n in sad_sort:
            cdf_corr.append(cdf[n - 1])
        return np.array(cdf_corr)

def obs_vs_pred_cdf(sad, obs_cdf, pred_cdf):
    '''Generates a structured array with n, observed cdf, and predicted cdf
    from the observed sad

     Parameters
    ----------
    sad : 1D np.array
        an array containing an SAD
    obs_cdf : array-like object
        array-like object containing observed cdf
    pred_cdf : array-like object
        array-like object containing predicted cdf
    
    Returns
    -------
    : Structured np.array, dtype=[('n', np.int), ('obs', np.float),
    ('pred', np.float)]
        Length of the returned structured array is the same as sad. 'n' is the 
        number of individuals within a species.

    '''
    
    sad = np.array(sad)
    obs_cdf = np.array(obs_cdf)
    pred_cdf = np.array(pred_cdf)
    assert (len(obs_cdf) == len(pred_cdf)) and (len(sad) == len(obs_cdf)),\
        "Array parameters must be of same length"
    sad_sorted = np.sort(sad)
    obs_vs_pred = np.empty(len(sad_sorted), dtype=[('n', np.int),\
                                                   ('obs', np.float),\
                                                   ('pred', np.float)])
    obs_vs_pred['n'] = sad_sorted
    obs_vs_pred['obs'] = obs_cdf
    obs_vs_pred['pred'] = pred_cdf
    return obs_vs_pred

def get_obs_and_pred_rarity(obs_sad, pred_sad, n=10):
    '''Generates the number of observed and predicted rare species.
    Rarity is defined as the number of species with abundance less than n.

    Parameters
    ----------
    obs_sad : 1D np.array
        an array containing the observed SAD
    pred_sad : 1D np.array
        an array containing the predicted SAD 
    n : int
        species are considered rare if they have abundances less than n

    Returns
    -------
    : dict
        Dictionary of observed and predicted rare species

    '''
    obs_sad = np.array(obs_sad)
    pred_sad = np.array(pred_sad)
    assert np.all(obs_sad != 0), "Observed SAD cannot contain zeros"
    assert np.all(pred_sad != 0), "Predicted SAD cannot contain zeros"
    obs_rare = np.sum(obs_sad < n)
    pred_rare = np.sum(pred_sad < n)
    return {'obs_rare' : obs_rare, 'pred_rare' : pred_rare}

def get_obs_and_pred_Nmax(obs_sad, pred_sad):
    '''Gets the Nmax for observed and predicted sads. 

    Parameters
    ----------
    obs_sad : 1D np.array
        an array containing the observed SAD
    pred_sad : 1d np.array
        an array containing the predicted SAD
    
     Returns
    -------
    : dict
        Dictionary of observed and predicted N max

    '''
    obs_sad = np.array(obs_sad)
    pred_sad = np.array(pred_sad)
    assert np.all(obs_sad != 0), "Observed SAD cannot contain zeros"
    assert np.all(pred_sad != 0), "Predicted SAD cannot contain zeros"
    obs_Nmax = np.max(obs_sad)
    pred_Nmax = np.max(pred_sad)
    return {'obs_Nmax' : obs_Nmax, 'pred_Nmax' : pred_Nmax}

def is_sad_geo_series(sad):
    '''
    '''
    #NOTE: Should I check dimensions?
    assert type(sad) == np.ndarray or type(sad) == list or type(sad) == tuple,\
           "Sad must be a tuple, list or nd.nparray"
    
    



"""def get_values_for_sad(sad, distr):
    '''Function takes in sad and returns state variables
    and other information based on specified distribution

    Parameters
    ----------
    sad : array like object
        The empirical SAD
    
    distr : string
        The distribution to which to compare the empirical sad:
        'mete' - METE
        'mete_approx' - METE with approximation
        'plognorm' - Poisson lognormal
        'trun_plognorm' - Truncated poisson lognormal
        'neg_binom' - Negative binomial
        'geo' - Geometric
        'lgsr' - Fisher's log series
    
    Returns
    -------
    : dict
        A dictionary containing state variables and other requested values
        'S' - Total species in SAD
        'N' - Total individuals in SAD
        'Nmax_obs' - Number of individuals in most abundant species
        'rarity_obs' - Number of species with n < 10
        'distr' - dictionary of distribution specific values
            'name' - name of distribution (see above)
            'nll' - negative-log likelihood
            'AICc' - Corrected AIC
            'Nmax_pred' - Predicted Nmax
            'rarity_pred' = Predicted rarity


    '''
    assert type(sad) == tuple or type(sad) == list or type(sad) == np.ndarray,\
                'SAD must be tuple, list, or ndarray'

    sad = np.array(sad)
    if len(np.where(sad == 0)[0]) != 0:
        raise ValueError("SAD cannot contain zeros")
    value_dict = {}
    value_dict['S'] = len(sad)
    value_dict['N'] = sum(sad)
    Nmax = get_obs_and_pred_Nmax(sad, distr)
    rarity = get_obs_and_pred_rarity(sad, distr)
    value_dict['Nmax_obs'] = Nmax[0]
    value_dict['rarity_obs'] = rarity[0]
    value_dict['distr'] = {}
    value_dict['distr']['name'] = distr
    value_dict['distr']['nll'] = predict_sad.nll(sad, distr)
    value_dict['distr']['params'] = predict_sad.distr_parameters(len(sad), sum(sad),\
                                        distr, sad=sad)
    value_dict['distr']['AICc'] = aic(value_dict['distr']['nll'],\
                                    len(value_dict['distr']['params']), len(sad))
    value_dict['distr']['Nmax_pred'] = Nmax[1]
    value_dict['distr']['rarity_pred'] = rarity[1]

    return value_dict"""











