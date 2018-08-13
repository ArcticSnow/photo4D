# coding:utf-8
"""

"""
from Process import process_from_array
from Utils import pictures_array_from_file

# *****
# Launching 3d reconstruction
# *****

# Mandatory arguments
# ======================================================================================================================


# list of the folders where the pictures are (1 folder is for one camera)
folders_list = ["cam1/", "Cam2/", "Cam3/"]

# the file from sort_pictures, which ordered sets by shooting time
# if you want to ignore some sets, just set the boolean to False
pictures_array = pictures_array_from_file("../linked_files.txt")

# the folder were results (point cloud and a quick recap for each set) will be saved
# temporary files and 3d reconstruction will be in this folder too
output_folder = "/Results/"

# Initial Orientation
# ======================================================================================================================

# path to the Ori folder of your initial orientation, previously computed with MicMac on a chosen pictures set
inori = "path2inori/Ori-Ini/"

# pictures used for the initial orientation, in the same order as the folders_list
# if these pictures are in pictures array, this argument can be set to None and will be automatically computed
pictures_ini = ["Set_camIni.JPG", "SetIni_cam2.JPG", "SetIni_cam3"]

# if your cameras were really motionless, you don't need to compute the orientation for each set, and re_estimate=False
# that means you don't have to detect GCP in all your pictures neither : you can skip the GCP parameters, but you will
# need to apply the MicMac GCPBascule on your initial orientation ("https://micmac.ensg.eu/index.php/GCPBascule")
re_estimate = True

# Micmac create a lot of files and folder during reconstructions, and some are really heavy, that's why all is deleted
# You can choose not to delete temporary folder the reconstruction, it can be useful for debugging
# Note that temporary folder from MicMac "Pastis", "Tmp-MM-Dir" and "Pyram" will be deleted anyway
delete_temp = True

# Initial Calibration
# ======================================================================================================================

# The initial calibration is needed only if you don't have any initial orientation
# path to the Ori folder of your initial calibration
incal = None

# Ground Control Points
# ======================================================================================================================

# The GCPs absolute coordinates, previously converted to Xml by MicMac function "GCPConvert"
gcp = "path2gcp/gcp.xml"

# the GCPs relative (image) coordinates, for all images of pictures array (this is the result of detect_from_s2d_xml() )
gcp_s2D = "path2s2d/gcp-S2D.xml"  # todo lancer detect_from_s2d_xml()

# Masks
# ======================================================================================================================

# Mask are really important if you want clean 3d models and to consequently shorten computation time
# Path to the folder containing masks from the "SaisieMasqQT" command todo verifier images_ini
# see https://micmac.ensg.eu/index.php/SaisieMasqQT
masq2d = "path2mask/"

# Other parameters
# ======================================================================================================================

# You can choose to apply a CLAHE (Contrast Limited Adaptive Histogram Equalization) on the pictures
# It is useful if there is a lot of snow on the pictures, to have a better image orientation
# about CLAHE, see "https://docs.opencv.org/3.1.0/d5/daf/tutorial_py_histogram_equalization.html"
clahe = False

# If you want to display the log from MicMac or hide it
display_micmac = True


# you can a condition on the date, to reconstruct only set which match this condition
# this parameter is a function, which return a boolean and take a datetime object as parameter
def condition(date):
    # use only set taken at 11h
    return date.hour == 11
cond = condition

# index of the master folder in folder list (from 0 to len(folders_list) )
# The master folder correspond to the "middle" camera, the one which see the more of the scene
# the pictures of this folder will be used as master image for the "Malt GeomImage" command
master_folder = 1

# MicMac parameters
# ======================================================================================================================
# for all these parameters, a more complete description is available on the MicMac wiki

# size of the images for the searching of tie points, it corresponds to the length of the longest side of the image (px)
# a value around 0.5 * side is recommended, however if you have only a few cameras (3), full resolution should helps
# -1 stands for full resolution , see "https://micmac.ensg.eu/index.php/Tapioca"
resol = -1

# distortion model used for the orientation of the images, each model compute different parameters
# "Fraser" and "RadialStd" are the most used, see the complete list here : "https://micmac.ensg.eu/index.php/Tapas"
# If you have a good intial orientation, use "Figee", to prevent MicMac from computing the calibration for each set
distortion_model = "Figee"

# Correlation in un correlated pixels # todo luc lexpliquera mieux
# the default value is 0.2
DefCor = 0.0

# if your coordinates are absolute, the numbers became too big for the .ply storage on 32 Bits and you lose accuracy
# to counter this effect it is possible to apply a shift to this coordinates, while writing the point cloud
shift = [300000, 5000000, 0]

process_from_array(folders_list, pictures_array, output_folder, incal=None, inori=inori,
                   pictures_ini=pictures_ini, gcp=gcp, gcp_S2D=gcp_s2D,
                   clahe=clahe, resol=resol,
                   distortion_model=distortion_model,
                   re_estimate=re_estimate, master_folder=master_folder, masq2D=masq2d, DefCor=DefCor, shift=shift,
                   delete_temp=delete_temp,
                   display_micmac=display_micmac, cond=cond)
