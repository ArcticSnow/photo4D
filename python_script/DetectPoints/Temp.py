# coding :utf8

import cv2 as cv
from matplotlib import pyplot as plt
import os
from pictures_process.Handle_Exif import *
from Process import pictures_array_from_file

"""
Je fait une fonction genre copy and process mais pour la détection des GCP
"""


def draw_cross(img, coord_point, size, color, thickness):
    x, y = coord_point
    xmax, xmin = int(x + size / 2), int(x - size / 2)
    ymax, ymin = int(y + size / 2), int(y - size / 2)
    cv.line(img, (xmin, ymax), (xmax, ymin), color, thickness=thickness)
    cv.line(img, (xmin, ymin), (xmax, ymax), color, thickness=thickness)
def sample_from_file(file_path):
    date, source_picture, gcp_name, pos_ini = load_sample_metadata(file_path)
    img = cv.imread(file_path)
    return {'img': img, 'pos_ini': pos_ini, 'gcp_name': gcp_name,
            'date': date, 'img_ini': source_picture,
            'path': file_path}

def create_sample(pos_ini, image_path, gcp_name="", size_sample=10, sample_folder="", sample_name=""):
    img = cv.imread(image_path)
    img_size = img.shape
    date = load_date(image_path)
    folder_path = '/'.join(image_path.split('/')[:-1]) + "/"
    image_name = image_path.split('/')[-1]
    image_ext = image_name.split('.')[-1]

    print("Creation of sample for image " + image_name)

    # set and check output path for the sample
    if sample_folder == "":
        sample_folder = folder_path + "Samples/"
        if gcp_name != "": sample_folder += gcp_name + "/"
    if not os.path.exists(sample_folder):
        os.mkdir(sample_folder)

    # set sample file name
    if sample_name == "":
        sample_name = "sample_" + image_name
    else:
        if sample_name.split('.')[-1] != image_ext:
            sample_name += "." + image_ext

    side = (max(img_size) * (size_sample / 100)) / 2

    minx, maxx, miny, maxy = int(pos_ini[1] - side), int(pos_ini[1] + side), int(pos_ini[0] - side), int(
        pos_ini[0] + side)
    sample = img[minx:maxx, miny:maxy, :]

    # write the sample file
    print(sample_folder + sample_name)
    if not os.path.exists(sample_folder + sample_name):
        print("Writting file to " + sample_folder + sample_name)
        cv.imwrite(sample_folder + sample_name, sample)
        write_sample_metadata(sample_folder+sample_name,date,image_name,gcp_name,pos_ini)

    # some of return values are just the same as input values, but it is for more interoperability with sample_from_pict
    return {'img': sample, 'pos_ini': pos_ini, 'gcp_name': gcp_name,
            'date': date, 'img_ini': image_name,
            'path': sample_folder + sample_name}


def detect_Gcp(img_scene, sample_list, method=cv.TM_CCORR_NORMED, GCP_name=None, Save_result=False, do_cross=False,
               draw_bounding=False):
    """
    :param img_path: path of image to apply feature matching opened with opencv
    :param sample_pos_list: list of tuple containing samples (opened with opencv) and their initial position for one GCP
    :param method: Open cv feature matching method (opencv documentation)
    todo peut etre dans la meme liste est plus intelligent ? ou un dico avec nom gcp, samples et ini
    :return: list of positions of max of correlation for each sample, ordered from best to worst
    """
    # loop on every image selected for a given ground point/sample
    list_correl = []  # stores the best feature matching for the all the samples of one GCP (value and position)
    for sample_dico in sample_list:
        sample = sample_dico['img']
        sample_size = sample.shape[0]
        pos_ini = sample_dico['pos_ini']  # initial position of the GCP for sample
        shift = sample_size / 2  # The point of interest must be in the center of the picture, which is square shaped

        # we assume that there is no such a big move between this scene_image and the previous,
        # so we can restrain research area near the initials positions (all scene images must have the same size)
        minx, maxx, miny, maxy = int(pos_ini[0] - 2 * shift), int(pos_ini[0] + 2 * shift), int(
            pos_ini[1] - 2 * shift), int(pos_ini[1] + 2 * shift)
        # do template matching on the restricted area
        result = cv.matchTemplate(img_scene[miny:maxy, minx:maxx], sample, method)
        if draw_bounding:
            cv.rectangle(img_scene, (minx, miny), (maxx, maxy), 255, 3)  # if we want to display the matching area

        # collecting max and min
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
        # correct location, which are for now relative to the matching area, and indicating the top letf of matched sample
        min_loc = min_loc[0] + minx + shift, min_loc[1] + miny + shift
        max_loc = max_loc[0] + minx + shift, max_loc[1] + miny + shift
        # add best match to list_correl
        if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
            list_correl.append((min_val, min_loc))
        else:
            list_correl.append((max_val, max_loc))
    # order list_correl from best match to worst according to method used
    list_correl.sort(reverse=method not in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED])
    if do_cross:
        draw_cross(img_scene, list_correl[0][1], 8, 255, 4)

    return list_correl


