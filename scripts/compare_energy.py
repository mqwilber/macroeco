#!/usr/bin/python

'''
Script to compare energy distributions
'''

__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

import macroeco.utils.global_strings as global_str

gui_name = '''Analysis of Macroecological Energy Metrics'''

summary = '''Compares a dataset's observed energy metrics against 
             predicted energy metrics'''

explanation = ''' This script allows you to compare observed energy metrics
against predicted energy metrics. There are two energy metrics that this script
can compare: individual energy distributions (IED) and species-level energy
distributions (SED).  The IED is a distribution of the energy of each
individual within a community.  The energy of each individual can be calculated
from the the biomass using the 3/4 allometric scaling law.  Other proxies for
energy, such as leaf surface area, can be used as well.  The IED is species
blind; it does not consider what species an individual belongs to. For
normalization purposes, each value of the empirical IED is divided by the
smallest empirical energy value. 

The SED is a distribution of the energy of each individual within a species.
So, for example, a community with 30 speices would have 30 SED's, one for each
species.  The entire community's energy distribution is normalized in the exact
same way as the IED and then individuals are placed into their respective
species and the SED's are generated. 


This script outputs rank energy distribution (rad) plots in which the observed
energy distribution is compared to the distributions given in the required
parameter predicted_SED_distributions and/or predicted_IED_distributions.  For
each plot, a corresponding csv file with the same name as the plot except with
a .csv extension is output containing the data used to make the plot. For all
SED plots, the species name is printed on the top of the plot.

For more information on energy distributions please reference and references
therein:

Harte, J. 2011. Maximum Entropy and Ecology: A Theory of Abundance,
Distribution, and Energetics. Oxford University Press.

'''

subset = global_str.subset 

criteria = global_str.criteria  + ''' An energy and/or mass column MUST be
assigned for this particular analysis''' 

predicted_SED_distributions = '''This parameter is the list of SED
distributions to which you can compare your observed data. 

You may use any number of the following SED distributions:
'theta'

Example input: ['theta']
'''

predicted_IED_distributions = '''This parameter is the list of IED 
distributions to which you can compare your observed data. 

You may use any number of the following IED distributions:
'psi'

Example input: ['psi']
'''

energy_metrics = ''' This parameter allows you to specify which energy
metric(s) you would like to examine. Chose one of the following and copy
exactly: ['SED'], ['IED'], or ['SED', 'IED'].'''

required_params = {'subset' : subset, 'criteria' : criteria,
                   'predicted_SED_distributions' : predicted_SED_distributions,
                   'predicted_IED_distributions' : predicted_IED_distributions,
                   'energy_metrics' : energy_metrics}

if __name__ == '__main__':

    import logging
    from macroeco.utils.workflow import Workflow
    from macroeco.empirical import Patch
    import macroeco.compare as comp
    from macroeco.output import SEDOutput, IEDOutput

    wf = Workflow(required_params=required_params, clog=True, 
                                                            svers=__version__)
    
    for data_path, output_ID, params in wf.single_datasets():

        # Put data in patch object
        patch = Patch(data_path, subset=params['subset'])

        # Calculate empirical metrics
        sad = patch.sad(params['criteria'])
        if set(params['energy_metrics']) == set(['SED', 'IED']) or\
           set(params['energy_metrics']) == set(['sed', 'ied']) :
            cmengy = patch.ied(params['criteria'])
            spengy = patch.sed(params['criteria'])

            # Make comparison objects 
            cmprt = comp.CompareSED((spengy, cmengy, sad),
                             params['predicted_SED_distributions'], patch=True)
            cmprp = comp.CompareIED((cmengy, sad), 
                             params['predicted_IED_distributions'], patch=True)
            
            # Make output objects and output plots
            sout = SEDOutput(output_ID)
            soup = IEDOutput(output_ID)
            sout.plot_reds(cmprt.compare_reds(), criteria=cmprt.sad_criteria)
            soup.plot_reds(cmprp.compare_reds(), criteria=cmprp.sad_criteria)

        elif set(params['energy_metrics']) == set(['IED']) or\
             set(params['energy_metrics']) == set(['ied']):
            cmengy = patch.ied(params['criteria'])
            cmprp = comp.CompareIED((cmengy, sad), 
                              params['predicted_IED_distributions'],patch=True)
            soup = IEDOutput(output_ID)
            soup.plot_reds(cmprp.compare_reds(), criteria=cmprp.sad_criteria)

        elif set(params['energy_metrics']) == set(['SED']) or\
             set(params['energy_metrics']) == set(['sed']):
            cmengy = patch.ied(params['criteria'])
            spengy = patch.sed(params['criteria'])

            cmprt = comp.CompareSED((spengy, cmengy, sad),
                             params['predicted_SED_distributions'], patch=True)
            sout = SEDOutput(output_ID)
            sout.plot_reds(cmprt.compare_reds(), criteria=cmprt.sad_criteria)

        logging.info('Completed analysis %s\n' % output_ID)
    logging.info("Completed 'compare_energy.py' script")




        








