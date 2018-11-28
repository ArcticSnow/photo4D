# Photo4D: open-source time-lapse photogrammetry 

Contributors by alphabetical orders:
- Simon Filhol (simon.filhol@geo.uio.no)
- Luc Girod (luc.girod@geo.uio.no)
- Alexis Perret (aperret2010@hotmail.fr)
- Guillaume Sutter (sutterguigui@gmail.com)

## Description

This project consists of an automated program to generate point cloud from time-lapse set of images from independent cameras. The software: 
​      1) sorts images by timestamps, 
​      2) assess the image quality based on lumincace and bluriness, 
​      3) identify automatically GCPs through the stacks of images, 
​      4) run Micmac to compute point clouds, and 
​      5) convert point cloud to rasters. 

The project should be based on open-source libraries, for public release. 

## Installation
1. install the latest version of [micmac](https://micmac.ensg.eu/index.php/Install)

2. install python 3.6, and with anaconda, create a virtual environment with the following packages: 
     - opencv 
     - pandas 
     - matplotlib
     - lxml
     - pillow
     - pyxif (that needs to be downloaded from https://github.com/zenwerk/Pyxif)
     ```sh
     wget https://github.com/zenwerk/Pyxif/archive/master.zip
     unzip Pyxif-master.zip
     cd Pyxif-master
     python setup.py install
     ```

 3. The package is available via Pypi

     ```python
     pip install photo4d
     ```

## Objectives

 1. Obtain 2D snow cover extent map
 2. Derive 3D maps for pairs of time-lpase pictures
 3. improve design (targets, camera set up and settings, image preprocessing, number of camera...)
 4. Assess accuracy, precision: compare to lidar, dGPS snow-deph measurements. What paramters have the largest influence on the results
 5. try automating every steps of the algorithm, and combine scripts into one program (app)
 6. Success??!

## Use

1. prepare your environment: 
      - create a Python 3.6 virtual environment in which you install the required libraries (see above)
      - Organize your photo with one folder per camera. For instance fodler /cam1 constains all the im ages of Camera 1.
      - create a folder for the project with inside the project folder a folder called Images containing itself one folder per camera
```bash
├── Project
    └── Images
         ├── Cam1
         ├── Cam2
         ├── Cam3
         └── Cam...
```


2. Set the path correctly in the file MicmacApp/Class_photo4D.py

```python

############################################################
## Part 1

# Set Project path
myproj = Photo4d(project_path="point to project folder /Project")

# Algorithm to sort images in triplets
myproj.sort_picture()

# Algorithm to check picture quality (exposure and blurriness)
myproj.check_picture()

############################################################
## Part 2: Manual preparation for MicMac

# Provide the name of one image to set the triplet of reference
myproj.set_selected_set("DSC00857.JPG")
# myproj.selected_picture_set = -1  # by default get the last set of image. Change to the correct index where there are good quality images

# command telling Micmac to compute camera orientation for the reference set
myproj.initial_orientation()

# Open MicMac user interface to define mask of the region of interest (ROI). Select a polygon for the ROI, and exit the window. This needs to be done for each camera.
myproj.create_mask()

############################################################
## Part 3: Derive GCPS in image stack

# Point the app to the text file with the GPS locations of the GCPs in format (name, East, North, Elec)
myproj.prepare_gcp_files("C:/Users/Alexis/Documents/Travail/Stage_Oslo/Grandeurnature/GCP/Pt_gps_gcp.txt")

# Pick GCPs manually with Micmac user interface on the reference set for each camera
myproj.pick_gcp()




#=========================================================== Continue help from here
#myproj.detect_GCPs()
#myproj.extract_GCPs()
myproj.process(resol=4000)
# Part 1, sort and flag good picture set
# myproj.sort_picture()
# myproj.check_picture()

# Part 2: Manual
# choose either:
# 		- Calibration, calibration of camera (TODO)
# 		- Orientation, estimate camera position

# myproj.selected_picture_set = -1  # by default get the last set of image. Change to the correct index where there are good quality images
# myproj.oriententation_intitial()

# myproj.selected_picture_set = -1
# myproj.create_mask()

# Part 3: Derive GCPS in image stack

# myproj.prepare_GCP_files("GCPs.txt")  # format the text file to

# myproj.selected_picture_set = -1
# myproj.pick_GCP()

# myproj.detect_GCPs()

# point GCP (manual)
# estimate on stack

# Part 4: Process images to point cloud
# myproj.process()
```


[Insert here example on how to use the package]

## Strategy

1. open RAW on Python and split image between snow area and other using threshold
2. expose using histogram equalizer both masked selection
3. recombine image to run through Micmac

4. run micmac script using different parameter (number of pics, position of camera, exposition
5. estimate model error against (lidar?). Test Micmac method on a scene with no snow

## Ressources

- Micmac: http://micmac.ensg.eu/index.php/Accueil
- relevant publications saved in Google drive
- Image processing images: skimage, openCV, Pillow
- rawpy, a package to open raw images in Python: https://pypi.python.org/pypi/rawpy  http://pythonhosted.org/rawpy/api/
- python package to read exif data: https://pip.pypa.io/en/latest/user_guide/

## Development

To work on a development version and keep using the latest change install it with the following

```python
pip install -e [path2folder/pybob]
```

and to upload latest change to Pypi.org, simply:

1. change the version number in the file ```photo4d/__version__.py```
2.  run from a terminal from the photo4D folder, given your $HOME/.pyc is correctly set:

```shell
python setup.py upload
```

