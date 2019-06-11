import cv2 as cv
import os

from photo4d.Process import pictures_array_from_file
from photo4d.Image_utils import load_date
import photo4d.XML_utils as uxml
from photo4d.Utils import exec_mm3d

from shutil import rmtree
import pandas as pd
import numpy as np


"""
Compute GCP positions using a MicMac command : Tapioca 
"""


def cut_image(image_path, pos, kernel_size, output_name="", output_folder="/"):
    """
    extract a portion of an image, centered on pos, of a given size (works for .JPG only)
    :param image_path: path of the input image
    :param pos: tuple, position for the center of output image (xpos, ypos)
    :param kernel_size: tuple, size of the output image, in pixels
    :param output_name: full name for output file (ex: "output.JPG")
    :param output_folder: folder for saving output, must already exist
    """
    if output_name == "": output_name = image_path.split('/')[-1].split(".")[-2] + "_cut" + ".JPG"
    if not os.path.exists(output_folder): os.makedirs(output_folder)
    img = cv.imread(image_path)
    pos = int(pos[0]), int(pos[1])
    ysize, xsize = img.shape[0], img.shape[1]
    if (0 <= pos[0] <= ysize) and (0 <= pos[1] <= xsize):
        xmin, xmax = pos[1] - kernel_size[1] // 2, (pos[1] + kernel_size[1] // 2)
        ymin, ymax = pos[0] - kernel_size[0] // 2, pos[0] + kernel_size[0] // 2

        output = img[ymin:ymax, xmin:xmax]

        cv.imwrite(output_folder + output_name, output)
    else:
        print("\033[0;31Position {} not in the picture {}, with size {}\image ignored\033[0m".format(pos, image_path,
                                                                                                     img.shape))


