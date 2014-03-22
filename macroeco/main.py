"""
===========================
Main (:mod:`macroeco.main`)
===========================

This module contains functions that execute macroecological analyses specified 
by user-generated `parameters.txt` configuration files. Instructions for 
creating parameter files can be found here.

.. autosummary::
   :toctree: generated/

   main

"""

from __future__ import division
import sys
import os
import shutil
import inspect
import configparser

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from mpltools import style
style.use('ggplot')
import matplotlib as mpl  # Colorblind safe palette
mpl.rcParams['axes.color_cycle'] = ['0072B2','D55E00','CC79A7','009E73', 
                                    'E69F00','F0E442','56B4E9']

from misc import get_log
import empirical as emp
import distributions2 as mod
import compare as comp


def main(param_path='parameters.txt'):
    """
    Entry point function for analysis based on parameter files.

    Parameters
    ----------
    param_dir : str
        Path to directory containing user-generated parameter file

    """

    # Confirm file is present and extract dir
    if not os.path.isfile(param_path):
        raise IOError, "Parameter file not found at %s" % param_path
    param_dir = os.path.dirname(param_path)
        
    # Get logger and announce start
    log = get_log(param_dir, clear=True)
    log.info('Starting analysis')

    # Read parameter file into params object
    params = configparser.ConfigParser()
    try:
        params.read(param_path)
    except:
        raise ValueError, "Parameter file is invalid"

    # Do analysis for each run with options dict (params + addl options)
    run_names = params.sections()
    for run_name in run_names:
        log.info('Starting run %s' % run_name)
        options = dict(params[run_name])
        options['param_dir'] = os.path.abspath(param_dir)
        options['run_dir'] = os.path.join(param_dir, run_name)
        _do_analysis(options)
    log.info('Finished analysis successfully')


def _do_analysis(options):
    """
    Do analysis for a single run, as specified by options.

    Parameters
    ----------
    options : dict
        Option names and values for analysis

    """

    module = _function_location(options)
    core_results = _call_analysis_function(options, module)

    if module == 'emp' and ('models' in options.keys()):
        fit_results = _fit_models(options, core_results)
    else:
        fit_results = None

    _save_results(options, module, core_results, fit_results)


def _function_location(options):
    # TODO: Add check for spec module
    func_name = options['analysis'].split('.')[0]  # Ignore method if present
    emp_funcs = [x[0] for x in inspect.getmembers(emp)]
    mod_funcs = [x[0] for x in inspect.getmembers(mod)]
    if func_name in emp_funcs:
        module = 'emp'
    elif func_name in mod_funcs:
        module = 'mod'
    else:
        raise ValueError, ("No analysis of type '%s' is available" % 
                           options['analysis'])
    return module


def _call_analysis_function(options, module):
    """
    Call function and get return, using inputs from options

    Parameters
    ----------
    options : dict
        Option names and values for analysis

    Returns
    -------
    tuple or list of tuples
        First element of the tuple gives a string describing the result and the 
        second element giving the result of the analysis as a dataframe. 
        Functions in the empirical module return a list of tuples, where each 
        tuple corresponds to a split. All other functions return a single 
        tuple.

    """

    args, kwargs = _get_args_kwargs(options, module)
    return eval("%s.%s(*args, **kwargs)" % (module, options['analysis']))


def _get_args_kwargs(options, module):
    """
    Given an analysis, options, and a module, extract args and kwargs
    """

    if module == 'emp':
        options = _emp_extra_options(options)
    arg_names, kw_names = _arg_kwarg_lists(options, module)

    # Create list of values for arg_names
    args = []
    for arg_name in arg_names:
        
        if arg_name == 'patch':  # For patch arg, append actual patch obj
            args.append(options['patch'])
            continue
        if arg_name == 'self':  # Ignore self from class methods
            continue
        if arg_name == 'k':  # scipy dists use k and x, we always use x
            arg_name = 'x'
        
        try:
            exec 'args.append(eval("%s"))' % options[arg_name]
        except SyntaxError: # eval failing because option is a string
            args.append(options[arg_name])
        except:
            raise ValueError, ("Value for required argument %s not provided"
                               % arg_name)

    # Create dict with vals for kw_names
    kwargs = {}
    for kw_name in kw_names:
        if kw_name in options.keys():  # If a value is given for this kwarg
            try:
                exec 'kwargs[kw_name] = eval("%s")' % options[kw_name]
            except SyntaxError:  # eval failing because value is a string
                kwargs[kw_name] = options[kw_name]
            except:
                raise ValueError, ("Value for optional argument %s is invalid" 
                                   % kw_name)

    return args, kwargs


