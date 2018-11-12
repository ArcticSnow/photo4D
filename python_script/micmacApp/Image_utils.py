# coding : utf8
"""

To keep metadata when we transform the picture, we use the module pyxif (MIT License), available at :
                         https://github.com/zenwerk/Pyxif
"""


from datetime import datetime
import sys, pyxif, time, os
import cv2 as cv
import numpy as np




def load_date(filename):
    """
    Load date of the shot, according to te image metadata
    :param filename: name/path of the file
    :return: datetime format
    """
    try:
        zeroth_dict, exif_dict, gps_dict = pyxif.load(filename)
        date,time=exif_dict[pyxif.PhotoGroup.DateTimeOriginal][1].split(" ")
        year, month,day = date.split(":")
        hour,minute,sec = time.split(":")
        dateimage= datetime(int(year), int(month), int(day), int(hour), int(minute) ,int(sec))
        return dateimage
    except KeyError:
        print("WARNING No date for file " + filename)
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + filename )
        return None


def load_lum(filename):
    """
    Load luminosity of the shot scene, according to te image metadata
    :param filename: name/path of the file
    :return: float, level of brightness

    TODO: Add a method to estimate BrightnessValue of image if the field is not available from picture EXIF.
    """
    try:
        zeroth_dict, exif_dict, gps_dict = pyxif.load(filename)
        num,denom=exif_dict[pyxif.PhotoGroup.BrightnessValue][1]
        brightness=num/denom
        return brightness
    except KeyError:
        print("WARNING No brightness data for file " + filename)
        print("Check if your exif data contains a 'BrightnessValue' tag ")
        return None
    except FileNotFoundError:
        print("WARNING Could not find file " + filename )
        return None



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

def lum(filename):
    image_bgr = cv.imread(filename)
    image_lab = cv.cvtColor(image_bgr, cv.COLOR_BGR2LAB)
    average_lum = cv.mean(cv.split(image_lab)[0])
    return average_lum


def blurr(filename,ksize = 3):
    image_bgr = cv.imread(filename)  # todo la converstion en gray devrait être fait à cette ligne
    # image_gray = cv.cvtColor(image_bgr, cv.COLOR_BGR2GRAY)
    return np.log(cv.Laplacian(image_bgr, cv.CV_64F,ksize=ksize).var())