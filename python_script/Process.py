# coding : uft8
import numpy as np
import pandas as pd
import os
from DetectPoints import Init_Points as ini
from DetectPoints import DetectPattern as dct
from WriteMicMacFiles import WriteXml as wxml
from WriteMicMacFiles import ReadXml as rxml
from pictures_process.Handle_Exif import load_date, load_lum
from pictures_process.Stats import blurr
from shutil import copyfile, rmtree, copytree
import time


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
        f.write(
            "# Pictures filtered with a minimum value of {} for brightness, {} for the variance of Laplacian\n".format(
                lum_inf, blur_inf))
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
                blur = blurr(path, 3)
                print(blur)
                if blur < min_blur:
                    min_blur = blur

            if min_lum < lum_inf or min_blur < blur_inf:
                pictures_array[i, 0] = False
    with open(main_folder_path + "linkedFiles.txt", 'a') as f:
        for line in pictures_array:
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


def copy_and_process(filepath_list, main_folder, folder_name="TMP_MicMac", image_path=".*JPG", resol=2000,
                     distortion_model="RadialStd", C3DC_type="MicMac", InCal=None, InOri=None, pictures_Ori=None):
    date = load_date(filepath_list[0])
    if date is not None:
        date_str = "{}-{}-{}_{}-{}".format(date.year, date.month, date.day, date.hour, date.minute)
        folder_path = main_folder + folder_name + "_" + date_str + "/"
    else:
        folder_path = main_folder + folder_name + filepath_list[0].split('/')[-1]
        date_str = filepath_list[0].split('/')[-1]  # if we can't find a date, put the name of the first picture...

    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    for filepath in filepath_list:
        filename = filepath.split("/")[-1]
        if filepath != folder_path + filename:
            copyfile(filepath, folder_path + filename)

    # detection of Tie points
    os.chdir(folder_path)
    command = 'mm3d Tapioca All "{}" {} ExpTxt=1'.format(image_path, resol)
    print(command)
    os.system(command)
    # relative orientation
    if InOri is not None:
        final_pictures = []
        new_Ori_path = folder_path + InOri.split('/')[-2] + "/"
        if not os.path.exists(new_Ori_path):
            copytree(InOri, new_Ori_path)  # We assume that the path is correctly written ( "/fgg/Ori-Truc/")
        for filepath in filepath_list:
            final_pictures.append (filepath.split("/")[-1])
        print(pictures_Ori)
        print(final_pictures)
        wxml.change_Ori(pictures_Ori, final_pictures,new_Ori_path)

    elif InCal is not None:
        new_Cal_path = folder_path + InCal.split('/')[-2] + "/"
        if not os.path.exists(new_Cal_path):
            copytree(InCal, new_Cal_path)  # We assume that the path is correctly written ( "/fgg/Ori-Truc/")
        command = 'echo | mm3d Tapas {} "{}" InCal={} ExpTxt=1'.format(distortion_model, image_path,
                                                                       InCal.split('/')[-2])
        print(command)
        os.system(command)
    else:
        command = 'echo | mm3d Tapas {} "{}" ExpTxt=1'.format(distortion_model, image_path)
        print(command)
        os.system(command)
        # todo rajouter figee


    # making Tie points cloud
    # here distortion_model is just the Orientation folder default name, from previous step
    command = 'echo | mm3d AperiCloud "{}" {} ExpTxt=1'.format(image_path, distortion_model)
    print(command)
    os.system(command)

    ply_name = date_str + "_" + C3DC_type + ".ply"  # todo le mettre en parametre
    command = 'echo | mm3d C3DC {} "{}" {} ExpTxt=1 Out={}'.format(C3DC_type, image_path, distortion_model, ply_name)
    print(command)
    os.system(command)
    os.system('exit')

    # Make stats about the reconstruction
    with open(date_str + '_recap.txt', 'w') as recap:
        recap.write("Summary of MicMac 3D reconstruction for " + date_str + "\n")
        string = "\nNumber of Tie Points : "
        df, tot = rxml.count_tiepoints_from_txt(folder_path)
        string += str(tot) + "\n\nFiles used :\n"
        for i in df.index.values:
            string += "  - {} taken on {}\n".format(i, load_date(folder_path + i))
        recap.write(string)

        if os.path.exists(folder_path + ply_name):
            copyfile(folder_path + ply_name, main_folder + "Result/" + ply_name)
            recap.write("\nStatus  : Success\n")
        else:
            recap.write("\nStatus  : Failure\n")

        # write a .txt with residuals
        if os.path.exists(folder_path + "Ori-" + distortion_model + "/"):  # if Tapas command worked
            dict = rxml.residual2txt(folder_path + "Ori-" + distortion_model + "/")
            recap.write("\nNumber of iterations : {}   Average Residual : {}\n".format(dict['nb_iters'], "%.4f" % dict[
                'AverageResidual']))
            recap.write("\nName           Residual     PercOk        Number of Tie Points\n")
            for i in df.index.values:
                recap.write(
                    "{} : {}       {}       {}\n".format(i, "%.4f" % float(dict[i][0]), "%.4f" % float(dict[i][1]),
                                                         dict[i][2]))
    copyfile(folder_path + date_str + '_recap.txt', main_folder + "Result/" + date_str + '_recap.txt')

    # delete temporary MicMac Files todo plutôt supprimer le dossier entier
    try:
        rmtree(folder_path + "Tmp-MM-Dir")
        rmtree(folder_path + "Ori-InterneScan")
        rmtree(folder_path + "Homol")
        rmtree(folder_path + "Pastis")
        rmtree(folder_path + "Pyram")
        rmtree(folder_path + "PIMs-" + C3DC_type)
        os.remove(folder_path + "cAppliMMByPair_0")
        os.remove(folder_path + "MMByPairCAWSI.xml")
        os.remove(folder_path + "MMByPairFiles.xml")
        os.remove(folder_path + "SauvApero.xml")  # todo peut être laisser celui là
        os.remove(folder_path + "WarnApero.txt")
    except FileNotFoundError:
        pass
    except PermissionError:
        print("Permission Denied :'(")
        # todo plus l'avoir


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


