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
import skimage.color as color
im_hsv = color.rgb2hsv(im)

plt.imshow(im_hsv[:,:,1], cmap=plt.cm.gray)



#===================================
# Methods to test and assess which is best in diverse lighting situations

#-----------------------------------
# Method 1: Simple thresholding

from skimage import exposure as xp

im_eq = xp.equalize_adapthist(im_hsv[:,:,2])

plt.figure()
plt.imshow(im_eq, cmap=plt.cm.gray)

plt.figure()
plt.imshow(im_hsv[:,:,2], cmap=plt.cm.gray)

im_thr_1 = im_eq<.4

plt.figure()
plt.imshow(im_thr_1 * im_eq, cmap=plt.cm.gray)

plt.figure()
plt.imshow(-im_thr_1 * im_eq, cmap=plt.cm.gray)


plt.figure()
plt.imshow(xp.equalize_hist(-im_thr_1 * im_eq)+xp.equalize_hist(im_thr_1 * im_eq), cmap=plt.cm.gray)

im_hsv_eq = im_hsv
im_hsv_eq[:,:,2] = xp.equalize_hist(-im_thr_1 * im_eq)+im_thr_1 * im_eq
rgb = color.hsv2rgb(im_hsv_eq)

plt.figure()
plt.imshow(im)

#-----------------------------------
# Method 2: Chan-Vese Segmentation
# http://scikit-image.org/docs/dev/auto_examples/segmentation/plot_chan_vese.html#sphx-glr-auto-examples-segmentation-plot-chan-vese-py

from skimage import data, img_as_float
from skimage.segmentation import chan_vese

cv = chan_vese(im_hsv[:,:,2], mu=0.25, lambda1=1, lambda2=1, tol=1e-3, max_iter=200,
               dt=0.5, init_level_set="checkerboard", extended_output=True)

fig, axes = plt.subplots(2, 2, figsize=(8, 8))
ax = axes.flatten()

ax[0].imshow(image, cmap="gray")
ax[0].set_axis_off()
ax[0].set_title("Original Image", fontsize=12)

ax[1].imshow(cv[0], cmap="gray")
ax[1].set_axis_off()
title = "Chan-Vese segmentation - {} iterations".format(len(cv[2]))
ax[1].set_title(title, fontsize=12)

ax[2].imshow(cv[1], cmap="gray")
ax[2].set_axis_off()
ax[2].set_title("Final Level Set", fontsize=12)

ax[3].plot(cv[2])
ax[3].set_title("Evolution of energy over iterations", fontsize=12)

fig.tight_layout()
plt.show()

import skimage.segmentatio
#-----------------------------------
# Method 3: Random walker segmentation
# http://scikit-image.org/docs/dev/auto_examples/segmentation/plot_random_walker_segmentation.html#sphx-glr-auto-examples-segmentation-plot-random-walker-segmentation-py


from skimage.segmentation import random_walker
from skimage.data import binary_blobs
from skimage.exposure import rescale_intensity
import skimage

# Generate noisy synthetic data
data = skimage.img_as_float(im_hsv[:,:,2])
sigma = 0.35
data += np.random.normal(loc=0, scale=sigma, size=data.shape)
data = rescale_intensity(data, in_range=(-sigma, 1 + sigma),
                         out_range=(-1, 1))

# The range of the binary image spans over (-1, 1).
# We choose the hottest and the coldest pixels as markers.
markers = np.zeros(data.shape, dtype=np.uint)
markers[data < -0.95] = 1
markers[data > 0.95] = 2

# Run random walker algorithm
labels = random_walker(data, markers, beta=10, mode='bf')

# Plot results
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(8, 3.2),
                                    sharex=True, sharey=True)
ax1.imshow(data, cmap='gray', interpolation='nearest')
ax1.axis('off')
ax1.set_adjustable('box-forced')
ax1.set_title('Noisy data')
ax2.imshow(markers, cmap='magma', interpolation='nearest')
ax2.axis('off')
ax2.set_adjustable('box-forced')
ax2.set_title('Markers')
ax3.imshow(labels, cmap='gray', interpolation='nearest')
ax3.axis('off')
ax3.set_adjustable('box-forced')
ax3.set_title('Segmentation')

fig.tight_layout()
plt.show()

# Include script in this if statement
if __name__ == '__main__':