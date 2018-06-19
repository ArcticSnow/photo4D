# coding : utf8

import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import os
from pictures_process.Handle_Exif import load_lum


def detect_snow(image):
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    shape = gray_image.shape

    result = cv.inRange(gray_image, 150, 255)

    image = cv.cvtColor(image, cv.COLOR_BGR2LAB)
    value = cv.split(image)[0]
    print(value)
    # value = np.array([image[:,:,2]])
    average = cv.mean(value)
    print(average[0])
    plt.imshow(result)
    # plt.show()


def lum(filename):
    image_bgr = cv.imread(filename)
    image_lab = cv.cvtColor(image_bgr, cv.COLOR_BGR2LAB)
    average_lum = cv.mean(cv.split(image_lab)[0])
    return average_lum


def blurr(filename,ksize = 3):
    image_bgr = cv.imread(filename)  # todo la converstion en gray devrait être fait à cette ligne
    # image_gray = cv.cvtColor(image_bgr, cv.COLOR_BGR2GRAY)
    return np.log(cv.Laplacian(image_bgr, cv.CV_64F,ksize=ksize).var())


def plot_lum(folder_path, image_ext="jpg"):
    i = 0
    file_list = np.sort(os.listdir(folder_path[0]))
    fig, ax = plt.subplots(2, 1)
    ax[0].set_title('Average luminosity of the picture')
    ax[1].set_title('Brightness from metadata')
    for filename in file_list:
        try:
            if filename.split(".")[-1].lower() == image_ext:
                path = folder_path[0] + filename
                print(path)
                mean = lum(path)

                ax[0].plot(i, mean[0], 'bo')
                try:
                    ax[1].plot(i, load_lum(path), 'bo')
                except ValueError:
                    pass
                i += 1
        except IndexError:
            pass

    plt.show()


def plot_blurr(folder_path, image_ext='jpg'):

    i = 0
    file_list = np.sort(os.listdir(folder_path[0]))
    log = open(folder_path[0] + 'log.txt', 'w')
    for filename in file_list:
        try:
            if filename.split(".")[-1].lower() == image_ext:
                path = folder_path[0] + filename
                print(path)
                i_blurr = blurr(path)
                log.write("{} : {}\n".format(filename, i_blurr))
                plt.plot(i, i_blurr, 'bo')
                i += 1
        except IndexError:
            pass
    log.close()
    # i = 0
    # file_list = np.sort(os.listdir(folder_path[1]))
    # for filename in file_list:
    #     try:
    #         if filename.split(".")[-1].lower() == image_ext:
    #             path = folder_path[1] + filename
    #             print(path)
    #             i_blurr = blurr(path)
    #             plt.plot(i, i_blurr, 'go')
    #             i += 1
    #     except IndexError:
    #         pass
    # i = 0
    # file_list = np.sort(os.listdir(folder_path[2]))
    # for filename in file_list:
    #     try:
    #         if filename.split(".")[-1].lower() == image_ext:
    #             path = folder_path[2] + filename
    #             print(path)
    #             i_blurr = blurr(path)
    #             plt.plot(i, i_blurr, 'ro')
    #             i += 1
    #     except IndexError:
    #         pass
    plt.show()


if __name__ == "__main__":
    print("process lanched")
    #img = cv.imread("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/DSC00853.JPG")
    #lum("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/cam_est/DSC00853.JPG")

    plot_blurr(["C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeur nature/Pictures/Cam_est/"])
