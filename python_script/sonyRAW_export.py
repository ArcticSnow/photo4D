from __future__ import division
import os, sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import rawpy

# Include class and function here

def open_SONY_raw(filename, gamma= (2.22,4.5), output_bps=8, brightness=1, exp_shift=4, exp_preserve_highlights=0.5 ):
    with rawpy.imread(filename) as raw:
        '''
        see the documentation at:
        http://pythonhosted.org/rawpy/api/rawpy.Params.html

        ==================================================
        From the help:

        exp_shift (float): exposure shift in linear scale. Usable range from 0.25 (2-stop darken) to 8.0 (3-stop lighter).
        exp_preserve_highlights (float): preserve highlights when lightening the image with exp_shift. From 0.0 to 1.0 (full preservation).

        '''
        rgb = raw.postprocess(gamma=gamma,
                              no_auto_bright=True,
                              bright=brightness,
                              output_bps=output_bps,
                              use_camera_wb=True,
                              exp_shift=exp_shift,
                              exp_preserve_highlights=exp_preserve_highlights)
        return rgb

im_file = '/home/arcticsnow/Github/photo4D/python_script/image_sample/DSC00007.ARW'

#=============================================================================================
# Test of each rawpy process parameter functions

# gamma

gamma_left = np.linspace(0,9,9)
gamma_right = np.linspace(0,9,9)


fig = plt.figure()
for idx in xrange(9):
    ax = fig.add_subplot(3, 3, idx+1) # this line adds sub-axes
    ax.imshow(open_SONY_raw(im_file, gamma=(gamma_left[idx],4.5))) # this line creates the image using the pre-defined sub axes
    ax.set_title('gamma_left = ' + str(gamma_left[idx]))


fig = plt.figure()
for idx in xrange(9):
    ax = fig.add_subplot(3, 3, idx+1) # this line adds sub-axes
    ax.imshow(open_SONY_raw(im_file, gamma=(2.222,gamma_right[idx]))) # this line creates the image using the pre-defined sub axes
    ax.set_title('gamma_right = ' + str(gamma_right[idx]))


# brightness
bright = np.linspace(0,5,9)

fig = plt.figure()
for idx in xrange(9):
    ax = fig.add_subplot(3, 3, idx+1) # this line adds sub-axes
    ax.imshow(open_SONY_raw(im_file, brightness=bright[idx])) # this line creates the image using the pre-defined sub axes
    ax.set_title('brightness = ' + str(bright[idx]))

# Exp_shift, This parameter varies between 0.25 and 8
Exp_shift = np.linspace(0.25,8,9)

fig = plt.figure()
for idx in xrange(9):
    ax = fig.add_subplot(3, 3, idx+1) # this line adds sub-axes
    ax.imshow(open_SONY_raw(im_file, exp_shift=Exp_shift[idx])) # this line creates the image using the pre-defined sub axes
    ax.set_title('Exp_shift = ' + str(Exp_shift[idx]))

# exp_preserve_highlights, This parameter varies between 0 and 1
Exp_pr = np.linspace(0,1,9)

fig = plt.figure()
for idx in xrange(9):
    ax = fig.add_subplot(3, 3, idx+1) # this line adds sub-axes
    ax.imshow(open_SONY_raw(im_file, exp_preserve_highlights=Exp_pr[idx])) # this line creates the image using the pre-defined sub axes
    ax.set_title('Exp_shift = ' + str(Exp_pr[idx]))


# Include script in this if statement
if __name__ == '__main__':