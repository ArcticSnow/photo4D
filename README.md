# Photo4D: a Project to generate 4D data from time-lapse cameras

Simon Filhol (simon.filhol@geo.uio.no)

Guillaume Sutter (sutterguigui@gmail.com)

Alexis Perret (aperret2010@hotmail.fr)

## Description

This project consists of an automated program to generate point cloud from time-lapse set of images from independent cameras. The software: 
      1) sorts images by timestamps, 
      2) assess the image quality based on lumincace and bluriness, 
      3) identify automatically GCPs through the stacks of images, 
      4) run Micmac to compute point clouds, and 
      5) convert point cloud to rasters. 

The project should be based on open-source libraries, for public release. 

## Installation
1. install the latest version of [micmac](https://micmac.ensg.eu/index.php/Install)
2. install python 3.6, and with anaconda, create a virtual environment with the following packages: 
     - opencv 
     - pandas 
     - matplotlib
     - lxml
 3. clone the github repository where you want on your system
     git clone ....

## Objectives

 1. Obtain 2D snow cover extent map
 2. Derive 3D maps for pairs of time-lpase pictures
 3. improve design (targets, camera set up and settings, image preprocessing, number of camera...)
 4. Assess accuracy, precision: compare to lidar, dGPS snow-deph measurements. What paramters have the largest influence on the results
 5. try automating every steps of the algorithm, and combine scripts into one program (app)
 6. Success??!

## Use

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