def _emp_extra_options(options):
    """
    Get special options patch, cols, and splits if analysis in emp module
    """

    metadata_path = os.path.normpath(os.path.join(options['param_dir'], 
                                                  options['metadata']))
    if not os.path.isfile(metadata_path):
        raise IOError, ("Path to metadata file %s is invalid." % 
                        metadata_path)

    options['patch'] = emp.Patch(metadata_path)
    options['cols'], options['splits'] = _get_cols_splits(options)

    return options


def _get_cols_splits(options):
    """
    Notes
    -----
    Always returns strings, even if dictionary or list is constructed here, to 
    ensure consistency with provided options.

    """

    cols = {}
    special_cols = ['spp_col', 'count_col', 'energy_col', 'mass_col']

    # Cols may be given as option or individual col options may be options
    if 'cols' in options.keys():
        cols = eval(options['cols'])  # Must be string representing dict
    else:
        for col in special_cols:
            cols[col] = options.get(col, None)
    
    # If col is still None, try to fall back to metadata
    for col in special_cols:
        if cols[col] is None:
            cols[col] = options['patch'].meta['Description'].get(col, None)

    # Splits may be given as option, else is set to None
    if 'splits' in options.keys():
        splits = options['splits']
    else:
        splits = None

    # Every metric requires a spp_col
    if 'spp_col' not in cols.keys():
        raise ValueError, 'spp_col not specified'

    return str(cols), str(splits)


def _arg_kwarg_lists(options, module):

    # Get names of args and kwargs to method specified by analysis option
    exec ("arg_and_kwd_names, _, _, kw_defaults = "
          "inspect.getargspec(%s.%s)" % (module, options['analysis']))
    if kw_defaults:  # If there are kwargs
        arg_names = arg_and_kwd_names[:-len(kw_defaults)]
        kw_names = arg_and_kwd_names[-len(kw_defaults):]
    else:  # If no kwargs
        arg_names = arg_and_kwd_names
        kw_names = []

    # Inspection for rv classes doesn't work since it uses args internally
    # Unless method is translate_args or fit2, appens shapes to args
    try:
        obj_meth = options['analysis'].split('.')
        if obj_meth[1] not in ['fit2', 'translate_args']:
            arg_names += eval(module+'.'+obj_meth[0]+'.'+"shapes.split(',')")
    except:
        pass

    return arg_names, kw_names


def _fit_models(options, core_results):
    """
    Fit models to empirical result from a function in emp module

    Parameters
    ----------
    options : dict
        Option names and values for analysis
    core_results : list of tuples
        Output of function in emp

    Returns
    -------
    list of dicts
        Each element in list corresponds to a split. The dict has a key for 
        each model given in options, and the value is a list of fitted 
        parameters (tuple), values (array), comparison statistic names (list), 
        and comparison statistic values (list).

    Notes
    -----
    To determine if the empirical result refers to a curve or a distribution, 
    the result dataframe is inspected for a column 'x', which indicates a 
    curve.

    """

    models = options['models'].replace(' ', '').split(';')

    # TODO: Make work for 2D results, i.e., curves, comm_sep, o_ring
    # TODO: Make work for curves in general (check if 'x' present in core_res)
    extra_results = []
    for core_result in core_results:  # Each split
        extra_result = {}
        for model in models:
            data = core_result[1]['y'].values
            fits = _get_fits(data, model)
            values = _get_values(data, model, fits)
            stat_names, stats = _get_comparison_statistic(values, fits)
            extra_result[model] = [fits, values, stat_names, stats]
        extra_results.append(extra_result)

    return extra_results


