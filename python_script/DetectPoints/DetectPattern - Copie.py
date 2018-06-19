# coding : uft8
import cv2 as cv
import numpy as np
import time
import os
import WriteMicMacFiles.WriteXml as wxml
import DetectPoints.Init_Points as ini


def detect_folder_opencv(query_folder, folder_path, pos, dist_matrix, method=cv.TM_CCORR_NORMED, save_res=False,
                         ext_files="jpg"):
    """

    :param query_folder:
    :param folder_path:
    :param pos: list of positions of samples in one image [[posX_samp1, posY_samp1] , [posX_samp2, posY_samp2] , ... ]
                The order must be the same as sample files in query_folder !!!
    :param dist_matrix:
    :param method: opencv method for template matching function, see opencv documentation
    :param save_res:
    :param ext_files:
    :return:
    """
    # collect samples
    sample_list = np.sort(os.listdir(query_folder))

    list_image_sample = []
    for i in range(len(sample_list)):

        sample = sample_list[i]
        try:
            if sample.split(".")[-1].lower() == ext_files:
                path = query_folder + sample
                img_sample = cv.imread(path, 0)
                list_image_sample.append([sample,[(
                    img_sample, pos[i])]])  # Stores the name of the file, and the first opencv image, others will be added during detection
        except IndexError :
            print("The position list does not fit the number of samples in " + query_folder)
            exit()
    # detection
    file_list = np.sort(os.listdir(folder_path))
    print("detection started")
    list_tot = []
    for filename in file_list:
        try:
            if filename.split(".")[-1].lower() == ext_files:
                path = folder_path + filename
                img_scene = cv.imread(path, 0)

                for i in range(len(list_image_sample)):
                    sample_name = list_image_sample[i][0]
                    sample_pictures = list_image_sample[i][1]

                    # loop on every image selected for a given ground point/sample
                    list_correl = [] # stores the values of correlation for the all the images for one sample
                    iter =0
                    for one_picture in sample_pictures:
                        image = one_picture[0]
                        sample_size = image.shape[0]
                        pos_ini = one_picture[1]
                        shift = (sample_size) / 2  # The point of interest must be in the center of the picture, which is square shaped

                        # we assume that there is no such a big move between this scene_image and the previous,
                        # so we can restrain research area near the other positions (all scene images must have the same size)
                        minx, maxx, miny, maxy = int(pos_ini[0] - 2 * shift), int(pos_ini[0] + 2 * shift), int(
                            pos_ini[1] - 2 * shift), int(pos_ini[1] + 2 * shift)

                        result = cv.matchTemplate(img_scene[miny:maxy, minx:maxx], image, method)
                        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
                        if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
                            list_correl.append((min_val,min_loc))
                        else:
                            list_correl.append((max_val,max_loc))

                    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
                    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
                        min = list_correl[0][0]
                        min_loc = list_correl[0][1]
                        for elem in list_correl:
                            if elem[0] < min:
                                min = elem[0]
                                min_loc = elem[1]
                        top_left = min_loc
                    else:
                        max = list_correl[0][0]
                        max_loc = list_correl[0][1]
                        for elem in list_correl:
                            if elem[0] > max:
                                max = elem[0]
                                max_loc = elem[1]
                        top_left = max_loc

                    top_left = top_left[0] + minx , top_left[1] + miny

                    if save_res:
                        bottom_right = (top_left[0] + sample_size, top_left[1] + sample_size)
                        cv.rectangle(img_scene, top_left, bottom_right, 255, 2)  # emprise du sample, au pic de correlation
                        cv.rectangle(img_scene, (minx,miny),(maxx,maxy), 255, 2) # emprise de la recherche
                        cv.putText(img_scene, "{}, {}".format(iter, sample_name), top_left, cv.FONT_HERSHEY_SIMPLEX,
                                    2,
                                    (0, 255, 255))
                        cv.imwrite(path + filename + "detect.jpg", img_scene)

                    new_pos = (int(top_left[0] + sample_size/2), int(top_left[1] + sample_size/2))
                    print("File n°{}, {}, processed for point {}".format(iter, filename, sample_name))
                    print("Difference between the initial position and the detected one : horizontally: {} vertically: {}\nn ".format(abs(pos_ini[0] - new_pos[0]),abs(pos_ini[1] - new_pos[1])))
                    iter +=1

        except IndexError:
            pass


if __name__ == "__main__":
    tic = time.time()
    pos = [(2970,1770), (2405, 1234), (781,1669),(820, 2785)]
    dist = ini.create_dist_matrix(pos)
    list = detect_folder_opencv(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/Samples/",
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/",
        pos, dist,
        cv.TM_CCORR_NORMED,save_res=False)
    # wxml.write_S2D_xmlfile(list, 'C:/Users/Alexis/Documents/Travail/Stage_Oslo/Donees_Guillaume/Data/TimeLapse/Finseelvi/20170601_0602_Cam_North/Processed/Temp/Appuis_fictifs-S2D.xml')

    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
