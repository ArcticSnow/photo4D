# coding : utf8
import cv2 as cv
from matplotlib import pyplot as plt

method=cv.TM_CCORR_NORMED
img = cv.imread("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/DSC00918_11h30.JPG")


list_vide= []
list_vide.append(["frite",[[img,1]]])
list_vide.append(["fritebis",[[img,2]]])

for frite in list_vide:
    print(frite[0])
    print(frite[1][0][1])

#cv.imwrite("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Test_scene_blindern/Pictures/ByCam/Cam2/DSC00918_11h30_cropped.JPG", petite)


"""
fig,ax = plt.subplots(2,1)
ax[0].imshow(petite)
ax[0].set_title('sample')
ax[1].imshow(petite_ini)
ax[1].set_title('ini')
plt.show()"""