def _get_fits(data, model):
    return eval("mod.%s.fit2(data)" % model)


def _get_values(data, model, fits):

    try:
        values = eval("mod.%s.pdf(data, *fits)" % model)
    except AttributeError:
        values = eval("mod.%s.pmf(data, *fits)" % model)
    except:
        pass
    
    return values

def _get_comparison_statistic(data, fits):
    return ['AIC'], [comp.get_AIC(data, fits)]


def _save_results(options, module, core_results, fit_results):
    """
    Save results of analysis as tables and figures

    Parameters
    ----------
    options : dict
        Option names and values for analysis
    module : str
        Module that contained function used to generate core_results
    core_results : list, dataframe, or array
        Results of main analysis
    fit_results : list
        Results of comparing emp analysis to models, None if not applicable

    """

    # Ensure that output dir for this run exists and is empty
    shutil.rmtree(options['run_dir'], ignore_errors=True)
    os.makedirs(options['run_dir'])

    # Write core results
    _write_core_tables(options, module, core_results)

    # Write additional results if analysis from emp
    if module == 'emp':
        _write_split_index_file(options, core_results)

    if fit_results:  # If models given
        for i, core_result in enumerate(core_results):
            models = options['models'].replace(' ','').split(';')
            _write_fitted_params(i, models, options, fit_results)
            _write_test_statistics(i, models, options, fit_results)
            _write_comparison_plots_tables(i, models, options,
                                           core_results, fit_results)


def _write_split_index_file(options, core_results):
    """
    Write table giving index of splits, giving number and combination
    """

    f_path = os.path.join(options['run_dir'], '_split_index.csv')
    with open(f_path, 'a') as f:
        for i, core_result in enumerate(core_results):
            f.write("%i,%s\n" % (i+1, str(core_result[0])))


def _write_core_tables(options, module, core_results):
    """
    Notes
    -----
    Depending on function that was called for analysis, core_results may be a 
    list of tuples (empirical), a dataframe, an array, or a single value.

    For the list of tuples from empirical, the second element of each tuple is 
    the raw result, and we write them all with the appropriate prefix. For 
    dataframes, we write them. For arrays or single values, we convert to data 
    frames and write them.

    """

    table_name = 'core_result.csv'
    single_file_path = os.path.join(options['run_dir'], table_name)

    if module == 'emp':  # List of tuples
        for i, core_result in enumerate(core_results):
            file_path = _get_file_path(i, options, table_name)
            core_result[1].to_csv(file_path, index=False, float_format='%.4f')

    elif type(core_results) == type(pd.DataFrame()):  # DataFrame
        core_results.to_csv(single_file_path, index=False, float_format='%.4f')

    else:  # Array or single value (atleast_1d corrects for unsized array)
        df = pd.DataFrame({'y': np.atleast_1d(core_results)})
        df.to_csv(single_file_path, index=False, float_format='%.4f')


def _get_file_path(spid, options, file_name):
    return os.path.join(options['run_dir'],
                        '%i_%s' % (spid+1, file_name))


def _write_fitted_params(spid, models, options, fit_results):

    f = open(_get_file_path(spid, options, 'fitted_params.csv'), 'w')
    f.write("Model, Fit Parameters\n")

    for model in models:
        fit_result = fit_results[spid][model]
        mod_fits = str(fit_result[0])[1:-1]  # Drop parens around tuple
        f.write("%s,%s\n" % (model, mod_fits))
    f.close()


