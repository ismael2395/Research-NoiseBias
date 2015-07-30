#!/usr/bin/env python
"""Allows the user to do N fittings of a galaxy produced in generate.py given a SNR and compare with the fisher formalism by displaying biases and 
correlation coefficients,etc. and also by displaying a triangle plot that summarizes this results and displays data points."""

import argparse

import os

import defaults
                                                                                
def main():
    """Give the instructions to run a bunch of fits either here or in SLAC and to reproduce results and produce triangle plot."""

    cts = defaults.constants()
    names = defaults.names()

    parser = argparse.ArgumentParser(description = 'Displays a triangle plot comparing the expected noise bias calculation with the fisher matrix formalism for a given file of galaxies.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--wdir', default = names.wdir, metavar = 'DIRECTORY', type = str,
    help = 'Specify a directory name where the output will be inputted and files read from.')
    parser.add_argument('--plots-dir', default = names.plots_dir, metavar = 'PLOTDIRECTORY', type = str,
    help = 'Specify a directory name where the plots will be saved')
    parser.add_argument('--galaxy-file', default = names.galaxy_file, metavar = 'FILENAME', type = str,
    help = 'Specify a file where galaxies will be registered or read from.')
    parser.add_argument('-rltsdir', default = names.rltsdir, metavar = 'RESULTS', type = str,
    help = 'Specify a directory where output data from fits will be produced')
    parser.add_argument('--snr', metavar = 'SNR', default = cts.snr, type = int,
    help = 'Specify signal to noise ratio of the run. Should use same snr between run_fits and produce_results, else it does not work.')
    parser.add_argument('-n', '--number-fits', default = 1, 
    type = int,
    help = 'Specify how many fits are run.')
    parser.add_argument('--run-fits', action = 'store_true',
    help = 'Run N different instantiations of noise of the added galaxies to \produce a triangle plot. Fits all galaxies in given file N times.')
    parser.add_argument('--run-fits-slac', metavar = 'SLAC_COMPUTER',
    help = 'Same as above but have to be logged in a SLAC computer.')
    parser.add_argument('--produce-results', action = 'store_true',
    help = 'Read each of the files produces from a fits trial in rltsdir and create a .csv file in the same directory, triangle.png (the graph of results) and sumresults.csv (condensation of all files that are processed by triangle.png)')
    parser.add_argument('--verbose', action = 'store_true',
    help = 'Prints technical information about the galaxy and the defaults used for the fitting')
    parser.add_argument('--info-file', action = 'store_true',
    help = 'Write relevant information to a .txt file for future reference')

    args = parser.parse_args()

    if args.run_fits:
        for i in range(args.number_fits):
            os.system("python runfits.py " + str(i) + " " +  str(args.snr) + " " +  str(args.wdir) + " " + str(args.galaxy_file) + " " + str(args.rltsdir))
        #print info about the fit just in case. 
        print 'Finish ' + str(args.number_fits) + ' fit with snr of ' + str(args.snr)

    elif args.run_fits_slac:
        os.system("bsub -q " + str(args.run_fits_slac) + " -J \"name[1-" + str(args.number_fits) + "]\" \"python runfits.py \$LSB_JOBINDEX " 
            + str(args.snr) + " " + str(args.wdir) + " " + str(args.galaxy_file) + " " + str(args.rltsdir) + "\"")

    elif args.produce_results:
        os.system("python readfits.py " +  str(args.wdir) + " " + str(args.galaxy_file) + " " + str(args.rltsdir) + " " + str(args.snr) + " " + str(args.plots_dir) + " " + str(args.verbose) + " " + str(args.info_file) + " " + str(args.number_fits))

if __name__ == '__main__':
    main()