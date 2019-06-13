# coding : utf8
"""

To keep metadata when we transform the picture, we use the module pyxif (MIT License), available at :
                         https://github.com/zenwerk/Pyxif
"""


from datetime import datetime
import pyxif, os
import cv2 as cv
import numpy as np



def sort_pictures(folder_path_list, output_path, ext="jpg", time_interval=600):
    """
    Regroup pictures from different folders if they are taken within timeInterval seconds of interval.
    Result is stored in an array/file,
    :param folder_path_list: list of the path to folders containing pictures, each folder is for one camera
    :param output_path: path of the output .txt file containing picture sets
    :param ext: extension of the pictures
    :param time_interval: interval in seconds, with corresponds to the maximum time elapsed between the shooting of pics
    :return: array with the sorted pictures. For each set a boolean is added, always True, but can be modified later
    """
    print("\n Collecting files\n..........................................")
    # create a list containing image names and dates for each folder
    list = []
    for folder_path in folder_path_list:
        image_date_list = []
        flist = os.listdir(folder_path)
        for filename in flist:
            try:
                if filename.split(".")[-1].lower() == ext.lower():
                    image_date_list.append((filename, load_date(os.path.join(folder_path,filename))))
            except IndexError:
                pass
        list.append(image_date_list)
    if len(list) < 1:
        print("WARNING not enough folder\nTwo or more folders are needed to sort files")
        return None
    elif [] in list:
        print("WARNING No image found in One or many folder(s)")
        return None

    sorted_pictures = []
    print(" Checking dates\n..........................................")
    with open(output_path, 'w') as f:
        f.write("# Pictures taken within {} of interval\n".format(time_interval))

    good, bad = 0, 0  # counters for correct and wrong sets
    # loop on the image of the first folder
    for image_ref in list[0]:
        date_ref = image_ref[1]
        pic_group = np.empty(len(list) + 2, dtype=object)
        pic_group[0] = date_ref.strftime("%Y-%m-%dT%H-%M-%S")
        pic_group[1] = False  # the pic_group[0] is a boolean, True if all a picture is found in every folder
        pic_group[2] = image_ref[0]
        # for_file = [image_ref[0]]  # list of the images taken within the interval

        # check for pictures taken whithin the interval
        for j in range(1, len(list)):
            folder = list[j]  # list of the (filename,date) of one folder
            i, found = 0, False
            while not found and i < len(folder):
                date_var = folder[i][1]
                diff = abs(date_ref - date_var)
                if diff.days * 86400 + diff.seconds < time_interval:  # if the two pictures are taken within 10 minutes
                    found = True
                    pic_group[j + 2] = folder[i][0]
                i += 1

        if None not in pic_group:
            good += 1
            pic_group[1] = True
            print(" Pictures found in every folder corresponding to the timeInterval " + pic_group[0] + "\n")
        else:
            bad += 1
            print(" Missing picture(s) corresponding to the timeInterval " + pic_group[0] + "\n")
                  
        sorted_pictures.append(pic_group)                 
        with open(output_path, 'a') as f:
            f.write(pic_group[0] + "," + str(pic_group[1]) + "," + ",".join(str(pic_group[2:])) + "\n")

    end_str = "# {} good set of pictures found, {} uncomplete sets, on a total of {} sets".format(good, bad, good + bad)
    print(end_str)
    with open(output_path, 'a') as f:
        f.write(end_str)
    return np.array(sorted_pictures)



def check_picture_quality(folder_list, output_path, pictures_array, lum_inf, blur_inf):
    """
    This function is supposed to be called after sort_pictures, as it uses the kind of array created by sort_pictures,
    which could be either collected from the return value of the function, or the file "linked_files.txt" created in
    the main folder
    It will filter pictures in which brightness is inferior to lum_inf and the "blur" (variance of Laplacian) is
    inferior to blur_min
    :param folder_list:
    :param output_path:
    :param pictures_array:
    :param lum_inf:
    :param blur_min:
    :return: same array, but some booleans will be set to False
    """
    print("\n Checking pictures\n..........................................")

    with open(output_path, 'w') as f:
        f.write(
            "# Pictures filtered with a minimum value of {} for brightness, {} for the variance of Laplacian\n".format(
                lum_inf, blur_inf))

    good, bad = 0, 0
    I, J = pictures_array.shape
    for i in range(I):
        if pictures_array[i, 1]:
            min_lum = 9999
            min_blur = 9999
            for j in range(2, J):
                path = os.path.join(folder_list[j - 2],pictures_array[i, j])
                lum = load_bright(path)

                if lum < min_lum:
                    min_lum = lum
                blur = blurr(path, 3)
                if blur < min_blur:
                    min_blur = blur

            if min_lum < lum_inf or min_blur < blur_inf:
                pictures_array[i, 1] = False
                bad += 1
            else:
                good += 1

    with open(output_path, 'a') as f:
        for line in pictures_array:
            f.write(str(line[0]) + "," + str(line[1]) + "," + ",".join(str(line[2:])) + "\n")
        end_line = " {} good set of pictures found, {} rejected sets, on a total of {} sets".format(good, bad, good + bad)
        f.write("#" + end_line)
        print(end_line)
    return pictures_array



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


def load_bright(filename):
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


def calc_lum(filename):
    image_bgr = cv.imread(filename)
    image_lab = cv.cvtColor(image_bgr, cv.COLOR_BGR2LAB)
    average_lum = cv.mean(cv.split(image_lab)[0])
    return average_lum



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
        out_path = ".".join(in_path.split(".")[:-1]) + "_clahe.JPG"

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

def blurr(filename,ksize = 3):
    image_bgr = cv.imread(filename)  # todo la converstion en gray devrait être fait à cette ligne
    # image_gray = cv.cvtColor(image_bgr, cv.COLOR_BGR2GRAY)
    return np.log(cv.Laplacian(image_bgr, cv.CV_64F,ksize=ksize).var())