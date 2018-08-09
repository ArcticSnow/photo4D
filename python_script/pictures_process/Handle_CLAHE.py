"""
Created on Fri Jun 30 09:44:23 2017

@author: Guillaume, Alexis



To keep metadata when we transform the picture, we use the module pyxif (MIT License), available at :
                         https://github.com/zenwerk/Pyxif
"""


import cv2 as cv
import time
import numpy as np
import os
import pyxif


def process_clahe_folder(in_folder, tileGridSize, grey=False, out_folder="", clip_limit=2,new_name_end="_Clahe"):
    """
    Apply CLAHE to all jpeg files if a given folder
    It is not possible to overwrite files, because the initial files are needed to copy-past metadata

    :param in_folder: input folder path
    :param tileGridSize: size of the "blocks" to apply local histogram equalization
    :param grey: if True, the image will be converted to grayscale
    :param clip_limit: contrast limit, used to avoid too much noise
    :param out_folder: output folder path
    :param new_name_end: string put at the end of output files, without the extension
    :return:
    """

    # Process all the jpeg pictures in the following folder
    flist = np.sort(os.listdir(in_folder))

    for f in flist:
        try:
            if f.split(".")[-1].lower() in ["jpg","jpeg"]:
                in_path = in_folder + f
                if out_folder == "":  out_folder = in_folder
                out_path = out_folder + f[:-4] + new_name_end + ".JPG"

                process_clahe(in_path, tileGridSize, grey=grey, out_path=out_path, clip_limit=clip_limit)
        except IndexError:
            pass


def process_clahe(in_path, tileGridSize, grey=False, out_path="", clip_limit=2):
    """
    Appy CLAHE (contrast limited adaptive histogram equalization) method on an image
    for more information about CLAHE, see https://docs.opencv.org/3.1.0/d5/daf/tutorial_py_histogram_equalization.html

    Overwriting image will raise an error, as the initial image is needed to copy-past metadata
    :param in_path: input image
    :param tileGridSize: size of the "blocks" to apply local histogram equalization
    :param grey: if True, the image will be converted to grayscale
    :param out_path: output path, the folders must exists and the image extension must be valid
            by default, output will be saved as input_path/input_name_clahe.JPG
    :param clip_limit: contrast limit, used to avoid too much noise
    """
    if out_path == "":
        out_path = ".".join(inpath.split(".")[:-1]) + "_clahe.JPG"

    # read input
    print("Processing CLAHE method on " + in_path.split("/")[-1])
    img = cv.imread(in_path)

    # convert color to gray
    if grey: img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # apply a median filter before clahe
    img = cv.medianBlur(img, 3)  
    
    # create clahe object
    clahe = cv.createCLAHE(clipLimit=clip_limit, tileGridSize=(tileGridSize, tileGridSize))  # CLAHE

    # apply CLAHE for each image channel, and then recreate the full image (only useful if gray==False)
    channels_ini = cv.split(img)
    channels_final = []
    for channel in channels_ini:
        # Apply CLAHE
        channels_final.append(clahe.apply(channel))
    img_final = cv.merge(channels_final)

    # save image and write metadata from initial file
    cv.imwrite(out_path, img_final)
    pyxif.transplant(in_path, out_path)


if __name__ == "__main__":
    tic = time.time()
    inpath = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/Verif/Fin/"
    process_clahe_folder(inpath, 8, grey=True, new_name_end="_")
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
