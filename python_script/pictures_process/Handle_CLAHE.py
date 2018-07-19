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
import matplotlib.pyplot as plt


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
        return rgb[12:-12,8:-8]  # Suppress border pixel, in order to match JPG size


def process_arw_clahe_folder(in_folder, tileGridSize, grey=False, metadata=False, out_folder="", new_name_end="_Clahe"):
    # Process all the .arw pictures in the following folder

    flist = np.sort(os.listdir(in_folder))

    for f in flist:
        try:
            if f.split(".")[-1].lower() == "arw":
                in_path = in_folder + f
                if out_folder == "":  out_folder = in_folder
                out_path = out_folder + f[:-4] + new_name_end + ".JPG"

                process_arw_clahe(in_path, tileGridSize, grey=grey, out_path=out_path, metadata=metadata,
                                  metadata_path="")
        except IndexError:
            pass

def process_arw_clahe(in_path, tileGridSize, grey=False, out_path="", metadata=False, metadata_path="",
                          clip_limit=2):

    if metadata and metadata_path == "":
        metadata_path = in_path[:-4] + ".JPG"

    print("Processing CLAHE method on " + in_path.split("/")[-1])
    rgb = open_SONY_raw(in_path, gamma=(2.222, 4.5), output_bps=16, brightness=1,
                            exp_shift=8, exp_preserve_highlights=1)

    im8bit = (rgb / 256).astype("uint8")  # Convert to 8-bits
    if grey: im8bit = cv2.cvtColor(im8bit, cv2.COLOR_BGR2GRAY)  # Convert to gray

    im8bit = cv2.medianBlur(im8bit, 3)  # Median Filter

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tileGridSize, tileGridSize))  # CLAHE

    channels_ini = cv2.split(im8bit)
    channels_final = []
    for channel in channels_ini:
        # Apply CLAHE for each channel
        channels_final.append(clahe.apply(channel))

    img_final = cv2.merge(channels_final)

    # save picture, keep metadata
    # metadata is taken from the JPG file with the same name in input folder
    if metadata:
        try:
            imageio.imsave(out_path, img_final)
            pyxif.transplant(metadata_path, out_path)
        except IOError:
            print("\033[0;31mWARNING Unable to open JPG , metadata are lost\033[0m")
    else:
        # Save the .JPG processed
        imageio.imsave(out_path, img_final)


if __name__ == "__main__":
    tic = time.time()
    inpath = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/TestdelaMortquitue/Mask/"
    process_arw_clahe_folder(inpath, 8, metadata=True, grey=True)

    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