def process_Gcp(main_folder_path, secondary_folder_list, pictures_array,
                samples_folder_list=None, save_res = False, do_cross = True, draw_bounding=True) :
    nb_pictures = len(pictures_array[0]) - 1 # remove the boolean from the count
    if len(secondary_folder_list) != nb_pictures:
        raise IndexError("It is needed to have the same number of pictures in a row of pictures_array than secondary folders")

    # load samples
    if samples_folder_list == None:
        samples_folder_list = []
        for folder in secondary_folder_list:
            samples_folder_list.append(folder + "Samples/")
    if len(secondary_folder_list) != nb_pictures:
        raise IndexError("It is needed to have the same number of pictures in a row of pictures_array than sample folders")


    samples_list = []
    for sample_folder in samples_folder_list:
        if os.path.exists(main_folder_path+sample_folder):
            samples_list.append(samples_from_directory(main_folder_path+sample_folder))

        else:
            samples_list.append({}) # todo voir appres, soit on a des pos ini et on crée, soit on se suicide

    for line in pictures_array:
        if line[0]:
            for i in range(nb_pictures):
                image_name = line[i + 1]
                image_path = main_folder_path + secondary_folder_list[i] + image_name
                print(image_path)
                image = cv.imread(image_path)
                image_result = [image_name]
                for gcp, samples in samples_list[i].items(): # todo iterer sur les gcp
                    print("\nDetection of point {} in image {}".format(gcp,image_name))
                    result = detect_Gcp(image,samples, GCP_name=gcp, do_cross=do_cross)
                    print("   detected at position {} with a score of {}, using a total of {} samples".format(
                        result[0][1], round(result[0][0], 3), len(samples)))
                    image_result.append((gcp,"{} {}".format(result[0][1][0],result[0][1][1])))
                if save_res:
                    ext = image_name.split('.')[-1]
                    cv.imwrite(main_folder_path + secondary_folder_list[i] + '.'.join(image_name.split('.')[:-1]) +
                               "_result." + ext,image)
def samples_from_directory(folder_path, ext = "jpg"):
    gcp_dico = {}
    for file in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path, file)):
            gcp_name = file  # I decided to use the directory name to identify the gcp
            sample_list = []
            for sample in os.listdir(os.path.join(folder_path + gcp_name) + "/"):
                if sample.split('.')[-1].lower() == ext:
                    sample_list.append(sample_from_file(os.path.join(folder_path,gcp_name,sample)))
            gcp_dico[gcp_name]=sample_list
    return gcp_dico


def presque_process(liste):
    score = 0
    liste_result = []
    for file in os.listdir("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est"):
        if file.split('.')[-1] == "JPG":
            img_scene = cv.imread(
                "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/" + file, 1)
            result = detect_Gcp(img_scene, liste)
            print("\nPicture {} processed for point {}".format(file, "GCP 4"))
            print("  {} samples were used\n  better match is at ({},{}) and with a score of {} ".format(len(result),
                                                                                                        result[0][1][0],
                                                                                                        result[0][1][1],
                                                                                                        result[0][0]))
            if 4750 < result[0][1][0] < 4755: score += 1
            draw_cross(img_scene,
                       (result[0][1][0], result[0][1][1]), sam1.shape[0], 255, 2)
            cv.imwrite(
                "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/" + file + "_oups.jpg",
                img_scene)
            liste_result.append(result)
    print(liste_result)
    print(score)


if __name__ == "__main__":
    score = 0
    sam1 = cv.imread(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samples/sample_1.jpg", 1)
    sam2 = cv.imread(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/plus de cam est/Samplesbis/sample_1.jpg",
        1)
    liste = [{'img': sam1, 'pos_ini': (4753.29546896857028, 1357.93743235653028), 'date': 'ok'}]
    #presque_process(liste)
    process_Gcp("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/",
                ["cam_est/", "cam_ouest/", "cam_mid/"],
                pictures_array_from_file("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/linkedFiles.txt"),
                save_res=True)



