import cv2 as cv
from matplotlib import pyplot as plt
import os
from WriteMicMacFiles import WriteXml as wxml
from WriteMicMacFiles import ReadXml as rxml
from Process import pictures_array_from_file
from shutil import rmtree
import pandas as pd
from pictures_process.Handle_Exif import load_date
import numpy as np

"""
Compute GCP positions using MicMac Tapioca 
"""


def match_samples(folder_path, pictures_pattern=".*JPG", file=None, resol=-1):
    if folder_path[-1] != "/": folder_path += "/"
    if not os.path.exists(folder_path):
        print("\033[0;31Invalid path " + folder_path + "\033[0m")
        exit(1)
    os.chdir(folder_path)
    if file is None:
        command = "mm3d Tapioca All {} {} ExpTxt=1".format(pictures_pattern, resol)
        os.system(command)


def cut_image(image_path, pos, window_size, output_name="", output_folder=""):
    """
    extract a portion of an image, centered on pos, of a given size
    :param image_path: path of the input image
    :param pos: tuple, position for the center of output image (xpos, ypos)
    :param window_size: tuple, size of the output image, in pixels
    :param output_path:
    :return:
    """
    if output_name == "": output_name = image_path.split('/')[-1].split(".")[-2] + "_cut" + ".JPG"
    input = cv.imread(image_path)
    pos = int(pos[0]), int(pos[1])
    ysize, xsize = input.shape[0], input.shape[1]
    if (0 <= pos[0] <= ysize) and (0 <= pos[1] <= xsize):
        xmin, xmax = pos[1] - window_size[1] // 2, (pos[1] + window_size[1] // 2)
        ymin, ymax = pos[0] - window_size[0] // 2, pos[0] + window_size[0] // 2

        output = input[ymin:ymax, xmin:xmax]

        cv.imwrite(output_folder + output_name, output)
    else:
        print("\033[0;31Position {} not in the picture {}, with size {}\image ignored\033[0m".format(pos, image_path,
                                                                                                     input.shape))


# not used anymore
def compute_translation(array):
    xsum = 0
    ysum = 0
    count = 0
    for line in array:
        xshift = float(line[2]) - float(line[0])
        yshift = float(line[3]) - float(line[1])
        xsum += xshift
        ysum += yshift
        count += 1
    return xsum / count, ysum / count


def create_extracts(pictures_array, folder_list, initial_position, window_size, samples_folder):
    nb_pictures = len(pictures_array[0]) - 1
    if nb_pictures != len(folder_list):
        print("\033[0;31Wrong number of folders\033[0m")
        exit(1)

    for line in pictures_array:
        if line[0]:
            print("extracting ")


