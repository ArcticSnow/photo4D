from __future__ import division
import os, sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import skimage as sk

'''
Find best way to segment snow from rocks.

First test using the JPEG image

Export two images from raw:
    1 with good exposition for whites
    1 with good exposition for rocks

Once segmented, equalize histogram, and combine the two segmented images
'''

#===================================
# Load JPEG image

im_file = '/home/arcticsnow/Github/photo4D/python_script/image_sample/DSC00007.JPG'
im = plt.imread(im_file)

#===================================
# Methods to test and assess which is best in diverse lighting situations

#-----------------------------------
# Method 1: Simple thresholding


#-----------------------------------
# Method 2: Chan-Vese Segmentation
# http://scikit-image.org/docs/dev/auto_examples/segmentation/plot_chan_vese.html#sphx-glr-auto-examples-segmentation-plot-chan-vese-py

#-----------------------------------
# Method 3: Random walker segmentation
# http://scikit-image.org/docs/dev/auto_examples/segmentation/plot_random_walker_segmentation.html#sphx-glr-auto-examples-segmentation-plot-random-walker-segmentation-py


# Include script in this if statement
if __name__ == '__main__':