"""
Created on Fri Jun 30 09:44:23 2017

@author: Guillaume, Alexis

To keep metadata when we transform the picture, we use the module pyxif (MIT License), available at :
                         https://github.com/zenwerk/Pyxif
"""

import rawpy
import imageio
import PIL.Image
import cv2
import time
import numpy as np
import os
from io import BytesIO
import pyxif


def open_SONY_raw(filename, gamma=(2.22, 4.5), output_bps=8, brightness=1, exp_shift=4, exp_preserve_highlights=0.5):
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


def process_arw_clahe(inpath, tileGridSize, metadata=False):
    # Process all the .arw pictures in the following folder

    flist = np.sort(os.listdir(inpath))

    for f in flist:
        try:
            if f.split(".")[-1].lower() == "arw":
                path = inpath + f
                rgb = open_SONY_raw(path, gamma=(2.222, 4.5), output_bps=16, brightness=1,
                                    exp_shift=8, exp_preserve_highlights=1)

                im8bit = (rgb / 256).astype("uint8")  # Convert to 8-bits
                im_gray = cv2.cvtColor(im8bit, cv2.COLOR_BGR2GRAY)  # Convert to gray
                im_gray = cv2.medianBlur(im_gray, 3)  # Median Filter

                clahe = cv2.createCLAHE(clipLimit=15, tileGridSize=(tileGridSize, tileGridSize))  # CLAHE
                gray = clahe.apply(im_gray)  # Apply CLAHE

                if metadata:
                    try:

                        imageio.imsave(path.split(".")[0] + "_rawpy_CLAHE.JPG", gray)
                        # todo changer le [0]
                        pyxif.transplant(inpath + f.split('.')[0] + ".JPG",path.split(".")[0] + "_rawpy_CLAHE.JPG")
                    except IOError:
                        print("Unable to open JPG")
                else:
                    # Save the .tif processed
                    imageio.imsave(path.split(".")[0] + "_rawpy_CLAHE.JPG", gray)
        except IndexError:
            pass


if __name__ == "__main__":
    tic = time.time()
    inpath = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Test_06_11-22h/"
    process_arw_clahe(inpath, 8, metadata=True)

    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