def create_extracts_from_S2D_xml(S2D_xml_path, folder_list, pictures_array, samples_folder_list=None,
                                 window_size=(200, 200)):
    """
    write extracts files from an xml with image position
    :param S2D_xml_path: file created by the function SaisieAppuisInitQT, in MicMac
    :param folder_list: list of folders containing pictures. One folder is for one camera
    :param samples_folder_list: list of folder where to save samples, in the same order as folder_list
            by default, create "Samples/" folder in each camera folder
    """

    if S2D_xml_path[-4:] != ".xml": raise IOError("The parameter S2D_xml_path must be an .xml file")
    for folder in folder_list:
        if not os.path.exists(folder):
            raise IOError("Invalid path " + folder + " in folder_list")

    # collecting data from xml
    list_img_measures = rxml.read_S2D_xmlfile(S2D_xml_path)
    panda_result = []  # just to know which image correspond to which folder
    # iterate over pictures
    for image in list_img_measures:
        image_name = image[0]
        meas_list = image[1]

        # try to found the image in all folders (assuming all pictures have different names)
        found = False
        nb_folders = len(folder_list)
        i = 0
        while not found and i < nb_folders:
            if image_name in os.listdir(folder_list[i]):
                found = True
                for measure in meas_list:
                    gcp = measure[0].rstrip(" ")
                    pos_ini = float(measure[1].split(" ")[0]), float(measure[1].split(" ")[1])
                    if folder_list[i][-1] != "/": folder_list[i] += "/"
                    if samples_folder_list is None:
                        samples_folder = "/".join(folder_list[i].split("/")[:-1]) + "/Samples/"
                    else:
                        samples_folder = samples_folder_list[i]

                    images_list = []
                    for line in pictures_array:
                        if line[0]:
                            print("lauch cut with parameters :\n",
                                  folder_list[i] + line[i + 1],
                                  (pos_ini[1], pos_ini[0]), window_size, samples_folder + gcp + "/")

                            cut_image(folder_list[i] + line[i + 1], (pos_ini[1], pos_ini[0]), window_size=window_size,
                                      output_folder=samples_folder + gcp + "/", output_name=line[i + 1])
                            images_list.append(line[i + 1])

                    wxml.write_couples_file(samples_folder + gcp + "/" + "couples.xml", image_name, images_list)
                    os.chdir(samples_folder + gcp + "/")
                    command = "mm3d Tapioca File couples.xml -1 ExpTxt=1"
                    os.system(command)
                    for picture_recap in os.listdir("Homol/Pastis" + image_name):
                        tie_points = rxml.get_tiepoints_from_txt("Homol/Pastis" + image_name + "/" + picture_recap)
                        transl = compute_translation(tie_points)
                        print(pos_ini, transl)
                        date = load_date(folder_list[i] + picture_recap[:-4])

                        for tiepoint in tie_points:
                            panda_result.append(
                                [".".join(picture_recap.split(".")[:-1]), gcp, tiepoint[0], tiepoint[1], i, date,
                                  tiepoint[2], tiepoint[3],pos_ini[0],pos_ini[1]])
                    try:
                        rmtree("Pastis")
                        rmtree("Tmp-MM-Dir")
                    except PermissionError:
                        print("couldn't erase temporary files due to permission error")

            else:
                i += 1
        if not found:
            print("\033[0;31Picture {} cannot be find in folder_list\033[0m".format(image_name))

    return pd.DataFrame(panda_result,
                        columns=['Image', 'GCP', 'Xini', 'Yini', 'folder_index', 'date', 'Xdetect','Ydetect', 'Xgcp_ini', 'Ygcp_ini'])


def extract_values(df, threshold=50,nb_values=5, max_dist=50):

    # compute new positions of GCP according to the shift of each tie point
    df['Xshift'] = df.Xgcp_ini + df.Xdetect - df.Xini
    df['Yshift'] = df.Ygcp_ini + df.Ydetect - df.Yini

    # compute vector module
    df['module'] = np.sqrt((df.Xini - df.Xdetect) ** 2 + (df.Yini - df.Ydetect) ** 2)

    # compute vector direction
    df['direction'] = np.arctan2((df.Xini - df.Xdetect), (df.Yini - df.Ydetect)) * 180 / np.pi + 180

    # compute from gcp and tie point in the initial image (gcp is in the center)
    df['dist'] = np.sqrt((df.Xini - df.Xgcp_ini) ** 2 + (df.Yini - df.Y_gcp_ini) ** 2)

    # filter outliers having a incoherent module
    df_filtered = df.loc[df.module <= threshold]

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
            measure = group2.Xshift.median(), group2.Yshift.median()

            date = group2.date.min()
            dic_gcp[gcp] = measure
            result.append([image, gcp, measure[0], measure[1], nb_tiepoints, date, nb_close_tiepoints])
        dic_image_gcp[image] = dic_gcp


    return dic_image_gcp, pd.DataFrame(result, columns=['Image', 'GCP', 'Xpos', 'Ypos', 'nb_tiepoints', 'date','nb_close_tiepoints'])

if __name__ == "__main__":
    # cut_image("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_est/DSC00877.JPG",
    #         (1356.3224072327157, 4753.768452711316), window_size = (200, 200),
    # output_folder="C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_est/Samples/GCP4/")

    # match_samples("Test_files")

    # print(compute_translation(rxml.get_tiepoints_from_Homol("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_est/Samples/GCP4/Homol/", "DSC00877_cut.JPG", "DSC00875_cut.JPG")))

    df = create_extracts_from_S2D_xml(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/MicMac_Initial/GCP-S2D.xml",
        ["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_est",
         "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_ouest",
         "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/cam_mid"],
        pictures_array=pictures_array_from_file(
            "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/Pictures/linkedFiles.txt")
    )

    df.to_csv("C:/Users/Alexis/Documents/Travail/Stage_Oslo/photo4D/python_script/Stats/test_sift.csv", sep=",")