def detect_from_s2d_xml(s2d_xml_path, folder_list, pictures_array, samples_folder_list=None,
    kernel_size=(200, 200), display_micmac=False):
    """
    write extracts files from an xml with image position, and launch detection of the points for all files in folder
    :param s2d_xml_path: file created by the function SaisieAppuisInitQT, in MicMac
    :param folder_list: list of folders containing pictures. One folder is for one camera
    :param samples_folder_list: list of folder where to save samples, in the same order as folder_list
            by default, create "Samples/" folder in each camera folder
    :param pictures_array: array containing names of pictures to process
            each row is considered as a set, and pictures names must be in the same order as secondary_folder_list
            the first item of a row is a boolean, indicating if the set is valid or not
    :param kernel_size: size of the portion of picture to cut for detection (in pixels)
    :param display_micmac: to activate or stop printing MicMac log
    :return:
    Data Frame where each row store initial and detected image position of the tie points :
    [image name, gcp name, TP coord X in image_ini, TP Y ini,index of folder/camera, date,
     TP coord X in image detect, TP Y detect, coord X GCP ini, Y GCP ini]
    """
    # do some checks, and set default values for sample_folder_list
    if s2d_xml_path[-4:] != ".xml": raise IOError("The parameter S2D_xml_path must be an .xml file")
    nb_folders = len(folder_list)
    for i in range(nb_folders):
        folder = folder_list[i]
        if not os.path.exists(folder):
            raise IOError("Invalid path " + folder + " in folder_list")
        if folder[-1] != "/": folder_list[i] += "/"

    if samples_folder_list is None:
        samples_folder_list = []
        for i in range(nb_folders):
            samples_folder_list.append(folder_list[i] + "Samples/")
    elif nb_folders != len(samples_folder_list):
        print("WARNING the parameter samples_folder_list must have the same number of folders as folder_list")
        return
    for i in range(nb_folders):
        samples_folder = samples_folder_list[i]
        if not os.path.exists(samples_folder):
            try:
                os.makedirs(samples_folder)
            except IOError:
                print("WARNING Invalid path " + samples_folder + " in samples_folder_list")
                return
        if samples_folder[-1] != "/": samples_folder_list[i] += "/"

    # ==================================================================================================================
    # collect data from xml
    dict_img = uxml.read_S2D_xmlfile(s2d_xml_path)
    panda_result = []  # store all the results
    # iterate over pictures
    for image in dict_img.keys():

        dict_measures = dict_img[image]

        # try to found the image in all folders (assuming all pictures have different names)
        # if the image is found, do the detection in this folder
        found = False
        i = 0
        while not found and i < nb_folders:
            if image in os.listdir(folder_list[i]):
                found = True
                # if the image is found, launch the detection
                #  ==============================================
                print("\nDetection launched for picture {} as reference...".format(image))
                for gcp in dict_measures.keys():
                    print("\n  Detection of point {} in folder  {}/{}".format(gcp, i + 1, nb_folders))
                    pos_ini = dict_measures[gcp]
                    date = load_date(folder_list[i] + image)
                    # add a line for the master image, with the gcp position, because micmac won't launch
                    # the detection on this one, but the point coordinates are still useful
                    panda_result.append(
                        [image, gcp, kernel_size[0]/2, kernel_size[1]/2, i, date,
                         kernel_size[0] / 2, kernel_size[1] / 2, pos_ini[0], pos_ini[1], image])

                    # creation of extract for each picture of the folder, around the point initial position
                    print("  Create extract for detection :\n")
                    images_list = []  # store pictures to use for detection
                    for line in pictures_array:
                        if line[0]:
                            print("  - " + line[i + 1] + "...  ", end="")

                            cut_image(folder_list[i] + line[i + 1], (pos_ini[1], pos_ini[0]), kernel_size=kernel_size,
                                      output_folder=samples_folder_list[i] + gcp + "/", output_name=line[i + 1])
                            images_list.append(line[i + 1])
                            print("done")

                    # launch Tapioca on the selected files
                    #  ==============================================
                    # create file telling MicMac which files to process
                    uxml.write_couples_file(samples_folder_list[i] + gcp + "/" + "couples.xml", image, images_list)
                    os.chdir(samples_folder_list[i] + gcp + "/")
                    print("\n  Launching MicMac...")
                    command = "mm3d Tapioca File couples.xml -1 ExpTxt=1"
                    success, error = exec_mm3d(command, display_micmac)

                    # read results and append it to result
                    #  ==============================================
                    print(success)
                    if success == 0:
                        print("  Tapioca executed with success, reading results")
                        # read output txt files
                        for picture_recap in os.listdir("Homol/Pastis" + image):
                            if picture_recap.split(".")[-1] == "txt":
                                tie_points = uxml.get_tiepoints_from_txt("Homol/Pastis" + image + "/" + picture_recap)
                                date = load_date(folder_list[i] + picture_recap[:-4])

                                for tie_point in tie_points:
                                    # append each tie point coordinates to the result
                                    # [image name, gcp name, TP coord X in image_ini, TP Y ini,index of folder/camera,
                                    #  date, TP coord X in image detect, TP Y detect, coord X GCP ini, Y GCP ini]
                                    panda_result.append(
                                        [".".join(picture_recap.split(".")[:-1]), gcp, tie_point[0], tie_point[1], i,
                                         date,
                                         tie_point[2], tie_point[3], pos_ini[0], pos_ini[1], image])
                        try:
                            rmtree("Pastis")
                            rmtree("Tmp-MM-Dir")
                        except PermissionError:
                            print("  couldn't erase temporary files due to permission error")
                    else:
                        print("  WARNING Fail in Tapioca :  " + str(error))

            else:
                i += 1
        if not found:
            print("\033[0;31Picture {} cannot be find in folder_list\033[0m".format(image))

    return pd.DataFrame(panda_result,
                        columns=['Image', 'GCP', 'Xini', 'Yini', 'folder_index', 'date', 'Xdetect', 'Ydetect',
                                 'Xgcp_ini', 'Ygcp_ini', 'Image_ini'])


