#!/usr/bin/python

'''
Script to compare sads
'''

__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

from macroeco.utils import global_strings

gui_name = '''Analysis of Species Abundance Distributions'''

summary = '''Compares a dataset's observed species abundance distribution
against predicted species abundance distributions'''


subset = '''Specifications for how you want to subset your data before the
analysis. Note that only the subsetted data will be included in the analysis.
The left-hand dropdown box contains all the columns of your dataset and you may
choose one or more to subset. Please see analysis explanation for more detail
and examples.'''

criteria = '''Specifications for how you want to divide your data during the
analysis. The words you see below are the shared columns of your dataset(s).
You must designate your species column with the special word 'species' found in
the dropdown menu. You are not required to fill any additional columns for this
analysis. Please see analysis explanation for more detail and examples.'''

# NOTE: Need to find a different way to specify which distributions they can
# use
predicted_SAD_distributions = '''A list of  SAD
distributions to which you can compare your observed data. 

You may use any number of the following SAD distributions: {!s} 

Example input: ['logser', 'plognorm_lt'] or ['nbd_lt']. The brackets MUST be
included.'''.format(global_strings.SAD_distributions)

rarity_measure = global_strings.rarity_measure + ''' In this analysis, the rarity
counts refer to individuals per species.'''

explanation = '''
ANALYSIS EXPLANATION\n
This script allows you to compare an observed species abundance distribution
(SAD) against any number of predicted SADs. An SAD is a distribution of the
number of individuals within each species for an entire community.  This
distribution can also be thought of as the probability that a given species in
your community will have 'n' individuals. If you were to fully census a
community with S species and N individuals, the N individuals would be
distributed among the S species in a certain way.  Ecologists often predict
that this "certain way" will take the form of a logseries or lognormal
distribution.  These predicted distributions are among some of the
distributions against which you can compare your observed SAD. For more
information on SADs please see the provided references and the references
therein.

This script outputs cumulative density function (cdf) plots and rank abundance
distribution (rad) plots in which the observed SAD distribution is compared to
the distributions given in the required parameter predicted_SAD_distributions.
For each plot, a corresponding csv file with the same name as the plot except
with a .csv extension is output containing the data used to make the plot.  In
addition, a summary .txt file is output containing summary values for the plot
and fitting statistics for the different predicted distributions you
choose. If you choose to split up your data, individual SADs are generated for
each subsection.  For example, if you had data from three different years and
you choose to split your data by year, you would get three SAD comparisons, one
for each year.


PARAMETER EXPLANATIONS

*** subset ***:

{0}

*** criteria ***:

{1}

*** rarity_measure ***:

{2}

*** predicted_SAD_distributions ***:

{3}

REFERENCES

Magurran, A. E. 1988. Ecological Diversity and Its Measuremnt. Princeton
University Press.

May, R. M. 1975. Patterns of species abundance and diversity. In Ecology and
Evolution of Communities (eds M. L. Cody and J. M. Diamond), Harvard University
Press.
'''.format(global_strings.subset, global_strings.criteria, global_strings.rarity_measure,
predicted_SAD_distributions)

required_params = {'criteria' : criteria, 'rarity_measure' : rarity_measure,
		           'predicted_SAD_distributions': predicted_SAD_distributions}

optional_params = {'subset' : (subset + ''' Optional. Default: ''', {})}

if __name__ == '__main__':

    import logging
    from macroeco.utils.workflow import Workflow
    from macroeco.empirical import Patch
    import macroeco.compare as comp
    from macroeco.output import DistOutput

    wf = Workflow(required_params=required_params,
                  clog=True, svers=__version__)

	    
    
    for data_path, output_ID, params in wf.single_datasets():
        for optpar in optional_params: #TODO: Move to workflow
            if not optpar in params:
                logging.info("Default value for {!s} in {!s}: {!s}".format(optpar,
                              output_ID,  str(optional_params[optpar][1])))
                params[optpar] = optional_params[optpar][1]

        patch = Patch(data_path, params['subset'])
        sad = patch.sad(params['criteria'], clean=True)

        cmpr = comp.CompareSAD(sad,
                            params['predicted_SAD_distributions'], patch=True)
        rads = cmpr.compare_rads()
        summary = cmpr.summary(rads, mins_list=params['rarity_measure'])
        
        sout = DistOutput(output_ID, 'sad')
        sout.write_summary_table(summary, criteria=cmpr.criteria)
        sout.plot_rads(rads, criteria=cmpr.criteria)
        sout.plot_cdfs(cmpr.compare_cdfs(), cmpr.data_list,
                        criteria=cmpr.criteria)
        logging.info('Completed analysis %s\n' % output_ID)
    logging.info("Completed 'compare_sad.py' script")




        







