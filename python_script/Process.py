# coding : uft8
import numpy as np
import pandas as pd
import os
from DetectPoints import Init_Points as ini
from DetectPoints import DetectPattern as dct
from WriteMicMacFiles import WriteXml as wxml
from pictures_process.Handle_Exif import load_date, load_lum
from pictures_process.Stats import blurr
from shutil import copyfile



def sort_pictures(folder_path_list, ext="jpg", time=600):
    print("Collecting files\n..........................................")
    ext = ext.lower()
    list = []
    for folder_path in folder_path_list:
        image_date_list = []
        flist = os.listdir(folder_path)
        for filename in flist:
            try:
                if filename.split(".")[-1].lower() == ext:
                    image_date_list.append((filename, load_date(folder_path + filename)))
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
    print("Checking dates\n..........................................")
    # loop on the image of the first folder
    with open("linkedFiles.txt", 'w') as f:
        f.write("# Pictures taken within {} of interval\n".format(time))
    for image_ref in list[0]:
        date_ref = image_ref[1]
        pic_group = np.empty(len(list) + 1, dtype=object)
        pic_group[0] = False  # the pic_group[0] is a boolean, True if all a picture is found in every folder
        pic_group[1] = image_ref[0]
        for_file = [image_ref[0]]  # list of the images taken within the interval
        for j in range(1, len(list)):
            folder = list[j]  # list of the filename of one folder
            i, found = 0, False
            while not found and i < len(folder):  # todo retirer les images ?
                date_var = load_date(folder_path_list[j] + folder[i][0])
                diff = abs(date_ref - date_var)
                if diff.days * 86400 + diff.seconds < time:  # if the two pictures are taken within 10 minutes
                    found = True
                    pic_group[j + 1] = folder[i][0]
                i += 1

        if None not in pic_group:
            pic_group[0] = True
            print("Pictures found in every folder corresponding to the time of " + pic_group[1] + "\n")
        else:
            print("Missing picture(s) corresponding to the time of " + pic_group[1] + "\n")
        sorted_pictures.append(pic_group)
        with open("linkedFiles.txt", 'a') as f:
            f.write(str(pic_group[0]) + "," + ",".join(pic_group[1:]) + "\n")
    return sorted_pictures


def check_pictures(main_folder_path, secondary_folder_list, pictures_array, lum_inf, blur_inf):
    """
    This function is supposed to be called after sort_pictures, as it uses the kind of array created by sort_pictures,
    which could be either collected from the return value of the function, or the file "linkedFiles.txt" created in
    the main folder
    It will filter pictures in which brightness is inferior to lum_inf and the "blur" (variance of Laplacian) is
    inferior to blur_min
    :param main_folder_path:
    :param secondary_folder_list:
    :param pictures_array:
    :param lum_inf:
    :param blur_min:
    :return: same array
    """
    print("Checking dates\n..........................................")
    # loop on the image of the first folder
    with open("linkedFiles.txt", 'w') as f:
        f.write("# Pictures filtered with a minimum value of {} for brightness, {} for the variance of Laplacian\n".format(lum_inf,blur_inf))
    I, J = pictures_array.shape
    for i in range(I):
        if pictures_array[i, 0]:
            min_lum = 9999
            min_blur = 9999
            for j in range(1, J):
                path = main_folder_path + secondary_folder_list[j - 1] + pictures_array[i, j]
                lum = load_lum(path)
                if lum < min_lum:
                    min_lum = lum
                blur =blurr(path,3)
                print(blur)
                if blur < min_blur:
                    min_blur = blur

            if min_lum < lum_inf or min_blur < blur_inf:
                pictures_array[i, 0] = False
    with open(main_folder_path + "linkedFiles.txt", 'a') as f:
        for line  in pictures_array:
            f.write(str(line[0]) + "," + ",".join(line[1:]) + "\n")
    return pictures_array


def pictures_array_from_file(filepath):
    """
    Could be way more efficient ! And does not handle any error for the moment
    :param filepath:
    :return:
    """
    print("Retrieving data from file " + filepath + "\n.......................................")
    all_lines = []
    with open(filepath, 'r') as file:
        for line in file.readlines():
            if line[0] != "#":
                list_temp = line.split(',')
                length = len(list_temp)
                array_line = np.empty(length, dtype=object)
                array_line[0] = bool(list_temp[0])
                for i in range(1, length):
                    array_line[i] = list_temp[i].rstrip('\n')
                all_lines.append(array_line)
        print("Done")
        return np.array(all_lines)

def copy_and_process(filepath_list,main_folder, folder_name = "TMP_MicMac", image_path = ".*JPG", resol = 2000, distortion_model="RadialStd"):
    folder_path = main_folder + folder_name + "/"
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    for filepath in filepath_list:
        filename = filepath.split("/")[-1]
        copyfile(filepath, folder_path+ filename)

    os.chdir(main_folder + folder_name + "/")
    command = 'mm3d Tapioca All "{}" {} '.format(image_path,resol )
    os.system(command)
    command = 'mm3d Tapas {} "{}"'.format(distortion_model,image_path)
    os.system(command)
    os.system('exit')
    


def main_GCP_estim(folder_path, image, points=0):
    os.chdir(folder_path)
    pos, dist_matrix = ini.init_Points(folder_path, image, points)
    coord_list, list_tot = dct.detect_folder_opencv(folder_path + "Samples/", folder_path, pos, dist_matrix)

    # Create MicMac xml with coordinates of the samples in each picture
    wxml.write_S2D_xmlfile(coord_list, 'Appuis_fictifs-S2D.xml')

    # create a panda DataFrame storing data for stats
    labels = ['IMG', 'Pti', 'Ptj', 'XPti', 'XPtj', 'XRefPti', 'XRefPtj', 'YPti', 'YPtj', 'YRefPti', 'YRefPtj', 'Distij',
              'DistRefij']
    df = pd.DataFrame.from_records(list_tot, columns=labels)

    # todo changer le chemin en relatif
    df.to_csv('C:/Users/Alexis/Documents/Travail/Stage_Oslo/Scripts_Python/Stats/data_for_stat_cam2.csv', sep=',',
              encoding='utf-8')


if __name__ == "__main__":
    # main_GCP_estim("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/","DSC00918_11h30.JPG",points = 'selection-S2D.xml')
    # sort_pictures(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/",
    #               "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_ouest/",
    #               "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_mid/"])
    #array = pictures_array_from_file("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Scripts_Python/linkedFiles.txt")
    #print(check_pictures("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/", ["cam_est/","cam_ouest/","cam_mid/"], array, 1, 5))
    copy_and_process(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Test_06_11-22h/DSC00864.JPG","C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Test_06_11-22h/DSC01965.JPG",
                      "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/MicMac_Test_06_11-22h/DSC03480.JPG"],
                     "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/")