def extract_values(df, magnitude_max=50, nb_values=5, max_dist=50, kernel_size=(200, 200), method="Median"):
    """
    extract detected positions from the DataFrame containing tie points coordinates
    feel free to add new methods
    :param df: DataFrame like the one from detect_from_s2d()
    :param magnitude_max: max value in pixels for the magnitude of the vector (from ini to detect)
    :param nb_values: max values to be used for the method
            the values used are the closest from the GCP initial position
    :param max_dist: max value in pixel for the distance from the GCP to the vector origin
    :param kernel_size: size of the extracts used for detection (to determine coordinates of gcp in the extracts)
    :param method: method to use for computing positions
    :return: tuple with 2 elements:
    - a dictionary containing the computed position of GCPs in each picture, readable for the others functions,
    indexed first by picture names and then by GCP names
    - a panda DataFrame containing the computed position of GCPs in each picture
    columns :
    ['Image', 'GCP', 'Xpos', 'Ypos', 'nb_tiepoints', 'date','nb_close_tiepoints']
    """

    # compute new positions of GCP according to the shift of each tie point
    df['Xshift'] = df.Xgcp_ini + df.Xdetect - df.Xini
    df['Yshift'] = df.Ygcp_ini + df.Ydetect - df.Yini

    # compute vector module
    df['magnitude'] = np.sqrt((df.Xini - df.Xdetect) ** 2 + (df.Yini - df.Ydetect) ** 2)

    # compute vector direction
    df['direction'] = np.arctan2((df.Xini - df.Xdetect), (df.Yini - df.Ydetect)) * 180 / np.pi + 180

    # compute from gcp and tie point in the initial image (gcp is in the center of the extracts)
    pos_center = kernel_size[0] / 2, kernel_size[1] / 2
    df['dist'] = np.sqrt((df.Xini - pos_center[0]) ** 2 + (df.Yini - pos_center[1]) ** 2)

    # filter outliers having a incoherent magnitude
    df_filtered = df.loc[df.magnitude <= magnitude_max]

    dic_image_gcp = {}
    result = []
    # iterate over images
    for image, group in df_filtered.groupby(['Image']):
        dic_gcp = {}
        for gcp, group_gcp in group.groupby(['GCP']):
            nb_tiepoints = group_gcp.shape[0]
            group_gcp_filtered = group_gcp.loc[group_gcp.dist <= max_dist]
            nb_close_tiepoints = group_gcp_filtered.shape[0]
            group2 = group_gcp_filtered.nsmallest(nb_values, 'dist')
            if group_gcp_filtered.shape[0] != 0: # if there is no values left in DataFrame, the point is ignored
                if method == "Median":
                    measure = group2.Xshift.median(), group2.Yshift.median()
                elif method == "Mean":
                    measure = group2.Xshift.mean(), group2.Yshift.mean()
                elif method == 'Min':
                    measure = group2.Xshift.min(), group2.Yshift.min()
                else:
                    print('Method must be one of these values:\n"Median"\n"Min"\n"Mean"')
                    return
                date = group2.date.min()
                dic_gcp[gcp] = measure


                result.append([image, gcp, measure[0], measure[1], nb_tiepoints, date, nb_close_tiepoints])
        if dic_gcp != {}: dic_image_gcp[image] = dic_gcp


    return dic_image_gcp, pd.DataFrame(result, columns=['Image', 'GCP', 'Xpos', 'Ypos', 'nb_tiepoints', 'date',
                                                        'nb_close_tiepoints'])


if __name__ == "__main__":
    df = detect_from_s2d_xml(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet/GCP/GCPs_pick-S2D.xml",
        ["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet/Images/Cam_east",
         "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet/Images/Cam_mid",
         "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet/Images/Cam_west"],
        pictures_array=pictures_array_from_file(
            "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/Mini_projet/set_definition.txt"),
        display_micmac=False
     )
    print(df)
    df.to_csv("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/test_beau.csv", sep=",")
    # df = pd.read_csv("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/test_sift_camtot_new_gcp.csv")
    # result = extract_values(df, threshold=50, nb_values=5, max_dist=200, method="Median")
    # print(result[0])
