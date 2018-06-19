# coding : uft8
import cv2 as cv
import matplotlib.pyplot as plt
from skimage.feature import match_template
import numpy as np
import time
import os
import pandas as pd
import WriteMicMacFiles.WriteXml as wxml
import DetectPoints.Init_Points as ini


def create_angle_matrix(samples_position_ini):
    """
    Compute the angle matrix between samples (in rad)
    :param samples_position_ini: list like [[posX_sample, posY_sample1], [posX_sample2, posY_sample2],...]
    :return: angle matrix, the index corresponds to the id of the sample
    """
    pass


def detect_and_plot(query_image, img_scene):
    result = match_template(img_scene, query_image)
    ij = np.unravel_index(np.argmax(result), result.shape)
    print(np.argmax(result))
    print(ij)
    x, y = ij[::-1]
    print(x, y)
    print(result[y, x])
    print(result[y - 10, x - 10])

    fig = plt.figure(figsize=(8, 3))
    ax1 = plt.subplot(1, 3, 1)
    ax2 = plt.subplot(1, 3, 2)
    ax3 = plt.subplot(1, 3, 3, sharex=ax2, sharey=ax2)

    ax1.imshow(query_image, cmap=plt.cm.gray)
    ax1.set_axis_off()
    ax1.set_title('template')

    ax2.imshow(img_scene, cmap=plt.cm.gray)
    ax2.set_axis_off()
    ax2.set_title('image')
    # highlight matched region
    hcoin, wcoin = query_image.shape
    rect = plt.Rectangle((x, y), wcoin, hcoin, edgecolor='r', facecolor='none')
    ax2.add_patch(rect)

    ax3.imshow(result)
    ax3.set_axis_off()
    ax3.set_title('`match_template`\nresult')
    # highlight matched region
    ax3.autoscale(False)
    ax3.plot(x, y, 'o', markeredgecolor='r', markerfacecolor='none', markersize=10)

    plt.show()


def detect(query_image, scene_image, nb_detect=1, method=cv.TM_CCORR_NORMED, save_res=False):
    """

    :param query_images: template to match (opened with opencv for better result)
    :param scene_image: image where to run the detection (opened with opencv for better result)
    :param nb_detect: number of the maximum correlation pics to detect
    :param method: method for the open cv matching function
    :param save_res:
    :return: a list containing
    """
    result = cv.matchTemplate(scene_image, query_image, method)
    if nb_detect == 1:
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
        # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
        if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
            top_left = min_loc
        else:
            top_left = max_loc
        return top_left
    elif nb_detect > 1:
        print("not implemented yet")
        return []
    else:
        raise TypeError("Number of detection must be an integer >= 1")


def detect_folder(query_folder, folder_path):
    # collecting samples
    sample_list = np.sort(os.listdir(query_folder))
    id = 1
    list_image_sample = []
    for sample in sample_list:
        if sample.split(".")[-1].lower() == "jpg":
            path = query_folder + sample
            img_sample = cv.imread(path, 0)
            list_image_sample.append([str(id), img_sample, sample])
            id += 1

            # detection
    file_list = np.sort(os.listdir(folder_path))
    coord_list = []
    num = 0
    print("detection started")
    for filename in file_list:
        try:
            if filename.split(".")[-1].lower() == "jpg":
                path = folder_path + filename
                img_scene = cv.imread(path, 0)
                meas_list = []
                for sample in list_image_sample:
                    result = match_template(img_scene, sample[1])
                    ij = np.unravel_index(np.argmax(result), result.shape)
                    x, y = ij[::-1]
                    meas_list.append([sample[0], "{} {}".format(x, y)])
                    print("File n°{}, {}, processed for point {}\n".format(num, filename, sample[2]))

                    top_left = (x, y)
                    bottom_right = (top_left[0] + sample[1].shape[0], top_left[1] + sample[1].shape[1])
                    cv.rectangle(img_scene, top_left, bottom_right, 255, 2)
                coord_list.append([filename, meas_list])
                cv.imwrite(folder_path + filename.split(".")[0] + "_processed_Skimage_" + ".JPG", img_scene)
                num += 1
        except IndexError:
            pass
    return coord_list