def _write_test_statistics(spid, models, options, fit_results):
    # TODO: Add delta test statistics columns

    f = open(_get_file_path(spid, options, 'test_statistics.csv'), 'w')

    # Gets stat name list from any element of result dict - same for all
    stat_names_list = next(fit_results[spid].itervalues())[2]
    stat_names_str = str(stat_names_list)[1:-1].strip("'")

    f.write("Theory, %s\n" % stat_names_str)

    for model in models:
        fit_result = fit_results[spid][model]
        fit_stats = str(fit_result[3])[1:-1]
        f.write("%s,%s\n" % (model, fit_stats))
    f.close()


def _write_comparison_plots_tables(spid, models, options, core_results, 
                                   fit_results):
    """
    Notes
    -----
    Only applies to analysis using functions from empirical in which models are 
    also given.

    - pdf/pmf vs histogram
    - cdf vs emp cdf
    - rad vs rad
    """

    core_result = core_results[spid][1]
    n_vals = len(core_result)

    # RAD
    x = np.arange(n_vals) + 1
    df = core_result.sort(columns='y', ascending=False)
    df.rename(columns={'y': 'empirical'}, inplace=True)
    df.insert(0, 'x', x)

    def calc_func(model, df, shapes):
        return eval("mod.%s.ppf((df['x']-0.5)/len(df), *shapes)" % model)[::-1]

    plot_exec_str="ax.scatter(df['x'], emp, color='k');ax.set_yscale('log')"

    _save_table_and_plot(spid, models, options, fit_results, 'data_pred_rad', 
                         df, calc_func, plot_exec_str)

    # CDF
    # TODO: This goes up by integers to max value, can be too large
    x, emp_cdf = comp.get_empirical_cdf(core_result['y'].values)
    df = pd.DataFrame({'x': x, 'empirical': emp_cdf})

    def calc_func(model, df, shapes):
        return eval("mod.%s.cdf(df['x'], *shapes)" % model)

    plot_exec_str = "ax.step(df['x'], emp, color='k', lw=3);ax.set_ylim(top=1)"

    _save_table_and_plot(spid, models, options, fit_results, 'data_pred_cdf', 
                         df, calc_func, plot_exec_str)

    # PDF/PMF
    hist_bins = 11
    emp_hist, edges = np.histogram(core_result['y'].values, hist_bins, 
                                   normed=True)
    x = (np.array(edges[:-1]) + np.array(edges[1:])) / 2
    df = pd.DataFrame({'x': x, 'empirical': emp_hist})

    def calc_func(model, df, shapes):
        try:
            return eval("mod.%s.pmf(np.floor(df['x']), *shapes)" % model)
        except:
            return eval("%s.pdf(df['x'], *shapes)" % model)

    plot_exec_str = "ax.bar(df['x']-width/2, emp, width=width, color='gray')"

    _save_table_and_plot(spid, models, options, fit_results, 'data_pred_pdf', 
                         df, calc_func, plot_exec_str)


def _save_table_and_plot(spid, models, options, fit_results, name, df, 
                         calc_func, plot_exec_str):

    f_path = _get_file_path(spid, options, '%s.csv' % name)
    p_path = _get_file_path(spid, options, '%s.pdf' % name)

    for model in models:
        fit_result = fit_results[spid][model]
        shapes = fit_result[0]
        result = calc_func(model, df, shapes)
        df[model] = result

    df.to_csv(f_path, index=False, float_format='%.4f')  # Table

    df_plt = df.set_index('x')  # Figure
    emp = df_plt['empirical']
    df_plt = df_plt.drop('empirical',1)

    width = df['x'].values[1] - df['x'].values[0]
    ax = df_plt.plot(lw=3)
    exec plot_exec_str
    ax = _pad_plot_frame(ax)
    fig = ax.get_figure()
    fig.savefig(p_path)

    plt.close('all')


def _pad_plot_frame(ax, pad=0.01):
    """
    Provides padding on sides of frame equal to pad fraction of plot
    """

    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    xrange = xmax - xmin
    yrange = ymax - ymin

    ax.set_xlim(xmin - xrange*pad, xmax + xrange*pad)
    ax.set_ylim(ymin - yrange*pad, ymax + yrange*pad)

    return ax


if __name__ == '__main__':
    main(sys.argv[1])