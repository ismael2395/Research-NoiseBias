#!/usr/bin/env python
"""This gathers the residuals and computes the bias from multiple .csv files scattered in a directory. 
Each file will not necessarily have only one row of results (although it will most of the times"""

import csv

import numpy as np 

import os

import sys

import triangle

import fisher

import math

import matplotlib.pyplot as plt

import matplotlib.mlab as mlab

import matplotlib.patches as mpatch

# import error_ellipse

import defaults

import galfun

def errorEllipseCor(centroid,correlation_matrix,alpha = 1.52):
    """Calculation for ellipse according to Dan Coe paper arxiv.0906.4123.
    One change we did was assuming that the units of x,y are not necessarily
    the same so that we instead plot the dimensionless correlation_matrix
    instead of the covariance_matrix.
    Confidence level by default is 68.3% -> alpha = 1.52 according to the 
    same paper. 
    """
    #var_x = correlation_matrix[0][0] #always 1 
    #var_y = correlation_matrix[1][1] #always 1
    rho_xy = correlation_matrix[0][1]

    #semimajor-axis
    #a = math.sqrt((var_x+var_y)/2 + 
     #   math.sqrt((((var_x - var_y)**2)/4) + var_xy**2))
    a = 1 + rho_xy
    b = 1 - rho_xy

    #semiminor-axis
    #b = math.sqrt((var_x+var_y)/2 - 
    #    math.sqrt((((var_x - var_y)**2)/4) + var_xy**2))


    #convert theta to degrees, for this ellipse always pi/4
    #theta = (1/2) * math.degrees(math.atan((2*var_xy)/(var_x-var_y)))
    theta = 45
    width = 2 * alpha * a
    height = 2 * alpha * b

    ellipse = mpatch.Ellipse(xy=centroid, width=width, height=height, 
                             angle = theta, edgecolor='r', fc='None', lw=2)

    return ellipse

def main(argv):
    (wdir, galaxy_file, rltsdir, snr, plots_dir, verbose, 
    info_file, number_fits) = (argv[1], argv[2], argv[3], float(argv[4]), 
    argv[5], argv[6], argv[7], int(argv[8]))

    names = defaults.names()
    g_parameters = galfun.GParameters(wdir=wdir, galaxy_file=galaxy_file)
    image = galfun.drawGalaxies(g_parameters=g_parameters, image = True)
    _, variance_noise = galfun.addNoise(image=image, snr=snr, noise_seed=0) 
    
    #fisher object contains results of fisher analysis
    fish = fisher.fisher(g_parameters = g_parameters, snr = snr)

    if not os.path.isdir(os.path.join(wdir, rltsdir)):
        os.mkdir(os.path.join(wdir, rltsdir))

    residuals = {}
    points = {}
    path = os.path.join(wdir,rltsdir)

    #generate residuals by reading every file in rltsdir
    for filename in os.listdir(path):
        with open(os.path.join(path,filename)) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                for param in row.keys():

                    if param not in residuals.keys(): 
                        residuals[param] = []
                    if param not in points.keys():
                        points[param] = [] 

                    residuals[param].append(float(g_parameters.params[param])
                                            -float(row[param]))

                    #pull part.
                    points[param].append((float(g_parameters.params[param])
                                            -float(row[param]))/(math.sqrt(fish.covariance_matrix[param,param])))

    biases = {param:np.mean(residuals[param]) for param in residuals.keys()}
    
    info = defaults.info(g_parameters, fish, fits_biases = biases, 
                         number_fits = number_fits)

    if verbose == 'True':
        for line in info.galaxy + info.fisher:
            print line

    if info_file == 'True':
        with open(os.path.join(wdir, names.info + '.txt'), 'w') as txtfile:
            for line in info.galaxy + info.fisher + info.fits:
                txtfile.write(line + '\n') 
    
    #produce pull plot. 
    extent = (-2.5,2.5)
    bins = 25
    norm_area = (extent[1]-extent[0]) * (number_fits/bins)

    fish_figure = plt.figure() 
    for i in range(fish.num_params): 
        for j in range(fish.num_params):
            #obtain 2d mean 
            #mean = fish.biases[fish.param_names[i]], fish.biases[fish.param_names[j]]
            mean = fish.biases[fish.param_names[i]],fish.biases[fish.param_names[j]]
            #obtain 2x2 cov matrix of the corresponding i,j elements.  
            cor = np.array([[fish.correlation_matrix[fish.param_names[a],fish.param_names[b]] for a in [i,j]] for b in [i,j]])

            if(i == j):
                #min_point = min(points[fish.param_names[i]])
                #max_point = max(points[fish.param_names[i]])
                sigma = 1 #gaussian always width of 1.
                
                #draw a gaussian for the diagonals
                    #in theory the width should some multiple of the variance of a given parameter. maybe 3, just a guess, 
                    #the number of subdivisions does not matter as long as its large enough.

                x = np.linspace(extent[0], extent[1], 1000)
                ax = fish_figure.add_subplot(fish.num_params,fish.num_params, fish.num_params * i + j + 1)
                ax.plot(x, norm_area * mlab.normpdf(x,mean[0],sigma))   
            elif(i > j):
                #draw an error_ellipse in off-diagonals.
                ellip = errorEllipseCor(centroid=mean, 
                                        correlation_matrix=cor)
                ax = fish_figure.add_subplot(fish.num_params,fish.num_params, fish.num_params * i + j + 1)
                ax.add_patch(ellip)
                # ax.set_xlim(mean[0] - 2, mean[1] + 2)
                # ax.set_ylim(mean[0] - 2, mean[1] + 2)
                # ax.autoscale(True) #useless. 
            else:
                ax = fish_figure.add_subplot(fish.num_params,fish.num_params, fish.num_params * i + j + 1)

            if(j == 0):
                ax.set_ylabel(fish.param_names[i])
            if(i == fish.num_params - 1):
                ax.set_xlabel(fish.param_names[j])

    #now we want to to do a triangle plot from triangle.py and overlap this figure. 

    #have to transform residual.values to a convenient form for the triangle plot. 
    extents = [extent]*6
    figure = triangle.corner(np.array(points.values()).transpose(), 
                             labels=fish.param_names,
                             extents = extents,
                             truths= biases.values(), plot_contours=True,
                             show_titles=True,
                             title_args={"fontsize": 12}, fig = fish_figure)
    # figure.gca().annotate("Triangle plot", xy=(0.5, 1.0), xycoords="figure fraction",
    #                       xytext=(0, -5), textcoords="offset points",
    #                       ha="center", va="top")


    print 'fisher biases predicted:'
    print fish.biases
    print 'residuals predicted:'
    print biases
    plt.show()



if __name__ == "__main__":
    main(sys.argv)