def detect_folder_opencv(query_folder, folder_path, pos, dist_matrix, method=cv.TM_CCORR_NORMED, save_res=False):
    # collecting samples
    sample_list = np.sort(os.listdir(query_folder))
    id = 1
    list_image_sample = []
    for sample in sample_list:
        if sample.split(".")[-1].lower() == "jpg":
            path = query_folder + sample
            img_sample = cv.imread(path, 0)
            list_image_sample.append([str(id), img_sample, sample])
            id += 1

    # detection
    file_list = np.sort(os.listdir(folder_path))
    coord_list = []
    iter = 0
    print("detection started")
    list_tot = []
    for filename in file_list:
        try:
            if filename.split(".")[-1].lower() == "jpg":
                path = folder_path + filename
                img_scene = cv.imread(path, 0)

                eval_list = []
                meas_list = []  # list of the measures in one image
                for sample in list_image_sample:
                    print('pas sage dans la boucle for {} {}'.format(filename,sample[2]))
                    pos_ini = pos[int(sample[0])-1]
                    shift = (sample[1].shape[
                        0]) / 2  # The point of interest must be in the center of the picture, which is square shaped



                    result = cv.matchTemplate(img_scene, sample[1], method) # todo faire une boucle sur tous les samples et prendre le max de correl + boucle d'angle
                    minx, maxx, miny,maxy = int(pos_ini[0] - 2*shift),int(pos_ini[0] + 2 * shift) ,int(pos_ini[1] - 2*shift), int(pos_ini[1] + 2 * shift)
                    print("en X : {} à {}, en Y : {} à {}".format(minx,maxx,miny,maxy))
                    petite = img_scene[miny:maxy,minx:maxx]


                    # todo ceci est temporaire
                    resultb = cv.matchTemplate(petite, sample[1], method)
                    min_valb, max_valb, min_locb, max_locb = cv.minMaxLoc(resultb)

                    top_left = min_locb
                    bottom_right = (
                        top_left[0] + int(sample[1].shape[1]/4),
                        top_left[1] + int(sample[1].shape[0]/4))
                    cv.rectangle(petite, top_left, bottom_right, 255, 2)
                    cv.imwrite(folder_path + filename + "petite" + str(int(sample[0]) + 1) + ".JPG", petite)



                    if save_res:
                        cv.imwrite(folder_path + filename + "_Correlation.JPG", result)

                    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)


                    min_locb = min_locb[0] + minx,min_locb[1] + miny
                    print(str(min_loc) + "Avec la petite : " + str(min_locb))
                    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
                    if method in [cv.TM_SQDIFF, cv.TM_SQDIFF_NORMED]:
                        top_left = min_loc
                    else:
                        top_left = max_loc

                    eval_list.append((int(top_left[0] + shift), int(top_left[1] + shift)))
                    print("File n°{}, {}, processed for point {}\n".format(iter, filename, sample[2]))
                    cv.putText(img_scene, "{}, {}".format(sample[0], sample[2]), top_left, cv.FONT_HERSHEY_SIMPLEX, 2,
                               (0, 255, 255))
                for i in range(len(eval_list)):
                    somme_ecarts = 0
                    meas_list.append([i, "{} {}".format(eval_list[i][0], eval_list[i][1])])
                    for j in range(len(eval_list)):
                        distij = np.sqrt(
                            (eval_list[i][0] - eval_list[j][0]) ** 2 + (eval_list[i][1] - eval_list[j][1]) ** 2)
                        somme_ecarts += np.abs(distij - dist_matrix[i, j])

                        if i != j:
                            list_tot.append(
                                (filename, i, j, eval_list[i][0], eval_list[j][0], pos[i][0], pos[j][0],  # name + Xpos
                                 eval_list[i][1], eval_list[j][1], pos[i][1], pos[j][1],  # Ypos
                                 distij, dist_matrix[i, j]))

                        # if somme_ecarts / len(eval_list) <= 200:
                        top_left = eval_list[i]
                        bottom_right = (
                            top_left[0] + list_image_sample[i][1].shape[1],
                            top_left[1] + list_image_sample[i][1].shape[0])
                        cv.rectangle(img_scene, top_left, bottom_right, 255, 2)

                    # meas_list.append([str(i), "{} {}".format(top_left[0], top_left[1])])
                    print("ecart dans l'image {}, pour le point {} : {}".format(filename, i,
                                                                                somme_ecarts / len(eval_list)))

                coord_list.append([filename, meas_list])
                #cv.imwrite(folder_path + filename.split(".")[0] + "_detect_opencv" + ".JPG", img_scene)
                iter += 1
        except IndexError:
            pass
    return coord_list, list_tot


def detect_fMatches(query_image, img_scene):
    # Initiate ORB detector
    orb = cv.ORB_create()
    # find the keypoints and descriptors with ORB
    kp1, des1 = orb.detectAndCompute(query_image, None)
    kp2, des2 = orb.detectAndCompute(img_scene, None)

    # create BFMatcher object
    bf = cv.BFMatcher(cv.NORM_HAMMING, crossCheck=True)
    # Match descriptors.
    matches = bf.match(des1, des2)
    # Sort them in the order of their distance.
    matches = sorted(matches, key=lambda x: x.distance)
    # Draw first 10 matches.
    img3 = cv.drawMatches(query_image, kp1, img_scene, kp2, matches[:2], None, flags=0)
    plt.imshow(img3), plt.show()


if __name__ == "__main__":
    tic = time.time()

    img2 = cv.imread(
        "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Donees_Guillaume/Data/TimeLapse/Finseelvi/20170601_0602_Cam_North/Processed/DSC00846_CLAHE_RGB.JPG",
        0)  # trainImage
    if (img2 is None) or (img2 is None):
        print("One or both of the images are missing\nPlease check the path of the images")
    else:
        pos = [[958, 1719], [2678, 1276], [696, 1406], [4675, 1753], [3560, 2354]]
        dist = ini.create_dist_matrix(pos)
        list1, list2 = detect_folder_opencv(
            "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Donees_Guillaume/Data/TimeLapse/Finseelvi/20170601_0602_Cam_North/Processed/Samples/",
            "C:/Users/Alexis/Documents/Travail/Stage_Oslo/Donees_Guillaume/Data/TimeLapse/Finseelvi/20170601_0602_Cam_North/Processed/",
            pos, dist,
            method=cv.TM_CCORR_NORMED)
        wxml.write_S2D_xmlfile(list1,
                               'C:/Users/Alexis/Documents/Travail/Stage_Oslo/Scripts_Python/Stats/Appuis_fictifs-S2D.xml')
        labels = ['IMG', 'Pti', 'Ptj', 'XPti', 'XPtj', 'XRefPti', 'XRefPtj', 'YPti', 'YPtj', 'YRefPti', 'YRefPtj',
                  'Distij', 'DistRefij']
        df = pd.DataFrame.from_records(list2, columns=labels)

        df.to_csv('C:/Users/Alexis/Documents/Travail/Stage_Oslo/Scripts_Python/Stats/data_for_stat.csv', sep=',',
                  encoding='utf-8')
    toc = time.time()
    temps = abs(toc - tic)
    print("Executed in {} seconds".format(round(temps, 3)))