def process_from_array(main_folder_path, secondary_folder_list, pictures_array, InCal=None, InOri=None,
                       pictures_Ori=None):
    if InOri is not None and pictures_Ori is None:  # todo cela sous entend que l'orientation initiale fait parti de la liste, c'est un peu débile
        flist = os.listdir(InOri)
        image = ""
        for file in flist:
            if len(file) > 12 and file[:12] == "Orientation-":
                image = file[12:-4]  # todo qu'est ce que c'est moche
                break
        print(image)
        I, J = pictures_array.shape
        i = 0
        found = False
        while i < I and not found:
            j = 1
            while j < J and not found:
                if pictures_array[i, j] == image:
                    found = True
                j += 1
            i += 1
        pictures_Ori = pictures_array[i - 1, 1:]
        print(pictures_Ori)

    for line in pictures_array:
        if line[0]:
            list_path = []
            for i in range(1, len(secondary_folder_list) + 1):
                list_path.append(main_folder_path + secondary_folder_list[i - 1] + str(line[i]))

            copy_and_process(
                list_path,
                main_folder_path, InCal=InCal, InOri=InOri, pictures_Ori=pictures_Ori)


if __name__ == "__main__":
    tic = time.time()
    print("process launched")
    # main_GCP_estim("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/","DSC00918_11h30.JPG",points = 'selection-S2D.xml')
    # sort_pictures(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_ouest/",
    #              "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_mid/"])

    # array = pictures_array_from_file("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Scripts_Python/linkedFiles.txt")
    # print(check_pictures("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/", ["cam_est/","cam_ouest/","cam_mid/"], array, 1, 5))
    array = pictures_array_from_file(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/linkedFiles.txt")
    folders = ["cam_est/", "cam_ouest/", "cam_mid/"]
    main_folder_path = "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/"
    process_from_array(main_folder_path, folders, array,
                       InOri="C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/TMP_MicMac_2018-6-12_8-16/Ori-RadialStd/")
    #copy_and_process(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/Cam_est/DSC00876.JPG",
    #                  "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/Cam_ouest/DSC01977.JPG",
    #                  "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/Cam_mid/DSC03492.JPG"],
    #                 "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/",
    #                 InOri="C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/TMP_MicMac_2018-6-12_8-16/Ori-RadialStd/",
    #                pictures_Ori=['DSC00874.JPG','DSC01975.JPG','DSC03490.JPG'])
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
